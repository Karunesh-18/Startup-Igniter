"""Billing in rupees via Razorpay.

  GET  /billing/me                   plan, usage, prices, public key id
  POST /billing/report-order         one-time Rs 299 order to unlock one analysis's full report
  POST /billing/subscribe            Pro subscription (Rs 999/month)
  POST /billing/verify               verify the Checkout signature, then grant access immediately
  POST /billing/cancel               cancel Pro at the end of the paid period
  POST /billing/webhook              Razorpay -> us (source of truth; idempotent)
  POST /billing/dev-activate         simulated payment, only with BILLING_DEV_MODE and never in production
  GET  /billing/payments             payment history

Amounts are integers in paise. Prices include GST.
"""

import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select

from api.deps import DB
from core.auth import CurrentPrincipal
from core.config import get_settings
from core.logging import get_logger
from db.product import Analysis, Payment, Subscription, WebhookEvent
from services.entitlements import analyses_used, is_pro

logger = get_logger(__name__)
router = APIRouter(prefix="/billing", tags=["Billing"])
API = "https://api.razorpay.com/v1"


# ── Razorpay client (httpx; no SDK needed) ────────────────────────────────────


def _configured() -> bool:
    s = get_settings()
    return bool(s.RAZORPAY_KEY_ID and s.RAZORPAY_KEY_SECRET)


async def _rz(method: str, path: str, body: dict | None = None) -> dict[str, Any]:
    s = get_settings()
    if not _configured():
        raise HTTPException(503, "Payments are not configured on this server.")
    async with httpx.AsyncClient(auth=(s.RAZORPAY_KEY_ID, s.RAZORPAY_KEY_SECRET), timeout=20) as c:
        r = await c.request(method, f"{API}{path}", json=body)
    if r.status_code >= 400:
        logger.warning("razorpay_error", status=r.status_code, body=r.text[:300])
        raise HTTPException(502, "The payment provider rejected the request.")
    return r.json()


def _sign(message: str, secret: str) -> str:
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()


def _eq(a: str, b: str) -> bool:
    return hmac.compare_digest(a or "", b or "")


async def _pro_plan_id() -> str:
    s = get_settings()
    if s.RAZORPAY_PLAN_PRO_ID:
        return s.RAZORPAY_PLAN_PRO_ID
    plan = await _rz("POST", "/plans", {
        "period": "monthly", "interval": 1,
        "item": {"name": "Startup Igniter Pro", "amount": s.PRICE_PRO_PAISE, "currency": "INR",
                 "description": "Unlimited analyses, AI co-founder chat, integrations, exports"},
    })
    s.RAZORPAY_PLAN_PRO_ID = plan["id"]  # cached for this process; set RAZORPAY_PLAN_PRO_ID to persist
    return plan["id"]


# ── State changes (shared by verify, webhook and dev-activate) ────────────────


async def _grant_report(db: DB, payment: Payment, payment_id: str | None) -> None:
    if payment.status == "paid":
        return
    payment.status, payment.paid_at = "paid", datetime.now(timezone.utc)
    payment.razorpay_payment_id = payment_id or payment.razorpay_payment_id
    if payment.analysis_id and (a := await db.get(Analysis, payment.analysis_id)):
        a.unlocked = True


async def _apply_subscription(db: DB, owner_id: uuid.UUID, entity: dict[str, Any]) -> None:
    sub = await db.get(Subscription, owner_id)
    if sub is None:
        sub = Subscription(owner_id=owner_id)
        db.add(sub)
    status = entity.get("status", "created")
    sub.razorpay_subscription_id = entity.get("id", sub.razorpay_subscription_id)
    sub.status = "active" if status in ("active", "authenticated") else \
        "cancelled" if status in ("cancelled", "completed") else "halted" if status in ("halted", "paused") else status
    if end := entity.get("current_end"):
        sub.current_period_end = datetime.fromtimestamp(end, tz=timezone.utc)


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/me")
async def me(db: DB, who: CurrentPrincipal) -> dict[str, Any]:
    s = get_settings()
    sub = await db.get(Subscription, who.id)
    pro = await is_pro(db, who.id)
    return {
        "plan": "pro" if pro else "free",
        "pro_until": sub.current_period_end if sub and pro else None,
        "cancelling": bool(sub and sub.status == "cancelled" and pro),
        "analyses_used": await analyses_used(db, who.id),
        "free_limit": s.FREE_ANALYSES,
        "prices": {"report_paise": s.PRICE_REPORT_PAISE, "pro_paise": s.PRICE_PRO_PAISE, "currency": "INR"},
        "razorpay_key_id": s.RAZORPAY_KEY_ID or None,
        "payments_enabled": _configured(),
        "dev_mode": s.BILLING_DEV_MODE and not s.is_production,
    }


class ReportOrderIn(BaseModel):
    analysis_id: uuid.UUID


@router.post("/report-order")
async def report_order(body: ReportOrderIn, db: DB, who: CurrentPrincipal) -> dict[str, Any]:
    a = await db.get(Analysis, body.analysis_id)
    if a is None or a.owner_id != who.id or a.status != "complete":
        raise HTTPException(404, "Analysis not found.")
    if a.unlocked:
        raise HTTPException(409, "This report is already unlocked.")
    s = get_settings()
    order = await _rz("POST", "/orders", {
        "amount": s.PRICE_REPORT_PAISE, "currency": "INR", "receipt": f"rpt-{a.id.hex[:24]}",
        "notes": {"kind": "report", "analysis_id": str(a.id), "owner_id": str(who.id)},
    })
    db.add(Payment(owner_id=who.id, kind="report", analysis_id=a.id, amount_paise=s.PRICE_REPORT_PAISE,
                   razorpay_order_id=order["id"]))
    await db.commit()
    return {"order_id": order["id"], "amount": s.PRICE_REPORT_PAISE, "currency": "INR", "key_id": s.RAZORPAY_KEY_ID}


@router.post("/subscribe")
async def subscribe(db: DB, who: CurrentPrincipal) -> dict[str, Any]:
    if await is_pro(db, who.id):
        raise HTTPException(409, "You are already on Pro.")
    s = get_settings()
    sub = await _rz("POST", "/subscriptions", {
        "plan_id": await _pro_plan_id(), "total_count": 120, "customer_notify": 1,
        "notes": {"kind": "pro", "owner_id": str(who.id)},
    })
    row = await db.get(Subscription, who.id)
    if row is None:
        db.add(Subscription(owner_id=who.id, status="created", razorpay_subscription_id=sub["id"]))
    else:
        row.razorpay_subscription_id, row.status = sub["id"], "created"
    await db.commit()
    return {"subscription_id": sub["id"], "key_id": s.RAZORPAY_KEY_ID, "amount": s.PRICE_PRO_PAISE, "currency": "INR"}


class VerifyIn(BaseModel):
    razorpay_payment_id: str
    razorpay_signature: str
    razorpay_order_id: str | None = None
    razorpay_subscription_id: str | None = None


@router.post("/verify")
async def verify(body: VerifyIn, db: DB, who: CurrentPrincipal) -> dict[str, Any]:
    secret = get_settings().RAZORPAY_KEY_SECRET
    if body.razorpay_order_id:
        if not _eq(_sign(f"{body.razorpay_order_id}|{body.razorpay_payment_id}", secret), body.razorpay_signature):
            raise HTTPException(400, "Invalid payment signature.")
        p = (await db.execute(select(Payment).where(
            Payment.razorpay_order_id == body.razorpay_order_id, Payment.owner_id == who.id))).scalar_one_or_none()
        if p is None:
            raise HTTPException(404, "Order not found.")
        await _grant_report(db, p, body.razorpay_payment_id)
    elif body.razorpay_subscription_id:
        if not _eq(_sign(f"{body.razorpay_payment_id}|{body.razorpay_subscription_id}", secret), body.razorpay_signature):
            raise HTTPException(400, "Invalid payment signature.")
        row = await db.get(Subscription, who.id)
        if row is None or row.razorpay_subscription_id != body.razorpay_subscription_id:
            raise HTTPException(404, "Subscription not found.")
        await _apply_subscription(db, who.id, await _rz("GET", f"/subscriptions/{body.razorpay_subscription_id}"))
    else:
        raise HTTPException(422, "order id or subscription id required.")
    await db.commit()
    return {"ok": True, "plan": "pro" if await is_pro(db, who.id) else "free"}


@router.post("/cancel")
async def cancel(db: DB, who: CurrentPrincipal) -> dict[str, Any]:
    row = await db.get(Subscription, who.id)
    if row is None or not row.razorpay_subscription_id or not await is_pro(db, who.id):
        raise HTTPException(404, "No active subscription.")
    if _configured():
        await _rz("POST", f"/subscriptions/{row.razorpay_subscription_id}/cancel", {"cancel_at_cycle_end": 1})
    row.status = "cancelled"  # Pro continues until current_period_end
    await db.commit()
    return {"ok": True, "pro_until": row.current_period_end}


@router.get("/payments")
async def payments(db: DB, who: CurrentPrincipal) -> list[dict[str, Any]]:
    rows = (await db.execute(select(Payment).where(Payment.owner_id == who.id).order_by(Payment.created_at.desc()))).scalars().all()
    return [{"id": str(p.id), "kind": p.kind, "amount_paise": p.amount_paise, "currency": p.currency,
             "status": p.status, "analysis_id": str(p.analysis_id) if p.analysis_id else None,
             "created_at": p.created_at, "paid_at": p.paid_at} for p in rows]


@router.post("/webhook", include_in_schema=False)
async def webhook(request: Request, db: DB) -> dict[str, bool]:
    raw = await request.body()
    secret = get_settings().RAZORPAY_WEBHOOK_SECRET
    if not secret or not _eq(_sign(raw.decode(), secret), request.headers.get("x-razorpay-signature", "")):
        raise HTTPException(400, "Bad signature.")
    event_id = request.headers.get("x-razorpay-event-id") or hashlib.sha256(raw).hexdigest()
    if await db.get(WebhookEvent, event_id):
        return {"ok": True}  # already processed
    db.add(WebhookEvent(id=event_id))
    event = json.loads(raw)
    payload = event.get("payload", {})
    kind = event.get("event", "")
    if kind in ("payment.captured", "order.paid"):
        pay = payload.get("payment", {}).get("entity", {})
        order_id = pay.get("order_id") or payload.get("order", {}).get("entity", {}).get("id")
        p = (await db.execute(select(Payment).where(Payment.razorpay_order_id == order_id))).scalar_one_or_none() if order_id else None
        if p:
            await _grant_report(db, p, pay.get("id"))
    elif kind.startswith("subscription."):
        ent = payload.get("subscription", {}).get("entity", {})
        owner = (ent.get("notes") or {}).get("owner_id")
        if owner:
            await _apply_subscription(db, uuid.UUID(owner), ent)
    await db.commit()
    return {"ok": True}


class DevActivateIn(BaseModel):
    kind: Literal["report", "pro"]
    analysis_id: uuid.UUID | None = None


@router.post("/dev-activate")
async def dev_activate(body: DevActivateIn, db: DB, who: CurrentPrincipal) -> dict[str, Any]:
    s = get_settings()
    if not s.BILLING_DEV_MODE or s.is_production:
        raise HTTPException(404, "Not found.")
    if body.kind == "report":
        a = await db.get(Analysis, body.analysis_id) if body.analysis_id else None
        if a is None or a.owner_id != who.id:
            raise HTTPException(404, "Analysis not found.")
        p = Payment(owner_id=who.id, kind="report", analysis_id=a.id, amount_paise=s.PRICE_REPORT_PAISE,
                    razorpay_order_id=f"dev_order_{uuid.uuid4().hex[:12]}")
        db.add(p)
        await _grant_report(db, p, f"dev_pay_{uuid.uuid4().hex[:12]}")
    else:
        row = await db.get(Subscription, who.id)
        if row is None:
            row = Subscription(owner_id=who.id)
            db.add(row)
        row.status, row.current_period_end = "active", datetime.fromtimestamp(time.time() + 30 * 86400, tz=timezone.utc)
        row.razorpay_subscription_id = f"dev_sub_{uuid.uuid4().hex[:12]}"
    await db.commit()
    return {"ok": True}
