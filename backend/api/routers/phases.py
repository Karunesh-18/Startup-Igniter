"""
Phases router — triggers AI analysis jobs and returns phase output.

Endpoints:
  POST /phases/{project_id}/idea          Trigger idea analysis job
  GET  /phases/{project_id}/idea          Get idea analysis result
  PATCH /phases/{project_id}/idea         User edits idea analysis before saving

  POST /phases/{project_id}/validation    Trigger validation + scoring job
  GET  /phases/{project_id}/validation    Get latest validation report + scores

  POST /phases/{project_id}/business      Trigger Lean Canvas generation
  GET  /phases/{project_id}/business      Get latest business plan

  GET  /phases/{project_id}/job/{job_id}  Poll job status

Rate limiting:
  POST endpoints check project.ai_calls_used < project.ai_calls_budget.
  If budget is exceeded, return 429.

Guardrails (enforced here, displayed by frontend):
  - Every response includes `"ai_generated": true` in the top-level payload.
  - The frontend must display: "AI-generated — verify independently."
"""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import DB, CurrentUser, EditableProject, OwnedProject
from db.models import (
    BusinessPlan,
    IdeaAnalysis,
    Project,
    RiskAssessment,
    Score,
    ValidationReport,
)
from workers.tasks import enqueue

router = APIRouter(prefix="/phases", tags=["Phases"])


# ── Schemas ───────────────────────────────────────────────────────────────────


class JobResponse(BaseModel):
    """Returned when an async AI job is enqueued."""
    job_id: str
    status: str = "queued"
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: dict[str, Any] | None = None


class IdeaAnalysisResponse(BaseModel):
    id: str
    project_id: str
    problem_statement: str | None
    target_audience: str | None
    value_proposition: str | None
    category_detection: dict[str, Any] | None
    category_confidence: float | None
    user_edited: bool
    created_at: str
    ai_generated: bool = True  # ← Guardrail flag


class IdeaEditRequest(BaseModel):
    """User-edited overrides for idea analysis fields."""
    problem_statement: str | None = None
    target_audience: str | None = None
    value_proposition: str | None = None


class ScoreDimension(BaseModel):
    dimension: str
    value: float
    weight: float
    rationale: str | None


class ValidationReportResponse(BaseModel):
    id: str
    project_id: str
    market_summary: str | None
    competitor_summary: str | None
    swot: dict[str, Any] | None
    total_score: float | None
    score_breakdown: dict[str, Any] | None
    scores: list[ScoreDimension]
    citations: dict[str, Any] | None
    ai_generated: bool = True
    created_at: str


class RiskItem(BaseModel):
    id: str
    risk_type: str
    severity: str
    description: str
    mitigation: str | None


class LeanCanvasResponse(BaseModel):
    id: str
    project_id: str
    lean_canvas: dict[str, Any]
    revenue_model: str | None
    pricing_notes: str | None
    user_edited: bool
    ai_generated: bool = True
    created_at: str


class LeanCanvasEditRequest(BaseModel):
    lean_canvas: dict[str, Any] | None = None
    revenue_model: str | None = None
    pricing_notes: str | None = None


# ── Budget check helper ───────────────────────────────────────────────────────

async def _check_and_increment_budget(project: Project, db: AsyncSession) -> None:
    """
    Raise 429 if the project has exhausted its AI call budget.
    Otherwise, increment the counter.
    """
    if project.ai_calls_used >= project.ai_calls_budget:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"AI call budget exhausted: {project.ai_calls_used}/{project.ai_calls_budget} calls used. "
                "Contact support to increase your budget."
            ),
        )
    project.ai_calls_used += 1  # type: ignore[assignment]
    db.add(project)
    await db.flush()


# ── Job polling ───────────────────────────────────────────────────────────────


@router.get(
    "/{project_id}/job/{job_id}",
    response_model=JobStatusResponse,
    summary="Poll async job status",
)
async def poll_job_status(
    project_id: uuid.UUID,
    job_id: str,
    project: OwnedProject,
) -> JobStatusResponse:
    """
    Check the status of an enqueued AI job.

    arq stores job results in Redis for `keep_result` seconds (default: 1 hour).
    Frontend should poll every 3-5 seconds until status is 'complete' or 'failed'.
    """
    try:
        from workers.tasks import get_arq_redis
        redis = await get_arq_redis()
        job = await redis.job_result(job_id)
        if job is None:
            return JobStatusResponse(job_id=job_id, status="queued")
        return JobStatusResponse(
            job_id=job_id,
            status="complete",
            result={"output": str(job)},
        )
    except Exception:
        return JobStatusResponse(job_id=job_id, status="unknown")


# ── Idea Phase ────────────────────────────────────────────────────────────────


@router.post(
    "/{project_id}/idea",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger idea analysis AI job",
)
async def trigger_idea_phase(
    project: EditableProject,
    db: DB,
) -> JobResponse:
    """
    Enqueue the idea analysis crew for this project.

    The job is processed asynchronously by the arq worker.
    Poll `GET /phases/{project_id}/job/{job_id}` for completion.

    Rate-limited: checks AI call budget before enqueueing.
    """
    await _check_and_increment_budget(project, db)
    await db.commit()

    job = await enqueue("run_idea_phase", project_id=str(project.id))
    job_id = str(job.job_id) if job else "local"

    return JobResponse(
        job_id=job_id,
        status="queued",
        message="Idea analysis started. Poll /phases/{project_id}/job/{job_id} for results.",
    )


@router.get(
    "/{project_id}/idea",
    response_model=IdeaAnalysisResponse,
    summary="Get idea analysis result",
)
async def get_idea_analysis(project: OwnedProject, db: DB) -> IdeaAnalysisResponse:
    """Return the latest idea analysis result for this project."""
    result = await db.execute(
        select(IdeaAnalysis).where(IdeaAnalysis.project_id == project.id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea analysis not found. Trigger the idea phase first.",
        )
    return IdeaAnalysisResponse(
        id=str(analysis.id),
        project_id=str(analysis.project_id),
        problem_statement=analysis.problem_statement,
        target_audience=analysis.target_audience,
        value_proposition=analysis.value_proposition,
        category_detection=analysis.category_detection,
        category_confidence=analysis.category_confidence,
        user_edited=analysis.user_edited,
        created_at=analysis.created_at.isoformat(),
    )


@router.patch(
    "/{project_id}/idea",
    response_model=IdeaAnalysisResponse,
    summary="Save user-edited idea analysis",
)
async def edit_idea_analysis(
    body: IdeaEditRequest,
    project: EditableProject,
    db: DB,
) -> IdeaAnalysisResponse:
    """
    Allow the user to edit AI-generated idea analysis before it propagates
    to project_memory and subsequent phases.

    Guardrail: sets `user_edited=True` so the system knows this was human-modified.
    """
    result = await db.execute(
        select(IdeaAnalysis).where(IdeaAnalysis.project_id == project.id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Run idea analysis first.")

    if body.problem_statement is not None:
        analysis.problem_statement = body.problem_statement  # type: ignore
    if body.target_audience is not None:
        analysis.target_audience = body.target_audience  # type: ignore
    if body.value_proposition is not None:
        analysis.value_proposition = body.value_proposition  # type: ignore

    analysis.user_edited = True  # type: ignore[assignment]
    db.add(analysis)

    # Update project_memory with edited values
    from workers.tasks import _upsert_memory
    if body.problem_statement:
        await _upsert_memory(db, project.id, "idea_problem_statement",
                             {"text": body.problem_statement}, "idea")
    if body.value_proposition:
        await _upsert_memory(db, project.id, "idea_value_proposition",
                             {"text": body.value_proposition}, "idea")
    if body.target_audience:
        await _upsert_memory(db, project.id, "idea_target_audience",
                             {"text": body.target_audience}, "idea")

    await db.commit()
    await db.refresh(analysis)

    return IdeaAnalysisResponse(
        id=str(analysis.id),
        project_id=str(analysis.project_id),
        problem_statement=analysis.problem_statement,
        target_audience=analysis.target_audience,
        value_proposition=analysis.value_proposition,
        category_detection=analysis.category_detection,
        category_confidence=analysis.category_confidence,
        user_edited=analysis.user_edited,
        created_at=analysis.created_at.isoformat(),
    )


# ── Validation Phase ──────────────────────────────────────────────────────────


@router.post(
    "/{project_id}/validation",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger validation + scoring job",
)
async def trigger_validation_phase(
    project: EditableProject,
    db: DB,
) -> JobResponse:
    """
    Enqueue the market research, competitor analysis, SWOT, and scoring crew.

    Requires: idea phase must be complete.
    """
    from workflow.engine import WorkflowEngine
    engine = WorkflowEngine(db)
    if not await engine.is_phase_complete(project, "idea"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complete the idea phase before running validation.",
        )

    await _check_and_increment_budget(project, db)
    await db.commit()

    job = await enqueue("run_validation_phase", project_id=str(project.id))
    job_id = str(job.job_id) if job else "local"

    return JobResponse(
        job_id=job_id,
        status="queued",
        message="Validation analysis started. Poll for results.",
    )


@router.get(
    "/{project_id}/validation",
    response_model=ValidationReportResponse,
    summary="Get latest validation report",
)
async def get_validation_report(project: OwnedProject, db: DB) -> ValidationReportResponse:
    """
    Return the most recent validation report with scores.

    ⚠️ Guardrail: `ai_generated: true` — frontend must display disclaimer.
    """
    result = await db.execute(
        select(ValidationReport)
        .where(ValidationReport.project_id == project.id)
        .order_by(ValidationReport.created_at.desc())
    )
    report = result.scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="No validation report found. Run validation first.")

    # Load scores
    scores_result = await db.execute(
        select(Score).where(Score.validation_report_id == report.id)
    )
    scores = list(scores_result.scalars().all())

    return ValidationReportResponse(
        id=str(report.id),
        project_id=str(report.project_id),
        market_summary=report.market_summary,
        competitor_summary=report.competitor_summary,
        swot=report.swot,
        total_score=report.total_score,
        score_breakdown=report.score_breakdown,
        scores=[
            ScoreDimension(
                dimension=s.dimension,
                value=s.value,
                weight=s.weight,
                rationale=s.rationale,
            )
            for s in scores
        ],
        citations=report.citations,
        created_at=report.created_at.isoformat(),
    )


@router.get(
    "/{project_id}/risks",
    response_model=list[RiskItem],
    summary="Get risk assessment items",
)
async def get_risks(project: OwnedProject, db: DB) -> list[RiskItem]:
    """Return all risk assessment items for this project."""
    result = await db.execute(
        select(RiskAssessment)
        .where(RiskAssessment.project_id == project.id)
        .order_by(RiskAssessment.created_at.desc())
    )
    risks = list(result.scalars().all())
    return [
        RiskItem(
            id=str(r.id),
            risk_type=r.risk_type,
            severity=r.severity,
            description=r.description,
            mitigation=r.mitigation,
        )
        for r in risks
    ]


# ── Business Phase ────────────────────────────────────────────────────────────


@router.post(
    "/{project_id}/business",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger Lean Canvas generation",
)
async def trigger_business_phase(
    project: EditableProject,
    db: DB,
) -> JobResponse:
    """
    Enqueue the business planning crew to generate a Lean Canvas from memory.

    Requires: validation phase must be complete.
    """
    from workflow.engine import WorkflowEngine
    engine = WorkflowEngine(db)
    if not await engine.is_phase_complete(project, "validation"):
        raise HTTPException(
            status_code=400,
            detail="Complete the validation phase before generating a business plan.",
        )

    await _check_and_increment_budget(project, db)
    await db.commit()

    job = await enqueue("run_business_phase", project_id=str(project.id))
    job_id = str(job.job_id) if job else "local"

    return JobResponse(
        job_id=job_id,
        status="queued",
        message="Business plan generation started.",
    )


@router.get(
    "/{project_id}/business",
    response_model=LeanCanvasResponse,
    summary="Get latest business plan",
)
async def get_business_plan(project: OwnedProject, db: DB) -> LeanCanvasResponse:
    """Return the latest Lean Canvas for this project."""
    result = await db.execute(
        select(BusinessPlan)
        .where(BusinessPlan.project_id == project.id)
        .order_by(BusinessPlan.created_at.desc())
    )
    plan = result.scalars().first()
    if not plan:
        raise HTTPException(status_code=404, detail="No business plan found. Run business phase first.")

    return LeanCanvasResponse(
        id=str(plan.id),
        project_id=str(plan.project_id),
        lean_canvas=plan.lean_canvas,
        revenue_model=plan.revenue_model,
        pricing_notes=plan.pricing_notes,
        user_edited=plan.user_edited,
        created_at=plan.created_at.isoformat(),
    )


@router.patch(
    "/{project_id}/business",
    response_model=LeanCanvasResponse,
    summary="Save user-edited Lean Canvas",
)
async def edit_business_plan(
    body: LeanCanvasEditRequest,
    project: EditableProject,
    db: DB,
) -> LeanCanvasResponse:
    """Allow user to edit the AI-generated Lean Canvas before locking it in."""
    result = await db.execute(
        select(BusinessPlan).where(BusinessPlan.project_id == project.id)
        .order_by(BusinessPlan.created_at.desc())
    )
    plan = result.scalars().first()
    if not plan:
        raise HTTPException(status_code=404, detail="Run business phase first.")

    if body.lean_canvas is not None:
        plan.lean_canvas = body.lean_canvas  # type: ignore
    if body.revenue_model is not None:
        plan.revenue_model = body.revenue_model  # type: ignore
    if body.pricing_notes is not None:
        plan.pricing_notes = body.pricing_notes  # type: ignore

    plan.user_edited = True  # type: ignore[assignment]
    db.add(plan)
    await db.commit()
    await db.refresh(plan)

    return LeanCanvasResponse(
        id=str(plan.id),
        project_id=str(plan.project_id),
        lean_canvas=plan.lean_canvas,
        revenue_model=plan.revenue_model,
        pricing_notes=plan.pricing_notes,
        user_edited=plan.user_edited,
        created_at=plan.created_at.isoformat(),
    )
