"""Technology Readiness Agent for TRL estimation, engineering complexity, and development risk evaluation."""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ai.config import get_ai_settings
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.context import ResearchPatentContext
from ai.schemas.research_patent import TechnologyReadiness
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


def load_agent_prompt(filename: str = "technology_readiness.md") -> str:
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
        "You are a Chief Technology Officer & System Architecture Specialist. "
        "Estimate Technology Readiness Level (TRL 1-9), evaluate technical feasibility, infrastructure complexity, "
        "engineering complexity, dependencies, scalability, and MVP timeline. Return pure JSON matching TechnologyReadiness schema."
    )


def validate_agent_output(raw_output: str) -> TechnologyReadiness:
    """Safely parse and validate raw LLM output into TechnologyReadiness model."""
    return validate_output(raw_output, TechnologyReadiness)


def get_technology_readiness_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temp: float = 0.2,
    mock_mode: bool = False,
) -> Union[Any, Dict[str, Any]]:
    """Initialize TechnologyReadinessAgent instance or fallback definition dict."""
    role = "Chief Technology Officer & System Architecture Specialist"
    goal = (
        "Estimate Technology Readiness Level (TRL 1 to 9), assess software engineering complexity, "
        "evaluate infrastructure requirements, identify technical dependencies, and estimate MVP timeline."
    )
    backstory = (
        "You are a veteran CTO and system software architect who has scaled high-concurrency cloud systems, "
        "conducted TRL audits for enterprise R&D programs, and derisked complex technical roadmaps."
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
        "agent_name": "technology_readiness_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": agent_tools,
        "mock_mode": mock_mode,
        "schema_class": TechnologyReadiness,
        "validate_output": validate_agent_output,
    }


def run_technology_readiness_agent(
    context: ResearchPatentContext,
    memory_manager: Optional[ProjectMemoryManager] = None,
    mock_mode: bool = False,
) -> TechnologyReadiness:
    """Execute technology readiness assessment reading from ResearchPatentContext container."""
    project_id = context.project_id
    idea_val = context.idea_validation
    paper_res = context.research_paper_analysis
    gap_res = context.innovation_gap_analysis

    ai_logger.info(
        f"Initializing TechnologyReadinessAgent: tier={ModelTier.HEAVY}, temp=0.2, mock={mock_mode}"
    )

    if context.research_bundle:
        ai_logger.debug("TechnologyReadinessAgent: Optional research_bundle present in context.")

    ai_logger.info(f"Running TechnologyReadinessAgent for project '{project_id}'...")

    category = idea_val.category_classification.primary_category
    problem = idea_val.problem_analysis.problem_statement
    value_prop = idea_val.value_proposition.core_value_proposition

    prev_context = ""
    if paper_res:
        prev_context += f"\nAcademic SOTA: {', '.join(paper_res.state_of_the_art_methods)}"
    if gap_res:
        prev_context += f"\nTechnical Gaps: {', '.join(gap_res.technical_gaps)}"

    system_prompt = load_agent_prompt("technology_readiness.md")
    user_prompt = (
        f"Perform a Technology Readiness Level (TRL) and engineering feasibility assessment for the following startup proposal:\n\n"
        f"Idea Text: '{idea_val.idea_text}'\n"
        f"Primary Category: {category}\n"
        f"Problem Statement: {problem}\n"
        f"Value Proposition: {value_prop}"
        f"{prev_context}\n\n"
        "Return pure JSON matching the TechnologyReadiness schema with fields: "
        "trl_level, trl_stage_name, technical_feasibility_assessment, infrastructure_complexity, "
        "engineering_complexity, technology_dependencies, scalability_assessment, development_risks, "
        "estimated_time_to_mvp_months, confidence_score, reasoning_summary, recommendations."
    )

    if mock_mode:
        raw_output = f"""{{
            "trl_level": 3,
            "trl_stage_name": "TRL 3: Analytical & Experimental Proof of Concept",
            "technical_feasibility_assessment": "High technical feasibility using established LLM APIs, webhooks, and sandboxed code execution.",
            "infrastructure_complexity": "Moderate",
            "engineering_complexity": "Moderate",
            "technology_dependencies": [
                "OpenAI / Anthropic / Groq LLM API",
                "GitHub Webhook API / Octokit",
                "Judge0 / Docker Sandboxed Execution Engine"
            ],
            "scalability_assessment": "Horizontal micro-service scaling with asynchronous worker queues (Celery/Redis) for background challenge synthesis.",
            "development_risks": [
                "LLM API response latency under heavy concurrent commit volume",
                "Code execution sandbox security isolation"
            ],
            "estimated_time_to_mvp_months": 3,
            "confidence_score": 0.89,
            "reasoning_summary": "TRL 3 rating based on verified component APIs available today. MVP build is realistic within 3 months using Docker-based code execution.",
            "recommendations": [
                "Build a CLI / GitHub Action prototype first before building full web UI",
                "Implement aggressive Redis caching for common coding challenge templates"
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
    ai_logger.info("Pydantic Validation Success: TechnologyReadiness successfully validated.")

    memory_mgr = memory_manager or ProjectMemoryManager(use_mock_store=True)
    memory_mgr.write_memory(
        project_id=project_id,
        key="technology_readiness",
        value=validated_analysis.model_dump(),
        source_phase="research_patent",
    )
    ai_logger.info(f"[LOCAL MEMORY] Saved 'technology_readiness' for project '{project_id}' in phase 'research_patent'")

    context.technology_readiness = validated_analysis

    ai_logger.info(
        f"Task Success: TRL Level = {validated_analysis.trl_level} ({validated_analysis.trl_stage_name}), "
        f"Confidence = {validated_analysis.confidence_score}"
    )
    ai_logger.info(f"Completed TechnologyReadinessAgent for project '{project_id}'.")

    return validated_analysis
