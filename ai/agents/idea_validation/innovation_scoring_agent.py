"""Innovation Scoring Agent for Idea Validation Phase."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ai.schemas.innovation_score import InnovationScoreAnalysis
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


def load_agent_prompt(filename: str = "innovation_scoring.md") -> str:
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
        "You are an Innovation & Technology Differentiation Specialist. "
        "Evaluate novelty, technology innovation, business model innovation, problem originality, differentiation, "
        "innovation level, strengths, improvement opportunities, confidence score, and reasoning. "
        "Return pure JSON only."
    )


def validate_agent_output(raw_output: str) -> InnovationScoreAnalysis:
    """Safely parse and validate raw string LLM response into InnovationScoreAnalysis Pydantic model.

    Args:
        raw_output: Raw text output received from LLM or Crew execution.

    Returns:
        Validated InnovationScoreAnalysis object.
    """
    return validate_output(raw_output, InnovationScoreAnalysis)


def get_innovation_scoring_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
    mock_mode: bool = False,
    tools: Optional[List[Any]] = None,
) -> Any:
    """Returns a configured CrewAI Agent instance for Innovation Scoring.

    Args:
        model_tier: Execution model tier (default: HEAVY for deep innovation assessment).
        temperature: LLM sampling temperature.
        api_key: Optional explicit Groq API key.
        mock_mode: If True, operates in test mode without live LLM network calls.
        tools: Optional list of tools to attach to agent.

    Returns:
        Configured CrewAI Agent instance (or dictionary agent container in fallback mode).
    """
    ai_logger.info(
        f"Initializing InnovationScoringAgent: tier={model_tier}, temp={temperature}, mock={mock_mode}"
    )

    llm = LLMFactory.get_llm(
        model_tier=model_tier,
        temperature=temperature,
        api_key=api_key,
        mock_mode=mock_mode,
    )

    prompt_text = load_agent_prompt("innovation_scoring.md")
    agent_tools = tools or []

    role = "Innovation & Technology Differentiation Specialist"
    goal = (
        "Evaluate novelty, technology innovation, business model innovation, problem originality, "
        "differentiation, innovation level, strengths, improvement opportunities, confidence score, and reasoning."
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

    # Reusable fallback agent dictionary for offline & unit testing
    return {
        "agent_name": "innovation_scoring_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": agent_tools,
        "mock_mode": mock_mode,
        "schema_class": InnovationScoreAnalysis,
        "validate_output": validate_agent_output,
    }
