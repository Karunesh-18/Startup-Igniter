"""Lean Canvas Agent for Business Planning Phase."""

from typing import Any, Dict, List, Optional
from ai.schemas.business_plan import LeanCanvas
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


def validate_agent_output(raw_output: str) -> LeanCanvas:
    """Validate raw output string into LeanCanvas Pydantic model."""
    return validate_output(raw_output, LeanCanvas)


def get_lean_canvas_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
    mock_mode: bool = False,
    tools: Optional[List[Any]] = None,
) -> Any:
    """Returns a configured CrewAI Agent instance for Lean Canvas Generation."""
    ai_logger.info(f"Initializing LeanCanvasAgent: tier={model_tier}, mock={mock_mode}")

    llm = LLMFactory.get_llm(model_tier=model_tier, temperature=temperature, api_key=api_key, mock_mode=mock_mode)

    role = "Chief Business Strategist & Lean Canvas Lead"
    goal = "Synthesize problem, solution, UVP, channels, and metrics into a Lean Canvas model."
    backstory = "Expert venture strategist who designs high-growth 9-box business model canvases."

    if HAS_CREWAI and CrewAIAgent is not None and not mock_mode:
        return CrewAIAgent(role=role, goal=goal, backstory=backstory, verbose=True, allow_delegation=False, llm=llm, tools=tools or [])

    return {
        "agent_name": "lean_canvas_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": tools or [],
        "mock_mode": mock_mode,
        "schema_class": LeanCanvas,
        "validate_output": validate_agent_output,
    }
