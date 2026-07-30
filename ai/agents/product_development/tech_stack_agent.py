"""Tech Stack Agent for Product Development Phase."""

from typing import Any, Dict, List, Optional
from ai.schemas.product_development import TechStackRecommendation
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


def validate_agent_output(raw_output: str) -> TechStackRecommendation:
    """Validate raw output string into TechStackRecommendation Pydantic model."""
    return validate_output(raw_output, TechStackRecommendation)


def get_tech_stack_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
    mock_mode: bool = False,
    tools: Optional[List[Any]] = None,
) -> Any:
    """Returns a configured CrewAI Agent instance for Tech Stack Recommendation."""
    ai_logger.info(f"Initializing TechStackAgent: tier={model_tier}, mock={mock_mode}")

    llm = LLMFactory.get_llm(model_tier=model_tier, temperature=temperature, api_key=api_key, mock_mode=mock_mode)

    role = "Chief Technology Officer (CTO) & Cloud Systems Architect"
    goal = "Select optimal frontend, backend, database, and cloud infrastructure per startup vertical."
    backstory = "Enterprise systems architect specializing in scalable microservices, FastAPI, and Next.js stacks."

    if HAS_CREWAI and CrewAIAgent is not None and not mock_mode:
        return CrewAIAgent(role=role, goal=goal, backstory=backstory, verbose=True, allow_delegation=False, llm=llm, tools=tools or [])

    return {
        "agent_name": "tech_stack_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": tools or [],
        "mock_mode": mock_mode,
        "schema_class": TechStackRecommendation,
        "validate_output": validate_agent_output,
    }
