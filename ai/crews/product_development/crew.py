"""Product Development Crew implementation orchestrating MVP roadmap & tech stack selection."""

from typing import Optional

from ai.crews.product_development.tasks import (
    execute_mvp_roadmap_task,
    recommend_tech_stack_task,
)
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.product_development import ProductDevelopmentResult
from ai.shared.logger import ai_logger


class ProductDevelopmentCrew:
    """Production orchestration engine for Product Development Crew."""

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
        category: str = "SaaS",
        mock_mode: bool = True,
    ) -> ProductDevelopmentResult:
        """Execute Product Development tasks and persist to project memory."""
        ai_logger.info(f"=== Starting ProductDevelopmentCrew Execution for Project '{project_id}' ===")

        mvp_features = execute_mvp_roadmap_task(project_id=project_id, idea_text=idea_text)
        tech_stack = recommend_tech_stack_task(project_id=project_id, category=category)

        arch_summary = (
            f"Architecture overview for '{idea_text}':\n"
            f"Frontend: {tech_stack.frontend}\n"
            f"Backend: {tech_stack.backend}\n"
            f"Database: {tech_stack.database}\n"
            f"Hosting: {tech_stack.hosting}"
        )

        result = ProductDevelopmentResult(
            project_id=project_id,
            mvp_features=mvp_features,
            tech_stack=tech_stack,
            architecture_overview=arch_summary,
            confidence_score=0.88,
        )

        self.memory_manager.write_memory(
            project_id=project_id,
            key="product_development_result",
            value=result.model_dump(),
            source_phase="product_development",
        )

        ai_logger.info(f"=== ProductDevelopmentCrew Execution Complete for Project '{project_id}' ===")
        return result


def get_product_development_crew(
    mock_mode: bool = True,
    memory_manager: Optional[ProjectMemoryManager] = None,
) -> ProductDevelopmentCrew:
    """Factory function for ProductDevelopmentCrew."""
    return ProductDevelopmentCrew(memory_manager=memory_manager, verbose=True)
