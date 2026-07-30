"""AI Agents Package — Exporting agent factories across all 12 startup phase domains."""

from ai.agents.branding_marketing import get_branding_marketing_agent
from ai.agents.business_planning import get_financial_model_agent, get_lean_canvas_agent
from ai.agents.community import get_community_peer_review_agent
from ai.agents.feasibility import get_feasibility_analyzer_agent
from ai.agents.funding import get_funding_readiness_agent
from ai.agents.growth_scaling import get_growth_scaling_agent
from ai.agents.idea_validation import (
    get_customer_identifier_agent,
    get_innovation_scoring_agent,
    get_problem_statement_analyzer_agent,
    get_startup_category_classifier_agent,
    get_startup_idea_analyzer_agent,
    get_value_proposition_analyzer_agent,
)
from ai.agents.legal_compliance import get_compliance_checklist_agent, get_legal_document_draft_agent
from ai.agents.market_research import (
    get_competitor_comparison_agent,
    get_competitor_discovery_agent,
    get_customer_persona_generator_agent,
    get_industry_analysis_agent,
    get_market_research_agent,
    get_tam_sam_som_estimator_agent,
    get_trend_analysis_agent,
)
from ai.agents.product_development import get_mvp_feature_agent, get_tech_stack_agent
from ai.agents.reporting import get_master_reporting_agent
from ai.agents.research_patent import get_prior_art_search_agent

__all__ = [
    "get_startup_idea_analyzer_agent",
    "get_problem_statement_analyzer_agent",
    "get_customer_identifier_agent",
    "get_value_proposition_analyzer_agent",
    "get_startup_category_classifier_agent",
    "get_innovation_scoring_agent",
    "get_market_research_agent",
    "get_industry_analysis_agent",
    "get_trend_analysis_agent",
    "get_competitor_discovery_agent",
    "get_competitor_comparison_agent",
    "get_customer_persona_generator_agent",
    "get_tam_sam_som_estimator_agent",
    "get_feasibility_analyzer_agent",
    "get_lean_canvas_agent",
    "get_financial_model_agent",
    "get_prior_art_search_agent",
    "get_compliance_checklist_agent",
    "get_legal_document_draft_agent",
    "get_mvp_feature_agent",
    "get_tech_stack_agent",
    "get_branding_marketing_agent",
    "get_growth_scaling_agent",
    "get_funding_readiness_agent",
    "get_master_reporting_agent",
    "get_community_peer_review_agent",
]
