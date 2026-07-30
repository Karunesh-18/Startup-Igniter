"""Trend Analysis Agent for macro, tech, consumer, and industry trend identification."""

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import httpx

from ai.config import get_ai_settings
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.context import MarketResearchContext
from ai.schemas.market_research import TrendAnalysis
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


def load_agent_prompt(filename: str = "trend_analysis.md") -> str:
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
        "You are a Senior Trend Analysis & Technology Futures Specialist. "
        "Analyze macro, technological, consumer, regulatory, and sustainability trends for the target industry. "
        "Return pure JSON only matching the TrendAnalysis schema."
    )


def validate_agent_output(raw_output: str) -> TrendAnalysis:
    """Safely parse and validate raw LLM output into TrendAnalysis Pydantic model.

    Args:
        raw_output: Raw string response from LLM call.

    Returns:
        Validated TrendAnalysis object.
    """
    return validate_output(raw_output, TrendAnalysis)


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


def get_trend_analysis_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
    mock_mode: bool = False,
    tools: Optional[List[Any]] = None,
) -> Any:
    """Returns a configured CrewAI Agent instance for Trend Analysis.

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
        f"Initializing TrendAnalysisAgent: tier={model_tier}, temp={temperature}, mock={mock_mode}"
    )

    llm = LLMFactory.get_llm(
        model_tier=model_tier,
        temperature=temperature,
        api_key=api_key,
        mock_mode=mock_mode,
    )

    prompt_text = load_agent_prompt("trend_analysis.md")
    agent_tools = tools or []

    role = "Senior Trend Analysis & Technology Futures Specialist"
    goal = (
        "Identify current, emerging, technology, consumer behavior, regulatory, sustainability, and investment trends, "
        "evaluating opportunities created and risks introduced by trends."
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
        "agent_name": "trend_analysis_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": agent_tools,
        "mock_mode": mock_mode,
        "schema_class": TrendAnalysis,
        "validate_output": validate_agent_output,
    }


def run_trend_analysis_agent(
    context: MarketResearchContext,
    memory_manager: Optional[ProjectMemoryManager] = None,
    mock_mode: bool = False,
) -> TrendAnalysis:
    """Execute trend analysis reading from MarketResearchContext.

    Args:
        context: MarketResearchContext container populated by previous steps.
        memory_manager: Optional ProjectMemoryManager instance.
        mock_mode: If True, uses mock simulation response for offline testing.

    Returns:
        Validated TrendAnalysis object.
    """
    settings = get_ai_settings()
    memory_mgr = memory_manager or ProjectMemoryManager(use_mock_store=True)

    if context.research_bundle:
        # Future enhancement: Use verified external research from ResearchManager (Tavily/Exa/Zyte)
        pass

    agent = get_trend_analysis_agent(
        model_tier=ModelTier.HEAVY,
        mock_mode=mock_mode,
    )

    idea_val = context.idea_validation
    mr_analysis = context.market_research
    ind_analysis = context.industry_analysis

    category = idea_val.category_classification.primary_category
    sec_categories = ", ".join(idea_val.category_classification.secondary_categories)
    problem = idea_val.problem_analysis.problem_statement
    value_prop = idea_val.value_proposition.core_value_proposition

    context_summary_parts = [
        f"Primary Category: {category} (Secondary: {sec_categories})",
        f"Problem Statement: {problem}",
        f"Value Proposition: {value_prop}",
    ]

    if mr_analysis:
        context_summary_parts.append(f"Market Stage: {mr_analysis.market_stage}")
        context_summary_parts.append(f"Market Demand: {mr_analysis.market_demand}")

    if ind_analysis:
        context_summary_parts.append(f"Industry Name: {ind_analysis.industry_name}")
        context_summary_parts.append(f"Industry Growth Rate: {ind_analysis.industry_growth_rate}")
        context_summary_parts.append(f"Tech Adoption Level: {ind_analysis.technology_adoption}")

    context_text = "\n".join(context_summary_parts)

    system_prompt = load_agent_prompt("trend_analysis.md")
    user_prompt = (
        f"Identify current, emerging, technology, consumer, regulatory, investment, and sustainability trends for:\n\n"
        f"{context_text}\n\n"
        "Return pure JSON matching the TrendAnalysis schema with fields: "
        "current_trends, emerging_trends, technology_trends, consumer_behavior_trends, "
        "regulatory_trends, investment_trends, sustainability_trends, future_predictions, "
        "opportunities_from_trends, risks_from_trends, trend_stability, trend_relevance, confidence_score."
    )

    if mock_mode:
        raw_output = f"""{{
            "current_trends": [
                "Accelerating adoption of generative AI in {category}",
                "Shift towards cloud-native software and API-first architectures"
            ],
            "emerging_trends": [
                "Autonomous AI agents operating in complex decision workflows",
                "Hyper-personalized real-time analytics"
            ],
            "technology_trends": [
                "Deep learning models for predictive automation",
                "Edge computing integration for low-latency processing"
            ],
            "consumer_behavior_trends": [
                "Demand for self-service digital platforms",
                "Expectation of instant response times and personalized experiences"
            ],
            "regulatory_trends": [
                "Tightening data privacy mandates (GDPR, CCPA)",
                "AI ethics and transparency governance frameworks"
            ],
            "investment_trends": [
                "High venture capital allocation towards AI-native SaaS solutions",
                "Increased strategic corporate venture activity"
            ],
            "sustainability_trends": [
                "Emphasis on energy-efficient cloud compute infrastructure",
                "ESG compliance reporting becoming standard for B2B buyers"
            ],
            "future_predictions": [
                "AI-driven personalization will become a baseline customer expectation within 3 years",
                "Consolidation of point solutions into unified platform architectures"
            ],
            "opportunities_from_trends": [
                "First-mover advantage in specialized AI workflows for {category}",
                "Ability to capture enterprise budgets shifting to intelligent automation"
            ],
            "risks_from_trends": [
                "Rapid technological obsolescence if architecture is not modular",
                "Increasing regulatory compliance costs"
            ],
            "trend_stability": "Highly Stable Long-Term Growth",
            "trend_relevance": "Critical High Impact",
            "confidence_score": 0.95
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
    context.trend_analysis = validated_analysis

    # Store validated output in ProjectMemory
    memory_mgr.write_memory(
        project_id=context.project_id,
        key="trend_analysis",
        value=validated_analysis.model_dump(),
        source_phase="market_research",
    )

    return validated_analysis
