"""Technical Feasibility Crew: spec-driven LLM call (see ai/crews/spec_runner.py), literal result in mock mode."""

from typing import Optional

from ai.crews.feasibility.tasks import execute_feasibility_analysis_task
from ai.crews.spec_runner import category_of, fetch_research, run_spec_crew
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.feasibility import FeasibilityResult
from ai.shared.logger import ai_logger


class FeasibilityCrew:
    """Production orchestration engine for Technical Feasibility Crew."""

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
    ) -> FeasibilityResult:
        """Execute the crew (prior = earlier crews' model_dumps keyed by crew) and save to project memory."""
        mock = self.mock_mode if mock_mode is None else mock_mode
        ai_logger.info(f"=== Starting FeasibilityCrew Execution for Project '{project_id}' (mock={mock}) ===")

        result = run_spec_crew(
            "feasibility",
            FeasibilityResult,
            project_id,
            idea_text,
            prior,
            None if mock else fetch_research("gather_tech_research", idea_text),
            lambda: execute_feasibility_analysis_task(project_id=project_id, idea_text=idea_text),
            mock,
        )

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
    return FeasibilityCrew(memory_manager=memory_manager, verbose=True, mock_mode=mock_mode)
