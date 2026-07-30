"""Funding Summary Agent."""

from typing import Any, List, Optional
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
    return validate_output(raw_output, FundingResult)


def get_funding_summary_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
    mock_mode: bool = False,
    tools: Optional[List[Any]] = None,
) -> Any:
    ai_logger.info(f"Initializing FundingSummaryAgent: tier={model_tier}, mock={mock_mode}")
    llm = LLMFactory.get_llm(model_tier=model_tier, temperature=temperature, api_key=api_key, mock_mode=mock_mode)

    role = "Funding & Investor Readiness Director"
    goal = "Synthesize 10-slide pitch decks, investor matching criteria, grant discoveries, and valuation models into investor roadmap."
    backstory = "Managing Director of venture fund synthesizing pitch decks and investor due diligence packages."

    if HAS_CREWAI and CrewAIAgent is not None and not mock_mode:
        return CrewAIAgent(role=role, goal=goal, backstory=backstory, verbose=True, allow_delegation=False, llm=llm, tools=tools or [])

    return {
        "agent_name": "funding_summary_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": tools or [],
        "mock_mode": mock_mode,
        "schema_class": FundingResult,
        "validate_output": validate_agent_output,
    }
