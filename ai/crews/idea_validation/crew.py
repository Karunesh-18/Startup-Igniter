"""Idea Validation Crew implementation executing 6 real agents sequentially with live Groq LLM reasoning."""

import os
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel

from ai.agents.idea_validation import (
    get_customer_identifier_agent,
    get_innovation_scoring_agent,
    get_problem_statement_analyzer_agent,
    get_startup_category_classifier_agent,
    get_startup_idea_analyzer_agent,
    get_value_proposition_analyzer_agent,
)
from ai.agents.idea_validation.customer_identifier import (
    validate_agent_output as validate_customer_output,
)
from ai.agents.idea_validation.innovation_scoring_agent import (
    validate_agent_output as validate_innovation_output,
)
from ai.agents.idea_validation.problem_statement_analyzer import (
    validate_agent_output as validate_problem_output,
)
from ai.agents.idea_validation.startup_category_classifier import (
    validate_agent_output as validate_category_output,
)
from ai.agents.idea_validation.startup_idea_analyzer import (
    validate_agent_output as validate_idea_output,
)
from ai.agents.idea_validation.value_proposition_analyzer import (
    validate_agent_output as validate_value_output,
)
from ai.config import get_ai_settings
from ai.crews.idea_validation.config import IdeaValidationCrewConfig
from ai.crews.idea_validation.tasks import (
    create_category_classification_task,
    create_customer_identification_task,
    create_innovation_scoring_task,
    create_problem_statement_analysis_task,
    create_startup_idea_analysis_task,
    create_value_proposition_analysis_task,
)
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.customer_identifier import CustomerIdentification
from ai.schemas.idea_validation import IdeaValidationResult, StartupIdeaAnalysis
from ai.schemas.innovation_score import InnovationScoreAnalysis
from ai.schemas.problem_statement import ProblemStatementAnalysis
from ai.schemas.startup_category import StartupCategoryClassification
from ai.schemas.value_proposition import ValuePropositionAnalysis
from ai.shared.logger import ai_logger

# Optional CrewAI Crew import check with type safety
try:
    from crewai import Crew as CrewAICrew, Process  # type: ignore
    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False
    CrewAICrew = None
    Process = None


# Legacy response model alias for backward compatibility
class IdeaValidationOutput(BaseModel):
    """Legacy compatibility model wrapping IdeaValidationResult."""

    project_id: str
    predicted_category: str
    category_confidence: float
    idea_summary: Dict[str, Any]
    problem_analysis: Dict[str, Any]
    customer_analysis: Dict[str, Any]
    value_proposition: Dict[str, Any]
    innovation_scoring: Optional[Dict[str, Any]] = None


def _call_live_groq_llm(
    system_prompt: str,
    user_prompt: str,
    model_name: str,
    temperature: float = 0.1,
    timeout: float = 45.0,
    max_retries: int = 6,
) -> str:
    """Execute live LLM completion call using OpenRouter (primary) or Groq."""
    from ai.shared.llm_provider import call_live_llm
    return call_live_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model_name=model_name,
        temperature=temperature,
        timeout=timeout,
        max_retries=max_retries,
    )


class IdeaValidationCrew:
    """Production Crew managing the 6 Idea Validation Agents sequentially with live Groq LLM."""

    def __init__(
        self,
        config: Optional[IdeaValidationCrewConfig] = None,
        memory_manager: Optional[ProjectMemoryManager] = None,
        mock_mode: bool = False,
    ) -> None:
        """Initialize Idea Validation Crew with 6 live agents and memory manager."""
        self.config = config or IdeaValidationCrewConfig()
        self.memory_manager = memory_manager or ProjectMemoryManager(use_mock_store=True)
        self.mock_mode = mock_mode

        # Instantiate all 6 agents
        self.idea_agent = get_startup_idea_analyzer_agent(
            model_tier=self.config.analysis_model_tier,
            mock_mode=self.mock_mode,
        )
        self.problem_agent = get_problem_statement_analyzer_agent(
            model_tier=self.config.analysis_model_tier,
            mock_mode=self.mock_mode,
        )
        self.customer_agent = get_customer_identifier_agent(
            model_tier=self.config.analysis_model_tier,
            mock_mode=self.mock_mode,
        )
        self.value_agent = get_value_proposition_analyzer_agent(
            model_tier=self.config.analysis_model_tier,
            mock_mode=self.mock_mode,
        )
        self.category_agent = get_startup_category_classifier_agent(
            model_tier=self.config.classifier_model_tier,
            mock_mode=self.mock_mode,
        )
        self.innovation_agent = get_innovation_scoring_agent(
            model_tier=self.config.analysis_model_tier,
            mock_mode=self.mock_mode,
        )

    def _get_backstory(self, agent: Any) -> str:
        """Extract backstory text from agent dictionary or CrewAIAgent."""
        if isinstance(agent, dict):
            return agent.get("backstory", "")
        return getattr(agent, "backstory", "")

    def run(self, project_id: str, idea_text: str) -> IdeaValidationResult:
        """Execute full 6-agent sequential Idea Validation Crew pipeline against live Groq LLM.

        Args:
            project_id: Project UUID string identifier.
            idea_text: Submitted raw startup idea proposal.

        Returns:
            IdeaValidationResult containing all 6 validated Pydantic models.
        """
        settings = get_ai_settings()
        ai_logger.info(f"Starting live IdeaValidationCrew run for project '{project_id}'")

        # ---------------------------------------------------------------------
        # Step 1: StartupIdeaAnalyzer
        # ---------------------------------------------------------------------
        print("\nRunning StartupIdeaAnalyzer...")
        idea_user_prompt = (
            f"Analyze the following startup proposal: '{idea_text}'.\n\n"
            "Return pure JSON matching the StartupIdeaAnalysis schema with fields: "
            "summary, startup_category, operational_pillars, technical_feasibility_score, "
            "rationale, key_assumptions, strengths, weaknesses."
        )
        raw_idea_text = _call_live_groq_llm(
            system_prompt=self._get_backstory(self.idea_agent),
            user_prompt=idea_user_prompt,
            model_name=settings.groq_model_heavy,
        )
        idea_model = validate_idea_output(raw_idea_text)
        self.memory_manager.write_memory(
            project_id=project_id,
            key="startup_analysis",
            value=idea_model.model_dump(),
            source_phase="idea",
        )
        self.memory_manager.write_memory(
            project_id=project_id,
            key="idea_analysis",
            value=idea_model.model_dump(),
            source_phase="idea",
        )
        print("Completed")

        # ---------------------------------------------------------------------
        # Step 2: ProblemStatementAnalyzer
        # ---------------------------------------------------------------------
        print("\nRunning ProblemStatementAnalyzer...")
        problem_user_prompt = (
            f"Deconstruct the problem statement for startup proposal: '{idea_text}'.\n"
            f"Context summary: {idea_model.summary}\n\n"
            "Return pure JSON matching the ProblemStatementAnalysis schema with fields: "
            "problem_statement, affected_users, root_causes, existing_solutions, solution_gaps, "
            "problem_severity, urgency_score, confidence_score."
        )
        raw_problem_text = _call_live_groq_llm(
            system_prompt=self._get_backstory(self.problem_agent),
            user_prompt=problem_user_prompt,
            model_name=settings.groq_model_heavy,
        )
        problem_model = validate_problem_output(raw_problem_text)
        self.memory_manager.write_memory(
            project_id=project_id,
            key="problem_analysis",
            value=problem_model.model_dump(),
            source_phase="idea",
        )
        print("Completed")

        # ---------------------------------------------------------------------
        # Step 3: CustomerIdentifier
        # ---------------------------------------------------------------------
        print("\nRunning CustomerIdentifier...")
        customer_user_prompt = (
            f"Identify target customers and personas for startup proposal: '{idea_text}'.\n"
            f"Problem context: {problem_model.problem_statement}\n\n"
            "Return pure JSON matching the CustomerIdentification schema with fields: "
            "primary_customers, secondary_customers, end_users, decision_makers, customer_segments, "
            "demographics, geographic_markets, industries, pain_points, customer_needs, motivations, "
            "adoption_barriers, willingness_to_pay, confidence_score."
        )
        raw_customer_text = _call_live_groq_llm(
            system_prompt=self._get_backstory(self.customer_agent),
            user_prompt=customer_user_prompt,
            model_name=settings.groq_model_heavy,
        )
        customer_model = validate_customer_output(raw_customer_text)
        self.memory_manager.write_memory(
            project_id=project_id,
            key="customer_analysis",
            value=customer_model.model_dump(),
            source_phase="idea",
        )
        print("Completed")

        # ---------------------------------------------------------------------
        # Step 4: ValuePropositionAnalyzer
        # ---------------------------------------------------------------------
        print("\nRunning ValuePropositionAnalyzer...")
        value_user_prompt = (
            f"Evaluate the value proposition for startup proposal: '{idea_text}'.\n"
            f"Target customer context: {customer_model.primary_customers}\n\n"
            "Return pure JSON matching the ValuePropositionAnalysis schema with fields: "
            "core_value_proposition, unique_selling_proposition, functional_benefits, emotional_benefits, "
            "customer_outcomes, differentiators, value_clarity_score, customer_value_score, confidence_score."
        )
        raw_value_text = _call_live_groq_llm(
            system_prompt=self._get_backstory(self.value_agent),
            user_prompt=value_user_prompt,
            model_name=settings.groq_model_heavy,
        )
        value_model = validate_value_output(raw_value_text)
        self.memory_manager.write_memory(
            project_id=project_id,
            key="value_proposition",
            value=value_model.model_dump(),
            source_phase="idea",
        )
        print("Completed")

        # ---------------------------------------------------------------------
        # Step 5: StartupCategoryClassifier
        # ---------------------------------------------------------------------
        print("\nRunning StartupCategoryClassifier...")
        category_user_prompt = (
            f"Classify the following startup proposal into industry taxonomy: '{idea_text}'.\n\n"
            "Return pure JSON matching the StartupCategoryClassification schema with fields: "
            "primary_category, secondary_categories, industry, technology_domains, business_model, "
            "revenue_model, startup_stage, target_market, confidence_score, reasoning."
        )
        raw_category_text = _call_live_groq_llm(
            system_prompt=self._get_backstory(self.category_agent),
            user_prompt=category_user_prompt,
            model_name=settings.groq_model_fast,
        )
        category_model = validate_category_output(raw_category_text)
        self.memory_manager.write_memory(
            project_id=project_id,
            key="category_classification",
            value=category_model.model_dump(),
            source_phase="idea",
        )
        print("Completed")

        # ---------------------------------------------------------------------
        # Step 6: InnovationScoringAgent
        # ---------------------------------------------------------------------
        print("\nRunning InnovationScoringAgent...")
        innovation_user_prompt = (
            f"Evaluate the innovation level for startup proposal: '{idea_text}'.\n"
            f"Category context: {category_model.primary_category}\n\n"
            "Return pure JSON matching the InnovationScoreAnalysis schema with fields: "
            "overall_innovation_score, innovation_level, novelty_score, technology_innovation_score, "
            "business_model_innovation_score, problem_originality_score, differentiation_score, "
            "strengths, improvement_opportunities, reasoning, confidence_score."
        )
        raw_innovation_text = _call_live_groq_llm(
            system_prompt=self._get_backstory(self.innovation_agent),
            user_prompt=innovation_user_prompt,
            model_name=settings.groq_model_heavy,
        )
        innovation_model = validate_innovation_output(raw_innovation_text)
        self.memory_manager.write_memory(
            project_id=project_id,
            key="innovation_scoring",
            value=innovation_model.model_dump(),
            source_phase="idea",
        )
        print("Completed\n")

        # ---------------------------------------------------------------------
        # Compute Dynamic Weighted Composite Score
        # ---------------------------------------------------------------------
        composite_score = round(
            0.20 * idea_model.technical_feasibility_score
            + 0.20 * problem_model.urgency_score
            + 0.20 * value_model.customer_value_score
            + 0.15 * category_model.confidence_score
            + 0.25 * innovation_model.overall_innovation_score,
            2,
        )

        result = IdeaValidationResult(
            project_id=project_id,
            idea_text=idea_text,
            idea_analysis=idea_model,
            problem_analysis=problem_model,
            customer_identification=customer_model,
            value_proposition=value_model,
            category_classification=category_model,
            innovation_scoring=innovation_model,
            overall_validation_score=composite_score,
        )

        ai_logger.info(
            f"IdeaValidationCrew completed for project '{project_id}'. Composite Score: {composite_score}/100"
        )
        return result


def get_idea_validation_crew(
    mock_mode: bool = False,
    memory_manager: Optional[ProjectMemoryManager] = None,
) -> IdeaValidationCrew:
    """Factory function returning configured IdeaValidationCrew instance."""
    return IdeaValidationCrew(mock_mode=mock_mode, memory_manager=memory_manager)
