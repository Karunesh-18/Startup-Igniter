"""Research & Patent Crew implementation orchestrating 7 research & patent agents sequentially."""

import os
from typing import Any, Dict, List, Optional

from ai.agents.research_patent import (
    run_existing_solution_analyzer_agent,
    run_innovation_gap_identifier_agent,
    run_intellectual_property_strategy_agent,
    run_patent_search_agent,
    run_research_paper_analyzer_agent,
    run_research_patent_summary_agent,
    run_technology_readiness_agent,
)
from ai.config import get_ai_settings
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.context import ResearchPatentContext
from ai.schemas.research_patent import ResearchPatentResult
from ai.shared.logger import ai_logger

try:
    from crewai import Crew as CrewAICrew, Process  # type: ignore
    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False
    CrewAICrew = None
    Process = None


class ResearchPatentCrew:
    """Production orchestration engine for the Research & Patent Analysis Crew (Crew 3).

    Executes 7 agents sequentially with strict output validation, context propagation,
    and memory persistence:
    1. PatentSearchAgent
    2. ResearchPaperAnalyzerAgent
    3. ExistingSolutionAnalyzerAgent
    4. InnovationGapIdentifierAgent
    5. TechnologyReadinessAgent
    6. IntellectualPropertyStrategyAgent
    7. ResearchPatentSummaryAgent
    """

    def __init__(
        self,
        memory_manager: Optional[ProjectMemoryManager] = None,
        verbose: bool = True,
    ):
        self.memory_manager = memory_manager or ProjectMemoryManager(use_mock_store=True)
        self.verbose = verbose

    def run(
        self,
        context: ResearchPatentContext,
        mock_mode: bool = False,
    ) -> ResearchPatentResult:
        """Execute all 7 Research & Patent Analysis tasks sequentially.

        Args:
            context: Populated ResearchPatentContext container (must include idea_validation).
            mock_mode: If True, executes agents in mock simulation mode without live LLM calls.

        Returns:
            Unified ResearchPatentResult composite model.
        """
        project_id = context.project_id
        ai_logger.info(
            f"=== Starting ResearchPatentCrew Execution for Project '{project_id}' (mock_mode={mock_mode}) ==="
        )

        if not context.idea_validation:
            raise ValueError("ResearchPatentContext must contain a valid IdeaValidationResult from Crew 1.")

        # Step 1: PatentSearchAgent
        ai_logger.info("[Crew Step 1/7] Running PatentSearchAgent...")
        patent_res = run_patent_search_agent(
            context=context,
            memory_manager=self.memory_manager,
            mock_mode=mock_mode,
        )
        context.patent_analysis = patent_res
        ai_logger.info(f"Task 1 Success: Patent Activity = '{patent_res.patent_activity_level}'")

        # Step 2: ResearchPaperAnalyzerAgent
        ai_logger.info("[Crew Step 2/7] Running ResearchPaperAnalyzerAgent...")
        paper_res = run_research_paper_analyzer_agent(
            context=context,
            memory_manager=self.memory_manager,
            mock_mode=mock_mode,
        )
        context.research_paper_analysis = paper_res
        ai_logger.info(f"Task 2 Success: Academic Novelty Score = {paper_res.academic_novelty_score}/100")

        # Step 3: ExistingSolutionAnalyzerAgent
        ai_logger.info("[Crew Step 3/7] Running ExistingSolutionAnalyzerAgent...")
        sol_res = run_existing_solution_analyzer_agent(
            context=context,
            memory_manager=self.memory_manager,
            mock_mode=mock_mode,
        )
        context.existing_solution_analysis = sol_res
        ai_logger.info(f"Task 3 Success: Market Maturity = '{sol_res.market_maturity}'")

        # Step 4: InnovationGapIdentifierAgent
        ai_logger.info("[Crew Step 4/7] Running InnovationGapIdentifierAgent...")
        gap_res = run_innovation_gap_identifier_agent(
            context=context,
            memory_manager=self.memory_manager,
            mock_mode=mock_mode,
        )
        context.innovation_gap_analysis = gap_res
        ai_logger.info(f"Task 4 Success: Overall Gap Score = {gap_res.overall_gap_score}/100")

        # Step 5: TechnologyReadinessAgent
        ai_logger.info("[Crew Step 5/7] Running TechnologyReadinessAgent...")
        trl_res = run_technology_readiness_agent(
            context=context,
            memory_manager=self.memory_manager,
            mock_mode=mock_mode,
        )
        context.technology_readiness = trl_res
        ai_logger.info(f"Task 5 Success: TRL Level = {trl_res.trl_level} ({trl_res.trl_stage_name})")

        # Step 6: IntellectualPropertyStrategyAgent
        ai_logger.info("[Crew Step 6/7] Running IntellectualPropertyStrategyAgent...")
        ip_res = run_intellectual_property_strategy_agent(
            context=context,
            memory_manager=self.memory_manager,
            mock_mode=mock_mode,
        )
        context.ip_strategy = ip_res
        ai_logger.info(f"Task 6 Success: IP Defensibility Score = {ip_res.ip_defensibility_score}/100")

        # Step 7: ResearchPatentSummaryAgent
        ai_logger.info("[Crew Step 7/7] Running ResearchPatentSummaryAgent...")
        final_result = run_research_patent_summary_agent(
            context=context,
            memory_manager=self.memory_manager,
            mock_mode=mock_mode,
        )
        context.research_patent_result = final_result

        # Save complete crew result in memory
        self.memory_manager.write_memory(
            project_id=project_id,
            key="research_patent_result",
            value=final_result.model_dump(),
            source_phase="research_patent",
        )
        ai_logger.info(f"[LOCAL MEMORY] Saved 'research_patent_result' for project '{project_id}' in phase 'research_patent'")

        ai_logger.info(
            f"=== ResearchPatentCrew Execution Complete: Novelty Score = {final_result.overall_novelty_score}, "
            f"TRL = {final_result.trl_level}, Confidence = {final_result.confidence_score} ==="
        )

        return final_result
