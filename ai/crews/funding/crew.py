"""Funding & Investor Readiness Crew implementation."""

from typing import Optional

from ai.crews.funding.tasks import execute_funding_readiness_task
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.funding import FundingResult
from ai.shared.logger import ai_logger


class FundingCrew:
    """Production orchestration engine for Funding Crew."""

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
    ) -> FundingResult:
        """Execute funding readiness tasks and save result to project memory."""
        ai_logger.info(f"=== Starting FundingCrew Execution for Project '{project_id}' ===")

        result = execute_funding_readiness_task(project_id=project_id, idea_text=idea_text)

        self.memory_manager.write_memory(
            project_id=project_id,
            key="funding_result",
            value=result.model_dump(),
            source_phase="funding",
        )

        ai_logger.info(f"=== FundingCrew Execution Complete for Project '{project_id}' ===")
        return result


def get_funding_crew(
    mock_mode: bool = True,
    memory_manager: Optional[ProjectMemoryManager] = None,
) -> FundingCrew:
    """Factory function for FundingCrew."""
    return FundingCrew(memory_manager=memory_manager, verbose=True)
