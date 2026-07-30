"""Feasibility Analysis Agent for Feasibility Phase."""

from typing import Any, Dict, List, Optional
from ai.schemas.feasibility import FeasibilityResult
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


def validate_agent_output(raw_output: str) -> FeasibilityResult:
    """Validate raw output string into FeasibilityResult Pydantic model."""
    return validate_output(raw_output, FeasibilityResult)


def get_feasibility_analyzer_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
    mock_mode: bool = False,
    tools: Optional[List[Any]] = None,
) -> Any:
    """Returns a configured CrewAI Agent instance for Feasibility Analysis."""
    ai_logger.info(f"Initializing FeasibilityAnalyzerAgent: tier={model_tier}, mock={mock_mode}")

    llm = LLMFactory.get_llm(model_tier=model_tier, temperature=temperature, api_key=api_key, mock_mode=mock_mode)

    role = "Senior Feasibility Risk Auditor"
    goal = "Evaluate technical, operational, and financial feasibility risks of startup proposals."
    backstory = "Expert technical auditor specializing in risk identification and mitigation strategies."

    if HAS_CREWAI and CrewAIAgent is not None and not mock_mode:
        return CrewAIAgent(role=role, goal=goal, backstory=backstory, verbose=True, allow_delegation=False, llm=llm, tools=tools or [])

    return {
        "agent_name": "feasibility_analyzer",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": tools or [],
        "mock_mode": mock_mode,
        "schema_class": FeasibilityResult,
        "validate_output": validate_agent_output,
    }
