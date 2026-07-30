"""Research Patent Service for orchestrating Research & Patent Crew execution."""

import uuid
from typing import Optional

from ai.crews.research_patent.crew import ResearchPatentCrew
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.context import ResearchPatentContext
from ai.schemas.idea_validation import IdeaValidationResult
from ai.schemas.market_research import MarketResearchResult
from ai.schemas.research_patent import ResearchPatentResult
from ai.shared.logger import ai_logger


class ResearchPatentService:
    """Production service encapsulating Research & Patent Analysis Crew execution."""

    def __init__(self, memory_manager: Optional[ProjectMemoryManager] = None):
        self.memory_manager = memory_manager or ProjectMemoryManager(use_mock_store=True)

    def run_research_patent(
        self,
        idea_validation: IdeaValidationResult,
        market_research: Optional[MarketResearchResult] = None,
        project_id: Optional[str] = None,
        mock_mode: bool = False,
    ) -> ResearchPatentResult:
        """Run complete Research & Patent Analysis based on IdeaValidationResult and optional MarketResearchResult.

        Args:
            idea_validation: IdeaValidationResult model output from Crew 1.
            market_research: Optional MarketResearchResult model output from Crew 2.
            project_id: Optional explicit project UUID string.
            mock_mode: If True, operates in test simulation mode without live LLM calls.

        Returns:
            Unified ResearchPatentResult model.
        """
        proj_id = project_id or idea_validation.project_id or f"proj-{uuid.uuid4().hex[:8]}"
        ai_logger.info(f"ResearchPatentService starting for project '{proj_id}' (mock={mock_mode}).")

        context = ResearchPatentContext(
            project_id=proj_id,
            idea_validation=idea_validation,
            market_research=market_research,
        )

        crew = ResearchPatentCrew(memory_manager=self.memory_manager)
        result = crew.run(context=context, mock_mode=mock_mode)

        ai_logger.info(
            f"ResearchPatentService finished for project '{proj_id}'. "
            f"Overall Novelty: {result.overall_novelty_score}/100, TRL: {result.trl_level}, Confidence: {result.confidence_score}."
        )

        return result
