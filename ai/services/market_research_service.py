"""Market Research Service for orchestrating Market Research Crew execution."""

import uuid
from typing import Optional

from ai.crews.market_research.crew import MarketResearchCrew
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.context import MarketResearchContext
from ai.schemas.idea_validation import IdeaValidationResult
from ai.schemas.market_research import MarketResearchResult
from ai.shared.logger import ai_logger


class MarketResearchService:
    """Production service encapsulating Market Research Crew execution."""

    def __init__(self, memory_manager: Optional[ProjectMemoryManager] = None):
        self.memory_manager = memory_manager or ProjectMemoryManager(use_mock_store=True)

    def run_market_research(
        self,
        idea_validation: IdeaValidationResult,
        project_id: Optional[str] = None,
        mock_mode: bool = False,
    ) -> MarketResearchResult:
        """Run complete Market Research analysis based on an IdeaValidationResult object.

        Args:
            idea_validation: IdeaValidationResult model output from Crew 1.
            project_id: Optional explicit project UUID.
            mock_mode: If True, operates in test mode without live LLM calls.

        Returns:
            Unified MarketResearchResult object.
        """
        proj_id = project_id or idea_validation.project_id or f"proj-{uuid.uuid4().hex[:8]}"
        ai_logger.info(f"MarketResearchService starting for project '{proj_id}' (mock={mock_mode}).")

        context = MarketResearchContext(
            project_id=proj_id,
            idea_validation=idea_validation,
        )

        crew = MarketResearchCrew(memory_manager=self.memory_manager)
        result = crew.run(context=context, mock_mode=mock_mode)

        ai_logger.info(
            f"MarketResearchService finished for project '{proj_id}'. "
            f"Overall Score: {result.overall_market_score}, Confidence: {result.confidence_score}."
        )

        return result
