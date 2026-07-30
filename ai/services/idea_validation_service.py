"""Idea Validation Service encapsulating business logic for running 6-agent validation.

Prepared for consumption by both CLI runners and future FastAPI endpoints.
"""

import uuid
from typing import Optional

from ai.crews.idea_validation.crew import IdeaValidationCrew, get_idea_validation_crew
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.idea_validation import IdeaValidationResult
from ai.shared.logger import ai_logger


class IdeaValidationService:
    """Service encapsulating the Idea Validation workflow execution and memory management."""

    def __init__(
        self,
        memory_manager: Optional[ProjectMemoryManager] = None,
    ) -> None:
        """Initialize Idea Validation Service.

        Args:
            memory_manager: Optional project memory manager instance.
        """
        self.memory_manager = memory_manager or ProjectMemoryManager(use_mock_store=True)

    def validate_idea(
        self,
        idea_text: str,
        project_id: Optional[str] = None,
    ) -> IdeaValidationResult:
        """Execute full 6-agent sequential Idea Validation pipeline against live LLMs.

        Args:
            idea_text: Raw startup idea proposal text.
            project_id: Optional explicit project ID. Generated if not provided.

        Returns:
            IdeaValidationResult Pydantic model containing complete validation analysis.
        """
        if not idea_text or not idea_text.strip():
            raise ValueError("Startup idea proposal text cannot be empty.")

        resolved_project_id = project_id or f"proj-val-{uuid.uuid4().hex[:8]}"
        ai_logger.info(
            f"IdeaValidationService starting validation for project '{resolved_project_id}'"
        )

        crew = get_idea_validation_crew(
            mock_mode=False,
            memory_manager=self.memory_manager,
        )

        result = crew.run(
            project_id=resolved_project_id,
            idea_text=idea_text.strip(),
        )

        ai_logger.info(
            f"IdeaValidationService completed for project '{resolved_project_id}' with score {result.overall_validation_score}/100"
        )
        return result


def get_idea_validation_service(
    memory_manager: Optional[ProjectMemoryManager] = None,
) -> IdeaValidationService:
    """Factory function returning configured IdeaValidationService instance."""
    return IdeaValidationService(memory_manager=memory_manager)
