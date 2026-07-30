"""Community & Peer Review Crew implementation."""

from typing import Optional

from ai.crews.community.tasks import execute_community_peer_review_task
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.community import CommunityResult
from ai.shared.logger import ai_logger


class CommunityCrew:
    """Production orchestration engine for Community Crew."""

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
    ) -> CommunityResult:
        """Execute community peer review tasks and save result to project memory."""
        ai_logger.info(f"=== Starting CommunityCrew Execution for Project '{project_id}' ===")

        result = execute_community_peer_review_task(project_id=project_id, idea_text=idea_text)

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
    return CommunityCrew(memory_manager=memory_manager, verbose=True)
