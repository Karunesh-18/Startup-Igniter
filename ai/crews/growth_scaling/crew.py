"""Growth & Scaling Crew implementation."""

from typing import Optional

from ai.crews.growth_scaling.tasks import execute_growth_scaling_task
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.growth_scaling import GrowthScalingResult
from ai.shared.logger import ai_logger


class GrowthScalingCrew:
    """Production orchestration engine for Growth & Scaling Crew."""

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
    ) -> GrowthScalingResult:
        """Execute growth strategy tasks and save result to project memory."""
        ai_logger.info(f"=== Starting GrowthScalingCrew Execution for Project '{project_id}' ===")

        result = execute_growth_scaling_task(project_id=project_id, idea_text=idea_text)

        self.memory_manager.write_memory(
            project_id=project_id,
            key="growth_scaling_result",
            value=result.model_dump(),
            source_phase="growth_scaling",
        )

        ai_logger.info(f"=== GrowthScalingCrew Execution Complete for Project '{project_id}' ===")
        return result


def get_growth_scaling_crew(
    mock_mode: bool = True,
    memory_manager: Optional[ProjectMemoryManager] = None,
) -> GrowthScalingCrew:
    """Factory function for GrowthScalingCrew."""
    return GrowthScalingCrew(memory_manager=memory_manager, verbose=True)
