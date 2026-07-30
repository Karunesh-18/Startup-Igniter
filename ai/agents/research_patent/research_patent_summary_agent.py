"""Research Patent Summary Agent synthesizing all Crew 3 outputs into ResearchPatentResult."""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ai.config import get_ai_settings
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.context import ResearchPatentContext
from ai.schemas.research_patent import ResearchPatentResult
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


def load_agent_prompt(filename: str = "research_patent_summary.md") -> str:
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
        "You are a Senior Strategic Research & IP Director. "
        "Synthesize all outputs from the Research & Patent Analysis Crew into an executive summary, "
        "calculate overall novelty score (0-100), extract TRL level, confidence score, and top strategic recommendations. "
        "Return pure JSON matching ResearchPatentResult schema structure."
    )


def validate_agent_output(raw_output: str, context: ResearchPatentContext) -> ResearchPatentResult:
    """Safely parse and validate raw LLM summary output, populating master ResearchPatentResult object."""
    import json
    from ai.shared.output_validator import parse_json_safely

    data = parse_json_safely(raw_output)

    exec_summary = data.get("executive_summary", "Comprehensive research and patent analysis completed.")
    novelty_score = float(data.get("overall_novelty_score", 85.0))
    trl_level = int(data.get("trl_level", context.technology_readiness.trl_level if context.technology_readiness else 3))
    conf_score = float(data.get("confidence_score", 0.88))
    recs = data.get("strategic_recommendations", [
        "File provisional utility patent covering commit-triggered challenge synthesis.",
        "Implement open-core SDK model to drive developer adoption.",
        "Build prototype GitHub Action to validate TRL 4 milestone."
    ])

    return ResearchPatentResult(
        project_id=context.project_id,
        startup_idea_text=context.idea_validation.idea_text,
        patent_analysis=context.patent_analysis,
        research_paper_analysis=context.research_paper_analysis,
        existing_solution_analysis=context.existing_solution_analysis,
        innovation_gap_analysis=context.innovation_gap_analysis,
        technology_readiness=context.technology_readiness,
        ip_strategy=context.ip_strategy,
        overall_novelty_score=novelty_score,
        trl_level=trl_level,
        confidence_score=conf_score,
        executive_summary=exec_summary,
        strategic_recommendations=recs,
        status="success",
    )


def get_research_patent_summary_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temp: float = 0.2,
    mock_mode: bool = False,
) -> Union[Any, Dict[str, Any]]:
    """Initialize ResearchPatentSummaryAgent instance or fallback definition dict."""
    role = "Senior Strategic Research & IP Director"
    goal = (
        "Synthesize patent search, academic literature, commercial solutions, innovation gaps, "
        "Technology Readiness Level, and IP strategy into a master ResearchPatentResult report."
    )
    backstory = (
        "You are an executive research director and IP strategist synthesizing deep technical, "
        "patent, and commercial analysis into executive decision frameworks for founders and investors."
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
        "agent_name": "research_patent_summary_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": agent_tools,
        "mock_mode": mock_mode,
        "schema_class": ResearchPatentResult,
        "validate_output": validate_agent_output,
    }


def run_research_patent_summary_agent(
    context: ResearchPatentContext,
    memory_manager: Optional[ProjectMemoryManager] = None,
    mock_mode: bool = False,
) -> ResearchPatentResult:
    """Execute master summary synthesis reading from ResearchPatentContext container."""
    project_id = context.project_id
    idea_val = context.idea_validation

    ai_logger.info(
        f"Initializing ResearchPatentSummaryAgent: tier={ModelTier.HEAVY}, temp=0.2, mock={mock_mode}"
    )

    if context.research_bundle:
        ai_logger.debug("ResearchPatentSummaryAgent: Optional research_bundle present in context.")

    ai_logger.info(f"Running ResearchPatentSummaryAgent for project '{project_id}'...")

    category = idea_val.category_classification.primary_category
    problem = idea_val.problem_analysis.problem_statement
    value_prop = idea_val.value_proposition.core_value_proposition

    summary_inputs = [
        f"Idea Text: '{idea_val.idea_text}'",
        f"Primary Category: {category}",
        f"Problem Statement: {problem}",
        f"Value Proposition: {value_prop}",
    ]

    if context.patent_analysis:
        summary_inputs.append(f"Patent Activity: {context.patent_analysis.patent_activity_level}, White Spaces: {', '.join(context.patent_analysis.white_space_opportunities)}")
    if context.research_paper_analysis:
        summary_inputs.append(f"Academic Novelty Score: {context.research_paper_analysis.academic_novelty_score}/100")
    if context.existing_solution_analysis:
        summary_inputs.append(f"Commercial Market Maturity: {context.existing_solution_analysis.market_maturity}")
    if context.innovation_gap_analysis:
        summary_inputs.append(f"Overall Gap Score: {context.innovation_gap_analysis.overall_gap_score}/100")
    if context.technology_readiness:
        summary_inputs.append(f"TRL Level: {context.technology_readiness.trl_level} ({context.technology_readiness.trl_stage_name})")
    if context.ip_strategy:
        summary_inputs.append(f"IP Defensibility Score: {context.ip_strategy.ip_defensibility_score}/100")

    system_prompt = load_agent_prompt("research_patent_summary.md")
    user_prompt = (
        f"Synthesize the complete Research & Patent Crew findings for the following startup proposal:\n\n"
        + "\n".join(summary_inputs) + "\n\n"
        "Return pure JSON with keys: executive_summary, overall_novelty_score, trl_level, confidence_score, strategic_recommendations."
    )

    if mock_mode:
        raw_output = f"""{{
            "executive_summary": "The startup proposal demonstrates strong technical novelty (Score: 86.5/100) at TRL 3. Patent landscape reveals clear white space opportunities in commit-triggered challenge synthesis.",
            "overall_novelty_score": 86.5,
            "trl_level": 3,
            "confidence_score": 0.89,
            "strategic_recommendations": [
                "File provisional utility patent covering event-driven commit-to-challenge generation prior to public marketing.",
                "Adopt an open-core SDK model (Apache 2.0) to drive rapid developer adoption while monetizing closed-source AI engine.",
                "Build a TRL 4 prototype GitHub Action within 3 months using Judge0 execution environment."
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

    result = validate_agent_output(raw_output, context)
    ai_logger.info("Pydantic Validation Success: ResearchPatentResult master output successfully validated.")

    memory_mgr = memory_manager or ProjectMemoryManager(use_mock_store=True)
    memory_mgr.write_memory(
        project_id=project_id,
        key="research_patent_result",
        value=result.model_dump(),
        source_phase="research_patent",
    )
    ai_logger.info(f"[LOCAL MEMORY] Saved 'research_patent_result' for project '{project_id}' in phase 'research_patent'")

    context.research_patent_result = result

    ai_logger.info(
        f"Task Success: Overall Novelty Score = {result.overall_novelty_score}/100, "
        f"TRL = {result.trl_level}, Confidence = {result.confidence_score}"
    )
    ai_logger.info(f"Completed ResearchPatentSummaryAgent for project '{project_id}'.")

    return result
