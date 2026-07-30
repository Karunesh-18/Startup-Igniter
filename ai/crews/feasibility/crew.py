"""Feasibility Crew implementation orchestrating feasibility scoring & risk assessment."""

from typing import Optional

from ai.crews.feasibility.tasks import execute_feasibility_analysis_task
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.feasibility import FeasibilityResult
from ai.shared.logger import ai_logger


class FeasibilityCrew:
    """Production orchestration engine for Feasibility Crew."""

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
    ) -> FeasibilityResult:
        """Execute feasibility assessment tasks and save to project memory."""
        ai_logger.info(f"=== Starting FeasibilityCrew Execution for Project '{project_id}' ===")

        result = execute_feasibility_analysis_task(project_id=project_id, idea_text=idea_text)

        self.memory_manager.write_memory(
            project_id=project_id,
            key="feasibility_result",
            value=result.model_dump(),
            source_phase="feasibility",
        )

        ai_logger.info(f"=== FeasibilityCrew Execution Complete for Project '{project_id}' ===")
        return result


def get_feasibility_crew(
    mock_mode: bool = True,
    memory_manager: Optional[ProjectMemoryManager] = None,
) -> FeasibilityCrew:
    """Factory function for FeasibilityCrew."""
    return FeasibilityCrew(memory_manager=memory_manager, verbose=True)
