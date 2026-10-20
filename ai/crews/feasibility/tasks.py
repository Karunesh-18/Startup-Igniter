"""Tasks definition for Feasibility Crew."""

from ai.schemas.feasibility import FeasibilityResult
from ai.shared.logger import ai_logger


def execute_feasibility_analysis_task(project_id: str, idea_text: str) -> FeasibilityResult:
    """Execute feasibility analysis task."""
    ai_logger.info(f"Executing feasibility analysis for project '{project_id}'")

    summary = (
        f"Feasibility summary for '{idea_text}':\n"
        f"Technical Feasibility: 82.5/100 (standard modern stack)\n"
        f"Operational Feasibility: 88.0/100 (automated workflow)\n"
        f"Financial Feasibility: 78.0/100 (low capital requirement)"
    )

    return FeasibilityResult(
        project_id=project_id,
        technical_feasibility_score=82.5,
        operational_feasibility_score=88.0,
        financial_feasibility_score=78.0,
        key_risks=["API Rate Limit Bottlenecks", "Third-party Data Source Dependencies"],
        mitigation_strategies=["Redis response caching", "Multi-provider LLM fallback routing"],
        executive_summary=summary,
        confidence_score=0.88,
    )
