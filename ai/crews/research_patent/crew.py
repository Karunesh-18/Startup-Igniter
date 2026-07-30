"""Research & Patent Crew implementation orchestrating USPTO prior-art searches."""

from typing import Optional

from ai.crews.research_patent.tasks import execute_patent_research_task
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.research_patent import PatentAnalysis
from ai.shared.logger import ai_logger


class ResearchPatentCrew:
    """Production orchestration engine for Research & Patent Crew."""

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
    ) -> PatentAnalysis:
        """Execute Patent Prior-Art search and persist results to project memory."""
        ai_logger.info(f"=== Starting ResearchPatentCrew Execution for Project '{project_id}' ===")

        analysis = execute_patent_research_task(project_id=project_id, idea_text=idea_text, mock_mode=mock_mode)

        self.memory_manager.write_memory(
            project_id=project_id,
            key="patent_analysis_result",
            value=analysis.model_dump(),
            source_phase="patent_research",
        )

        ai_logger.info(f"=== ResearchPatentCrew Execution Complete for Project '{project_id}' ===")
        return analysis


def get_research_patent_crew(
    mock_mode: bool = True,
    memory_manager: Optional[ProjectMemoryManager] = None,
) -> ResearchPatentCrew:
    """Factory function for ResearchPatentCrew."""
    return ResearchPatentCrew(memory_manager=memory_manager, verbose=True)
