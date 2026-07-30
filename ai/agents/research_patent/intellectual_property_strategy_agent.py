"""Intellectual Property Strategy Agent for formulating patent strategy, trade secrets, and IP defensibility."""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ai.config import get_ai_settings
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.context import ResearchPatentContext
from ai.schemas.research_patent import IPStrategy
from ai.shared.constants import ModelTier
from ai.shared.llm_provider import LLMFactory
from ai.shared.logger import ai_logger
from ai.shared.output_validator import validate_output

try:
    from crewai import Agent as CrewAIAgent  # type: ignore
    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False
    CrewAIAgent = None


def load_agent_prompt(filename: str = "intellectual_property_strategy.md") -> str:
    """Load agent prompt instructions from prompts/research_patent directory."""
    prompt_path = (
        Path(__file__).resolve().parent.parent.parent
        / "prompts"
        / "research_patent"
        / filename
    )
    if prompt_path.is_file():
        return prompt_path.read_text(encoding="utf-8")
    ai_logger.warning(
        f"Prompt file '{filename}' not found at {prompt_path}. Using default fallback prompt."
    )
    return (
        "You are a Chief IP Counsel & Strategic Patent Strategist. "
        "Formulate an actionable IP strategy covering patents, trade secrets, copyright, licensing, "
        "defensive IP, open-source strategy, and IP defensibility score. Return pure JSON matching IPStrategy schema."
    )


def validate_agent_output(raw_output: str) -> IPStrategy:
    """Safely parse and validate raw LLM output into IPStrategy model."""
    return validate_output(raw_output, IPStrategy)


def get_intellectual_property_strategy_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temp: float = 0.2,
    mock_mode: bool = False,
) -> Union[Any, Dict[str, Any]]:
    """Initialize IntellectualPropertyStrategyAgent instance or fallback definition dict."""
    role = "Chief IP Counsel & Strategic Patent Strategist"
    goal = (
        "Formulate a multi-layered IP protection strategy recommending patent filings, trade secret protections, "
        "copyright boundaries, licensing frameworks, open-source strategy, and defensive publication tactics."
    )
    backstory = (
        "You are a partner at a leading tech IP law firm with deep expertise in software patents, "
        "open-source dual-licensing models, trade secret protection frameworks, and enterprise IP moats."
    )

    llm = LLMFactory.get_llm(tier=model_tier, temperature=temp, mock_mode=mock_mode)
    agent_tools: list[Any] = []

    if HAS_CREWAI and CrewAIAgent is not None:
        return CrewAIAgent(
            role=role,
            goal=goal,
            backstory=backstory,
            verbose=True,
            allow_delegation=False,
            tools=agent_tools,
            llm=llm,
        )

    return {
        "agent_name": "intellectual_property_strategy_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": agent_tools,
        "mock_mode": mock_mode,
        "schema_class": IPStrategy,
        "validate_output": validate_agent_output,
    }


def run_intellectual_property_strategy_agent(
    context: ResearchPatentContext,
    memory_manager: Optional[ProjectMemoryManager] = None,
    mock_mode: bool = False,
) -> IPStrategy:
    """Execute IP strategy formulation reading from ResearchPatentContext container."""
    project_id = context.project_id
    idea_val = context.idea_validation
    patent_res = context.patent_analysis
    gap_res = context.innovation_gap_analysis
    trl_res = context.technology_readiness

    ai_logger.info(
        f"Initializing IntellectualPropertyStrategyAgent: tier={ModelTier.HEAVY}, temp=0.2, mock={mock_mode}"
    )

    if context.research_bundle:
        ai_logger.debug("IntellectualPropertyStrategyAgent: Optional research_bundle present in context.")

    ai_logger.info(f"Running IntellectualPropertyStrategyAgent for project '{project_id}'...")

    category = idea_val.category_classification.primary_category
    problem = idea_val.problem_analysis.problem_statement
    value_prop = idea_val.value_proposition.core_value_proposition

    prev_context = ""
    if patent_res:
        prev_context += f"\nPatentability Assessment: {patent_res.patentability_assessment}"
    if gap_res:
        prev_context += f"\nDifferentiation Opportunities: {', '.join(gap_res.differentiation_opportunities)}"

    system_prompt = load_agent_prompt("intellectual_property_strategy.md")
    user_prompt = (
        f"Formulate a comprehensive IP protection strategy for the following startup proposal:\n\n"
        f"Idea Text: '{idea_val.idea_text}'\n"
        f"Primary Category: {category}\n"
        f"Problem Statement: {problem}\n"
        f"Value Proposition: {value_prop}"
        f"{prev_context}\n\n"
        "Return pure JSON matching the IPStrategy schema with fields: "
        "patent_strategy_recommendations, trade_secret_opportunities, copyright_protection_areas, "
        "licensing_considerations, defensive_ip_tactics, open_source_strategy, ip_defensibility_score, "
        "confidence_score, reasoning_summary, recommendations."
    )

    if mock_mode:
        raw_output = f"""{{
            "patent_strategy_recommendations": [
                "File US provisional utility patent for 'Event-driven repository commit analysis to micro-coding challenge synthesis'",
                "Pursue PCT international application within 12 months targeting US, EU, and JP markets"
            ],
            "trade_secret_opportunities": [
                "Proprietary AST feature extraction heuristics and prompt distillation templates",
                "Developer interaction telemetry dataset used for difficulty calibration"
            ],
            "copyright_protection_areas": [
                "Proprietary backend challenge synthesis engine source code",
                "Curated micro-challenge problem library and solution test suites"
            ],
            "licensing_considerations": [
                "B2B SaaS commercial API subscription agreement with non-exclusive usage rights",
                "Strict enterprise data privacy clause (no customer code used for public model training)"
            ],
            "defensive_ip_tactics": [
                "Publish defensive blog post on generic commit trigger mechanics to prevent competitor broad patents",
                "Maintain internal timestamped engineering logs for prior invention proof"
            ],
            "open_source_strategy": "Dual-licensing / Open-core model (Open-source CLI/SDK under Apache 2.0 + Closed-source enterprise AI engine)",
            "ip_defensibility_score": 83,
            "confidence_score": 0.90,
            "reasoning_summary": "Strong multi-layered IP moat combining provisional utility patent, backend trade secrets, and open-core developer adoption strategy.",
            "recommendations": [
                "File provisional utility patent prior to public marketing announcement",
                "Establish strict internal trade secret access controls for LLM prompt templates"
            ]
        }}"""
    else:
        ai_logger.info(f"Initializing LLM: model=openrouter/{get_ai_settings().openrouter_model_heavy}, temp=0.2, mock=False")
        from ai.shared.llm_provider import call_live_llm
        raw_output = call_live_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model_name=get_ai_settings().openrouter_model_heavy,
            temperature=0.2,
        )

    validated_analysis = validate_agent_output(raw_output)
    ai_logger.info("Pydantic Validation Success: IPStrategy successfully validated.")

    memory_mgr = memory_manager or ProjectMemoryManager(use_mock_store=True)
    memory_mgr.write_memory(
        project_id=project_id,
        key="ip_strategy",
        value=validated_analysis.model_dump(),
        source_phase="research_patent",
    )
    ai_logger.info(f"[LOCAL MEMORY] Saved 'ip_strategy' for project '{project_id}' in phase 'research_patent'")

    context.ip_strategy = validated_analysis

    ai_logger.info(
        f"Task Success: IP Defensibility Score = {validated_analysis.ip_defensibility_score}, "
        f"Confidence = {validated_analysis.confidence_score}"
    )
    ai_logger.info(f"Completed IntellectualPropertyStrategyAgent for project '{project_id}'.")

    return validated_analysis
