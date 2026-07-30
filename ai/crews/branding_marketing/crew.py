"""Branding & Marketing Crew implementation."""

from typing import Optional

from ai.crews.branding_marketing.tasks import execute_branding_marketing_task
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.branding_marketing import BrandingMarketingResult
from ai.shared.logger import ai_logger


class BrandingMarketingCrew:
    """Production orchestration engine for Branding & Marketing Crew."""

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
        mock_mode: bool = True,
    ) -> BrandingMarketingResult:
        """Execute branding & marketing tasks and save result to project memory."""
        ai_logger.info(f"=== Starting BrandingMarketingCrew Execution for Project '{project_id}' ===")

        result = execute_branding_marketing_task(project_id=project_id, idea_text=idea_text)

        self.memory_manager.write_memory(
            project_id=project_id,
            key="branding_marketing_result",
            value=result.model_dump(),
            source_phase="branding_marketing",
        )

        ai_logger.info(f"=== BrandingMarketingCrew Execution Complete for Project '{project_id}' ===")
        return result


def get_branding_marketing_crew(
    mock_mode: bool = True,
    memory_manager: Optional[ProjectMemoryManager] = None,
) -> BrandingMarketingCrew:
    """Factory function for BrandingMarketingCrew."""
    return BrandingMarketingCrew(memory_manager=memory_manager, verbose=True)
