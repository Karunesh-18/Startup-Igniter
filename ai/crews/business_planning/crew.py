"""Business Planning Crew implementation orchestrating Lean Canvas and financial modeling."""

from typing import Optional

from ai.crews.business_planning.tasks import (
    create_financial_model_task,
    create_lean_canvas_task,
)
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.business_plan import BusinessPlanResult
from ai.shared.logger import ai_logger


class BusinessPlanningCrew:
    """Production orchestration engine for Business Planning Crew."""

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
    ) -> BusinessPlanResult:
        """Execute Business Planning tasks and persist to project memory."""
        ai_logger.info(f"=== Starting BusinessPlanningCrew Execution for Project '{project_id}' ===")

        lean_canvas = create_lean_canvas_task(project_id=project_id, idea_text=idea_text, mock_mode=mock_mode)
        financial_model = create_financial_model_task(project_id=project_id, mock_mode=mock_mode)

        summary = (
            f"Business Plan for '{idea_text}':\n"
            f"UVP: {lean_canvas.unique_value_proposition}\n"
            f"Revenue Model: {financial_model.pricing_model}\n"
            f"Year 1 Projection: {financial_model.year_1_revenue_projection}"
        )

        result = BusinessPlanResult(
            project_id=project_id,
            lean_canvas=lean_canvas,
            financial_model=financial_model,
            executive_summary=summary,
            confidence_score=0.88,
        )

        self.memory_manager.write_memory(
            project_id=project_id,
            key="business_plan_result",
            value=result.model_dump(),
            source_phase="business_planning",
        )

        ai_logger.info(f"=== BusinessPlanningCrew Execution Complete for Project '{project_id}' ===")
        return result


def get_business_planning_crew(
    mock_mode: bool = True,
    memory_manager: Optional[ProjectMemoryManager] = None,
) -> BusinessPlanningCrew:
    """Factory function for BusinessPlanningCrew."""
    return BusinessPlanningCrew(memory_manager=memory_manager, verbose=True)
