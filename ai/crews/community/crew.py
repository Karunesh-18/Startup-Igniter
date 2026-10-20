"""Community & Peer Review Crew: spec-driven LLM call (see ai/crews/spec_runner.py), literal result in mock mode."""

from typing import Optional

from ai.crews.community.tasks import execute_community_peer_review_task
from ai.crews.spec_runner import run_spec_crew
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.community import CommunityResult
from ai.shared.logger import ai_logger


class CommunityCrew:
    """Production orchestration engine for Community & Peer Review Crew."""

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
    ) -> CommunityResult:
        """Execute the crew (prior = earlier crews' model_dumps keyed by crew) and save to project memory."""
        mock = self.mock_mode if mock_mode is None else mock_mode
        ai_logger.info(f"=== Starting CommunityCrew Execution for Project '{project_id}' (mock={mock}) ===")

        result = run_spec_crew(
            "community",
            CommunityResult,
            project_id,
            idea_text,
            prior,
            None,
            lambda: execute_community_peer_review_task(project_id=project_id, idea_text=idea_text),
            mock,
        )

        self.memory_manager.write_memory(
            project_id=project_id,
            key="community_result",
            value=result.model_dump(),
            source_phase="community",
        )

        ai_logger.info(f"=== CommunityCrew Execution Complete for Project '{project_id}' ===")
        return result


def get_community_crew(
    mock_mode: bool = True,
    memory_manager: Optional[ProjectMemoryManager] = None,
) -> CommunityCrew:
    """Factory function for CommunityCrew."""
    return CommunityCrew(memory_manager=memory_manager, verbose=True, mock_mode=mock_mode)
