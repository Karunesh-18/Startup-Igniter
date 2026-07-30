"""Production workflow orchestrating Idea Validation (Crew 1) and Market Research (Crew 2)."""

import uuid
from typing import Optional

from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.idea_validation import IdeaValidationResult
from ai.schemas.market_research import MarketResearchResult
from ai.schemas.startup_analysis import StartupAnalysisResult
from ai.services.idea_validation_service import IdeaValidationService
from ai.services.market_research_service import MarketResearchService
from ai.shared.logger import ai_logger


class StartupAnalysisWorkflow:
    """Orchestrates end-to-end multi-crew pipeline combining Idea Validation and Market Research."""

    def __init__(self, memory_manager: Optional[ProjectMemoryManager] = None) -> None:
        """Initialize StartupAnalysisWorkflow.

        Args:
            memory_manager: Optional shared ProjectMemoryManager instance.
        """
        self.memory_manager = memory_manager or ProjectMemoryManager(use_mock_store=True)
        self.idea_validation_service = IdeaValidationService(memory_manager=self.memory_manager)
        self.market_research_service = MarketResearchService(memory_manager=self.memory_manager)

    def run_workflow(
        self,
        idea_text: str,
        project_id: Optional[str] = None,
        mock_mode: bool = False,
    ) -> StartupAnalysisResult:
        """Execute full pipeline: User Startup Idea -> Crew 1 (Idea Validation) -> Crew 2 (Market Research).

        The user enters their startup idea proposal ONLY ONCE.

        Args:
            idea_text: User startup idea text proposal.
            project_id: Optional explicit project ID.
            mock_mode: If True, operates in test mock mode without live network LLM calls.

        Returns:
            Unified StartupAnalysisResult combining validation, market research, and readiness score.
        """
        if not idea_text or not idea_text.strip():
            raise ValueError("Startup idea proposal text cannot be empty.")

        resolved_project_id = project_id or f"proj-{uuid.uuid4().hex[:8]}"
        ai_logger.info(
            f"=== [START WORKFLOW] Executing StartupAnalysisWorkflow for Project '{resolved_project_id}' ==="
        )

        # --------------------------------------------------------------------
        # Phase 1: Idea Validation Crew (Crew 1)
        # --------------------------------------------------------------------
        ai_logger.info("--> Running Phase 1: Idea Validation Service (Crew 1)...")
        try:
            val_result: IdeaValidationResult = self.idea_validation_service.validate_idea(
                idea_text=idea_text.strip(),
                project_id=resolved_project_id,
            )
        except Exception as exc:
            ai_logger.error(f"Phase 1 (Idea Validation Crew) failed: {exc}")
            raise RuntimeError(f"Idea Validation Crew execution failed: {exc}") from exc

        if not val_result:
            raise RuntimeError("Phase 1 (Idea Validation Crew) produced an empty result.")

        ai_logger.info(
            f"--> Phase 1 Complete. Validation Score: {val_result.overall_validation_score}/100.0"
        )

        # --------------------------------------------------------------------
        # Phase 2: Market Research Crew (Crew 2)
        # --------------------------------------------------------------------
        ai_logger.info("--> Running Phase 2: Market Research Service (Crew 2)...")
        mr_result: Optional[MarketResearchResult] = None
        mr_error: Optional[str] = None

        try:
            mr_result = self.market_research_service.run_market_research(
                idea_validation=val_result,
                project_id=resolved_project_id,
                mock_mode=mock_mode,
            )
            ai_logger.info(
                f"--> Phase 2 Complete. Market Score: {mr_result.overall_market_score}/100.0"
            )
        except Exception as exc:
            mr_error = str(exc)
            ai_logger.warning(
                f"Phase 2 (Market Research Crew) encountered error: {mr_error}. Generating partial analysis result."
            )

        # --------------------------------------------------------------------
        # Phase 3: Synthesis & Readiness Score Calculation
        # --------------------------------------------------------------------
        ai_logger.info("--> Synthesizing Master StartupAnalysisResult...")

        if mr_result is not None:
            # Dynamic Weighted Calculation combining multi-dimensional criteria:
            # Innovation & Validation (50%), Market Attractiveness & Sizing (50%)
            val_score = float(val_result.overall_validation_score)
            mr_score = float(mr_result.overall_market_score)
            readiness_score = round(0.50 * val_score + 0.50 * mr_score, 2)
            readiness_score = min(max(readiness_score, 0.0), 100.0)

            val_confidence = round(
                (
                    val_result.customer_identification.confidence_score
                    + val_result.category_classification.confidence_score
                )
                / 2.0,
                2,
            )
            avg_confidence = min(max(round((val_confidence + mr_result.confidence_score) / 2.0, 2), 0.0), 1.0)
            status_str = "success"

            executive_summary = (
                f"STRATEGIC ANALYSIS SUMMARY FOR '{val_result.idea_text}' ({val_result.category_classification.primary_category}):\n\n"
                f"1. IDEA VALIDATION SCORE: {val_score}/100\n"
                f"   - Target Customer: {', '.join(val_result.customer_identification.primary_customers[:2])}\n"
                f"   - Unique Value Proposition: {val_result.value_proposition.core_value_proposition}\n"
                f"   - Innovation Score: {val_result.innovation_scoring.overall_innovation_score}/100 ({val_result.innovation_scoring.innovation_level})\n\n"
                f"2. MARKET RESEARCH SCORE: {mr_score}/100\n"
                f"   - Industry: {mr_result.industry_analysis.industry_name} ({mr_result.industry_analysis.industry_lifecycle_stage})\n"
                f"   - Positioning Score: {mr_result.competitor_comparison.overall_competitive_score}/10.0\n"
                f"   - Customer Persona: {mr_result.customer_persona.primary_persona.persona_name} ({mr_result.customer_persona.primary_persona.occupation})\n"
                f"   - Market Opportunity: TAM = {mr_result.tam_sam_som.tam_value}, SAM = {mr_result.tam_sam_som.sam_value}, SOM = {mr_result.tam_sam_som.som_value}\n\n"
                f"OVERALL READINESS RATING: {readiness_score}/100.0 (Confidence: {avg_confidence})"
            )
        else:
            readiness_score = round(val_result.overall_validation_score * 0.5, 2)
            val_confidence = round(
                (
                    val_result.customer_identification.confidence_score
                    + val_result.category_classification.confidence_score
                )
                / 2.0,
                2,
            )
            avg_confidence = min(max(val_confidence, 0.0), 1.0)
            status_str = "partial_failure"

            executive_summary = (
                f"PARTIAL ANALYSIS SUMMARY FOR '{val_result.idea_text}':\n\n"
                f"1. IDEA VALIDATION SCORE: {val_result.overall_validation_score}/100\n"
                f"   - Category: {val_result.category_classification.primary_category}\n"
                f"   - Innovation Score: {val_result.innovation_scoring.overall_innovation_score}/100\n\n"
                f"2. MARKET RESEARCH STATUS: FAILED ({mr_error})\n\n"
                f"OVERALL READINESS RATING: {readiness_score}/100.0 (Partial Analysis)"
            )

        master_result = StartupAnalysisResult(
            project_id=resolved_project_id,
            startup_idea_text=val_result.idea_text,
            idea_validation=val_result,
            market_research=mr_result,
            overall_summary=executive_summary,
            overall_readiness_score=readiness_score,
            confidence_score=avg_confidence,
            status=status_str,
            error_message=mr_error,
        )

        # Save to Project Memory
        self.memory_manager.write_memory(
            project_id=resolved_project_id,
            key="master_startup_analysis",
            value=master_result.model_dump(),
            source_phase="full_pipeline",
        )

        ai_logger.info(
            f"=== [END WORKFLOW] StartupAnalysisWorkflow Complete for '{resolved_project_id}'. "
            f"Readiness Score: {master_result.overall_readiness_score}/100, Status: {master_result.status} ==="
        )

        return master_result
