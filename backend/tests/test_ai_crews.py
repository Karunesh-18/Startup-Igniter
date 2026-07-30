import pytest

from ai.crews.business_planning.crew import get_business_planning_crew
from ai.crews.legal_compliance.crew import get_legal_compliance_crew
from ai.crews.product_development.crew import get_product_development_crew
from ai.crews.research_patent.crew import get_research_patent_crew


@pytest.mark.asyncio
async def test_business_planning_crew():
    crew = get_business_planning_crew(mock_mode=True)
    res = crew.run(project_id="test_proj_1", idea_text="AI Startup Operating System", mock_mode=True)
    assert res.project_id == "test_proj_1"
    assert res.lean_canvas.unique_value_proposition != ""
    assert res.financial_model.pricing_model != ""


@pytest.mark.asyncio
async def test_research_patent_crew():
    crew = get_research_patent_crew(mock_mode=True)
    res = crew.run(project_id="test_proj_2", idea_text="Autonomous AI Agents", mock_mode=True)
    assert res.project_id == "test_proj_2"
    assert res.patent_number != ""
    assert len(res.key_claims) > 0


@pytest.mark.asyncio
async def test_legal_compliance_crew():
    crew = get_legal_compliance_crew(mock_mode=True)
    res = crew.run(project_id="test_proj_3", idea_text="FinTech Payment Aggregator", category="FinTech", mock_mode=True)
    assert res.project_id == "test_proj_3"
    assert len(res.compliance_checklist) > 0
    assert res.draft_nda is not None
    assert "DISCLAIMER" in res.draft_nda.disclaimer


@pytest.mark.asyncio
async def test_product_development_crew():
    crew = get_product_development_crew(mock_mode=True)
    res = crew.run(project_id="test_proj_4", idea_text="HealthTech Diagnostics AI", category="HealthTech", mock_mode=True)
    assert res.project_id == "test_proj_4"
    assert len(res.mvp_features) > 0
    assert res.tech_stack.frontend != ""
