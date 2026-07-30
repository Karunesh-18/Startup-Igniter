"""TAM SAM SOM Estimator Agent for market sizing calculations."""

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import httpx

from ai.config import get_ai_settings
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.context import MarketResearchContext
from ai.schemas.market_research import TAMSAMSOMAnalysis
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


def load_agent_prompt(filename: str = "tam_sam_som.md") -> str:
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
        "You are a Senior Financial & Market Sizing Specialist. "
        "Estimate TAM, SAM, SOM values, descriptions, and methodology based on validated startup outputs. "
        "Return pure JSON matching the TAMSAMSOMAnalysis schema."
    )


def validate_agent_output(raw_output: str) -> TAMSAMSOMAnalysis:
    """Safely parse and validate raw LLM output into TAMSAMSOMAnalysis Pydantic model.

    Args:
        raw_output: Raw string response from LLM call.

    Returns:
        Validated TAMSAMSOMAnalysis object.
    """
    return validate_output(raw_output, TAMSAMSOMAnalysis)


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


def get_tam_sam_som_estimator_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
    mock_mode: bool = False,
    tools: Optional[List[Any]] = None,
) -> Any:
    """Returns a configured CrewAI Agent instance for TAM SAM SOM estimation."""
    ai_logger.info(
        f"Initializing TAMSAMSOMEstimatorAgent: tier={model_tier}, temp={temperature}, mock={mock_mode}"
    )

    llm = LLMFactory.get_llm(
        model_tier=model_tier,
        temperature=temperature,
        api_key=api_key,
        mock_mode=mock_mode,
    )

    prompt_text = load_agent_prompt("tam_sam_som.md")
    agent_tools = tools or []

    role = "Senior Financial & Market Sizing Specialist"
    goal = (
        "Quantify Total Addressable Market (TAM), Serviceable Addressable Market (SAM), "
        "and Serviceable Obtainable Market (SOM) using rigorous top-down and bottom-up financial methodologies."
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

    return {
        "agent_name": "tam_sam_som_estimator_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": agent_tools,
        "mock_mode": mock_mode,
        "schema_class": TAMSAMSOMAnalysis,
        "validate_output": validate_agent_output,
    }


def run_tam_sam_som_estimator_agent(
    context: MarketResearchContext,
    memory_manager: Optional[ProjectMemoryManager] = None,
    mock_mode: bool = False,
) -> TAMSAMSOMAnalysis:
    """Execute TAM SAM SOM estimation reading from MarketResearchContext.

    Args:
        context: MarketResearchContext container populated by previous steps.
        memory_manager: Optional ProjectMemoryManager instance.
        mock_mode: If True, uses mock simulation response for offline testing.

    Returns:
        Validated TAMSAMSOMAnalysis object.
    """
    settings = get_ai_settings()
    memory_mgr = memory_manager or ProjectMemoryManager(use_mock_store=True)

    if context.research_bundle:
        # Future enhancement: Use verified external research from ResearchManager (Tavily/Exa/Zyte)
        pass

    agent = get_tam_sam_som_estimator_agent(
        model_tier=ModelTier.HEAVY,
        mock_mode=mock_mode,
    )

    idea_val = context.idea_validation
    mr_analysis = context.market_research
    ind_analysis = context.industry_analysis
    tr_analysis = context.trend_analysis
    comp_comp = context.competitor_comparison
    persona = context.customer_persona

    category = idea_val.category_classification.primary_category
    value_prop = idea_val.value_proposition.core_value_proposition

    context_parts = [
        f"Idea Text: '{idea_val.idea_text}'",
        f"Primary Category: {category}",
        f"Value Proposition: {value_prop}",
    ]

    if ind_analysis:
        context_parts.append(f"Industry Name: {ind_analysis.industry_name}")
    if persona:
        context_parts.append(f"Primary Persona Occupation: {persona.primary_persona.occupation}")
        context_parts.append(f"Primary Persona Income/Budget: {persona.primary_persona.income_range}")

    context_text = "\n".join(context_parts)

    system_prompt = load_agent_prompt("tam_sam_som.md")
    user_prompt = (
        f"Estimate TAM, SAM, and SOM values and market sizing methodology for:\n\n"
        f"{context_text}\n\n"
        "Return pure JSON matching the TAMSAMSOMAnalysis schema with tam_description, tam_value, sam_description, sam_value, som_description, som_value, methodology, confidence_score."
    )

    if mock_mode:
        raw_output = f"""{{
            "tam_description": "Global market for {category} software applications across mid-market and enterprise organizations.",
            "tam_value": "$38.5 Billion",
            "sam_description": "Serviceable addressable market within North America and Europe targeting B2B operations departments.",
            "sam_value": "$5.4 Billion",
            "som_description": "Realistic serviceable obtainable market targetable within 3 years assuming 2.5% market capture.",
            "som_value": "$135 Million",
            "methodology": "Hybrid top-down industry benchmark evaluation combined with bottom-up ARPU per persona estimation.",
            "confidence_score": 0.90
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
    context.tam_sam_som = validated_analysis

    # Store validated output in ProjectMemory
    memory_mgr.write_memory(
        project_id=context.project_id,
        key="tam_sam_som",
        value=validated_analysis.model_dump(),
        source_phase="market_research",
    )

    return validated_analysis
