"""Who may do what. Plans (INR): Free (score + verdict preview, limited runs),
Report (Rs 299 one-time per analysis: full report), Pro (Rs 999/month: everything).
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from db.product import Analysis, Subscription

PRO_FEATURES = {"chat", "integrations", "experiments", "export"}
RUNS_PER_HOUR = 6  # abuse guard, applies to everyone


def paywall(feature: str, message: str) -> HTTPException:
    """402 with a machine-readable body the UI turns into an upgrade prompt."""
    return HTTPException(402, detail={"code": "upgrade_required", "feature": feature, "message": message})


async def is_pro(db: AsyncSession, user_id: uuid.UUID) -> bool:
    sub = await db.get(Subscription, user_id)
    if sub is None or sub.status not in ("active", "cancelled"):
        return False
    end = sub.current_period_end
    if end is None:
        return False
    if end.tzinfo is None:  # SQLite returns naive datetimes
        end = end.replace(tzinfo=timezone.utc)
    return end > datetime.now(timezone.utc)  # a cancelled sub stays Pro until the period ends


async def require_pro(db: AsyncSession, user_id: uuid.UUID, feature: str) -> None:
    if not await is_pro(db, user_id):
        raise paywall(feature, f"{feature.capitalize()} is part of Pro (Rs {get_settings().PRICE_PRO_PAISE // 100}/month).")


async def analyses_used(db: AsyncSession, user_id: uuid.UUID) -> int:
    q = select(func.count()).select_from(Analysis).where(
        Analysis.owner_id == user_id, Analysis.status.in_(("running", "complete"))
    )
    return (await db.execute(q)).scalar_one()


async def check_can_start(db: AsyncSession, user_id: uuid.UUID) -> None:
    s = get_settings()
    if not await is_pro(db, user_id) and await analyses_used(db, user_id) >= s.FREE_ANALYSES:
        raise paywall("analysis", f"You have used your {s.FREE_ANALYSES} free analyses. Go Pro for unlimited.")
    last_hour = (await db.execute(
        select(func.count()).select_from(Analysis).where(
            Analysis.owner_id == user_id, Analysis.created_at >= datetime.now(timezone.utc) - timedelta(hours=1)
        )
    )).scalar_one()
    if last_hour >= RUNS_PER_HOUR:
        raise HTTPException(429, "Too many analyses in the last hour. Try again later.")


LOCKED_CREWS_NOTE = "Full report: all 13 crews, evidence ledger, sources, debate, roadmap and exports."


def redact(result: dict[str, Any] | None) -> dict[str, Any] | None:
    """Free preview: score, verdict label + rationale, summary and per-crew scores only."""
    if not result:
        return result
    verdict = result.get("verdict") or {}
    keep = (
        "project_id", "idea_text", "status", "mode", "ai_generated", "overall_readiness_score",
        "score_range", "confidence", "executive_summary", "crew_scores", "grounding",
    )
    out = {k: result[k] for k in keep if k in result}
    out["verdict"] = {"label": verdict.get("label"), "rationale": verdict.get("rationale")} if verdict else None
    out["locked"] = True
    out["locked_note"] = LOCKED_CREWS_NOTE
    return out
