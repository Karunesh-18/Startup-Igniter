"""Problem Statement Analyzer Agent for Idea Validation Phase."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ai.schemas.problem_statement import ProblemStatementAnalysis
from ai.shared.constants import ModelTier
from ai.shared.logger import ai_logger
from ai.shared.output_validator import validate_output


def load_agent_prompt(filename: str = "problem_statement.md") -> str:
    """Load agent prompt instructions from prompts directory."""
    prompt_path = (
        Path(__file__).resolve().parent.parent.parent
        / "prompts"
        / "idea_validation"
        / filename
    )
    if prompt_path.is_file():
        return prompt_path.read_text(encoding="utf-8")
    ai_logger.warning(
        f"Prompt file '{filename}' not found at {prompt_path}. Using default fallback prompt."
    )
    return (
        "You are a Lead Problem Validation Strategist evaluating pain points. "
        "Deconstruct core problem statements, root causes, solution gaps, severity, and urgency. "
        "Return pure JSON only."
    )


def validate_agent_output(raw_output: str) -> ProblemStatementAnalysis:
    """Safely parse and validate raw string LLM response into ProblemStatementAnalysis Pydantic model.

    Args:
        raw_output: Raw text output received from LLM or Crew execution.

    Returns:
        Validated ProblemStatementAnalysis object.
    """
    return validate_output(raw_output, ProblemStatementAnalysis)


def get_problem_statement_analyzer_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
    mock_mode: bool = False,
    tools: Optional[List[Any]] = None,
) -> Any:
    """Returns an agent configuration dictionary for Problem Statement Analysis.

    Args:
        model_tier: Execution model tier (default: HEAVY for deep analysis).
        temperature: LLM sampling temperature.
        api_key: Optional explicit Groq API key.
        mock_mode: If True, operates in test mode without live LLM network calls.
        tools: Optional list of tools to attach to agent.

    Returns:
        Agent configuration dictionary consumed by the crew orchestrator.
    """
    ai_logger.info(
        f"Initializing ProblemStatementAnalyzerAgent: tier={model_tier}, temp={temperature}, mock={mock_mode}"
    )

    prompt_text = load_agent_prompt("problem_statement.md")
    agent_tools = tools or []

    role = "Lead Problem Validation Strategist"
    goal = (
        "Deconstruct core problem statements, evaluate pain-point intensity, "
        "root causes, solution gaps, market urgency, and affected user groups."
    )
    backstory = prompt_text

    # Reusable fallback agent dictionary for offline & unit testing
    return {
        "agent_name": "problem_statement_analyzer",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "tools": agent_tools,
        "mock_mode": mock_mode,
        "schema_class": ProblemStatementAnalysis,
        "validate_output": validate_agent_output,
    }
