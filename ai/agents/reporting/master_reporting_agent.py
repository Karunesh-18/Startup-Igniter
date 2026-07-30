"""Master Executive Reporting Agent."""

from typing import Any, Dict, List, Optional
from ai.schemas.reporting import MasterReportResult
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


def validate_agent_output(raw_output: str) -> MasterReportResult:
    """Validate raw output string into MasterReportResult Pydantic model."""
    return validate_output(raw_output, MasterReportResult)


def get_master_reporting_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
    mock_mode: bool = False,
    tools: Optional[List[Any]] = None,
) -> Any:
    """Returns a configured CrewAI Agent instance for Master Executive Reporting."""
    ai_logger.info(f"Initializing MasterReportingAgent: tier={model_tier}, mock={mock_mode}")

    llm = LLMFactory.get_llm(model_tier=model_tier, temperature=temperature, api_key=api_key, mock_mode=mock_mode)

    role = "Executive Intelligence & Master Synthesis Director"
    goal = "Consolidate multi-phase memory findings into an executive report with overall readiness score."
    backstory = "Executive reporting lead synthesizing market, technical, legal, and financial findings into actionable founder roadmaps."

    if HAS_CREWAI and CrewAIAgent is not None and not mock_mode:
        return CrewAIAgent(role=role, goal=goal, backstory=backstory, verbose=True, allow_delegation=False, llm=llm, tools=tools or [])

    return {
        "agent_name": "master_reporting_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": tools or [],
        "mock_mode": mock_mode,
        "schema_class": MasterReportResult,
        "validate_output": validate_agent_output,
    }
