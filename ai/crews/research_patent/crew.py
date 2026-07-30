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
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.context import ResearchPatentContext
from ai.schemas.research_patent import ResearchPatentResult
from ai.shared.logger import ai_logger


class ResearchPatentCrew:
    """Production orchestration engine for Research & Patent Crew (Crew 3).

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
        context: Optional[ResearchPatentContext] = None,
        project_id: Optional[str] = None,
        idea_text: Optional[str] = None,
        mock_mode: bool = False,
    ) -> ResearchPatentResult:
        """Execute all 7 Research & Patent Analysis tasks sequentially.

        Args:
            context: Populated ResearchPatentContext container.
            project_id: Optional explicit project UUID (if context not supplied).
            idea_text: Optional raw startup idea (if context not supplied).
            mock_mode: If True, operates offline in simulation mode.

        Returns:
            Unified ResearchPatentResult master model output.
        """
        if context is None:
            pid = project_id or "proj-default"
            from ai.schemas.idea_validation import IdeaValidationResult, StartupIdeaAnalysis
            from ai.schemas.problem_statement import ProblemStatementAnalysis
            from ai.schemas.value_proposition import ValuePropositionAnalysis
            from ai.schemas.startup_category import StartupCategoryClassification
            from ai.schemas.innovation_score import InnovationScoreAnalysis

            mock_val = IdeaValidationResult(
                project_id=pid,
                idea_text=idea_text or "Default startup idea",
                idea_analysis=StartupIdeaAnalysis(summary="Default summary", startup_category="SaaS"),
                problem_analysis=ProblemStatementAnalysis(problem_statement="Default problem"),
                value_proposition=ValuePropositionAnalysis(core_value_proposition="Default value"),
                category_classification=StartupCategoryClassification(primary_category="SaaS"),
                innovation_scoring=InnovationScoreAnalysis(overall_innovation_score=80.0),
            )
            context = ResearchPatentContext(project_id=pid, idea_validation=mock_val)

        proj_id = context.project_id
        ai_logger.info(f"=== Starting ResearchPatentCrew Execution for Project '{proj_id}' (mock_mode={mock_mode}) ===")

        # Task 1: Patent Search
        ai_logger.info("[Crew 3 Step 1/7] Running PatentSearchAgent...")
        pat_analysis = run_patent_search_agent(context=context, memory_manager=self.memory_manager, mock_mode=mock_mode)
        context.patent_analysis = pat_analysis

        # Task 2: Research Paper Analysis
        ai_logger.info("[Crew 3 Step 2/7] Running ResearchPaperAnalyzerAgent...")
        paper_analysis = run_research_paper_analyzer_agent(context=context, memory_manager=self.memory_manager, mock_mode=mock_mode)
        context.research_paper_analysis = paper_analysis

        # Task 3: Existing Solution Analysis
        ai_logger.info("[Crew 3 Step 3/7] Running ExistingSolutionAnalyzerAgent...")
        solution_analysis = run_existing_solution_analyzer_agent(context=context, memory_manager=self.memory_manager, mock_mode=mock_mode)
        context.existing_solution_analysis = solution_analysis

        # Task 4: Innovation Gap Identifier
        ai_logger.info("[Crew 3 Step 4/7] Running InnovationGapIdentifierAgent...")
        gap_analysis = run_innovation_gap_identifier_agent(context=context, memory_manager=self.memory_manager, mock_mode=mock_mode)
        context.innovation_gap_analysis = gap_analysis

        # Task 5: Technology Readiness
        ai_logger.info("[Crew 3 Step 5/7] Running TechnologyReadinessAgent...")
        trl_analysis = run_technology_readiness_agent(context=context, memory_manager=self.memory_manager, mock_mode=mock_mode)
        context.technology_readiness = trl_analysis

        # Task 6: Intellectual Property Strategy
        ai_logger.info("[Crew 3 Step 6/7] Running IntellectualPropertyStrategyAgent...")
        ip_analysis = run_intellectual_property_strategy_agent(context=context, memory_manager=self.memory_manager, mock_mode=mock_mode)
        context.ip_strategy = ip_analysis

        # Task 7: Research Patent Summary
        ai_logger.info("[Crew 3 Step 7/7] Running ResearchPatentSummaryAgent...")
        summary_result = run_research_patent_summary_agent(context=context, memory_manager=self.memory_manager, mock_mode=mock_mode)

        self.memory_manager.write_memory(
            project_id=proj_id,
            key="research_patent_result",
            value=summary_result.model_dump(),
            source_phase="research_patent",
        )

        ai_logger.info(
            f"=== ResearchPatentCrew Execution Complete: Novelty={summary_result.overall_novelty_score}, "
            f"TRL={summary_result.trl_level}, Confidence={summary_result.confidence_score} ==="
        )
        return summary_result


def get_research_patent_crew(
    mock_mode: bool = True,
    memory_manager: Optional[ProjectMemoryManager] = None,
) -> ResearchPatentCrew:
    """Factory function for ResearchPatentCrew."""
    return ResearchPatentCrew(memory_manager=memory_manager, verbose=True)
