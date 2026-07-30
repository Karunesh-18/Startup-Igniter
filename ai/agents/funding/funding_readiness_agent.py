"""Funding Readiness Agent."""

from typing import Any, Dict, List, Optional
from ai.schemas.funding import FundingResult
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


def validate_agent_output(raw_output: str) -> FundingResult:
    """Validate raw output string into FundingResult Pydantic model."""
    return validate_output(raw_output, FundingResult)


def get_funding_readiness_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
    mock_mode: bool = False,
    tools: Optional[List[Any]] = None,
) -> Any:
    """Returns a configured CrewAI Agent instance for Funding Readiness."""
    ai_logger.info(f"Initializing FundingReadinessAgent: tier={model_tier}, mock={mock_mode}")

    llm = LLMFactory.get_llm(model_tier=model_tier, temperature=temperature, api_key=api_key, mock_mode=mock_mode)

    role = "Venture Capital Partner & Investor Readiness Advisor"
    goal = "Formulate 10-slide pitch deck outlines, pre-money valuation ranges, and due diligence checklists."
    backstory = "VC partner who has evaluated 1,000+ pitch decks and guided Seed-stage fundraising rounds."

    if HAS_CREWAI and CrewAIAgent is not None and not mock_mode:
        return CrewAIAgent(role=role, goal=goal, backstory=backstory, verbose=True, allow_delegation=False, llm=llm, tools=tools or [])

    return {
        "agent_name": "funding_readiness_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": tools or [],
        "mock_mode": mock_mode,
        "schema_class": FundingResult,
        "validate_output": validate_agent_output,
    }
