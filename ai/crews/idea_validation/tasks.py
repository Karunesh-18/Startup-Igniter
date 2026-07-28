"""Task definitions for Idea Validation Crew."""

from typing import Any, Dict, Optional

try:
    from crewai import Task as CrewAITask  # type: ignore
    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False
    CrewAITask = None


def create_category_classification_task(agent: Any, idea_text: str) -> Any:
    """Create task for categorizing startup idea."""
    description = f"Classify the following startup idea into standard system categories: '{idea_text}'."
    expected_output = "Structured JSON containing predicted_category, confidence score, and rationale."

    if HAS_CREWAI and CrewAITask is not None and not (isinstance(agent, dict) and agent.get("mock_mode")):
        return CrewAITask(
            description=description,
            expected_output=expected_output,
            agent=agent,
        )
    return {
        "task_name": "category_classification",
        "description": description,
        "expected_output": expected_output,
        "agent": agent,
    }


def create_idea_analysis_task(agent: Any, idea_text: str) -> Any:
    """Create task for holistic startup idea architectural analysis."""
    description = f"Analyze the core concepts, operational pillars, and feasibility of the startup idea: '{idea_text}'."
    expected_output = "Structured JSON containing summary, operational pillars, technical_feasibility_score, and key assumptions."

    if HAS_CREWAI and CrewAITask is not None and not (isinstance(agent, dict) and agent.get("mock_mode")):
        return CrewAITask(
            description=description,
            expected_output=expected_output,
            agent=agent,
        )
    return {
        "task_name": "idea_analysis",
        "description": description,
        "expected_output": expected_output,
        "agent": agent,
    }


def create_problem_analysis_task(agent: Any, idea_text: str) -> Any:
    """Create task for problem statement deconstruction and urgency evaluation."""
    description = f"Deconstruct problem severity, frequency, workarounds, and urgency for startup idea: '{idea_text}'."
    expected_output = "Structured JSON containing core_problem, severity, frequency, workarounds, and urgency_score."

    if HAS_CREWAI and CrewAITask is not None and not (isinstance(agent, dict) and agent.get("mock_mode")):
        return CrewAITask(
            description=description,
            expected_output=expected_output,
            agent=agent,
        )
    return {
        "task_name": "problem_analysis",
        "description": description,
        "expected_output": expected_output,
        "agent": agent,
    }


def create_customer_identification_task(agent: Any, idea_text: str) -> Any:
    """Create task for customer persona and ICP identification."""
    description = f"Identify primary ICP, secondary personas, buyer vs user dynamics, and channels for startup idea: '{idea_text}'."
    expected_output = "Structured JSON containing primary_icp, secondary_personas, willingness_to_pay, and channels."

    if HAS_CREWAI and CrewAITask is not None and not (isinstance(agent, dict) and agent.get("mock_mode")):
        return CrewAITask(
            description=description,
            expected_output=expected_output,
            agent=agent,
        )
    return {
        "task_name": "customer_identification",
        "description": description,
        "expected_output": expected_output,
        "agent": agent,
    }


def create_value_proposition_task(agent: Any, idea_text: str) -> Any:
    """Create task for UVP formulation and moat assessment."""
    description = f"Formulate unique value proposition, quantifiable ROI benefits, and competitive moats for startup idea: '{idea_text}'."
    expected_output = "Structured JSON containing unique_value_prop, quantifiable_benefits, moats, and strength_score."

    if HAS_CREWAI and CrewAITask is not None and not (isinstance(agent, dict) and agent.get("mock_mode")):
        return CrewAITask(
            description=description,
            expected_output=expected_output,
            agent=agent,
        )
    return {
        "task_name": "value_proposition",
        "description": description,
        "expected_output": expected_output,
        "agent": agent,
    }
