"""Registry of what to generate training data for.

Reuses the REAL agent factories and schemas from `ai/` directly rather than
re-declaring prompts or schemas here — the whole point of this corpus is to
teach the model to do exactly what the live pipeline's agents ask, so the
generator must be unable to drift from them.

For the 20 IMPLEMENTED agents (crews 1-3): imports the real `get_*_agent()`
factory, pulling `backstory` (system prompt) and `schema_class` straight out
of the dict it returns -- the same dict `ai/crews/*/crew.py` consumes at
runtime.

For the 9 SPECIFIED crews (4-12, currently hardcoded-literal stubs): there is
no per-agent prompt/schema yet (see docs/phases/04-*.md through 12-*.md --
several stub schemas don't even have a 1:1 field for every listed agent).
Training data for these is generated at the CREW level against the existing
crew-level result schema, with a synthesized system prompt derived from the
crew's stated purpose in docs/phases/. This produces a legitimate SFT
example for "given this idea, produce a BrandingMarketingResult" even though
no per-agent split exists to fine-tune against yet.
"""

from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Type

from pydantic import BaseModel

# --- 20 implemented, per-agent entries --------------------------------------

from ai.agents.idea_validation import (
    get_customer_identifier_agent,
    get_innovation_scoring_agent,
    get_problem_statement_analyzer_agent,
    get_startup_category_classifier_agent,
    get_startup_idea_analyzer_agent,
    get_value_proposition_analyzer_agent,
)
from ai.agents.market_research.competitor_comparison_agent import get_competitor_comparison_agent
from ai.agents.market_research.competitor_discovery_agent import get_competitor_discovery_agent
from ai.agents.market_research.customer_persona_generator import get_customer_persona_generator_agent
from ai.agents.market_research.industry_analysis_agent import get_industry_analysis_agent
from ai.agents.market_research.market_research_agent import get_market_research_agent
from ai.agents.market_research.tam_sam_som_estimator import get_tam_sam_som_estimator_agent
from ai.agents.market_research.trend_analysis_agent import get_trend_analysis_agent
from ai.agents.research_patent.existing_solution_analyzer_agent import get_existing_solution_analyzer_agent
from ai.agents.research_patent.innovation_gap_identifier_agent import get_innovation_gap_identifier_agent
from ai.agents.research_patent.intellectual_property_strategy_agent import get_intellectual_property_strategy_agent
from ai.agents.research_patent.patent_search_agent import get_patent_search_agent
from ai.agents.research_patent.research_paper_analyzer_agent import get_research_paper_analyzer_agent
from ai.agents.research_patent.technology_readiness_agent import get_technology_readiness_agent


@dataclass(frozen=True)
class TrainingTarget:
    """One thing to generate synthetic examples for: either a real per-agent
    call (crew_id 1-3) or a crew-level call (crew_id 4-12)."""

    agent_id: int  # matches frontend/src/data/crews.ts ids; 0 for crew-level (specified) targets
    crew_id: int
    name: str
    get_agent_fn: Optional[Callable[..., Any]]  # None for specified crew-level targets
    schema_class: Optional[Type[BaseModel]] = None  # required for crew-level targets
    crew_level: bool = False


# Each get_*_agent() call below uses mock_mode=True purely to avoid any
# network dependency AT REGISTRY IMPORT TIME (some factories are pure dict
# builders regardless, but this keeps the contract explicit) -- generate.py
# then calls the real gateway per example, not this registry.
IMPLEMENTED_TARGETS: List[TrainingTarget] = [
    TrainingTarget(1, 1, "startup_idea_analyzer", get_startup_idea_analyzer_agent),
    TrainingTarget(2, 1, "problem_statement_analyzer", get_problem_statement_analyzer_agent),
    TrainingTarget(3, 1, "customer_identifier", get_customer_identifier_agent),
    TrainingTarget(4, 1, "value_proposition_analyzer", get_value_proposition_analyzer_agent),
    TrainingTarget(5, 1, "startup_category_classifier", get_startup_category_classifier_agent),
    TrainingTarget(6, 1, "innovation_scoring_agent", get_innovation_scoring_agent),
    TrainingTarget(7, 2, "market_research_agent", get_market_research_agent),
    TrainingTarget(8, 2, "industry_analysis_agent", get_industry_analysis_agent),
    TrainingTarget(9, 2, "trend_analysis_agent", get_trend_analysis_agent),
    TrainingTarget(10, 2, "competitor_discovery_agent", get_competitor_discovery_agent),
    TrainingTarget(11, 2, "competitor_comparison_agent", get_competitor_comparison_agent),
    TrainingTarget(12, 2, "customer_persona_generator", get_customer_persona_generator_agent),
    TrainingTarget(13, 2, "tam_sam_som_estimator", get_tam_sam_som_estimator_agent),
    TrainingTarget(14, 3, "patent_search_agent", get_patent_search_agent),
    TrainingTarget(15, 3, "research_paper_analyzer_agent", get_research_paper_analyzer_agent),
    TrainingTarget(16, 3, "innovation_gap_identifier_agent", get_innovation_gap_identifier_agent),
    TrainingTarget(17, 3, "technology_readiness_agent", get_technology_readiness_agent),
    TrainingTarget(18, 3, "intellectual_property_strategy_agent", get_intellectual_property_strategy_agent),
    # existing_solution_analyzer_agent: the 7th, unlisted crew-3 agent (see
    # docs/agents/67-existing-solution-analyzer.md). Included here since it's
    # implemented and real -- agent_id 0 marks it as outside the 66.
    TrainingTarget(0, 3, "existing_solution_analyzer_agent", get_existing_solution_analyzer_agent),
    # research_patent_summary_agent intentionally excluded: its output isn't
    # validated against one Pydantic schema (see docs/architecture/0005-grounding-layer.md's
    # "Known gaps"), so it has no clean schema_class to train a repair-loop /
    # guided-decoding target against yet.
]


# --- 9 specified, crew-level entries ----------------------------------------

from ai.schemas.branding_marketing import BrandingMarketingResult
from ai.schemas.business_plan import BusinessPlanResult
from ai.schemas.community import CommunityResult
from ai.schemas.feasibility import FeasibilityResult
from ai.schemas.funding import FundingResult
from ai.schemas.growth_scaling import GrowthScalingResult
from ai.schemas.legal_compliance import LegalComplianceResult
from ai.schemas.product_development import ProductDevelopmentResult
from ai.schemas.reporting import MasterReportResult

SPECIFIED_TARGETS: List[TrainingTarget] = [
    TrainingTarget(0, 4, "feasibility_crew", None, FeasibilityResult, crew_level=True),
    TrainingTarget(0, 5, "business_planning_crew", None, BusinessPlanResult, crew_level=True),
    TrainingTarget(0, 6, "product_development_crew", None, ProductDevelopmentResult, crew_level=True),
    TrainingTarget(0, 7, "legal_compliance_crew", None, LegalComplianceResult, crew_level=True),
    TrainingTarget(0, 8, "branding_marketing_crew", None, BrandingMarketingResult, crew_level=True),
    TrainingTarget(0, 9, "funding_crew", None, FundingResult, crew_level=True),
    TrainingTarget(0, 10, "growth_scaling_crew", None, GrowthScalingResult, crew_level=True),
    TrainingTarget(0, 11, "community_crew", None, CommunityResult, crew_level=True),
    TrainingTarget(0, 12, "reporting_crew", None, MasterReportResult, crew_level=True),
]

CREW_PURPOSE = {
    4: "Assess whether this idea can be engineered: architecture, infrastructure, scalability, and security risk.",
    5: "Produce a Lean Canvas and a financial model (pricing, CAC/LTV, year-1 revenue projection).",
    6: "Produce an MVP feature roadmap, a tech stack recommendation, and an architecture overview.",
    7: "Produce a jurisdiction-aware legal/compliance checklist and draft (non-final) legal documents.",
    8: "Produce brand name candidates, a tagline, positioning, and a go-to-market channel strategy.",
    9: "Assess fundraising readiness: pitch deck structure, valuation range, and investor type fit.",
    10: "Recommend acquisition channels, a growth mechanic, a retention playbook, and target KPIs.",
    11: "Surface community/mentor/accelerator recommendations relevant to this idea's category.",
    12: "Synthesize every prior phase's output into one executive summary and readiness score.",
}


def all_targets() -> List[TrainingTarget]:
    return IMPLEMENTED_TARGETS + SPECIFIED_TARGETS
