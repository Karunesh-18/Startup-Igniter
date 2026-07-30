"""Research Paper Analyzer Agent for academic literature and state-of-the-art method assessment."""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ai.config import get_ai_settings
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.context import ResearchPatentContext
from ai.schemas.idea_validation import IdeaValidationResult
from ai.schemas.research_patent import ResearchPaperAnalysis
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


def load_agent_prompt(filename: str = "research_paper_analyzer.md") -> str:
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
        "You are a Senior Academic & Research Literature Analyst. "
        "Analyze published academic papers, state-of-the-art methods, theoretical breakthroughs, "
        "and technical limitations relevant to the proposal. "
        "Return pure JSON only matching the ResearchPaperAnalysis schema."
    )


def validate_agent_output(raw_output: str) -> ResearchPaperAnalysis:
    """Safely parse and validate raw LLM output into ResearchPaperAnalysis model."""
    return validate_output(raw_output, ResearchPaperAnalysis)


def get_research_paper_analyzer_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temp: float = 0.2,
    mock_mode: bool = False,
) -> Union[Any, Dict[str, Any]]:
    """Initialize ResearchPaperAnalyzerAgent instance or fallback definition dict."""
    role = "Academic & Scientific Research Literature Specialist"
    goal = (
        "Evaluate state-of-the-art research papers, academic innovations, open scientific problems, "
        "and algorithmic limitations related to the startup proposal."
    )
    backstory = (
        "You are a leading computer science and domain research scientist with deep expertise in analyzing "
        "scientific publications (arXiv, IEEE, ACM, Nature), benchmarking state-of-the-art models, "
        "and bridging academic theory into production software."
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
        "agent_name": "research_paper_analyzer_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": agent_tools,
        "mock_mode": mock_mode,
        "schema_class": ResearchPaperAnalysis,
        "validate_output": validate_agent_output,
    }


def run_research_paper_analyzer_agent(
    context: ResearchPatentContext,
    memory_manager: Optional[ProjectMemoryManager] = None,
    mock_mode: bool = False,
) -> ResearchPaperAnalysis:
    """Execute academic paper research analysis reading from ResearchPatentContext container."""
    project_id = context.project_id
    idea_val = context.idea_validation
    patent_analysis = context.patent_analysis

    ai_logger.info(
        f"Initializing ResearchPaperAnalyzerAgent: tier={ModelTier.HEAVY}, temp=0.2, mock={mock_mode}"
    )

    if context.research_bundle:
        ai_logger.debug("ResearchPaperAnalyzerAgent: Optional research_bundle present in context.")

    ai_logger.info(f"Running ResearchPaperAnalyzerAgent for project '{project_id}'...")

    category = idea_val.category_classification.primary_category
    problem = idea_val.problem_analysis.problem_statement
    value_prop = idea_val.value_proposition.core_value_proposition

    patent_text = ""
    if patent_analysis:
        patent_text = f"\nRelated Tech Domains: {', '.join(patent_analysis.related_technology_domains)}"

    system_prompt = load_agent_prompt("research_paper_analyzer.md")
    user_prompt = (
        f"Perform an academic research paper and state-of-the-art analysis for the following startup proposal:\n\n"
        f"Idea Text: '{idea_val.idea_text}'\n"
        f"Primary Category: {category}\n"
        f"Problem Statement: {problem}\n"
        f"Value Proposition: {value_prop}"
        f"{patent_text}\n\n"
        "Return pure JSON matching the ResearchPaperAnalysis schema with fields: "
        "key_research_papers, state_of_the_art_methods, academic_innovations, open_problems, "
        "technical_limitations, emerging_research_trends, academic_novelty_score, confidence_score, "
        "reasoning_summary, recommendations."
    )

    if mock_mode:
        raw_output = f"""{{
            "key_research_papers": [
                "Attention Is All You Need (Vaswani et al.)",
                "Deep Learning for Real-Time Event Stream Analysis (IEEE 2024)"
            ],
            "state_of_the_art_methods": [
                "Transformer-based sequence modeling",
                "Graph neural networks for code AST representation"
            ],
            "academic_innovations": [
                "Zero-shot prompt distillation for localized challenge generation",
                "Context-aware embeddings for continuous skill evaluation"
            ],
            "open_problems": [
                "High computational cost of real-time multi-modal AST evaluation",
                "Catastrophic forgetting in personalized learning feedback loops"
            ],
            "technical_limitations": [
                "Latency overhead when parsing large git commit diffs in real time",
                "Finite context window constraints for complex multi-file codebases"
            ],
            "emerging_research_trends": [
                "Lightweight on-device code generation models",
                "Self-correcting agentic feedback loops"
            ],
            "academic_novelty_score": 84,
            "confidence_score": 0.88,
            "reasoning_summary": "High academic novelty in translating event-driven commit hooks into micro-learning challenges.",
            "recommendations": [
                "Implement lightweight AST parsing before calling heavy LLMs",
                "Benchmark system latency against published arXiv baselines"
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
    ai_logger.info("Pydantic Validation Success: ResearchPaperAnalysis successfully validated.")

    memory_mgr = memory_manager or ProjectMemoryManager(use_mock_store=True)
    memory_mgr.write_memory(
        project_id=project_id,
        key="research_paper_analysis",
        value=validated_analysis.model_dump(),
        source_phase="research_patent",
    )
    ai_logger.info(f"[LOCAL MEMORY] Saved 'research_paper_analysis' for project '{project_id}' in phase 'research_patent'")

    context.research_paper_analysis = validated_analysis

    ai_logger.info(
        f"Task Success: Academic Novelty Score = {validated_analysis.academic_novelty_score}, "
        f"Confidence = {validated_analysis.confidence_score}"
    )
    ai_logger.info(f"Completed ResearchPaperAnalyzerAgent for project '{project_id}'.")

    return validated_analysis
