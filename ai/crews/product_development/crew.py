"""Product Development Crew: spec-driven LLM call (see ai/crews/spec_runner.py), literal result in mock mode."""

from typing import Optional

from ai.crews.product_development.tasks import mock_result
from ai.crews.spec_runner import run_spec_crew
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.product_development import ProductDevelopmentResult
from ai.shared.logger import ai_logger


class ProductDevelopmentCrew:
    """Production orchestration engine for Product Development Crew."""

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
        category: str = "SaaS",
        mock_mode: Optional[bool] = None,
        prior: Optional[dict] = None,
    ) -> ProductDevelopmentResult:
        """Execute the crew (prior = earlier crews' model_dumps keyed by crew) and save to project memory."""
        mock = self.mock_mode if mock_mode is None else mock_mode
        ai_logger.info(f"=== Starting ProductDevelopmentCrew Execution for Project '{project_id}' (mock={mock}) ===")

        result = run_spec_crew(
            "product_development",
            ProductDevelopmentResult,
            project_id,
            idea_text,
            prior,
            None,
            lambda: mock_result(project_id=project_id, idea_text=idea_text, category=category),
            mock,
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
    return ProductDevelopmentCrew(memory_manager=memory_manager, verbose=True, mock_mode=mock_mode)
