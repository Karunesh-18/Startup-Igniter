"""Market Research Crew implementation orchestrating 7 market research agents sequentially."""

import os
from typing import Any, Dict, List, Optional

from ai.agents.market_research import (
    run_competitor_comparison_agent,
    run_competitor_discovery_agent,
    run_customer_persona_generator_agent,
    run_industry_analysis_agent,
    run_market_research_agent,
    run_tam_sam_som_estimator_agent,
    run_trend_analysis_agent,
)
from ai.config import get_ai_settings
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.context import MarketResearchContext
from ai.schemas.market_research import MarketResearchResult
from ai.shared.logger import ai_logger

# Optional CrewAI Crew import check with type safety
try:
    from crewai import Crew as CrewAICrew, Process  # type: ignore
    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False
    CrewAICrew = None
    Process = None


class MarketResearchCrew:
    """Production orchestration engine for the Market Research Crew.

    Executes 7 agents sequentially with strict output validation, context propagation,
    and memory persistence:
    1. MarketResearchAgent
    2. IndustryAnalysisAgent
    3. TrendAnalysisAgent
    4. CompetitorDiscoveryAgent
    5. CompetitorComparisonAgent
    6. CustomerPersonaGenerator
    7. TAMSAMSOMEstimator
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
        context: MarketResearchContext,
        mock_mode: bool = False,
    ) -> MarketResearchResult:
        """Execute all 7 Market Research tasks sequentially.

        Args:
            context: Populated MarketResearchContext container (must include idea_validation).
            mock_mode: If True, operates offline in simulation mode.

        Returns:
            Unified MarketResearchResult object.
        """
        project_id = context.project_id
        ai_logger.info(
            f"=== Starting MarketResearchCrew Execution for Project '{project_id}' (mock_mode={mock_mode}) ==="
        )

        if not context.idea_validation:
            raise ValueError("MarketResearchContext must contain a valid IdeaValidationResult.")

        # --------------------------------------------------------------------
        # Task 1: Market Research Overview
        # --------------------------------------------------------------------
        ai_logger.info("[Crew Step 1/7] Running MarketResearchAgent...")
        mr_analysis = run_market_research_agent(
            context=context,
            memory_manager=self.memory_manager,
            mock_mode=mock_mode,
        )
        if not mr_analysis:
            raise RuntimeError("Task 1 (MarketResearchAgent) failed to produce a valid output.")
        ai_logger.info(f"Task 1 Success: Confidence Score = {mr_analysis.confidence_score}")

        # --------------------------------------------------------------------
        # Task 2: Industry Analysis
        # --------------------------------------------------------------------
        ai_logger.info("[Crew Step 2/7] Running IndustryAnalysisAgent...")
        ind_analysis = run_industry_analysis_agent(
            context=context,
            memory_manager=self.memory_manager,
            mock_mode=mock_mode,
        )
        if not ind_analysis:
            raise RuntimeError("Task 2 (IndustryAnalysisAgent) failed to produce a valid output.")
        ai_logger.info(f"Task 2 Success: Industry = '{ind_analysis.industry_name}'")

        # --------------------------------------------------------------------
        # Task 3: Trend Analysis
        # --------------------------------------------------------------------
        ai_logger.info("[Crew Step 3/7] Running TrendAnalysisAgent...")
        trend_analysis = run_trend_analysis_agent(
            context=context,
            memory_manager=self.memory_manager,
            mock_mode=mock_mode,
        )
        if not trend_analysis:
            raise RuntimeError("Task 3 (TrendAnalysisAgent) failed to produce a valid output.")
        ai_logger.info(f"Task 3 Success: Identified {len(trend_analysis.technology_trends)} tech trends.")

        # --------------------------------------------------------------------
        # Task 4: Competitor Discovery
        # --------------------------------------------------------------------
        ai_logger.info("[Crew Step 4/7] Running CompetitorDiscoveryAgent...")
        comp_disc = run_competitor_discovery_agent(
            context=context,
            memory_manager=self.memory_manager,
            mock_mode=mock_mode,
        )
        if not comp_disc:
            raise RuntimeError("Task 4 (CompetitorDiscoveryAgent) failed to produce a valid output.")
        ai_logger.info(f"Task 4 Success: Discovered {len(comp_disc.direct_competitors)} direct competitors.")

        # --------------------------------------------------------------------
        # Task 5: Competitor Comparison
        # --------------------------------------------------------------------
        ai_logger.info("[Crew Step 5/7] Running CompetitorComparisonAgent...")
        comp_comp = run_competitor_comparison_agent(
            context=context,
            memory_manager=self.memory_manager,
            mock_mode=mock_mode,
        )
        if not comp_comp:
            raise RuntimeError("Task 5 (CompetitorComparisonAgent) failed to produce a valid output.")
        ai_logger.info(f"Task 5 Success: Overall Competitive Score = {comp_comp.overall_competitive_score}")

        # --------------------------------------------------------------------
        # Task 6: Customer Persona Generator
        # --------------------------------------------------------------------
        ai_logger.info("[Crew Step 6/7] Running CustomerPersonaGenerator...")
        cust_persona = run_customer_persona_generator_agent(
            context=context,
            memory_manager=self.memory_manager,
            mock_mode=mock_mode,
        )
        if not cust_persona:
            raise RuntimeError("Task 6 (CustomerPersonaGenerator) failed to produce a valid output.")
        ai_logger.info(f"Task 6 Success: Primary Persona = '{cust_persona.primary_persona.persona_name}'")

        # --------------------------------------------------------------------
        # Task 7: TAM SAM SOM Estimator
        # --------------------------------------------------------------------
        ai_logger.info("[Crew Step 7/7] Running TAMSAMSOMEstimator...")
        tam_sam_som = run_tam_sam_som_estimator_agent(
            context=context,
            memory_manager=self.memory_manager,
            mock_mode=mock_mode,
        )
        if not tam_sam_som:
            raise RuntimeError("Task 7 (TAMSAMSOMEstimator) failed to produce a valid output.")
        ai_logger.info(f"Task 7 Success: TAM = {tam_sam_som.tam_value}, SOM = {tam_sam_som.som_value}")

        # --------------------------------------------------------------------
        # Overall Summary & Score Synthesis
        # --------------------------------------------------------------------
        ai_logger.info("Synthesizing final Market Research Crew output result...")

        cat = context.idea_validation.category_classification.primary_category

        overall_summary = (
            f"Comprehensive Market Research Analysis for '{context.idea_validation.idea_text}' ({cat}):\n\n"
            f"1. Market Overview: {mr_analysis.market_overview}\n"
            f"2. Industry Landscape: Operating in the {ind_analysis.industry_name} sector at stage '{ind_analysis.industry_lifecycle_stage}'.\n"
            f"3. Key Trends: Driven by technology trends such as {', '.join(trend_analysis.technology_trends[:2])}.\n"
            f"4. Competitive Environment: Key direct competitors include {', '.join(comp_disc.market_leaders[:2])}. Positioning score: {comp_comp.overall_competitive_score}/10.\n"
            f"5. Target Persona: Core buyer profile '{cust_persona.primary_persona.persona_name}' ({cust_persona.primary_persona.occupation}).\n"
            f"6. Market Sizing: Total Addressable Market (TAM) estimated at {tam_sam_som.tam_value}, SAM at {tam_sam_som.sam_value}, and SOM at {tam_sam_som.som_value}."
        )

        # Dynamic Market Opportunity Score Calculation (0.0 to 100.0)
        # Weights: Market Overview (25%), Industry (25%), Trend (25%), Competitive Score (25%)
        s1 = float(mr_analysis.confidence_score) * 100.0
        s2 = float(ind_analysis.confidence_score) * 100.0
        s3 = float(trend_analysis.confidence_score) * 100.0
        s4 = float(comp_comp.overall_competitive_score) * 10.0  # scale 0-10 to 0-100

        overall_market_score = round(0.25 * s1 + 0.25 * s2 + 0.25 * s3 + 0.25 * s4, 2)
        overall_market_score = min(max(overall_market_score, 0.0), 100.0)

        # Confidence Score Calculation (Average of 7 task confidence scores)
        conf_scores = [
            mr_analysis.confidence_score,
            ind_analysis.confidence_score,
            trend_analysis.confidence_score,
            comp_disc.confidence_score,
            comp_comp.confidence_score,
            cust_persona.confidence_score,
            tam_sam_som.confidence_score,
        ]
        avg_confidence = round(sum(conf_scores) / len(conf_scores), 2)
        avg_confidence = min(max(avg_confidence, 0.0), 1.0)

        final_result = MarketResearchResult(
            project_id=project_id,
            market_research=mr_analysis,
            industry_analysis=ind_analysis,
            trend_analysis=trend_analysis,
            competitor_discovery=comp_disc,
            competitor_comparison=comp_comp,
            customer_persona=cust_persona,
            tam_sam_som=tam_sam_som,
            overall_summary=overall_summary,
            overall_market_score=overall_market_score,
            confidence_score=avg_confidence,
        )

        # Save master result to ProjectMemory
        self.memory_manager.write_memory(
            project_id=project_id,
            key="market_research_result",
            value=final_result.model_dump(),
            source_phase="market_research",
        )

        ai_logger.info(
            f"=== MarketResearchCrew Execution Complete: Score = {overall_market_score}, Confidence = {avg_confidence} ==="
        )

        return final_result
