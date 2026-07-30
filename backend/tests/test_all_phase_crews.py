import pytest

from ai.crews.branding_marketing.crew import get_branding_marketing_crew
from ai.crews.business_planning.crew import get_business_planning_crew
from ai.crews.community.crew import get_community_crew
from ai.crews.feasibility.crew import get_feasibility_crew
from ai.crews.funding.crew import get_funding_crew
from ai.crews.growth_scaling.crew import get_growth_scaling_crew
from ai.crews.idea_validation.crew import get_idea_validation_crew
from ai.crews.legal_compliance.crew import get_legal_compliance_crew
from ai.crews.market_research.crew import MarketResearchCrew
from ai.crews.product_development.crew import get_product_development_crew
from ai.crews.reporting.crew import get_reporting_crew
from ai.crews.research_patent.crew import get_research_patent_crew


@pytest.mark.asyncio
async def test_idea_validation_crew():
    crew = get_idea_validation_crew(mock_mode=True)
    res = crew.run(project_id="p1", idea_text="FinTech AI SaaS Platform")
    assert res.project_id == "p1"
    assert res.overall_validation_score > 0


@pytest.mark.asyncio
async def test_feasibility_crew():
    crew = get_feasibility_crew(mock_mode=True)
    res = crew.run(project_id="p2", idea_text="DeepTech Quantum Computing OS")
    assert res.project_id == "p2"
    assert res.technical_feasibility_score > 0


@pytest.mark.asyncio
async def test_branding_marketing_crew():
    crew = get_branding_marketing_crew(mock_mode=True)
    res = crew.run(project_id="p3", idea_text="EdTech AI Tutor")
    assert res.project_id == "p3"
    assert len(res.brand_name_suggestions) > 0


@pytest.mark.asyncio
async def test_growth_scaling_crew():
    crew = get_growth_scaling_crew(mock_mode=True)
    res = crew.run(project_id="p4", idea_text="HealthTech Diagnostics App")
    assert res.project_id == "p4"
    assert res.viral_loop_mechanic != ""


@pytest.mark.asyncio
async def test_funding_crew():
    crew = get_funding_crew(mock_mode=True)
    res = crew.run(project_id="p5", idea_text="AgriTech Drone Monitoring")
    assert res.project_id == "p5"
    assert len(res.pitch_deck_slides) == 10


@pytest.mark.asyncio
async def test_reporting_crew():
    crew = get_reporting_crew(mock_mode=True)
    res = crew.run(project_id="p6", idea_text="AI Startup Operating System")
    assert res.project_id == "p6"
    assert res.overall_readiness_score > 0


@pytest.mark.asyncio
async def test_community_crew():
    crew = get_community_crew(mock_mode=True)
    res = crew.run(project_id="p7", idea_text="DevTools API Gateway")
    assert res.project_id == "p7"
    assert len(res.recommended_mentors) > 0


@pytest.mark.asyncio
async def test_all_standalone_agent_factories():
    from ai import agents

    factories = [
        agents.get_startup_idea_analyzer_agent,
        agents.get_problem_statement_analyzer_agent,
        agents.get_customer_identifier_agent,
        agents.get_value_proposition_analyzer_agent,
        agents.get_startup_category_classifier_agent,
        agents.get_innovation_scoring_agent,
        agents.get_market_research_agent,
        agents.get_industry_analysis_agent,
        agents.get_trend_analysis_agent,
        agents.get_competitor_discovery_agent,
        agents.get_competitor_comparison_agent,
        agents.get_customer_persona_generator_agent,
        agents.get_tam_sam_som_estimator_agent,
        agents.get_feasibility_analyzer_agent,
        agents.get_lean_canvas_agent,
        agents.get_financial_model_agent,
        agents.get_prior_art_search_agent,
        agents.get_compliance_checklist_agent,
        agents.get_legal_document_draft_agent,
        agents.get_mvp_feature_agent,
        agents.get_tech_stack_agent,
        agents.get_branding_marketing_agent,
        agents.get_growth_scaling_agent,
        agents.get_funding_readiness_agent,
        agents.get_master_reporting_agent,
        agents.get_community_peer_review_agent,
    ]

    assert len(factories) == 26
    for factory in factories:
        agent_obj = factory(mock_mode=True)
        assert agent_obj is not None
