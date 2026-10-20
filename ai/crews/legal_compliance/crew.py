"""Legal & Compliance Crew: spec-driven LLM call (see ai/crews/spec_runner.py), literal result in mock mode."""

from typing import Optional

from ai.crews.legal_compliance.tasks import mock_result
from ai.crews.spec_runner import category_of, fetch_research, run_spec_crew
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.legal_compliance import LegalComplianceResult
from ai.shared.logger import ai_logger


class LegalComplianceCrew:
    """Production orchestration engine for Legal & Compliance Crew."""

    def __init__(
        self,
        memory_manager: Optional[ProjectMemoryManager] = None,
        verbose: bool = True,
        mock_mode: bool = True,
    ):
        self.memory_manager = memory_manager or ProjectMemoryManager(use_mock_store=True)
        self.verbose = verbose
        self.mock_mode = mock_mode

    def run(
        self,
        project_id: str,
        idea_text: str,
        category: str = "SaaS",
        mock_mode: Optional[bool] = None,
        prior: Optional[dict] = None,
    ) -> LegalComplianceResult:
        """Execute the crew (prior = earlier crews' model_dumps keyed by crew) and save to project memory."""
        mock = self.mock_mode if mock_mode is None else mock_mode
        ai_logger.info(f"=== Starting LegalComplianceCrew Execution for Project '{project_id}' (mock={mock}) ===")

        result = run_spec_crew(
            "legal_compliance",
            LegalComplianceResult,
            project_id,
            idea_text,
            prior,
            None if mock else fetch_research("gather_regulatory_research", category_of(prior, category), "global"),
            lambda: mock_result(project_id=project_id, idea_text=idea_text, category=category),
            mock,
        )

        self.memory_manager.write_memory(
            project_id=project_id,
            key="legal_compliance_result",
            value=result.model_dump(),
            source_phase="legal_compliance",
        )

        ai_logger.info(f"=== LegalComplianceCrew Execution Complete for Project '{project_id}' ===")
        return result


def get_legal_compliance_crew(
    mock_mode: bool = True,
    memory_manager: Optional[ProjectMemoryManager] = None,
) -> LegalComplianceCrew:
    """Factory function for LegalComplianceCrew."""
    return LegalComplianceCrew(memory_manager=memory_manager, verbose=True, mock_mode=mock_mode)
