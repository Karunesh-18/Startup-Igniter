"""Ideas, analyses, paywall, billing webhooks, chat and integrations (SQLite, pipeline stubbed)."""

import asyncio
import hashlib
import hmac
import json
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from api.main import app
from core.config import get_settings
from core.security import create_access_token
from services import runner
from tests.conftest import TestSessionFactory

PAYLOAD = {
    "project_id": "x", "idea_text": "t", "status": "success", "ai_generated": True, "mode": "live",
    "overall_readiness_score": 72.5, "score_range": {"low": 60, "high": 80}, "confidence": 70,
    "verdict": {"label": "pivot", "rationale": "Core need is real.", "would_change_my_mind": ["a"], "pivot_suggestions": []},
    "grounding": {"score": 60.0, "claims": 5, "contradicted": 0, "sources": 9},
    "ledger": [], "sources": [], "signals": {}, "crew_scores": {"idea_validation": 70},
    "hypotheses": [{"hypothesis": "Users pay Rs 500", "metric": ">5% convert"}],
    "executive_summary": "Summary.", "strategic_recommendations": ["Do X"],
    "market_research": {"overall_market_score": 70},
    "skeptic": {"top_risks": [{"risk": "Churn", "likelihood": 60, "impact": 70, "mitigation": "Onboarding"}]},
    "product_development": {"mvp_features": [{"feature_name": "Login", "description": "d", "priority": "Must Have", "complexity": "Low"}]},
}


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "BILLING_DEV_MODE", True)
    monkeypatch.setattr(s, "RAZORPAY_WEBHOOK_SECRET", "whsec_test")
    monkeypatch.setattr(s, "RAZORPAY_KEY_SECRET", "key_secret")
    monkeypatch.setattr(runner, "session_factory", lambda: TestSessionFactory)

    def fake_pipeline(idea_text, project_id, mock=False, github_repo=None, emit=lambda e: None, should_stop=lambda: False):
        emit({"type": "crew_complete", "crew": "idea_validation", "label": "Idea Validation", "result": {"x": 1}})
        return {**PAYLOAD, "idea_text": idea_text, "project_id": project_id}

    monkeypatch.setattr("ai.pipeline.run_pipeline", fake_pipeline)


@pytest_asyncio.fixture
async def c(db):
    from api.deps import get_db

    async def override():
        yield db

    app.dependency_overrides[get_db] = override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


def user() -> dict:
    uid = uuid.uuid4()
    return {"id": uid, "h": {"Authorization": f"Bearer {create_access_token(uid)}"}}


IDEA = {"idea_text": "A marketplace that connects home cooks with office workers for lunch."}


async def run_analysis(c, u, idea_id) -> str:
    r = await c.post(f"/api/v1/ideas/{idea_id}/analyses", headers=u["h"])
    assert r.status_code == 202, r.text
    aid = r.json()["analysis_id"]
    for _ in range(50):
        g = await c.get(f"/api/v1/analyses/{aid}", headers=u["h"])
        if g.json()["status"] != "running":
            return aid
        await asyncio.sleep(0.1)
    raise AssertionError("analysis never finished")


@pytest.mark.asyncio
async def test_requires_valid_token(c):
    assert (await c.get("/api/v1/ideas")).status_code == 401
    forged = "eyJhbGciOiJub25lIn0.eyJzdWIiOiIxMTExMTExMS0xMTExLTExMTEtMTExMS0xMTExMTExMTExMTEifQ."
    assert (await c.get("/api/v1/ideas", headers={"Authorization": f"Bearer {forged}"})).status_code == 401


@pytest.mark.asyncio
async def test_ideas_are_private(c):
    a, b = user(), user()
    idea = (await c.post("/api/v1/ideas", json=IDEA, headers=a["h"])).json()
    assert idea["title"].startswith("A marketplace")
    assert len((await c.get("/api/v1/ideas", headers=a["h"])).json()) == 1
    assert (await c.get("/api/v1/ideas", headers=b["h"])).json() == []
    assert (await c.get(f"/api/v1/ideas/{idea['id']}", headers=b["h"])).status_code == 404
    assert (await c.delete(f"/api/v1/ideas/{idea['id']}", headers=b["h"])).status_code == 404
    assert (await c.post("/api/v1/ideas", json={"idea_text": "short"}, headers=a["h"])).status_code == 422


@pytest.mark.asyncio
async def test_free_preview_is_redacted_and_quota_enforced(c):
    u = user()
    idea = (await c.post("/api/v1/ideas", json=IDEA, headers=u["h"])).json()
    for _ in range(get_settings().FREE_ANALYSES):
        aid = await run_analysis(c, u, idea["id"])
    body = (await c.get(f"/api/v1/analyses/{aid}", headers=u["h"])).json()
    assert body["result"]["locked"] is True and body["result"]["verdict"]["label"] == "pivot"
    assert "market_research" not in body["result"] and "ledger" not in body["result"]
    blocked = await c.post(f"/api/v1/ideas/{idea['id']}/analyses", headers=u["h"])
    assert blocked.status_code == 402 and blocked.json()["detail"]["code"] == "upgrade_required"


@pytest.mark.asyncio
async def test_report_purchase_unlocks_via_webhook(c):
    u = user()
    idea = (await c.post("/api/v1/ideas", json=IDEA, headers=u["h"])).json()
    aid = await run_analysis(c, u, idea["id"])
    assert (await c.get(f"/api/v1/analyses/{aid}/export", headers=u["h"])).status_code == 402

    # Simulate an order created by /billing/report-order, then Razorpay's webhook.
    from db.product import Payment

    order = f"order_{uuid.uuid4().hex[:10]}"
    async with TestSessionFactory() as s:
        s.add(Payment(owner_id=u["id"], kind="report", analysis_id=uuid.UUID(aid), amount_paise=29900, razorpay_order_id=order))
        await s.commit()
    event = json.dumps({"event": "order.paid", "payload": {"payment": {"entity": {"id": "pay_1", "order_id": order}}}})
    sig = hmac.new(b"whsec_test", event.encode(), hashlib.sha256).hexdigest()
    hdr = {"x-razorpay-signature": sig, "x-razorpay-event-id": "evt_1" + order}
    bad = await c.post("/api/v1/billing/webhook", content=event, headers={**hdr, "x-razorpay-signature": "0" * 64})
    assert bad.status_code == 400
    assert (await c.post("/api/v1/billing/webhook", content=event, headers=hdr)).status_code == 200
    assert (await c.post("/api/v1/billing/webhook", content=event, headers=hdr)).status_code == 200  # idempotent

    full = (await c.get(f"/api/v1/analyses/{aid}", headers=u["h"])).json()
    assert full["unlocked"] and "market_research" in full["result"]
    md = await c.get(f"/api/v1/analyses/{aid}/export?format=md", headers=u["h"])
    assert md.status_code == 200 and "Verdict: PIVOT" in md.text


@pytest.mark.asyncio
async def test_verify_checks_signature(c):
    u = user()
    r = await c.post("/api/v1/billing/verify", headers=u["h"], json={
        "razorpay_payment_id": "pay_x", "razorpay_order_id": "order_x", "razorpay_signature": "nope"})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_pro_unlocks_chat_experiments_and_integrations(c, monkeypatch):
    u = user()
    idea = (await c.post("/api/v1/ideas", json=IDEA, headers=u["h"])).json()
    aid = await run_analysis(c, u, idea["id"])
    for method, path in (("post", f"/api/v1/ideas/{idea['id']}/chat"),
                         ("post", f"/api/v1/ideas/{idea['id']}/experiments/seed"),
                         ("put", "/api/v1/integrations/github")):
        r = await getattr(c, method)(path, headers=u["h"], json={"message": "hi", "token": "x" * 12})
        assert r.status_code == 402, path

    assert (await c.post("/api/v1/billing/dev-activate", json={"kind": "pro"}, headers=u["h"])).status_code == 200
    assert (await c.get("/api/v1/billing/me", headers=u["h"])).json()["plan"] == "pro"
    assert (await c.get(f"/api/v1/analyses/{aid}", headers=u["h"])).json()["unlocked"] is True

    seeded = await c.post(f"/api/v1/ideas/{idea['id']}/experiments/seed", headers=u["h"])
    assert [e["hypothesis"] for e in seeded.json()] == ["Users pay Rs 500"]
    assert (await c.post(f"/api/v1/ideas/{idea['id']}/experiments/seed", headers=u["h"])).json() == []

    # SSRF guard on user-supplied webhook URLs
    for url in ("https://localhost/hook", "http://example.com/hook", "https://127.0.0.1/x"):
        r = await c.put("/api/v1/integrations/webhook", json={"token": url}, headers=u["h"])
        assert r.status_code == 422, url

    preview = await c.post(f"/api/v1/analyses/{aid}/push/github", json={"repo": "me/app"}, headers=u["h"])
    titles = [i["title"] for i in preview.json()["issues"]]
    assert preview.json()["dry_run"] and "[MVP] Login" in titles and any(t.startswith("[Risk]") for t in titles)

    monkeypatch.setattr("ai.llm.chat.stream_chat", lambda messages, **k: iter(["Hello ", "founder."]))
    monkeypatch.setattr("api.routers.chat._revise", lambda idea, u_, r: {"title": "T", "idea_text": "New idea text here", "changes": ["x"]})
    r = await c.post(f"/api/v1/ideas/{idea['id']}/chat", json={"message": "Target students instead"}, headers=u["h"])
    events = [json.loads(line) for line in r.text.splitlines()]
    assert [e["type"] for e in events] == ["delta", "delta", "message"]
    msg = events[-1]["message"]
    assert msg["content"] == "Hello founder." and msg["proposal_status"] == "pending"

    done = await c.post(f"/api/v1/chat/messages/{msg['id']}/proposal", json={"action": "accept"}, headers=u["h"])
    assert done.json()["idea"]["idea_text"] == "New idea text here"
    assert (await c.get(f"/api/v1/ideas/{idea['id']}", headers=u["h"])).json()["idea_text"] == "New idea text here"
    assert len((await c.get(f"/api/v1/ideas/{idea['id']}/chat", headers=u["h"])).json()) == 2
