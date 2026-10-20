"""ai/crews/spec_runner.py: doc-driven prompts, mock path, and live path through the gateway's validation."""

from ai.crews.funding.tasks import execute_funding_readiness_task
from ai.crews.spec_runner import build_system_prompt, run_spec_crew
from ai.schemas.funding import FundingResult


def test_system_prompt_includes_phase_and_only_that_crews_agent_docs():
    prompt = build_system_prompt("funding")
    assert "Phase 09: Funding Readiness" in prompt
    for agent in ("Funding Readiness Agent", "Investor Matcher", "Valuation Advisor", "Funding Summary"):
        assert agent in prompt
    assert "Growth Loops" not in prompt  # agent 54 belongs to the growth crew
    assert "JSON" in prompt


def test_mock_path_returns_literal_without_calling_gateway(monkeypatch):
    import ai.llm.gateway as gw

    monkeypatch.setattr(gw, "get_gateway", lambda: (_ for _ in ()).throw(AssertionError("gateway called")))
    res = run_spec_crew(
        "funding", FundingResult, "p1", "idea", None, None,
        lambda: execute_funding_readiness_task("p1", "idea"), mock_mode=True,
    )
    assert isinstance(res, FundingResult) and res.project_id == "p1"


def test_live_path_validates_gateway_json_and_forces_project_id(monkeypatch):
    import ai.llm.gateway as gw

    payload = execute_funding_readiness_task("model-made-this-up", "idea").model_copy(
        update={"fundraising_target": "$750k pre-seed"}
    )
    seen = {}

    def fake_invoke(self, **kwargs):
        seen.update(kwargs)
        return payload.model_dump_json()

    monkeypatch.setattr(gw.LLMGateway, "invoke", fake_invoke)
    res = run_spec_crew(
        "funding", FundingResult, "p-live", "Drone crop monitoring",
        {"feasibility": {"technical_feasibility_score": 81}}, "[1] Some source",
        lambda: (_ for _ in ()).throw(AssertionError("mock used")), mock_mode=False,
    )
    assert isinstance(res, FundingResult)
    assert res.project_id == "p-live"
    assert res.fundraising_target == "$750k pre-seed"
    assert "Drone crop monitoring" in seen["user_prompt"]
    assert "technical_feasibility_score" in seen["user_prompt"]
    assert "[1] Some source" in seen["user_prompt"]
    assert "Investor Matcher" in seen["system_prompt"]
