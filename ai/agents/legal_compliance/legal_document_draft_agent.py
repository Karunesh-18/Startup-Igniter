"""Legal Document Draft Agent for Legal & Compliance Phase."""

from typing import Any, Dict, List, Optional
from ai.schemas.legal_compliance import LegalDocumentDraft
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


def validate_agent_output(raw_output: str) -> LegalDocumentDraft:
    """Validate raw output string into LegalDocumentDraft Pydantic model."""
    return validate_output(raw_output, LegalDocumentDraft)


def get_legal_document_draft_agent(
    model_tier: ModelTier = ModelTier.HEAVY,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
    mock_mode: bool = False,
    tools: Optional[List[Any]] = None,
) -> Any:
    """Returns a configured CrewAI Agent instance for Legal Document Drafting."""
    ai_logger.info(f"Initializing LegalDocumentDraftAgent: tier={model_tier}, mock={mock_mode}")

    llm = LLMFactory.get_llm(model_tier=model_tier, temperature=temperature, api_key=api_key, mock_mode=mock_mode)

    role = "Startup Contract Counsel"
    goal = "Draft standardized legal contracts (Mutual NDA, Founder Agreement) with disclaimer headers."
    backstory = "Legal drafting specialist focused on early-stage founder equity agreements and non-disclosure contracts."

    if HAS_CREWAI and CrewAIAgent is not None and not mock_mode:
        return CrewAIAgent(role=role, goal=goal, backstory=backstory, verbose=True, allow_delegation=False, llm=llm, tools=tools or [])

    return {
        "agent_name": "legal_document_draft_agent",
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "llm": llm,
        "tools": tools or [],
        "mock_mode": mock_mode,
        "schema_class": LegalDocumentDraft,
        "validate_output": validate_agent_output,
    }
