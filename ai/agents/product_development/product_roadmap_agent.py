"""Product Roadmap Agent."""

from typing import Any, List, Optional
from ai.schemas.product_development import ProductDevelopmentResult
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


def validate_agent_output(raw_output: str) -> ProductDevelopmentResult:
    return validate_output(raw_output, ProductDevelopmentResult)


def get_product_roadmap_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
    mock_mode: bool = False,
    tools: Optional[List[Any]] = None,
) -> Any:
    ai_logger.info(f"Initializing ProductRoadmapAgent: tier={model_tier}, mock={mock_mode}")
    llm = LLMFactory.get_llm(model_tier=model_tier, temperature=temperature, api_key=api_key, mock_mode=mock_mode)

    role = "Agile Product Manager & Release Planner"
    goal = "Formulate 3-month MVP launch sprints, milestone goals, and feature release sequences."
    backstory = "Senior Product Manager creating quarterly sprint roadmaps and milestone release timelines."

    if HAS_CREWAI and CrewAIAgent is not None and not mock_mode:
        return CrewAIAgent(role=role, goal=goal, backstory=backstory, verbose=True, allow_delegation=False, llm=llm, tools=tools or [])

    return {
        "agent_name": "product_roadmap_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": tools or [],
        "mock_mode": mock_mode,
        "schema_class": ProductDevelopmentResult,
        "validate_output": validate_agent_output,
    }
