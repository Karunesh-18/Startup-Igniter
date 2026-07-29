"""Task definitions for Idea Validation Crew.

Defines production CrewAI Tasks for each of the 6 idea validation agents:
1. StartupIdeaAnalyzer
2. ProblemStatementAnalyzer
3. CustomerIdentifier
4. ValuePropositionAnalyzer
5. StartupCategoryClassifier
6. InnovationScoringAgent

Task outputs are configured with output_pydantic for structured Pydantic model validation.
"""

from typing import Any, Dict, List, Optional

from ai.schemas.customer_identifier import CustomerIdentification
from ai.schemas.idea_validation import StartupIdeaAnalysis
from ai.schemas.innovation_score import InnovationScoreAnalysis
from ai.schemas.problem_statement import ProblemStatementAnalysis
from ai.schemas.startup_category import StartupCategoryClassification
from ai.schemas.value_proposition import ValuePropositionAnalysis

# Optional CrewAI Task import check with type safety
try:
    from crewai import Task as CrewAITask  # type: ignore
    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False
    CrewAITask = None


# ============================================================================
# 1. StartupIdeaAnalyzer Task
# ============================================================================
def create_startup_idea_analysis_task(
    agent: Any, idea_text: str, context: Optional[List[Any]] = None
) -> Any:
    """Create CrewAI task for holistic startup idea architectural analysis."""
    description = (
        f"Analyze the core concept, operational pillars, technical feasibility, "
        f"and key assumptions for the raw startup proposal: '{idea_text}'. "
        "Return pure JSON matching the StartupIdeaAnalysis Pydantic schema."
    )
    expected_output = (
        "Valid JSON object matching StartupIdeaAnalysis schema with fields: "
        "summary, startup_category, operational_pillars, technical_feasibility_score, "
        "rationale, key_assumptions, strengths, weaknesses."
    )

    if HAS_CREWAI and CrewAITask is not None and not (isinstance(agent, dict) and agent.get("mock_mode")):
        kwargs: Dict[str, Any] = {
            "description": description,
            "expected_output": expected_output,
            "agent": agent,
            "output_pydantic": StartupIdeaAnalysis,
        }
        if context:
            kwargs["context"] = context
        return CrewAITask(**kwargs)

    return {
        "task_name": "startup_idea_analysis",
        "description": description,
        "expected_output": expected_output,
        "agent": agent,
        "schema_class": StartupIdeaAnalysis,
        "context": context,
    }


# ============================================================================
# 2. ProblemStatementAnalyzer Task
# ============================================================================
def create_problem_statement_analysis_task(
    agent: Any, idea_text: str, context: Optional[List[Any]] = None
) -> Any:
    """Create CrewAI task for problem statement deconstruction and pain point severity evaluation."""
    description = (
        f"Deconstruct the problem statement, affected users, root causes, existing workarounds, "
        f"solution gaps, severity, urgency, and confidence score for proposal: '{idea_text}'. "
        "Re-use prior analysis context where appropriate instead of re-analyzing the raw idea. "
        "Return pure JSON matching the ProblemStatementAnalysis Pydantic schema."
    )
    expected_output = (
        "Valid JSON object matching ProblemStatementAnalysis schema with fields: "
        "problem_statement, affected_users, root_causes, existing_solutions, solution_gaps, "
        "problem_severity, urgency_score, confidence_score."
    )

    if HAS_CREWAI and CrewAITask is not None and not (isinstance(agent, dict) and agent.get("mock_mode")):
        kwargs: Dict[str, Any] = {
            "description": description,
            "expected_output": expected_output,
            "agent": agent,
            "output_pydantic": ProblemStatementAnalysis,
        }
        if context:
            kwargs["context"] = context
        return CrewAITask(**kwargs)

    return {
        "task_name": "problem_statement_analysis",
        "description": description,
        "expected_output": expected_output,
        "agent": agent,
        "schema_class": ProblemStatementAnalysis,
        "context": context,
    }


# ============================================================================
# 3. CustomerIdentifier Task
# ============================================================================
def create_customer_identification_task(
    agent: Any, idea_text: str, context: Optional[List[Any]] = None
) -> Any:
    """Create CrewAI task for target customer, buyer persona, and ICP identification."""
    description = (
        f"Identify primary target customers, secondary customers, end users, decision makers, "
        f"customer segments, demographics, geographic markets, industries, pain points, needs, "
        f"motivations, adoption barriers, willingness to pay, and confidence score for: '{idea_text}'. "
        "Leverage prior idea and problem statement context. "
        "Return pure JSON matching the CustomerIdentification Pydantic schema."
    )
    expected_output = (
        "Valid JSON object matching CustomerIdentification schema with fields: "
        "primary_customers, secondary_customers, end_users, decision_makers, customer_segments, "
        "demographics, geographic_markets, industries, pain_points, customer_needs, motivations, "
        "adoption_barriers, willingness_to_pay, confidence_score."
    )

    if HAS_CREWAI and CrewAITask is not None and not (isinstance(agent, dict) and agent.get("mock_mode")):
        kwargs: Dict[str, Any] = {
            "description": description,
            "expected_output": expected_output,
            "agent": agent,
            "output_pydantic": CustomerIdentification,
        }
        if context:
            kwargs["context"] = context
        return CrewAITask(**kwargs)

    return {
        "task_name": "customer_identification",
        "description": description,
        "expected_output": expected_output,
        "agent": agent,
        "schema_class": CustomerIdentification,
        "context": context,
    }


# ============================================================================
# 4. ValuePropositionAnalyzer Task
# ============================================================================
def create_value_proposition_analysis_task(
    agent: Any, idea_text: str, context: Optional[List[Any]] = None
) -> Any:
    """Create CrewAI task for core value proposition formulation and differentiator assessment."""
    description = (
        f"Evaluate the core value proposition, unique selling proposition (USP), functional and "
        f"emotional benefits, customer outcomes, differentiators, value clarity score, customer value score, "
        f"and confidence score for proposal: '{idea_text}'. "
        "Re-use prior customer identification and problem analysis context. "
        "Return pure JSON matching the ValuePropositionAnalysis Pydantic schema."
    )
    expected_output = (
        "Valid JSON object matching ValuePropositionAnalysis schema with fields: "
        "core_value_proposition, unique_selling_proposition, functional_benefits, emotional_benefits, "
        "customer_outcomes, differentiators, value_clarity_score, customer_value_score, confidence_score."
    )

    if HAS_CREWAI and CrewAITask is not None and not (isinstance(agent, dict) and agent.get("mock_mode")):
        kwargs: Dict[str, Any] = {
            "description": description,
            "expected_output": expected_output,
            "agent": agent,
            "output_pydantic": ValuePropositionAnalysis,
        }
        if context:
            kwargs["context"] = context
        return CrewAITask(**kwargs)

    return {
        "task_name": "value_proposition_analysis",
        "description": description,
        "expected_output": expected_output,
        "agent": agent,
        "schema_class": ValuePropositionAnalysis,
        "context": context,
    }


# ============================================================================
# 5. StartupCategoryClassifier Task
# ============================================================================
def create_category_classification_task(
    agent: Any, idea_text: str, context: Optional[List[Any]] = None
) -> Any:
    """Create CrewAI task for classifying startup primary/secondary categories, industry, and models."""
    description = (
        f"Classify the primary and secondary startup categories, industry vertical, technology domains, "
        f"business model, revenue model, startup stage, target market, confidence score, and reasoning "
        f"for proposal: '{idea_text}'. "
        "Return pure JSON matching the StartupCategoryClassification Pydantic schema."
    )
    expected_output = (
        "Valid JSON object matching StartupCategoryClassification schema with fields: "
        "primary_category, secondary_categories, industry, technology_domains, business_model, "
        "revenue_model, startup_stage, target_market, confidence_score, reasoning."
    )

    if HAS_CREWAI and CrewAITask is not None and not (isinstance(agent, dict) and agent.get("mock_mode")):
        kwargs: Dict[str, Any] = {
            "description": description,
            "expected_output": expected_output,
            "agent": agent,
            "output_pydantic": StartupCategoryClassification,
        }
        if context:
            kwargs["context"] = context
        return CrewAITask(**kwargs)

    return {
        "task_name": "category_classification",
        "description": description,
        "expected_output": expected_output,
        "agent": agent,
        "schema_class": StartupCategoryClassification,
        "context": context,
    }


# ============================================================================
# 6. InnovationScoringAgent Task
# ============================================================================
def create_innovation_scoring_task(
    agent: Any, idea_text: str, context: Optional[List[Any]] = None
) -> Any:
    """Create CrewAI task for assessing novelty, technology innovation, and innovation score."""
    description = (
        f"Evaluate the overall innovation score, innovation level, novelty score, technology innovation score, "
        f"business model innovation score, problem originality score, differentiation score, strengths, "
        f"improvement opportunities, reasoning, and confidence score for proposal: '{idea_text}'. "
        "Re-use prior analysis context across idea, value proposition, and classification. "
        "Return pure JSON matching the InnovationScoreAnalysis Pydantic schema."
    )
    expected_output = (
        "Valid JSON object matching InnovationScoreAnalysis schema with fields: "
        "overall_innovation_score, innovation_level, novelty_score, technology_innovation_score, "
        "business_model_innovation_score, problem_originality_score, differentiation_score, "
        "strengths, improvement_opportunities, reasoning, confidence_score."
    )

    if HAS_CREWAI and CrewAITask is not None and not (isinstance(agent, dict) and agent.get("mock_mode")):
        kwargs: Dict[str, Any] = {
            "description": description,
            "expected_output": expected_output,
            "agent": agent,
            "output_pydantic": InnovationScoreAnalysis,
        }
        if context:
            kwargs["context"] = context
        return CrewAITask(**kwargs)

    return {
        "task_name": "innovation_scoring",
        "description": description,
        "expected_output": expected_output,
        "agent": agent,
        "schema_class": InnovationScoreAnalysis,
        "context": context,
    }


# Backward-compatibility function aliases
create_idea_analysis_task = create_startup_idea_analysis_task
create_problem_analysis_task = create_problem_statement_analysis_task
create_value_proposition_task = create_value_proposition_analysis_task
