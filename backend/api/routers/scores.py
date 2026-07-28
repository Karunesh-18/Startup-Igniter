"""
Scores router — multi-dimensional readiness scores for the radar chart.

Endpoints:
  GET /scores/{project_id}          Latest scores across all dimensions
  GET /scores/{project_id}/history  Score history for trend visualization
"""

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from api.deps import DB, OwnedProject
from db.models import Score, ValidationReport
from workflow.scoring import DIMENSION_WEIGHTS, score_label

router = APIRouter(prefix="/scores", tags=["Scores"])


# ── Schemas ───────────────────────────────────────────────────────────────────


class ScorePoint(BaseModel):
    """Single dimension score point for the radar chart."""
    dimension: str
    value: float
    weight: float
    weighted_contribution: float
    rationale: str | None


class RadarChartData(BaseModel):
    """
    Payload ready for recharts/chart.js RadarChart consumption.

    `data` is formatted as [{dimension: "market", value: 65, ...}, ...]
    """
    project_id: str
    total_score: float
    score_label: str
    report_id: str
    data: list[ScorePoint]
    ai_generated: bool = True


class ScoreHistoryEntry(BaseModel):
    report_id: str
    total_score: float
    score_label: str
    created_at: str


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get(
    "/{project_id}",
    response_model=RadarChartData,
    summary="Get latest readiness scores for radar chart",
)
async def get_scores(project: OwnedProject, db: DB) -> RadarChartData:
    """
    Return the most recent validation report's scores, formatted for the
    frontend radar chart.

    ⚠️ Guardrail: `ai_generated: true` — frontend must display:
       "AI-generated scores — for informational purposes only."
    """
    # Latest validation report
    report_result = await db.execute(
        select(ValidationReport)
        .where(ValidationReport.project_id == project.id)
        .order_by(ValidationReport.created_at.desc())
    )
    report = report_result.scalars().first()
    if not report:
        raise HTTPException(
            status_code=404,
            detail="No validation report found. Run the validation phase first.",
        )

    # Scores for this report
    scores_result = await db.execute(
        select(Score).where(Score.validation_report_id == report.id)
    )
    scores = list(scores_result.scalars().all())

    if not scores:
        raise HTTPException(
            status_code=404,
            detail="Scores not yet computed for this report.",
        )

    data = [
        ScorePoint(
            dimension=s.dimension,
            value=s.value,
            weight=s.weight,
            weighted_contribution=round(s.value * s.weight, 4),
            rationale=s.rationale,
        )
        for s in scores
    ]

    total = report.total_score or 0.0
    return RadarChartData(
        project_id=str(project.id),
        total_score=total,
        score_label=score_label(total),
        report_id=str(report.id),
        data=data,
    )


@router.get(
    "/{project_id}/history",
    response_model=list[ScoreHistoryEntry],
    summary="Get score history for trend visualization",
)
async def get_score_history(project: OwnedProject, db: DB) -> list[ScoreHistoryEntry]:
    """Return all historical validation scores for this project, newest first."""
    result = await db.execute(
        select(ValidationReport)
        .where(
            ValidationReport.project_id == project.id,
            ValidationReport.total_score.isnot(None),
        )
        .order_by(ValidationReport.created_at.desc())
    )
    reports = list(result.scalars().all())

    return [
        ScoreHistoryEntry(
            report_id=str(r.id),
            total_score=r.total_score,
            score_label=score_label(r.total_score or 0),
            created_at=r.created_at.isoformat(),
        )
        for r in reports
    ]
