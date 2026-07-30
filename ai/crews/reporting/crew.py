"""Master Executive Reporting Crew implementation."""

from typing import Optional

from ai.crews.reporting.tasks import execute_master_reporting_task
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.reporting import MasterReportResult
from ai.shared.logger import ai_logger


class ReportingCrew:
    """Production orchestration engine for Master Executive Reporting Crew."""

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
    ) -> MasterReportResult:
        """Execute master reporting tasks and save result to project memory."""
        ai_logger.info(f"=== Starting ReportingCrew Execution for Project '{project_id}' ===")

        result = execute_master_reporting_task(project_id=project_id, idea_text=idea_text)

        self.memory_manager.write_memory(
            project_id=project_id,
            key="master_report_result",
            value=result.model_dump(),
            source_phase="reporting",
        )

        ai_logger.info(f"=== ReportingCrew Execution Complete for Project '{project_id}' ===")
        return result


def get_reporting_crew(
    mock_mode: bool = True,
    memory_manager: Optional[ProjectMemoryManager] = None,
) -> ReportingCrew:
    """Factory function for ReportingCrew."""
    return ReportingCrew(memory_manager=memory_manager, verbose=True)
