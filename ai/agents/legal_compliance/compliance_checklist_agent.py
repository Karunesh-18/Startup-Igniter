"""Compliance Checklist Agent for Legal & Compliance Phase."""

from typing import Any, Dict, List, Optional
from ai.schemas.legal_compliance import LegalComplianceResult
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


def validate_agent_output(raw_output: str) -> LegalComplianceResult:
    """Validate raw output string into LegalComplianceResult Pydantic model."""
    return validate_output(raw_output, LegalComplianceResult)


def get_compliance_checklist_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
    mock_mode: bool = False,
    tools: Optional[List[Any]] = None,
) -> Any:
    """Returns a configured CrewAI Agent instance for Legal Compliance Checklist."""
    ai_logger.info(f"Initializing ComplianceChecklistAgent: tier={model_tier}, mock={mock_mode}")

    llm = LLMFactory.get_llm(model_tier=model_tier, temperature=temperature, api_key=api_key, mock_mode=mock_mode)

    role = "Corporate Legal Compliance Lead"
    goal = "Map statutory incorporation requirements (MCA, GST, DPIIT, DPDP Act) per startup vertical."
    backstory = "Corporate lawyer specializing in startup incorporation, tax compliance, and regulatory licensing."

    if HAS_CREWAI and CrewAIAgent is not None and not mock_mode:
        return CrewAIAgent(role=role, goal=goal, backstory=backstory, verbose=True, allow_delegation=False, llm=llm, tools=tools or [])

    return {
        "agent_name": "compliance_checklist_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": tools or [],
        "mock_mode": mock_mode,
        "schema_class": LegalComplianceResult,
        "validate_output": validate_agent_output,
    }
