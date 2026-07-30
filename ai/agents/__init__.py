"""AI Agents Package — Exporting 55 standalone agent factories across all 12 startup phase domains."""

from ai.agents.branding_marketing import (
    get_branding_marketing_agent,
    get_digital_marketing_agent,
    get_go_to_market_agent,
    get_marketing_strategy_agent,
    get_naming_advisor_agent,
)
from ai.agents.business_planning import (
    get_business_plan_summary_agent,
    get_cost_structure_agent,
    get_financial_model_agent,
    get_lean_canvas_agent,
    get_pricing_strategy_agent,
    get_revenue_model_agent,
)
from ai.agents.community import (
    get_accelerator_recommendation_agent,
    get_community_peer_review_agent,
    get_mentor_recommendation_agent,
    get_startup_ecosystem_agent,
)
from ai.agents.feasibility import (
    get_architecture_recommendation_agent,
    get_feasibility_analyzer_agent,
    get_feasibility_summary_agent,
    get_infrastructure_planner_agent,
    get_scalability_assessment_agent,
    get_security_assessment_agent,
)
from ai.agents.funding import (
    get_funding_readiness_agent,
    get_funding_summary_agent,
    get_grant_discovery_agent,
    get_investor_matcher_agent,
    get_valuation_advisor_agent,
)
from ai.agents.growth_scaling import (
    get_expansion_planner_agent,
    get_growth_scaling_agent,
    get_international_expansion_agent,
    get_partnership_advisor_agent,
)
from ai.agents.idea_validation import (
    get_customer_identifier_agent,
    get_innovation_scoring_agent,
    get_problem_statement_analyzer_agent,
    get_startup_category_classifier_agent,
    get_startup_idea_analyzer_agent,
    get_value_proposition_analyzer_agent,
)
from ai.agents.legal_compliance import (
    get_compliance_checklist_agent,
    get_data_privacy_agent,
    get_legal_document_draft_agent,
    get_legal_summary_agent,
    get_licensing_advisor_agent,
    get_startup_registration_advisor_agent,
)
from ai.agents.market_research import (
    get_competitor_comparison_agent,
    get_competitor_discovery_agent,
    get_customer_persona_generator_agent,
    get_industry_analysis_agent,
    get_market_research_agent,
    get_tam_sam_som_estimator_agent,
    get_trend_analysis_agent,
)
from ai.agents.product_development import (
    get_development_effort_estimator_agent,
    get_mvp_feature_agent,
    get_product_development_summary_agent,
    get_product_roadmap_agent,
    get_tech_stack_agent,
    get_ux_recommendation_agent,
)
from ai.agents.reporting import (
    get_action_plan_generator_agent,
    get_final_report_generator_agent,
    get_master_reporting_agent,
    get_roadmap_generator_agent,
    get_startup_readiness_scoring_agent,
)
from ai.agents.research_patent import (
    get_innovation_gap_identifier_agent,
    get_intellectual_property_strategy_agent,
    get_prior_art_search_agent,
    get_research_paper_analyzer_agent,
    get_research_patent_summary_agent,
    get_technology_readiness_agent,
)

__all__ = [
    # Idea Validation (6)
    "get_startup_idea_analyzer_agent",
    "get_problem_statement_analyzer_agent",
    "get_customer_identifier_agent",
    "get_value_proposition_analyzer_agent",
    "get_startup_category_classifier_agent",
    "get_innovation_scoring_agent",
    # Market Research (7)
    "get_market_research_agent",
    "get_industry_analysis_agent",
    "get_trend_analysis_agent",
    "get_competitor_discovery_agent",
    "get_competitor_comparison_agent",
    "get_customer_persona_generator_agent",
    "get_tam_sam_som_estimator_agent",
    # Research & Patent (6)
    "get_prior_art_search_agent",
    "get_research_paper_analyzer_agent",
    "get_innovation_gap_identifier_agent",
    "get_technology_readiness_agent",
    "get_intellectual_property_strategy_agent",
    "get_research_patent_summary_agent",
    # Technical Feasibility (6)
    "get_feasibility_analyzer_agent",
    "get_architecture_recommendation_agent",
    "get_infrastructure_planner_agent",
    "get_scalability_assessment_agent",
    "get_security_assessment_agent",
    "get_feasibility_summary_agent",
    # Business Planning (6)
    "get_lean_canvas_agent",
    "get_financial_model_agent",
    "get_revenue_model_agent",
    "get_cost_structure_agent",
    "get_pricing_strategy_agent",
    "get_business_plan_summary_agent",
    # Product Development (6)
    "get_mvp_feature_agent",
    "get_tech_stack_agent",
    "get_product_roadmap_agent",
    "get_development_effort_estimator_agent",
    "get_ux_recommendation_agent",
    "get_product_development_summary_agent",
    # Legal & Compliance (6)
    "get_compliance_checklist_agent",
    "get_legal_document_draft_agent",
    "get_data_privacy_agent",
    "get_licensing_advisor_agent",
    "get_startup_registration_advisor_agent",
    "get_legal_summary_agent",
    # Branding & Marketing (5)
    "get_branding_marketing_agent",
    "get_naming_advisor_agent",
    "get_marketing_strategy_agent",
    "get_go_to_market_agent",
    "get_digital_marketing_agent",
    # Funding Readiness (5)
    "get_funding_readiness_agent",
    "get_investor_matcher_agent",
    "get_grant_discovery_agent",
    "get_valuation_advisor_agent",
    "get_funding_summary_agent",
    # Growth & Scaling (4)
    "get_growth_scaling_agent",
    "get_expansion_planner_agent",
    "get_partnership_advisor_agent",
    "get_international_expansion_agent",
    # Community & Ecosystem (4)
    "get_community_peer_review_agent",
    "get_mentor_recommendation_agent",
    "get_accelerator_recommendation_agent",
    "get_startup_ecosystem_agent",
    # Executive Reporting (5)
    "get_master_reporting_agent",
    "get_startup_readiness_scoring_agent",
    "get_roadmap_generator_agent",
    "get_action_plan_generator_agent",
    "get_final_report_generator_agent",
]
