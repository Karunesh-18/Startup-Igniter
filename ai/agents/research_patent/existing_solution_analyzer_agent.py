"""Existing Solution Analyzer Agent for commercial software, startup, and open-source landscape evaluation."""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ai.config import get_ai_settings
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.context import ResearchPatentContext
from ai.schemas.research_patent import ExistingSolutionAnalysis
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


def load_agent_prompt(filename: str = "existing_solution_analyzer.md") -> str:
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
        "You are a Senior Commercial Product & Competitive Technology Analyst. "
        "Analyze existing startups, commercial products, enterprise software, open-source repositories, "
        "and market maturity. Return pure JSON only matching the ExistingSolutionAnalysis schema."
    )


def validate_agent_output(raw_output: str) -> ExistingSolutionAnalysis:
    """Safely parse and validate raw LLM output into ExistingSolutionAnalysis model."""
    return validate_output(raw_output, ExistingSolutionAnalysis)


def get_existing_solution_analyzer_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temp: float = 0.2,
    mock_mode: bool = False,
) -> Union[Any, Dict[str, Any]]:
    """Initialize ExistingSolutionAnalyzerAgent instance or fallback definition dict."""
    role = "Commercial Solution & Open-Source Landscape Specialist"
    goal = (
        "Analyze commercial products, venture-backed startups, enterprise software suites, "
        "and open-source projects to evaluate market maturity and uncover solution gaps."
    )
    backstory = (
        "You are an enterprise software architect and product strategist specializing in commercial product benchmarks, "
        "open-source ecosystem mapping, and technical solution gap analysis."
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
        "agent_name": "existing_solution_analyzer_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": agent_tools,
        "mock_mode": mock_mode,
        "schema_class": ExistingSolutionAnalysis,
        "validate_output": validate_agent_output,
    }


def run_existing_solution_analyzer_agent(
    context: ResearchPatentContext,
    memory_manager: Optional[ProjectMemoryManager] = None,
    mock_mode: bool = False,
) -> ExistingSolutionAnalysis:
    """Execute existing solution analysis reading from ResearchPatentContext container."""
    project_id = context.project_id
    idea_val = context.idea_validation
    mr_result = context.market_research

    ai_logger.info(
        f"Initializing ExistingSolutionAnalyzerAgent: tier={ModelTier.HEAVY}, temp=0.2, mock={mock_mode}"
    )

    if context.research_bundle:
        ai_logger.debug("ExistingSolutionAnalyzerAgent: Optional research_bundle present in context.")

    ai_logger.info(f"Running ExistingSolutionAnalyzerAgent for project '{project_id}'...")

    category = idea_val.category_classification.primary_category
    problem = idea_val.problem_analysis.problem_statement
    value_prop = idea_val.value_proposition.core_value_proposition

    mr_context_text = ""
    if mr_result and mr_result.competitor_discovery:
        mr_context_text += f"\nDirect Competitors: {', '.join([c.name for c in mr_result.competitor_discovery.direct_competitors])}"

    system_prompt = load_agent_prompt("existing_solution_analyzer.md")
    user_prompt = (
        f"Perform an existing commercial product and open-source landscape analysis for the following startup proposal:\n\n"
        f"Idea Text: '{idea_val.idea_text}'\n"
        f"Primary Category: {category}\n"
        f"Problem Statement: {problem}\n"
        f"Value Proposition: {value_prop}"
        f"{mr_context_text}\n\n"
        "Return pure JSON matching the ExistingSolutionAnalysis schema with fields: "
        "existing_startups, commercial_products, enterprise_software, open_source_projects, "
        "existing_technologies, market_maturity, solution_gaps, confidence_score, reasoning_summary, recommendations."
    )

    if mock_mode:
        raw_output = f"""{{
            "existing_startups": [
                "LeetCode",
                "Exercism",
                "ByteByteGo"
            ],
            "commercial_products": [
                "Pluralsight Skills",
                "Coursera for Enterprise",
                "Udemy Business"
            ],
            "enterprise_software": [
                "Cornerstone OnDemand",
                "SAP Litmos"
            ],
            "open_source_projects": [
                "Judge0 Code Execution Engine",
                "Monaco Editor"
            ],
            "existing_technologies": [
                "Static video tutorials",
                "Manual quiz generation",
                "Browser-based sandboxed IDEs"
            ],
            "market_maturity": "Growing",
            "solution_gaps": [
                "Existing platforms offer static courses requiring dedicated hours rather than 5-minute micro-learning",
                "No commercial product integrates directly with real-time GitHub commit triggers",
                "Lack of automated personalized challenge synthesis tailored to immediate codebase context"
            ],
            "confidence_score": 0.91,
            "reasoning_summary": "Commercial solutions focus on long-form video courses and manual quizzes, leaving a major gap in commit-triggered micro-challenges.",
            "recommendations": [
                "Position heavily on 5-minute workflow integration rather than replacing LMS platforms",
                "Leverage open-source execution engines (Judge0) to lower initial MVP build costs"
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
    ai_logger.info("Pydantic Validation Success: ExistingSolutionAnalysis successfully validated.")

    memory_mgr = memory_manager or ProjectMemoryManager(use_mock_store=True)
    memory_mgr.write_memory(
        project_id=project_id,
        key="existing_solution_analysis",
        value=validated_analysis.model_dump(),
        source_phase="research_patent",
    )
    ai_logger.info(f"[LOCAL MEMORY] Saved 'existing_solution_analysis' for project '{project_id}' in phase 'research_patent'")

    context.existing_solution_analysis = validated_analysis

    ai_logger.info(
        f"Task Success: Market Maturity = '{validated_analysis.market_maturity}', "
        f"Confidence = {validated_analysis.confidence_score}"
    )
    ai_logger.info(f"Completed ExistingSolutionAnalyzerAgent for project '{project_id}'.")

    return validated_analysis
