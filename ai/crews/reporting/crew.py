"""Master Executive Reporting Crew: spec-driven LLM call (see ai/crews/spec_runner.py), literal result in mock mode."""

from typing import Optional

from ai.crews.reporting.tasks import execute_master_reporting_task
from ai.crews.spec_runner import run_spec_crew
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.reporting import MasterReportResult
from ai.shared.logger import ai_logger


class ReportingCrew:
    """Production orchestration engine for Master Executive Reporting Crew."""

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
        mock_mode: Optional[bool] = None,
        prior: Optional[dict] = None,
    ) -> MasterReportResult:
        """Execute the crew (prior = earlier crews' model_dumps keyed by crew) and save to project memory."""
        mock = self.mock_mode if mock_mode is None else mock_mode
        ai_logger.info(f"=== Starting ReportingCrew Execution for Project '{project_id}' (mock={mock}) ===")

        result = run_spec_crew(
            "reporting",
            MasterReportResult,
            project_id,
            idea_text,
            prior,
            None,
            lambda: execute_master_reporting_task(project_id=project_id, idea_text=idea_text),
            mock,
        )

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
    return ReportingCrew(memory_manager=memory_manager, verbose=True, mock_mode=mock_mode)
