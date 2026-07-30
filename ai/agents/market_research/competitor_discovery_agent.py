"""Competitor Discovery Agent for identifying direct, indirect, and emerging market competitors."""

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import httpx

from ai.config import get_ai_settings
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.context import MarketResearchContext
from ai.schemas.market_research import CompetitorDiscovery
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


def load_agent_prompt(filename: str = "competitor_discovery.md") -> str:
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
        "You are a Senior Competitor Intelligence & Market Landscape Specialist. "
        "Discover direct, indirect, and emerging competitors, market leaders, and alternative solutions. "
        "Return pure JSON only matching the CompetitorDiscovery schema."
    )


def validate_agent_output(raw_output: str) -> CompetitorDiscovery:
    """Safely parse and validate raw LLM output into CompetitorDiscovery Pydantic model.

    Args:
        raw_output: Raw string response from LLM call.

    Returns:
        Validated CompetitorDiscovery object.
    """
    return validate_output(raw_output, CompetitorDiscovery)


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


def get_competitor_discovery_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
    mock_mode: bool = False,
    tools: Optional[List[Any]] = None,
) -> Any:
    """Returns a configured CrewAI Agent instance for Competitor Discovery.

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
        f"Initializing CompetitorDiscoveryAgent: tier={model_tier}, temp={temperature}, mock={mock_mode}"
    )

    llm = LLMFactory.get_llm(
        model_tier=model_tier,
        temperature=temperature,
        api_key=api_key,
        mock_mode=mock_mode,
    )

    prompt_text = load_agent_prompt("competitor_discovery.md")
    agent_tools = tools or []

    role = "Senior Competitor Intelligence & Market Landscape Specialist"
    goal = (
        "Identify direct, indirect, and emerging competitors, market leaders, startup challengers, "
        "and alternative solutions based on validated proposal context."
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
        "agent_name": "competitor_discovery_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": agent_tools,
        "mock_mode": mock_mode,
        "schema_class": CompetitorDiscovery,
        "validate_output": validate_agent_output,
    }


def run_competitor_discovery_agent(
    context: MarketResearchContext,
    memory_manager: Optional[ProjectMemoryManager] = None,
    mock_mode: bool = False,
) -> CompetitorDiscovery:
    """Execute competitor discovery reading from MarketResearchContext.

    Args:
        context: MarketResearchContext container populated by previous steps.
        memory_manager: Optional ProjectMemoryManager instance.
        mock_mode: If True, uses mock simulation response for offline testing.

    Returns:
        Validated CompetitorDiscovery object.
    """
    settings = get_ai_settings()
    memory_mgr = memory_manager or ProjectMemoryManager(use_mock_store=True)

    if context.research_bundle:
        # Future enhancement: Use verified external research from ResearchManager (Tavily/Exa/Zyte)
        pass

    agent = get_competitor_discovery_agent(
        model_tier=ModelTier.HEAVY,
        mock_mode=mock_mode,
    )

    idea_val = context.idea_validation
    mr_analysis = context.market_research
    ind_analysis = context.industry_analysis
    tr_analysis = context.trend_analysis

    category = idea_val.category_classification.primary_category
    sec_categories = ", ".join(idea_val.category_classification.secondary_categories)
    problem = idea_val.problem_analysis.problem_statement
    value_prop = idea_val.value_proposition.core_value_proposition
    target_customers = ", ".join(idea_val.customer_identification.primary_customers)

    context_parts = [
        f"Idea Text: '{idea_val.idea_text}'",
        f"Primary Category: {category} (Secondary: {sec_categories})",
        f"Problem Statement: {problem}",
        f"Target Customers: {target_customers}",
        f"Value Proposition: {value_prop}",
    ]

    if mr_analysis:
        context_parts.append(f"Market Stage: {mr_analysis.market_stage}")
    if ind_analysis:
        context_parts.append(f"Industry Name: {ind_analysis.industry_name}")
    if tr_analysis:
        context_parts.append(f"Tech Trends: {', '.join(tr_analysis.technology_trends[:3])}")

    context_text = "\n".join(context_parts)

    system_prompt = load_agent_prompt("competitor_discovery.md")
    user_prompt = (
        f"Identify direct, indirect, and emerging competitors, market leaders, startup challengers, and alternative solutions for:\n\n"
        f"{context_text}\n\n"
        "Return pure JSON matching the CompetitorDiscovery schema with fields: "
        "direct_competitors, indirect_competitors, emerging_competitors, market_leaders, "
        "startup_challengers, alternative_solutions, competition_intensity, major_competitor_count, confidence_score."
    )

    if mock_mode:
        raw_output = f"""{{
            "direct_competitors": [
                {{
                    "name": "Leading{category}Platform",
                    "category": "Direct",
                    "description": "Established provider of cloud-based {category} solutions for mid-market clients.",
                    "target_market": "Enterprise & Mid-market",
                    "primary_offering": "Cloud {category} Platform"
                }},
                {{
                    "name": "Global{category}Corp",
                    "category": "Direct",
                    "description": "Legacy market leader with widespread enterprise integration.",
                    "target_market": "Global Enterprise",
                    "primary_offering": "Legacy {category} Suite"
                }}
            ],
            "indirect_competitors": [
                {{
                    "name": "GenericSaaSProvider",
                    "category": "Indirect",
                    "description": "Generic workflow automation suite customizable for {category}.",
                    "target_market": "General B2B Businesses",
                    "primary_offering": "Workflow Automation Suite"
                }}
            ],
            "emerging_competitors": [
                {{
                    "name": "NextGenAIStartup",
                    "category": "Emerging",
                    "description": "Early-stage YC backed AI startup disrupting niche sub-segments.",
                    "target_market": "Early Adopter Tech Startups",
                    "primary_offering": "AI Autonomous Agent Tooling"
                }}
            ],
            "market_leaders": ["Global{category}Corp", "Leading{category}Platform"],
            "startup_challengers": ["NextGenAIStartup", "InnovateAI"],
            "alternative_solutions": ["Manual Spreadsheets", "In-house Custom Scripts", "Outsourced Agencies"],
            "competition_intensity": "Moderate to High",
            "major_competitor_count": 5,
            "confidence_score": 0.93
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
    context.competitor_discovery = validated_analysis

    # Store validated output in ProjectMemory
    memory_mgr.write_memory(
        project_id=context.project_id,
        key="competitor_discovery",
        value=validated_analysis.model_dump(),
        source_phase="market_research",
    )

    return validated_analysis
