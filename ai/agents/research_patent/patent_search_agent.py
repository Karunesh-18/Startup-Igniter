"""Patent Search Agent for analytical IP landscape, prior art, and white space discovery."""

import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ai.config import get_ai_settings
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.context import ResearchPatentContext
from ai.schemas.idea_validation import IdeaValidationResult
from ai.schemas.market_research import MarketResearchResult
from ai.schemas.research_patent import PatentAnalysis
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


def load_agent_prompt(filename: str = "patent_search.md") -> str:
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
        "You are a Senior Patent & Intellectual Property Research Specialist. "
        "Perform a high-level analytical assessment of existing patent activity, prior art, major assignees, "
        "freedom-to-operate observations, and unclaimed white spaces for the startup proposal. "
        "Return pure JSON only matching the PatentAnalysis schema."
    )


def validate_agent_output(raw_output: str) -> PatentAnalysis:
    """Safely parse and validate raw LLM output into PatentAnalysis Pydantic model.

    Args:
        raw_output: Raw string response from LLM call.

    Returns:
        Validated PatentAnalysis object.
    """
    return validate_output(raw_output, PatentAnalysis)


def get_patent_search_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temp: float = 0.2,
    mock_mode: bool = False,
) -> Union[Any, Dict[str, Any]]:
    """Initialize PatentSearchAgent instance or fallback definition dict.

    Args:
        model_tier: LLM model tier selection.
        temp: Temperature setting for LLM call.
        mock_mode: If True, operates in simulation mode without network LLM calls.

    Returns:
        CrewAI Agent object if HAS_CREWAI is True, otherwise agent configuration dictionary.
    """
    role = "Patent & Intellectual Property Research Specialist"
    goal = (
        "Analyze startup technology concepts to assess patent landscape density, identify major assignees, "
        "discover unclaimed white spaces, evaluate freedom-to-operate observations, and uncover patentability opportunities."
    )
    backstory = (
        "You are a world-class patent attorney and IP strategist with deep expertise in global patent databases "
        "(USPTO, EPO, WIPO), prior art analysis, technological white space identification, and FTO risk mitigation."
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
        "agent_name": "patent_search_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": agent_tools,
        "mock_mode": mock_mode,
        "schema_class": PatentAnalysis,
        "validate_output": validate_agent_output,
    }


def run_patent_search_agent(
    context: Union[ResearchPatentContext, IdeaValidationResult],
    memory_manager: Optional[ProjectMemoryManager] = None,
    mock_mode: bool = False,
) -> PatentAnalysis:
    """Execute patent landscape & prior art assessment using ResearchPatentContext container.

    Args:
        context: ResearchPatentContext container (or IdeaValidationResult for backward compatibility).
        memory_manager: Optional ProjectMemoryManager instance.
        mock_mode: If True, uses mock simulation response for offline testing.

    Returns:
        Validated PatentAnalysis object.
    """
    if isinstance(context, ResearchPatentContext):
        patent_context = context
        validation_result = context.idea_validation
        project_id = context.project_id
        mr_result = context.market_research
    else:
        validation_result = context
        project_id = validation_result.project_id
        patent_context = ResearchPatentContext(
            project_id=project_id,
            idea_validation=validation_result,
        )
        mr_result = None

    ai_logger.info(
        f"Initializing PatentSearchAgent: tier={ModelTier.HEAVY}, temp=0.2, mock={mock_mode}"
    )

    # Research bundle placeholder check (Future Version 2 Tavily/Exa/Zyte integration)
    if patent_context.research_bundle:
        ai_logger.debug("PatentSearchAgent: Optional research_bundle present in context.")

    ai_logger.info(f"Running PatentSearchAgent for project '{project_id}'...")

    category = validation_result.category_classification.primary_category
    sec_categories = ", ".join(validation_result.category_classification.secondary_categories)
    problem = validation_result.problem_analysis.problem_statement
    value_prop = validation_result.value_proposition.core_value_proposition
    innovation_score = validation_result.innovation_scoring.overall_innovation_score

    mr_context_text = ""
    if mr_result and mr_result.industry_analysis:
        mr_context_text += f"\nIndustry Name: {mr_result.industry_analysis.industry_name}"
    if mr_result and mr_result.market_research:
        mr_context_text += f"\nMarket Stage: {mr_result.market_research.market_stage}"

    system_prompt = load_agent_prompt("patent_search.md")
    user_prompt = (
        f"Perform an analytical patent search and IP landscape assessment for the following startup proposal:\n\n"
        f"Idea Text: '{validation_result.idea_text}'\n"
        f"Primary Category: {category} (Secondary: {sec_categories})\n"
        f"Problem Statement: {problem}\n"
        f"Core Value Proposition: {value_prop}\n"
        f"Innovation Score: {innovation_score}/100"
        f"{mr_context_text}\n\n"
        "Return pure JSON matching the PatentAnalysis schema with fields: "
        "existing_patent_summary, patent_landscape, major_patent_holders, related_technology_domains, "
        "patent_activity_level, potential_patent_conflicts, white_space_opportunities, patentability_assessment, "
        "freedom_to_operate_observations, innovation_opportunities, patent_risks, novelty_assessment, confidence_score."
    )

    if mock_mode:
        raw_output = f"""{{
            "existing_patent_summary": "Active patent ecosystem surrounding {category} technologies with strong foundational coverage by enterprise leaders.",
            "patent_landscape": "Moderate density patent landscape with accelerating filings in machine learning architectures and automated workflows.",
            "major_patent_holders": [
                "International Business Machines Corp (IBM)",
                "Microsoft Corporation",
                "Google LLC / Alphabet Inc."
            ],
            "related_technology_domains": [
                "G06N - Computer systems based on specific computational models",
                "G06F - Electric digital data processing"
            ],
            "patent_activity_level": "High",
            "potential_patent_conflicts": [
                "Potential overlapping claims around real-time automated data ingestion pipelines",
                "Broad patents on adaptive user interface personalization"
            ],
            "white_space_opportunities": [
                "Unclaimed white space in lightweight context-aware micro-learning algorithms",
                "Integration of real-time developer commit hooks with dynamic challenge generation"
            ],
            "patentability_assessment": "Core concept demonstrates strong patentability in its specific algorithmic orchestration and commit-triggered workflow.",
            "freedom_to_operate_observations": [
                "FTO is favorable for software application layer implementation",
                "Recommend filing narrow utility patent focusing on commit-driven challenge synthesis"
            ],
            "innovation_opportunities": [
                "Patent proprietary developer behavior feedback loop architecture",
                "Protect unique real-time code snippet dynamic evaluation method"
            ],
            "patent_risks": [
                "Risk of broad prior art claims from legacy e-learning assignees",
                "Patent thicket around generic automated question generation"
            ],
            "novelty_assessment": "High technical novelty specifically in the real-time GitHub event triggers combined with automated micro-coding challenge synthesis.",
            "confidence_score": 0.85
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
    ai_logger.info("Pydantic Validation Success: PatentAnalysis successfully validated.")

    memory_mgr = memory_manager or ProjectMemoryManager(use_mock_store=True)
    memory_mgr.write_memory(
        project_id=project_id,
        key="patent_analysis",
        value=validated_analysis.model_dump(),
        source_phase="research_patent",
    )
    ai_logger.info(f"[LOCAL MEMORY] Saved 'patent_analysis' for project '{project_id}' in phase 'research_patent'")

    if isinstance(context, ResearchPatentContext):
        context.patent_analysis = validated_analysis

    ai_logger.info(
        f"Task Success: Patent Activity Level = '{validated_analysis.patent_activity_level}', "
        f"Confidence = {validated_analysis.confidence_score}"
    )
    ai_logger.info(f"Completed PatentSearchAgent for project '{project_id}'.")

    return validated_analysis
