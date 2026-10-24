"""Digest, evidence ledger and pipeline (offline: stub gateway, mock crews)."""

from ai.evidence.ledger import ClaimCheck, ClaimItem, ClaimList, best_passages, build_ledger, _passages
from ai.evidence.sources import SourcePool
from ai.pipeline import CREW_LABELS, run_pipeline
from ai.shared.digest import crew_confidence, crew_score, digest_crew, pct


def test_pct_and_crew_score_scales():
    assert pct(0.8, "confidence_score") == 80 and pct(7, "technical_score") == 7  # no magnitude guessing
    r = {"overall_market_score": 64.0, "technical_feasibility_score": 10, "confidence_score": 0.5}
    assert crew_score(r) == 64.0 and crew_confidence(r) == 50.0
    assert crew_score({"a_score": 10, "b_score": 30, "confidence_score": 0.9}) == 20.0


def test_digest_keeps_late_fields_and_respects_budget():
    big = {"summary": "S" * 50, "items": [f"item {i}" for i in range(50)], "z_last_score": 77, "notes": "N" * 5000}
    d = digest_crew("x", big, budget=600)
    assert len(d) <= 600 and "z_last_score" in d or "S" * 50 in d
    assert d.startswith("x [score")


class StubGateway:
    """Claims about the market are in the source; the revenue claim is not."""

    def invoke_structured(self, *, schema_class, user_prompt, **_):
        if schema_class is ClaimList:
            return ClaimList(claims=[
                ClaimItem(claim="The Indian tiffin market is worth 1,200 crore rupees.", kind="external_fact"),
                ClaimItem(claim="Customers will pay 450 rupees per day.", kind="external_fact"),
                ClaimItem(claim="We will target a CAC under 500 rupees.", kind="plan"),
            ])
        claim, passage = user_prompt.split("\n\nPassage: ")
        claim = claim.removeprefix("Claim: ")
        if "1,200 crore" in claim and "1,200 crore" in passage:
            return ClaimCheck(label="supported", quote="The Indian tiffin market is worth 1,200 crore rupees.")
        return ClaimCheck(label="unrelated")


def test_ledger_only_counts_verbatim_supported_claims():
    pool = SourcePool()
    pool.add("https://example.com/a", "Market note", "The Indian tiffin market is worth 1,200 crore rupees. It grows fast.")
    ledger = build_ledger({"market_research": {"overall_market_score": 70}}, pool, StubGateway())
    by_claim = {e["claim"]: e for e in ledger["entries"]}
    ok = by_claim["The Indian tiffin market is worth 1,200 crore rupees."]
    assert ok["status"] == "supported" and ok["source"]["url"] == "https://example.com/a"
    assert by_claim["Customers will pay 450 rupees per day."]["status"] == "unsupported"
    assert ledger["grounding_score"] == 50.0


def test_fabricated_quote_is_not_supported():
    class Liar(StubGateway):
        def invoke_structured(self, *, schema_class, **kw):
            if schema_class is ClaimList:
                return ClaimList(claims=[ClaimItem(claim="The tiffin market is worth 1,200 crore rupees.", kind="external_fact")])
            return ClaimCheck(label="supported", quote="A sentence the source never contains.")

    pool = SourcePool()
    pool.add("https://example.com/a", "t", "The tiffin market is worth 1,200 crore rupees.")
    assert build_ledger({"market_research": {"x": 1}}, pool, Liar())["entries"][0]["status"] == "unsupported"


def test_numbers_outweigh_words_in_retrieval():
    pool = SourcePool()
    pool.add("u1", "a", "Tiffin delivery is popular among office workers in many cities.")
    pool.add("u2", "b", "Revenue reached 1,200 crore in 2025.")
    top = best_passages("tiffin revenue 1,200 crore", _passages(pool), k=1)
    assert top and top[0][1] == 2


def test_mock_pipeline_end_to_end():
    events = []
    out = run_pipeline("A tutoring app that adapts lessons to each student's pace", "t1", mock=True, emit=events.append)
    assert out["mode"] == "mock" and list(CREW_LABELS) == [e["crew"] for e in events if e["type"] == "crew_complete"]
    assert 0 <= out["overall_readiness_score"] <= 100 and out["verdict"]["label"] in ("go", "pivot", "no-go")
    assert out["score_range"]["low"] <= out["overall_readiness_score"] <= out["score_range"]["high"]
    assert all(0 <= v <= 100 for v in out["crew_scores"].values() if v is not None)


def test_pipeline_stops_when_asked():
    assert run_pipeline("A tutoring app that adapts lessons", "t2", mock=True, should_stop=lambda: True) is None


def test_later_crew_failure_is_reported_not_fatal(monkeypatch):
    from ai.crews.funding.crew import FundingCrew

    def boom(self, *a, **k):
        raise ValueError("model returned broken JSON")

    monkeypatch.setattr(FundingCrew, "run", boom)
    events = []
    out = run_pipeline("A tutoring app that adapts lessons to each student's pace", "t3", mock=True, emit=events.append)
    assert out["failed_crews"] == ["funding"] and out["funding"] is None
    assert any(e["type"] == "crew_failed" and e["crew"] == "funding" for e in events)
    assert out["overall_readiness_score"] > 0 and out["reporting"] is not None
