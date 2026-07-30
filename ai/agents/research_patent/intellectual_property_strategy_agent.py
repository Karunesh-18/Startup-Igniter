"""Intellectual Property Strategy Agent."""

from typing import Any, List, Optional
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
    return validate_output(raw_output, PatentAnalysis)


def get_intellectual_property_strategy_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
    mock_mode: bool = False,
    tools: Optional[List[Any]] = None,
) -> Any:
    ai_logger.info(f"Initializing IntellectualPropertyStrategyAgent: tier={model_tier}, mock={mock_mode}")
    llm = LLMFactory.get_llm(model_tier=model_tier, temperature=temperature, api_key=api_key, mock_mode=mock_mode)

    role = "Chief Intellectual Property Counsel"
    goal = "Formulate IP protection roadmap including provisional patents, trademarks, and trade secrets."
    backstory = "Patent attorney advising tech startups on defensive IP strategies and patent portfolios."

    if HAS_CREWAI and CrewAIAgent is not None and not mock_mode:
        return CrewAIAgent(role=role, goal=goal, backstory=backstory, verbose=True, allow_delegation=False, llm=llm, tools=tools or [])

    return {
        "agent_name": "intellectual_property_strategy_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": tools or [],
        "mock_mode": mock_mode,
        "schema_class": PatentAnalysis,
        "validate_output": validate_agent_output,
    }
