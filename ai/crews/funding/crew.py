"""Funding & Investor Readiness Crew: spec-driven LLM call (see ai/crews/spec_runner.py), literal result in mock mode."""

from typing import Optional

from ai.crews.funding.tasks import execute_funding_readiness_task
from ai.crews.spec_runner import category_of, fetch_research, run_spec_crew
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.funding import FundingResult
from ai.shared.logger import ai_logger


class FundingCrew:
    """Production orchestration engine for Funding & Investor Readiness Crew."""

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
    ) -> FundingResult:
        """Execute the crew (prior = earlier crews' model_dumps keyed by crew) and save to project memory."""
        mock = self.mock_mode if mock_mode is None else mock_mode
        ai_logger.info(f"=== Starting FundingCrew Execution for Project '{project_id}' (mock={mock}) ===")

        result = run_spec_crew(
            "funding",
            FundingResult,
            project_id,
            idea_text,
            prior,
            None if mock else fetch_research("gather_funding_research", category_of(prior, idea_text)),
            lambda: execute_funding_readiness_task(project_id=project_id, idea_text=idea_text),
            mock,
        )

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
    return FundingCrew(memory_manager=memory_manager, verbose=True, mock_mode=mock_mode)
