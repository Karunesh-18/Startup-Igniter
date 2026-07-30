"""Competitor Comparison Agent for comparing the startup against discovered market competitors."""

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import httpx

from ai.config import get_ai_settings
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.context import MarketResearchContext
from ai.schemas.market_research import CompetitorComparison
from ai.shared.constants import ModelTier
from ai.shared.llm_provider import LLMFactory
from ai.shared.logger import ai_logger
from ai.shared.output_validator import validate_output

# Optional CrewAI import check with type safety
try:
    from crewai import Agent as CrewAIAgent  # type: ignore
    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False
    CrewAIAgent = None


def load_agent_prompt(filename: str = "competitor_comparison.md") -> str:
    """Load agent prompt instructions from prompts/market_research directory."""
    prompt_path = (
        Path(__file__).resolve().parent.parent.parent
        / "prompts"
        / "market_research"
        / filename
    )
    if prompt_path.is_file():
        return prompt_path.read_text(encoding="utf-8")
    ai_logger.warning(
        f"Prompt file '{filename}' not found at {prompt_path}. Using default fallback prompt."
    )
    return (
        "You are a Senior Competitive Strategy & Market Differentiation Specialist. "
        "Compare the startup against discovered competitors across features, technology, customer alignment, and pricing. "
        "Return pure JSON only matching the CompetitorComparison schema."
    )


def validate_agent_output(raw_output: str) -> CompetitorComparison:
    """Safely parse and validate raw LLM output into CompetitorComparison Pydantic model.

    Args:
        raw_output: Raw string response from LLM call.

    Returns:
        Validated CompetitorComparison object.
    """
    return validate_output(raw_output, CompetitorComparison)


def _call_live_groq_llm(
    system_prompt: str,
    user_prompt: str,
    model_name: str,
    temperature: float = 0.2,
    timeout: float = 45.0,
    max_retries: int = 8,
) -> str:
    """Execute live LLM completion call using OpenRouter (primary) or Groq."""
    from ai.shared.llm_provider import call_live_llm
    return call_live_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model_name=model_name,
        temperature=temperature,
        timeout=timeout,
        max_retries=max_retries,
    )


def get_competitor_comparison_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
    mock_mode: bool = False,
    tools: Optional[List[Any]] = None,
) -> Any:
    """Returns a configured CrewAI Agent instance for Competitor Comparison.

    Args:
        model_tier: Model execution tier (default: HEAVY).
        temperature: Sampling temperature (default: 0.2).
        api_key: Optional explicit API key.
        mock_mode: If True, operates in test mode without live LLM calls.
        tools: Optional list of tools to attach.

    Returns:
        Configured CrewAI Agent instance (or dictionary agent container in fallback mode).
    """
    ai_logger.info(
        f"Initializing CompetitorComparisonAgent: tier={model_tier}, temp={temperature}, mock={mock_mode}"
    )

    llm = LLMFactory.get_llm(
        model_tier=model_tier,
        temperature=temperature,
        api_key=api_key,
        mock_mode=mock_mode,
    )

    prompt_text = load_agent_prompt("competitor_comparison.md")
    agent_tools = tools or []

    role = "Senior Competitive Strategy & Market Differentiation Specialist"
    goal = (
        "Evaluate and compare the startup proposal against discovered market competitors across advantages, "
        "vulnerabilities, feature set, technology stack, and positioning."
    )
    backstory = prompt_text

    if HAS_CREWAI and CrewAIAgent is not None and not mock_mode:
        return CrewAIAgent(
            role=role,
            goal=goal,
            backstory=backstory,
            verbose=True,
            allow_delegation=False,
            llm=llm,
            tools=agent_tools,
        )

    # Reusable fallback agent dictionary for offline & unit testing
    return {
        "agent_name": "competitor_comparison_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": agent_tools,
        "mock_mode": mock_mode,
        "schema_class": CompetitorComparison,
        "validate_output": validate_agent_output,
    }


def run_competitor_comparison_agent(
    context: MarketResearchContext,
    memory_manager: Optional[ProjectMemoryManager] = None,
    mock_mode: bool = False,
) -> CompetitorComparison:
    """Execute competitor comparison reading from MarketResearchContext.

    Args:
        context: MarketResearchContext container populated by previous steps.
        memory_manager: Optional ProjectMemoryManager instance.
        mock_mode: If True, uses mock simulation response for offline testing.

    Returns:
        Validated CompetitorComparison object.
    """
    settings = get_ai_settings()
    memory_mgr = memory_manager or ProjectMemoryManager(use_mock_store=True)

    if context.research_bundle:
        # Future enhancement: Use verified external research from ResearchManager (Tavily/Exa/Zyte)
        pass

    agent = get_competitor_comparison_agent(
        model_tier=ModelTier.HEAVY,
        mock_mode=mock_mode,
    )

    idea_val = context.idea_validation
    mr_analysis = context.market_research
    ind_analysis = context.industry_analysis
    tr_analysis = context.trend_analysis
    comp_disc = context.competitor_discovery

    category = idea_val.category_classification.primary_category
    problem = idea_val.problem_analysis.problem_statement
    value_prop = idea_val.value_proposition.core_value_proposition

    comp_summary_text = ""
    if comp_disc:
        direct_names = [c.name for c in comp_disc.direct_competitors]
        leaders = comp_disc.market_leaders
        challengers = comp_disc.startup_challengers
        comp_summary_text = (
            f"Direct Competitors: {', '.join(direct_names)}\n"
            f"Market Leaders: {', '.join(leaders)}\n"
            f"Startup Challengers: {', '.join(challengers)}\n"
            f"Competition Intensity: {comp_disc.competition_intensity}\n"
        )

    context_parts = [
        f"Idea Text: '{idea_val.idea_text}'",
        f"Primary Category: {category}",
        f"Problem Statement: {problem}",
        f"Core Value Proposition: {value_prop}",
        comp_summary_text,
    ]

    context_text = "\n".join([p for p in context_parts if p.strip()])

    system_prompt = load_agent_prompt("competitor_comparison.md")
    user_prompt = (
        f"Perform a comprehensive competitive comparison for the startup proposal against discovered competitors:\n\n"
        f"{context_text}\n\n"
        "Return pure JSON matching the CompetitorComparison schema with fields: "
        "startup_position, competitive_advantages, competitive_weaknesses, feature_comparison, "
        "technology_comparison, customer_focus_comparison, pricing_strategy_comparison, "
        "innovation_comparison, market_positioning, competitive_gap, differentiation_opportunities, "
        "overall_competitive_score (0.0-10.0), confidence_score (0.0-1.0)."
    )

    if mock_mode:
        raw_output = f"""{{
            "startup_position": "Innovative challenger leveraging native AI automation to target unserved mid-market segments.",
            "competitive_advantages": [
                "Proprietary AI decision automation engine",
                "10x faster implementation time compared to legacy enterprise platforms",
                "Significantly lower total cost of ownership"
            ],
            "competitive_weaknesses": [
                "Lower brand recognition compared to established market leaders",
                "Smaller initial feature surface area compared to decade-old suites"
            ],
            "feature_comparison": [
                "Startup: Real-time AI automated workflows vs Competitors: Manual rule-based configuration",
                "Startup: Modern API-first integration vs Competitors: Legacy custom connectors"
            ],
            "technology_comparison": "Startup utilizes modern LLM & agentic microservices architecture, whereas incumbents rely on monolithic legacy databases.",
            "customer_focus_comparison": "Startup specifically targets mid-market agility and fast ROI, while incumbents focus on heavy global enterprise contracts.",
            "pricing_strategy_comparison": "Usage-based transparent SaaS tier vs Incumbent expensive multi-year enterprise license locks.",
            "innovation_comparison": "High rate of AI model iterations and continuous feature deployment compared to annual legacy release cycles.",
            "market_positioning": "The premier AI-native automation solution for agile mid-market teams.",
            "competitive_gap": [
                "Unserved need for affordable, instant-deploy AI workflows",
                "Lack of self-service onboarding among incumbent competitors"
            ],
            "differentiation_opportunities": [
                "Position as the fastest-time-to-value provider in {category}",
                "Leverage AI accuracy guarantees as a key trust differentiator"
            ],
            "overall_competitive_score": 8.5,
            "confidence_score": 0.94
        }}"""
    else:
        raw_output = _call_live_groq_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model_name=settings.groq_model_heavy,
            temperature=0.2,
        )

    validated_analysis = validate_agent_output(raw_output)

    # Populate context object
    context.competitor_comparison = validated_analysis

    # Store validated output in ProjectMemory
    memory_mgr.write_memory(
        project_id=context.project_id,
        key="competitor_comparison",
        value=validated_analysis.model_dump(),
        source_phase="market_research",
    )

    return validated_analysis
