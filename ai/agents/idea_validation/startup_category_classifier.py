"""Startup Category Classifier Agent for Idea Validation Phase."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ai.schemas.startup_category import StartupCategoryClassification
from ai.shared.constants import ModelTier
from ai.shared.logger import ai_logger
from ai.shared.output_validator import validate_output


def load_agent_prompt(filename: str = "startup_category_classifier.md") -> str:
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
        "You are a Startup Taxonomy & Categorization Lead. "
        "Classify startup proposals into primary/secondary categories, industry verticals, tech domains, "
        "business model, revenue model, startup stage, target market, confidence score, and reasoning. "
        "Return pure JSON only."
    )


def validate_agent_output(raw_output: str) -> StartupCategoryClassification:
    """Safely parse and validate raw string LLM response into StartupCategoryClassification Pydantic model.

    Args:
        raw_output: Raw text output received from LLM or Crew execution.

    Returns:
        Validated StartupCategoryClassification object.
    """
    return validate_output(raw_output, StartupCategoryClassification)


def get_startup_category_classifier_agent(
    model_tier: ModelTier = ModelTier.FAST,
    temperature: float = 0.1,
    api_key: Optional[str] = None,
    mock_mode: bool = False,
    tools: Optional[List[Any]] = None,
) -> Any:
    """Returns an agent configuration dictionary for Startup Category Classification.

    Args:
        model_tier: Execution model tier (default: FAST for rapid taxonomy classification).
        temperature: LLM sampling temperature.
        api_key: Optional explicit Groq API key.
        mock_mode: If True, operates in test mode without live LLM network calls.
        tools: Optional list of tools to attach to agent.

    Returns:
        Agent configuration dictionary consumed by the crew orchestrator.
    """
    ai_logger.info(
        f"Initializing StartupCategoryClassifierAgent: tier={model_tier}, temp={temperature}, mock={mock_mode}"
    )

    prompt_text = load_agent_prompt("startup_category_classifier.md")
    agent_tools = tools or []

    role = "Startup Category & Taxonomy Lead"
    goal = (
        "Classify raw startup proposals into primary/secondary categories, industry verticals, "
        "tech domains, business models, revenue models, startup stages, target markets, confidence scores, and reasoning."
    )
    backstory = prompt_text

    # Reusable fallback agent dictionary for offline & unit testing
    return {
        "agent_name": "startup_category_classifier",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "tools": agent_tools,
        "mock_mode": mock_mode,
        "schema_class": StartupCategoryClassification,
        "validate_output": validate_agent_output,
    }
