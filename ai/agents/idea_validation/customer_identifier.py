"""Customer Identifier Agent for Idea Validation Phase."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ai.schemas.customer_identifier import CustomerIdentification
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


def load_agent_prompt(filename: str = "customer_identifier.md") -> str:
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
        "You are a Target Audience & User Persona Strategist. "
        "Identify primary target customers, secondary customers, end users, decision makers, customer segments, "
        "demographics, geographic markets, industries, pain points, needs, motivations, adoption barriers, willingness to pay, and confidence score. "
        "Return pure JSON only."
    )


def validate_agent_output(raw_output: str) -> CustomerIdentification:
    """Safely parse and validate raw string LLM response into CustomerIdentification Pydantic model.

    Args:
        raw_output: Raw text output received from LLM or Crew execution.

    Returns:
        Validated CustomerIdentification object.
    """
    return validate_output(raw_output, CustomerIdentification)


def get_customer_identifier_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
    mock_mode: bool = False,
    tools: Optional[List[Any]] = None,
) -> Any:
    """Returns a configured CrewAI Agent instance for Target Customer Identification.

    Args:
        model_tier: Execution model tier (default: HEAVY for deep analysis).
        temperature: LLM sampling temperature.
        api_key: Optional explicit Groq API key.
        mock_mode: If True, operates in test mode without live LLM network calls.
        tools: Optional list of tools to attach to agent.

    Returns:
        Configured CrewAI Agent instance (or dictionary agent container in fallback mode).
    """
    ai_logger.info(
        f"Initializing CustomerIdentifierAgent: tier={model_tier}, temp={temperature}, mock={mock_mode}"
    )

    llm = LLMFactory.get_llm(
        model_tier=model_tier,
        temperature=temperature,
        api_key=api_key,
        mock_mode=mock_mode,
    )

    prompt_text = load_agent_prompt("customer_identifier.md")
    agent_tools = tools or []

    role = "Target Audience & User Persona Strategist"
    goal = (
        "Identify primary target customers, secondary customers, end users, decision makers, "
        "customer segments, demographics, geographic markets, industries, customer pain points, "
        "needs, motivations, adoption barriers, willingness to pay, and confidence score."
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
        "agent_name": "customer_identifier",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": agent_tools,
        "mock_mode": mock_mode,
        "schema_class": CustomerIdentification,
        "validate_output": validate_agent_output,
    }
