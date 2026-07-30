"""Market Research Agent for high-level market landscape assessment."""

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import httpx

from ai.config import get_ai_settings
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.context import MarketResearchContext
from ai.schemas.idea_validation import IdeaValidationResult
from ai.schemas.market_research import MarketResearchAnalysis
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


def load_agent_prompt(filename: str = "market_research.md") -> str:
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
        "You are a Senior Market Research & Industry Analysis Specialist. "
        "Perform a high-level macro market assessment for the startup proposal based on validation findings. "
        "Return pure JSON only matching the MarketResearchAnalysis schema."
    )


def validate_agent_output(raw_output: str) -> MarketResearchAnalysis:
    """Safely parse and validate raw LLM output into MarketResearchAnalysis Pydantic model.

    Args:
        raw_output: Raw string response from LLM call.

    Returns:
        Validated MarketResearchAnalysis object.
    """
    return validate_output(raw_output, MarketResearchAnalysis)


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


def get_market_research_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
    mock_mode: bool = False,
    tools: Optional[List[Any]] = None,
) -> Any:
    """Returns a configured CrewAI Agent instance for Market Research.

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
        f"Initializing MarketResearchAgent: tier={model_tier}, temp={temperature}, mock={mock_mode}"
    )

    llm = LLMFactory.get_llm(
        model_tier=model_tier,
        temperature=temperature,
        api_key=api_key,
        mock_mode=mock_mode,
    )

    prompt_text = load_agent_prompt("market_research.md")
    agent_tools = tools or []

    role = "Senior Market Research & Industry Analysis Specialist"
    goal = (
        "Conduct a comprehensive high-level market assessment analyzing market stage, "
        "maturity, demand drivers, opportunities, challenges, and future trajectory based on validated startup outputs."
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
        "agent_name": "market_research_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": agent_tools,
        "mock_mode": mock_mode,
        "schema_class": MarketResearchAnalysis,
        "validate_output": validate_agent_output,
    }


def run_market_research_agent(
    context: Union[MarketResearchContext, IdeaValidationResult],
    memory_manager: Optional[ProjectMemoryManager] = None,
    mock_mode: bool = False,
) -> MarketResearchAnalysis:
    """Execute high-level market assessment using MarketResearchContext container.

    Args:
        context: MarketResearchContext container (or IdeaValidationResult for backward compatibility).
        memory_manager: Optional ProjectMemoryManager instance.
        mock_mode: If True, uses mock simulation response for offline testing.

    Returns:
        Validated MarketResearchAnalysis object.
    """
    if isinstance(context, MarketResearchContext):
        market_context = context
        validation_result = context.idea_validation
        project_id = context.project_id
    else:
        validation_result = context
        project_id = validation_result.project_id
        market_context = MarketResearchContext(
            project_id=project_id,
            idea_validation=validation_result,
        )

    settings = get_ai_settings()
    memory_mgr = memory_manager or ProjectMemoryManager(use_mock_store=True)

    if market_context.research_bundle:
        # Future enhancement: Use verified external research from ResearchManager (Tavily/Exa/Zyte)
        pass

    agent = get_market_research_agent(
        model_tier=ModelTier.HEAVY,
        mock_mode=mock_mode,
    )

    category = validation_result.category_classification.primary_category
    sec_categories = ", ".join(validation_result.category_classification.secondary_categories)
    problem = validation_result.problem_analysis.problem_statement
    customers = ", ".join(validation_result.customer_identification.primary_customers)
    value_prop = validation_result.value_proposition.core_value_proposition
    innovation_score = validation_result.innovation_scoring.overall_innovation_score

    system_prompt = load_agent_prompt("market_research.md")
    user_prompt = (
        f"Perform a high-level market assessment for the following validated startup proposal:\n\n"
        f"Idea Text: '{validation_result.idea_text}'\n"
        f"Startup Primary Category: {category} (Secondary: {sec_categories})\n"
        f"Problem Statement: {problem}\n"
        f"Target Primary Customers: {customers}\n"
        f"Core Value Proposition: {value_prop}\n"
        f"Overall Innovation Score: {innovation_score}/100\n\n"
        "Return pure JSON matching the MarketResearchAnalysis schema with fields: "
        "market_overview, industry_overview, market_stage, market_maturity, market_size_summary, "
        "market_demand, market_opportunities, market_challenges, growth_drivers, market_risks, "
        "future_outlook, confidence_score."
    )

    if mock_mode:
        raw_output = f"""{{
            "market_overview": "High-growth market landscape driven by digital transformation in {category}.",
            "industry_overview": "Rapidly evolving {category} sector with increasing technology adoption.",
            "market_stage": "Growth",
            "market_maturity": "Growth Stage",
            "market_size_summary": "Multi-billion dollar global market opportunity with strong CAGR expansion.",
            "market_demand": "High accelerating demand across key target customer segments.",
            "market_opportunities": [
                "Expansion into underserved regional markets",
                "Integration with next-generation AI automation frameworks"
            ],
            "market_challenges": [
                "Navigating complex regulatory compliance frameworks",
                "Customer acquisition friction in legacy environments"
            ],
            "growth_drivers": [
                "Surging demand for automated AI solutions",
                "Increasing institutional investment in modern technology"
            ],
            "market_risks": [
                "Macroeconomic volatility affecting technology budgets",
                "Competitive entry from incumbent platform providers"
            ],
            "future_outlook": "Positive 3-5 year growth outlook with strong market expansion potential.",
            "confidence_score": 0.92
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
    market_context.market_research = validated_analysis

    # Store validated output in ProjectMemory
    memory_mgr.write_memory(
        project_id=project_id,
        key="market_research",
        value=validated_analysis.model_dump(),
        source_phase="market_research",
    )

    return validated_analysis
