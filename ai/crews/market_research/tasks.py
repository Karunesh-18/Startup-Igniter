"""Task definitions for Market Research Crew.

Defines production CrewAI Tasks for each of the 7 market research agents:
1. MarketResearchAgent
2. IndustryAnalysisAgent
3. TrendAnalysisAgent
4. CompetitorDiscoveryAgent
5. CompetitorComparisonAgent
6. CustomerPersonaGenerator
7. TAMSAMSOMEstimator

Task outputs are configured with output_pydantic for structured Pydantic model validation.
"""

from typing import Any, Dict, List, Optional

from ai.schemas.market_research import (
    CompetitorComparison,
    CompetitorDiscovery,
    CustomerPersona,
    IndustryAnalysis,
    MarketResearchAnalysis,
    TAMSAMSOMAnalysis,
    TrendAnalysis,
)

# Optional CrewAI Task import check with type safety
try:
    from crewai import Task as CrewAITask  # type: ignore
    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False
    CrewAITask = None


# ============================================================================
# Task 1: MarketResearchAgent Task
# ============================================================================
def create_market_research_task(
    agent: Any, context: Optional[List[Any]] = None
) -> Any:
    """Create CrewAI task for holistic market overview analysis."""
    description = (
        "Conduct comprehensive high-level market research overview based on validated startup outputs. "
        "Return pure JSON matching the MarketResearchAnalysis Pydantic schema."
    )
    expected_output = (
        "Valid JSON object matching MarketResearchAnalysis schema with fields: "
        "market_overview, target_market_size, market_growth_rate, key_drivers, "
        "key_challenges, target_audience_summary, competitive_landscape_summary, "
        "market_attractiveness_score, confidence_score."
    )

    if HAS_CREWAI and CrewAITask is not None and not (isinstance(agent, dict) and agent.get("mock_mode")):
        kwargs: Dict[str, Any] = {
            "description": description,
            "expected_output": expected_output,
            "agent": agent,
            "output_pydantic": MarketResearchAnalysis,
        }
        if context:
            kwargs["context"] = context
        return CrewAITask(**kwargs)

    return {
        "task_name": "market_research",
        "description": description,
        "expected_output": expected_output,
        "agent": agent,
        "schema_class": MarketResearchAnalysis,
        "context": context,
    }


# ============================================================================
# Task 2: IndustryAnalysisAgent Task
# ============================================================================
def create_industry_analysis_task(
    agent: Any, context: Optional[List[Any]] = None
) -> Any:
    """Create CrewAI task for macro industry landscape analysis."""
    description = (
        "Analyze macro industry structure, maturity, regulatory environment, and competitive dynamics. "
        "Return pure JSON matching the IndustryAnalysis Pydantic schema."
    )
    expected_output = (
        "Valid JSON object matching IndustryAnalysis schema with fields: "
        "industry_name, industry_stage, regulatory_environment, entry_barriers, "
        "industry_attractiveness_score, confidence_score."
    )

    if HAS_CREWAI and CrewAITask is not None and not (isinstance(agent, dict) and agent.get("mock_mode")):
        kwargs: Dict[str, Any] = {
            "description": description,
            "expected_output": expected_output,
            "agent": agent,
            "output_pydantic": IndustryAnalysis,
        }
        if context:
            kwargs["context"] = context
        return CrewAITask(**kwargs)

    return {
        "task_name": "industry_analysis",
        "description": description,
        "expected_output": expected_output,
        "agent": agent,
        "schema_class": IndustryAnalysis,
        "context": context,
    }


# ============================================================================
# Task 3: TrendAnalysisAgent Task
# ============================================================================
def create_trend_analysis_task(
    agent: Any, context: Optional[List[Any]] = None
) -> Any:
    """Create CrewAI task for emerging market and technological trend analysis."""
    description = (
        "Identify emerging technological, consumer, regulatory, and business trends. "
        "Return pure JSON matching the TrendAnalysis Pydantic schema."
    )
    expected_output = (
        "Valid JSON object matching TrendAnalysis schema with fields: "
        "tech_trends, consumer_behavior_trends, market_opportunities, "
        "trend_impact_score, confidence_score."
    )

    if HAS_CREWAI and CrewAITask is not None and not (isinstance(agent, dict) and agent.get("mock_mode")):
        kwargs: Dict[str, Any] = {
            "description": description,
            "expected_output": expected_output,
            "agent": agent,
            "output_pydantic": TrendAnalysis,
        }
        if context:
            kwargs["context"] = context
        return CrewAITask(**kwargs)

    return {
        "task_name": "trend_analysis",
        "description": description,
        "expected_output": expected_output,
        "agent": agent,
        "schema_class": TrendAnalysis,
        "context": context,
    }


# ============================================================================
# Task 4: CompetitorDiscoveryAgent Task
# ============================================================================
def create_competitor_discovery_task(
    agent: Any, context: Optional[List[Any]] = None
) -> Any:
    """Create CrewAI task for direct, indirect, and emerging competitor discovery."""
    description = (
        "Identify key direct, indirect, and emerging competitors in the target industry. "
        "Return pure JSON matching the CompetitorDiscovery Pydantic schema."
    )
    expected_output = (
        "Valid JSON object matching CompetitorDiscovery schema with fields: "
        "direct_competitors, indirect_competitors, emerging_competitors, "
        "market_leaders, startup_challengers, competition_intensity, confidence_score."
    )

    if HAS_CREWAI and CrewAITask is not None and not (isinstance(agent, dict) and agent.get("mock_mode")):
        kwargs: Dict[str, Any] = {
            "description": description,
            "expected_output": expected_output,
            "agent": agent,
            "output_pydantic": CompetitorDiscovery,
        }
        if context:
            kwargs["context"] = context
        return CrewAITask(**kwargs)

    return {
        "task_name": "competitor_discovery",
        "description": description,
        "expected_output": expected_output,
        "agent": agent,
        "schema_class": CompetitorDiscovery,
        "context": context,
    }


# ============================================================================
# Task 5: CompetitorComparisonAgent Task
# ============================================================================
def create_competitor_comparison_task(
    agent: Any, context: Optional[List[Any]] = None
) -> Any:
    """Create CrewAI task for competitive positioning and benchmarking."""
    description = (
        "Compare startup positioning against discovered competitors on features, pricing, and technology. "
        "Return pure JSON matching the CompetitorComparison Pydantic schema."
    )
    expected_output = (
        "Valid JSON object matching CompetitorComparison schema with fields: "
        "startup_position, competitive_advantages, competitive_weaknesses, "
        "feature_comparison, technology_comparison, overall_competitive_score, confidence_score."
    )

    if HAS_CREWAI and CrewAITask is not None and not (isinstance(agent, dict) and agent.get("mock_mode")):
        kwargs: Dict[str, Any] = {
            "description": description,
            "expected_output": expected_output,
            "agent": agent,
            "output_pydantic": CompetitorComparison,
        }
        if context:
            kwargs["context"] = context
        return CrewAITask(**kwargs)

    return {
        "task_name": "competitor_comparison",
        "description": description,
        "expected_output": expected_output,
        "agent": agent,
        "schema_class": CompetitorComparison,
        "context": context,
    }


# ============================================================================
# Task 6: CustomerPersonaGenerator Task
# ============================================================================
def create_customer_persona_task(
    agent: Any, context: Optional[List[Any]] = None
) -> Any:
    """Create CrewAI task for detailed buyer and user persona generation."""
    description = (
        "Develop primary and secondary target customer personas covering demographics, behaviors, and pain points. "
        "Return pure JSON matching the CustomerPersona Pydantic schema."
    )
    expected_output = (
        "Valid JSON object matching CustomerPersona schema with fields: "
        "primary_persona, secondary_personas, confidence_score."
    )

    if HAS_CREWAI and CrewAITask is not None and not (isinstance(agent, dict) and agent.get("mock_mode")):
        kwargs: Dict[str, Any] = {
            "description": description,
            "expected_output": expected_output,
            "agent": agent,
            "output_pydantic": CustomerPersona,
        }
        if context:
            kwargs["context"] = context
        return CrewAITask(**kwargs)

    return {
        "task_name": "customer_persona",
        "description": description,
        "expected_output": expected_output,
        "agent": agent,
        "schema_class": CustomerPersona,
        "context": context,
    }


# ============================================================================
# Task 7: TAMSAMSOMEstimator Task
# ============================================================================
def create_tam_sam_som_task(
    agent: Any, context: Optional[List[Any]] = None
) -> Any:
    """Create CrewAI task for TAM, SAM, and SOM financial market sizing estimation."""
    description = (
        "Quantify Total Addressable Market (TAM), Serviceable Addressable Market (SAM), and Serviceable Obtainable Market (SOM). "
        "Return pure JSON matching the TAMSAMSOMAnalysis Pydantic schema."
    )
    expected_output = (
        "Valid JSON object matching TAMSAMSOMAnalysis schema with fields: "
        "tam_description, tam_value, sam_description, sam_value, "
        "som_description, som_value, methodology, confidence_score."
    )

    if HAS_CREWAI and CrewAITask is not None and not (isinstance(agent, dict) and agent.get("mock_mode")):
        kwargs: Dict[str, Any] = {
            "description": description,
            "expected_output": expected_output,
            "agent": agent,
            "output_pydantic": TAMSAMSOMAnalysis,
        }
        if context:
            kwargs["context"] = context
        return CrewAITask(**kwargs)

    return {
        "task_name": "tam_sam_som",
        "description": description,
        "expected_output": expected_output,
        "agent": agent,
        "schema_class": TAMSAMSOMAnalysis,
        "context": context,
    }
