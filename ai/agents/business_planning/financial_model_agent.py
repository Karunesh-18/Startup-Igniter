"""Financial Model Agent for Business Planning Phase."""

from typing import Any, Dict, List, Optional
from ai.schemas.business_plan import FinancialModel
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


def validate_agent_output(raw_output: str) -> FinancialModel:
    """Validate raw output string into FinancialModel Pydantic model."""
    return validate_output(raw_output, FinancialModel)


def get_financial_model_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
    mock_mode: bool = False,
    tools: Optional[List[Any]] = None,
) -> Any:
    """Returns a configured CrewAI Agent instance for Financial Modeling."""
    ai_logger.info(f"Initializing FinancialModelAgent: tier={model_tier}, mock={mock_mode}")

    llm = LLMFactory.get_llm(model_tier=model_tier, temperature=temperature, api_key=api_key, mock_mode=mock_mode)

    role = "Startup Financial Analyst & Pricing Architect"
    goal = "Formulate unit economics, pricing tiers, CAC/LTV, and 3-year revenue projections."
    backstory = "Venture capital financial analyst specializing in SaaS unit economics and financial modeling."

    if HAS_CREWAI and CrewAIAgent is not None and not mock_mode:
        return CrewAIAgent(role=role, goal=goal, backstory=backstory, verbose=True, allow_delegation=False, llm=llm, tools=tools or [])

    return {
        "agent_name": "financial_model_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": tools or [],
        "mock_mode": mock_mode,
        "schema_class": FinancialModel,
        "validate_output": validate_agent_output,
    }
