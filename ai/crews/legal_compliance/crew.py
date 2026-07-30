"""Legal & Compliance Crew implementation orchestrating compliance checklists & legal document drafting."""

from typing import Optional

from ai.crews.legal_compliance.tasks import (
    draft_legal_documents_task,
    generate_compliance_checklist_task,
)
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.legal_compliance import LegalComplianceResult
from ai.shared.logger import ai_logger


class LegalComplianceCrew:
    """Production orchestration engine for Legal & Compliance Crew."""

    def __init__(
        self,
        memory_manager: Optional[ProjectMemoryManager] = None,
        verbose: bool = True,
    ):
        self.memory_manager = memory_manager or ProjectMemoryManager(use_mock_store=True)
        self.verbose = verbose

    def run(
        self,
        project_id: str,
        idea_text: str,
        category: str = "SaaS",
        mock_mode: bool = True,
    ) -> LegalComplianceResult:
        """Execute legal compliance tasks and save to project memory."""
        ai_logger.info(f"=== Starting LegalComplianceCrew Execution for Project '{project_id}' ===")

        checklist = generate_compliance_checklist_task(project_id=project_id, category=category)
        nda_draft = draft_legal_documents_task(project_id=project_id, idea_text=idea_text)

        summary = f"Legal readiness roadmap compiled with {len(checklist)} key compliance items and draft NDA generated."

        result = LegalComplianceResult(
            project_id=project_id,
            compliance_checklist=checklist,
            draft_nda=nda_draft,
            overall_summary=summary,
            confidence_score=0.90,
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
    return LegalComplianceCrew(memory_manager=memory_manager, verbose=True)
