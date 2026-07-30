"""Industry Analysis Agent for macro sector dynamics assessment."""

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import httpx

from ai.config import get_ai_settings
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.context import MarketResearchContext
from ai.schemas.idea_validation import IdeaValidationResult
from ai.schemas.market_research import IndustryAnalysis
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


def load_agent_prompt(filename: str = "industry_analysis.md") -> str:
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
        "You are a Senior Industry Analyst & Sector Dynamics Specialist. "
        "Perform a comprehensive macro industry analysis based on validated startup outputs and market research context. "
        "Return pure JSON only matching the IndustryAnalysis schema."
    )


def validate_agent_output(raw_output: str) -> IndustryAnalysis:
    """Safely parse and validate raw LLM output into IndustryAnalysis Pydantic model.

    Args:
        raw_output: Raw string response from LLM call.

    Returns:
        Validated IndustryAnalysis object.
    """
    return validate_output(raw_output, IndustryAnalysis)


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


def get_industry_analysis_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
    mock_mode: bool = False,
    tools: Optional[List[Any]] = None,
) -> Any:
    """Returns a configured CrewAI Agent instance for Industry Analysis.

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
        f"Initializing IndustryAnalysisAgent: tier={model_tier}, temp={temperature}, mock={mock_mode}"
    )

    llm = LLMFactory.get_llm(
        model_tier=model_tier,
        temperature=temperature,
        api_key=api_key,
        mock_mode=mock_mode,
    )

    prompt_text = load_agent_prompt("industry_analysis.md")
    agent_tools = tools or []

    role = "Senior Industry Analyst & Sector Dynamics Specialist"
    goal = (
        "Conduct a comprehensive macro industry analysis evaluating industry lifecycle, growth rate, "
        "drivers, entry barriers, regulatory environment, and investment activity based on validated context."
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
        "agent_name": "industry_analysis_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": agent_tools,
        "mock_mode": mock_mode,
        "schema_class": IndustryAnalysis,
        "validate_output": validate_agent_output,
    }


def run_industry_analysis_agent(
    context: MarketResearchContext,
    memory_manager: Optional[ProjectMemoryManager] = None,
    mock_mode: bool = False,
) -> IndustryAnalysis:
    """Execute macro industry analysis reading from MarketResearchContext.

    Args:
        context: MarketResearchContext container populated by previous steps.
        memory_manager: Optional ProjectMemoryManager instance.
        mock_mode: If True, uses mock simulation response for offline testing.

    Returns:
        Validated IndustryAnalysis object.
    """
    settings = get_ai_settings()
    memory_mgr = memory_manager or ProjectMemoryManager(use_mock_store=True)

    if context.research_bundle:
        # Future enhancement: Use verified external research from ResearchManager (Tavily/Exa/Zyte)
        pass

    agent = get_industry_analysis_agent(
        model_tier=ModelTier.HEAVY,
        mock_mode=mock_mode,
    )

    idea_val = context.idea_validation
    mr_analysis = context.market_research

    category = idea_val.category_classification.primary_category
    sec_categories = ", ".join(idea_val.category_classification.secondary_categories)
    problem = idea_val.problem_analysis.problem_statement
    value_prop = idea_val.value_proposition.core_value_proposition

    mr_context_text = ""
    if mr_analysis:
        mr_context_text = (
            f"Market Stage: {mr_analysis.market_stage}\n"
            f"Market Demand: {mr_analysis.market_demand}\n"
            f"Market Overview: {mr_analysis.market_overview}\n"
        )

    system_prompt = load_agent_prompt("industry_analysis.md")
    user_prompt = (
        f"Perform an in-depth macro industry analysis for the following validated proposal:\n\n"
        f"Startup Primary Category: {category} (Secondary: {sec_categories})\n"
        f"Problem Statement: {problem}\n"
        f"Core Value Proposition: {value_prop}\n"
        f"{mr_context_text}\n"
        "Return pure JSON matching the IndustryAnalysis schema with fields: "
        "industry_name, industry_description, industry_classification, industry_lifecycle_stage, "
        "industry_maturity, industry_growth_rate, industry_drivers, industry_challenges, "
        "entry_barriers, regulatory_environment, technology_adoption, innovation_level, "
        "investment_activity, future_outlook, confidence_score."
    )

    if mock_mode:
        raw_output = f"""{{
            "industry_name": "{category} Industry",
            "industry_description": "Global sector providing technology-enabled solutions and services in {category}.",
            "industry_classification": "Software & Technology Services / {category}",
            "industry_lifecycle_stage": "Growth",
            "industry_maturity": "Growth Stage",
            "industry_growth_rate": "12.5% CAGR expected over 2024-2030",
            "industry_drivers": [
                "Accelerating digital transformation and cloud migration",
                "Increasing adoption of artificial intelligence and automation"
            ],
            "industry_challenges": [
                "High regulatory and compliance overhead",
                "Shortage of specialized technical talent"
            ],
            "entry_barriers": [
                "High customer switching costs",
                "Required domain expertise and regulatory certifications"
            ],
            "regulatory_environment": "Strict compliance environment requiring adherence to regional data privacy and industry regulations.",
            "technology_adoption": "Rapid technology adoption driven by competitive efficiency pressures.",
            "innovation_level": "High innovation intensity driven by AI advancements.",
            "investment_activity": "Strong VC and private equity investment inflows into growth-stage providers.",
            "future_outlook": "Robust 3-5 year growth trajectory backed by sustained enterprise demand.",
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
    context.industry_analysis = validated_analysis

    # Store validated output in ProjectMemory
    memory_mgr.write_memory(
        project_id=context.project_id,
        key="industry_analysis",
        value=validated_analysis.model_dump(),
        source_phase="market_research",
    )

    return validated_analysis
