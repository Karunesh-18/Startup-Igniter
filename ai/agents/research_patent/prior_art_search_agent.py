"""Prior Art Search Agent for Patent Research Phase."""

from typing import Any, Dict, List, Optional
from ai.schemas.research_patent import PatentAnalysis
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


def validate_agent_output(raw_output: str) -> PatentAnalysis:
    """Validate raw output string into PatentAnalysis Pydantic model."""
    return validate_output(raw_output, PatentAnalysis)


def get_prior_art_search_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
    mock_mode: bool = False,
    tools: Optional[List[Any]] = None,
) -> Any:
    """Returns a configured CrewAI Agent instance for Patent Prior-Art Search."""
    ai_logger.info(f"Initializing PriorArtSearchAgent: tier={model_tier}, mock={mock_mode}")

    llm = LLMFactory.get_llm(model_tier=model_tier, temperature=temperature, api_key=api_key, mock_mode=mock_mode)

    role = "USPTO Patent Attorney & Prior-Art Researcher"
    goal = "Query public patent databases and evaluate prior-art similarity and claim overlap."
    backstory = "Registered patent attorney specializing in USPTO searches and IP infringement risk assessment."

    if HAS_CREWAI and CrewAIAgent is not None and not mock_mode:
        return CrewAIAgent(role=role, goal=goal, backstory=backstory, verbose=True, allow_delegation=False, llm=llm, tools=tools or [])

    return {
        "agent_name": "prior_art_search_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": tools or [],
        "mock_mode": mock_mode,
        "schema_class": PatentAnalysis,
        "validate_output": validate_agent_output,
    }
