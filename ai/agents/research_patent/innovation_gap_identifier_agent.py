"""Innovation Gap Identifier Agent for cross-analyzing patents, research, and products to pinpoint gaps."""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ai.config import get_ai_settings
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.context import ResearchPatentContext
from ai.schemas.research_patent import InnovationGapAnalysis
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


def load_agent_prompt(filename: str = "innovation_gap_identifier.md") -> str:
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
        "You are a Chief Innovation Officer & Strategic Gap Specialist. "
        "Cross-analyze the startup proposal against patents, research papers, and commercial products to identify "
        "technical, product, customer, and market gaps. Return pure JSON only matching InnovationGapAnalysis schema."
    )


def validate_agent_output(raw_output: str) -> InnovationGapAnalysis:
    """Safely parse and validate raw LLM output into InnovationGapAnalysis model."""
    return validate_output(raw_output, InnovationGapAnalysis)


def get_innovation_gap_identifier_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temp: float = 0.2,
    mock_mode: bool = False,
) -> Union[Any, Dict[str, Any]]:
    """Initialize InnovationGapIdentifierAgent instance or fallback definition dict."""
    role = "Chief Innovation Officer & Strategic Gap Specialist"
    goal = (
        "Cross-analyze prior art patents, published literature, and commercial solutions "
        "to synthesize technical, product, customer, and market gaps for strategic differentiation."
    )
    backstory = (
        "You are a strategic innovation consultant specializing in technology gap discovery, "
        "competitive white-space identification, and defensible product moat building."
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
        "agent_name": "innovation_gap_identifier_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": agent_tools,
        "mock_mode": mock_mode,
        "schema_class": InnovationGapAnalysis,
        "validate_output": validate_agent_output,
    }


def run_innovation_gap_identifier_agent(
    context: ResearchPatentContext,
    memory_manager: Optional[ProjectMemoryManager] = None,
    mock_mode: bool = False,
) -> InnovationGapAnalysis:
    """Execute innovation gap identification reading from ResearchPatentContext container."""
    project_id = context.project_id
    idea_val = context.idea_validation
    patent_res = context.patent_analysis
    paper_res = context.research_paper_analysis
    sol_res = context.existing_solution_analysis

    ai_logger.info(
        f"Initializing InnovationGapIdentifierAgent: tier={ModelTier.HEAVY}, temp=0.2, mock={mock_mode}"
    )

    if context.research_bundle:
        ai_logger.debug("InnovationGapIdentifierAgent: Optional research_bundle present in context.")

    ai_logger.info(f"Running InnovationGapIdentifierAgent for project '{project_id}'...")

    category = idea_val.category_classification.primary_category
    problem = idea_val.problem_analysis.problem_statement
    value_prop = idea_val.value_proposition.core_value_proposition

    prev_context = ""
    if patent_res:
        prev_context += f"\nPatent White Spaces: {', '.join(patent_res.white_space_opportunities)}"
    if paper_res:
        prev_context += f"\nResearch Open Problems: {', '.join(paper_res.open_problems)}"
    if sol_res:
        prev_context += f"\nExisting Solution Gaps: {', '.join(sol_res.solution_gaps)}"

    system_prompt = load_agent_prompt("innovation_gap_identifier.md")
    user_prompt = (
        f"Cross-analyze the following startup proposal against patents, research, and existing solutions:\n\n"
        f"Idea Text: '{idea_val.idea_text}'\n"
        f"Primary Category: {category}\n"
        f"Problem Statement: {problem}\n"
        f"Value Proposition: {value_prop}"
        f"{prev_context}\n\n"
        "Return pure JSON matching the InnovationGapAnalysis schema with fields: "
        "technical_gaps, product_gaps, customer_gaps, market_gaps, innovation_opportunities, "
        "differentiation_opportunities, overall_gap_score, confidence_score, reasoning_summary, recommendations."
    )

    if mock_mode:
        raw_output = f"""{{
            "technical_gaps": [
                "Real-time AST parsing coupled with sub-second LLM challenge generation",
                "Automated validation of generated code challenges without manual test cases"
            ],
            "product_gaps": [
                "Lack of IDE / GitHub event-driven micro-interventions under 5 minutes",
                "Absence of dynamic adaptive difficulty based on commit complexity"
            ],
            "customer_gaps": [
                "Professional developers lack time for 30-minute video courses during work hours",
                "Engineering managers lack real-time visibility into team skill progression"
            ],
            "market_gaps": [
                "Unexploited B2B developer productivity market segment between LMS platforms and leetcode tools"
            ],
            "innovation_opportunities": [
                "Proprietary commit-triggered challenge synthesis engine",
                "Adaptive developer skill progression model"
            ],
            "differentiation_opportunities": [
                "Zero friction workflow integration (runs inside GitHub/IDE without switching context)",
                "Hyper-relevant challenge generation based on active repository commits"
            ],
            "overall_gap_score": 88,
            "confidence_score": 0.90,
            "reasoning_summary": "Substantial unclaimed gap at the intersection of developer commit events and 5-minute micro-learning synthesis.",
            "recommendations": [
                "Build a GitHub Action / Webhook integration as the primary entry point",
                "Patent the real-time commit-to-challenge mapping algorithm"
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
    ai_logger.info("Pydantic Validation Success: InnovationGapAnalysis successfully validated.")

    memory_mgr = memory_manager or ProjectMemoryManager(use_mock_store=True)
    memory_mgr.write_memory(
        project_id=project_id,
        key="innovation_gap_analysis",
        value=validated_analysis.model_dump(),
        source_phase="research_patent",
    )
    ai_logger.info(f"[LOCAL MEMORY] Saved 'innovation_gap_analysis' for project '{project_id}' in phase 'research_patent'")

    context.innovation_gap_analysis = validated_analysis

    ai_logger.info(
        f"Task Success: Overall Gap Score = {validated_analysis.overall_gap_score}, "
        f"Confidence = {validated_analysis.confidence_score}"
    )
    ai_logger.info(f"Completed InnovationGapIdentifierAgent for project '{project_id}'.")

    return validated_analysis
