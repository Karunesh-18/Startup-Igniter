"""Market Research Agent package."""

from ai.agents.market_research.competitor_comparison_agent import (
    get_competitor_comparison_agent,
    run_competitor_comparison_agent,
)
from ai.agents.market_research.competitor_discovery_agent import (
    get_competitor_discovery_agent,
    run_competitor_discovery_agent,
)
from ai.agents.market_research.customer_persona_generator import (
    get_customer_persona_generator_agent,
    run_customer_persona_generator_agent,
)
from ai.agents.market_research.industry_analysis_agent import (
    get_industry_analysis_agent,
    run_industry_analysis_agent,
)
from ai.agents.market_research.market_research_agent import (
    get_market_research_agent,
    run_market_research_agent,
    validate_agent_output,
)
from ai.agents.market_research.trend_analysis_agent import (
    get_trend_analysis_agent,
    run_trend_analysis_agent,
)

from ai.agents.market_research.tam_sam_som_estimator import (
    get_tam_sam_som_estimator_agent,
    run_tam_sam_som_estimator_agent,
)

__all__ = [
    "get_market_research_agent",
    "run_market_research_agent",
    "validate_agent_output",
    "get_industry_analysis_agent",
    "run_industry_analysis_agent",
    "get_trend_analysis_agent",
    "run_trend_analysis_agent",
    "get_competitor_discovery_agent",
    "run_competitor_discovery_agent",
    "get_competitor_comparison_agent",
    "run_competitor_comparison_agent",
    "get_customer_persona_generator_agent",
    "run_customer_persona_generator_agent",
    "get_tam_sam_som_estimator_agent",
    "run_tam_sam_som_estimator_agent",
]
