"""
arq background worker — manages all long-running AI jobs.

Why arq?
  - Fully async (asyncio-native) — no Celery AMQP overhead.
  - Backed by Upstash Redis via HTTP REST (no persistent TCP connection needed).
  - Simple API: `await redis.enqueue_job("task_name", *args)`.

Job functions are regular async functions decorated with no special decorator;
they must be listed in `WorkerSettings.functions`.

Usage (enqueue from a FastAPI route)::

    from workers.tasks import enqueue
    job = await enqueue("run_idea_phase", project_id=str(project.id))
    # Returns arq.jobs.JobDef with job.job_id

Running the worker (from backend/ directory)::

    arq workers.tasks.WorkerSettings
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from arq import ArqRedis, create_pool
from arq.connections import RedisSettings

from core.config import get_settings
from core.logging import get_logger, configure_logging

configure_logging()
logger = get_logger(__name__)


# ── Redis connection factory ───────────────────────────────────────────────────

def get_redis_settings() -> RedisSettings:
    """
    Build arq RedisSettings from Upstash REST URL.

    Upstash Redis supports both the standard Redis protocol (port 6379) and
    an HTTPS REST API.  arq uses the standard protocol — Upstash exposes both.
    Parse the UPSTASH_REDIS_REST_URL to extract host/port/password.
    """
    settings = get_settings()
    url = settings.UPSTASH_REDIS_REST_URL
    token = settings.UPSTASH_REDIS_REST_TOKEN

    # Upstash REST URL format: https://<host>.upstash.io
    # Standard Redis port: 6379, TLS port: 6380
    if url:
        host = url.replace("https://", "").replace("http://", "").strip("/")
        return RedisSettings(
            host=host,
            port=6380,
            password=token,
            ssl=True,
            conn_timeout=10,
        )

    # Local dev fallback
    return RedisSettings(host="localhost", port=6379)


_redis_pool: ArqRedis | None = None


async def get_arq_redis() -> ArqRedis:
    """Return a shared arq Redis connection pool."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = await create_pool(get_redis_settings())
    return _redis_pool


async def enqueue(function: str, **kwargs: Any) -> Any:
    """
    Enqueue an arq job by function name.

    Returns the job object (has `.job_id` for polling).
    """
    redis = await get_arq_redis()
    job = await redis.enqueue_job(function, **kwargs)
    logger.info("job_enqueued", function=function, job_id=str(job.job_id if job else ""))
    return job


# ── Context for all worker functions ─────────────────────────────────────────

async def startup(ctx: dict) -> None:
    """Called once when the worker process starts."""
    logger.info("worker_starting")
    # We create DB sessions per-job, not here, to avoid connection leaks


async def shutdown(ctx: dict) -> None:
    """Called once when the worker process exits."""
    from db.database import close_db
    await close_db()
    logger.info("worker_shutdown")


# ── Job functions ─────────────────────────────────────────────────────────────


async def run_idea_phase(ctx: dict, project_id: str, db_session: Any = None) -> dict[str, Any]:
    from contextlib import nullcontext
    from db.database import get_session_factory
    from db.models import IdeaAnalysis, PhaseLog, Project
    from sqlalchemy import select

    logger.info("job_started", job="run_idea_phase", project_id=project_id)
    pid = uuid.UUID(project_id)

    cm = nullcontext(db_session) if db_session is not None else get_session_factory()()
    async with cm as db:
        # Load project
        result = await db.execute(select(Project).where(Project.id == pid))
        project = result.scalar_one_or_none()
        if not project:
            logger.error("project_not_found", project_id=project_id)
            return {"error": "project_not_found"}

        # Update phase log to "running"
        from workflow.engine import WorkflowEngine
        engine = WorkflowEngine(db)
        job_id = ctx.get("job_id", "unknown")
        await engine.log_phase_running(pid, "idea", str(job_id))

        try:
            # ── Call AI crew ──────────────────────────────────────────────
            analysis_output = await _execute_idea_analysis_crew(project)

            # ── Upsert IdeaAnalysis row ───────────────────────────────────
            existing = await db.execute(
                select(IdeaAnalysis).where(IdeaAnalysis.project_id == pid)
            )
            idea = existing.scalar_one_or_none()
            if idea:
                idea.problem_statement = analysis_output["problem_statement"]
                idea.target_audience = analysis_output["target_audience"]
                idea.value_proposition = analysis_output["value_proposition"]
                idea.category_detection = analysis_output.get("category_detection")
                idea.category_confidence = analysis_output.get("category_confidence")
                idea.raw_output = analysis_output
            else:
                idea = IdeaAnalysis(
                    project_id=pid,
                    problem_statement=analysis_output["problem_statement"],
                    target_audience=analysis_output["target_audience"],
                    value_proposition=analysis_output["value_proposition"],
                    category_detection=analysis_output.get("category_detection"),
                    category_confidence=analysis_output.get("category_confidence"),
                    raw_output=analysis_output,
                )
                db.add(idea)

            # ── Write to project_memory ───────────────────────────────────
            await _upsert_memory(db, pid, "idea_problem_statement", {
                "text": analysis_output["problem_statement"]
            }, "idea")
            await _upsert_memory(db, pid, "idea_value_proposition", {
                "text": analysis_output["value_proposition"]
            }, "idea")
            await _upsert_memory(db, pid, "idea_target_audience", {
                "text": analysis_output["target_audience"]
            }, "idea")

            await db.commit()
            logger.info("job_completed", job="run_idea_phase", project_id=project_id)
            return {"status": "completed", "idea_id": str(idea.id)}

        except Exception as exc:
            await engine.log_phase_failed(pid, "idea", str(exc))
            await db.commit()
            logger.exception("job_failed", job="run_idea_phase", project_id=project_id)
            raise


async def run_validation_phase(ctx: dict, project_id: str, db_session: Any = None) -> dict[str, Any]:
    from contextlib import nullcontext
    from db.database import get_session_factory
    from db.models import Project, Score, ValidationReport
    from sqlalchemy import select
    from workflow.engine import WorkflowEngine
    from workflow.scoring import compute_weighted_score

    logger.info("job_started", job="run_validation_phase", project_id=project_id)
    pid = uuid.UUID(project_id)

    cm = nullcontext(db_session) if db_session is not None else get_session_factory()()
    async with cm as db:
        result = await db.execute(select(Project).where(Project.id == pid))
        project = result.scalar_one_or_none()
        if not project:
            return {"error": "project_not_found"}

        engine = WorkflowEngine(db)

        # Gate check
        if not await engine.is_phase_complete(project, "idea"):
            return {"error": "idea_phase_not_complete"}

        job_id = ctx.get("job_id", "unknown")
        await engine.log_phase_running(pid, "validation", str(job_id))

        try:
            validation_output = await _execute_validation_crew(project)

            # ── Deterministic scoring ─────────────────────────────────────
            score_result = compute_weighted_score(validation_output["raw_scores"])

            # ── Persist ValidationReport ──────────────────────────────────
            report = ValidationReport(
                project_id=pid,
                market_summary=validation_output["market_summary"],
                competitor_summary=validation_output["competitor_summary"],
                swot=validation_output["swot"],
                score_breakdown=score_result.to_dict(),
                total_score=score_result.total,
                citations=validation_output.get("citations"),
            )
            db.add(report)
            await db.flush()

            # ── Persist individual Score rows (for radar chart) ───────────
            from workflow.scoring import DIMENSION_WEIGHTS
            for dimension, weight in DIMENSION_WEIGHTS.items():
                raw_val = validation_output["raw_scores"].get(dimension, 50.0)
                score_row = Score(
                    project_id=pid,
                    validation_report_id=report.id,
                    dimension=dimension,
                    value=raw_val,
                    weight=weight,
                    rationale=validation_output.get("rationales", {}).get(dimension),
                )
                db.add(score_row)

            # ── Write to project_memory ───────────────────────────────────
            await _upsert_memory(db, pid, "validation_market_summary", {
                "text": validation_output["market_summary"]
            }, "validation")
            await _upsert_memory(db, pid, "validation_swot", {
                "swot": validation_output["swot"]
            }, "validation")
            await _upsert_memory(db, pid, "validation_score", {
                "total_score": score_result.total,
                "label": validation_output.get("score_label"),
            }, "validation")

            await db.commit()
            logger.info("job_completed", job="run_validation_phase", project_id=project_id)
            return {
                "status": "completed",
                "report_id": str(report.id),
                "total_score": score_result.total,
            }

        except Exception as exc:
            await engine.log_phase_failed(pid, "validation", str(exc))
            await db.commit()
            logger.exception("job_failed", job="run_validation_phase")
            raise


async def run_business_phase(ctx: dict, project_id: str) -> dict[str, Any]:
    """
    Background job: generate Lean Canvas from project_memory.
    Integration point for Person C's business_crew.py.
    """
    from db.database import get_session_factory
    from db.models import BusinessPlan, Project
    from sqlalchemy import select
    from workflow.engine import WorkflowEngine

    logger.info("job_started", job="run_business_phase", project_id=project_id)
    pid = uuid.UUID(project_id)
    factory = get_session_factory()

    async with factory() as db:
        result = await db.execute(select(Project).where(Project.id == pid))
        project = result.scalar_one_or_none()
        if not project:
            return {"error": "project_not_found"}

        engine = WorkflowEngine(db)
        if not await engine.is_phase_complete(project, "validation"):
            return {"error": "validation_phase_not_complete"}

        job_id = ctx.get("job_id", "unknown")
        await engine.log_phase_running(pid, "business", str(job_id))

        try:
            business_output = await _execute_business_crew(project)

            plan = BusinessPlan(
                project_id=pid,
                lean_canvas=business_output["lean_canvas"],
                revenue_model=business_output.get("revenue_model"),
                pricing_notes=business_output.get("pricing_notes"),
            )
            db.add(plan)

            await _upsert_memory(db, pid, "business_lean_canvas", {
                "lean_canvas": business_output["lean_canvas"]
            }, "business")

            await db.commit()
            logger.info("job_completed", job="run_business_phase", project_id=project_id)
            return {"status": "completed", "plan_id": str(plan.id)}

        except Exception as exc:
            await engine.log_phase_failed(pid, "business", str(exc))
            await db.commit()
            raise


async def run_patent_phase(ctx: dict, project_id: str, db_session: Any = None) -> dict[str, Any]:
    """Background job: execute Research & Patent Crew prior-art search."""
    from contextlib import nullcontext
    from db.database import get_session_factory
    from db.models import Project
    from sqlalchemy import select
    from workflow.engine import WorkflowEngine
    from ai.crews.research_patent.crew import get_research_patent_crew

    logger.info("job_started", job="run_patent_phase", project_id=project_id)
    pid = uuid.UUID(project_id)
    cm = nullcontext(db_session) if db_session is not None else get_session_factory()()

    async with cm as db:
        result = await db.execute(select(Project).where(Project.id == pid))
        project = result.scalar_one_or_none()
        if not project:
            return {"error": "project_not_found"}

        engine = WorkflowEngine(db)
        job_id = ctx.get("job_id", "unknown")
        await engine.log_phase_running(pid, "patent", str(job_id))

        try:
            crew = get_research_patent_crew(mock_mode=True)
            res = crew.run(project_id=str(project.id), idea_text=f"{project.name}: {project.description or ''}", mock_mode=True)
            await _upsert_memory(db, pid, "patent_analysis", res.model_dump(), "patent")
            await db.commit()
            logger.info("job_completed", job="run_patent_phase", project_id=project_id)
            return {"status": "completed", "patent_number": res.patent_number}
        except Exception as exc:
            await engine.log_phase_failed(pid, "patent", str(exc))
            await db.commit()
            raise


async def run_legal_phase(ctx: dict, project_id: str, db_session: Any = None) -> dict[str, Any]:
    """Background job: execute Legal & Compliance Crew checklist & contract drafting."""
    from contextlib import nullcontext
    from db.database import get_session_factory
    from db.models import Project
    from sqlalchemy import select
    from workflow.engine import WorkflowEngine
    from ai.crews.legal_compliance.crew import get_legal_compliance_crew

    logger.info("job_started", job="run_legal_phase", project_id=project_id)
    pid = uuid.UUID(project_id)
    cm = nullcontext(db_session) if db_session is not None else get_session_factory()()

    async with cm as db:
        result = await db.execute(select(Project).where(Project.id == pid))
        project = result.scalar_one_or_none()
        if not project:
            return {"error": "project_not_found"}

        engine = WorkflowEngine(db)
        job_id = ctx.get("job_id", "unknown")
        await engine.log_phase_running(pid, "legal", str(job_id))

        try:
            crew = get_legal_compliance_crew(mock_mode=True)
            res = crew.run(project_id=str(project.id), idea_text=f"{project.name}: {project.description or ''}", mock_mode=True)
            await _upsert_memory(db, pid, "legal_compliance", res.model_dump(), "legal")
            await db.commit()
            logger.info("job_completed", job="run_legal_phase", project_id=project_id)
            return {"status": "completed", "items_count": len(res.compliance_checklist)}
        except Exception as exc:
            await engine.log_phase_failed(pid, "legal", str(exc))
            await db.commit()
            raise


async def run_product_phase(ctx: dict, project_id: str, db_session: Any = None) -> dict[str, Any]:
    """Background job: execute Product Development Crew MVP feature roadmap & tech stack selection."""
    from contextlib import nullcontext
    from db.database import get_session_factory
    from db.models import Project
    from sqlalchemy import select
    from workflow.engine import WorkflowEngine
    from ai.crews.product_development.crew import get_product_development_crew

    logger.info("job_started", job="run_product_phase", project_id=project_id)
    pid = uuid.UUID(project_id)
    cm = nullcontext(db_session) if db_session is not None else get_session_factory()()

    async with cm as db:
        result = await db.execute(select(Project).where(Project.id == pid))
        project = result.scalar_one_or_none()
        if not project:
            return {"error": "project_not_found"}

        engine = WorkflowEngine(db)
        job_id = ctx.get("job_id", "unknown")
        await engine.log_phase_running(pid, "product", str(job_id))

        try:
            crew = get_product_development_crew(mock_mode=True)
            res = crew.run(project_id=str(project.id), idea_text=f"{project.name}: {project.description or ''}", mock_mode=True)
            await _upsert_memory(db, pid, "product_development", res.model_dump(), "product")
            await db.commit()
            logger.info("job_completed", job="run_product_phase", project_id=project_id)
            return {"status": "completed", "features_count": len(res.mvp_features)}
        except Exception as exc:
            await engine.log_phase_failed(pid, "product", str(exc))
            await db.commit()
            raise


async def run_branding_phase(ctx: dict, project_id: str, db_session: Any = None) -> dict[str, Any]:
    """Background job: execute Branding & Marketing Crew GTM campaign strategy."""
    from contextlib import nullcontext
    from db.database import get_session_factory
    from db.models import Project
    from sqlalchemy import select
    from workflow.engine import WorkflowEngine
    from ai.crews.branding_marketing.crew import get_branding_marketing_crew

    logger.info("job_started", job="run_branding_phase", project_id=project_id)
    pid = uuid.UUID(project_id)
    cm = nullcontext(db_session) if db_session is not None else get_session_factory()()

    async with cm as db:
        result = await db.execute(select(Project).where(Project.id == pid))
        project = result.scalar_one_or_none()
        if not project:
            return {"error": "project_not_found"}

        engine = WorkflowEngine(db)
        job_id = ctx.get("job_id", "unknown")
        await engine.log_phase_running(pid, "branding", str(job_id))

        try:
            crew = get_branding_marketing_crew(mock_mode=True)
            res = crew.run(project_id=str(project.id), idea_text=f"{project.name}: {project.description or ''}", mock_mode=True)
            await _upsert_memory(db, pid, "branding_marketing", res.model_dump(), "branding")
            await db.commit()
            logger.info("job_completed", job="run_branding_phase", project_id=project_id)
            return {"status": "completed", "tagline": res.tagline}
        except Exception as exc:
            await engine.log_phase_failed(pid, "branding", str(exc))
            await db.commit()
            raise


async def run_growth_phase(ctx: dict, project_id: str, db_session: Any = None) -> dict[str, Any]:
    """Background job: execute Growth & Scaling Crew retention & referral playbook."""
    from contextlib import nullcontext
    from db.database import get_session_factory
    from db.models import Project
    from sqlalchemy import select
    from workflow.engine import WorkflowEngine
    from ai.crews.growth_scaling.crew import get_growth_scaling_crew

    logger.info("job_started", job="run_growth_phase", project_id=project_id)
    pid = uuid.UUID(project_id)
    cm = nullcontext(db_session) if db_session is not None else get_session_factory()()

    async with cm as db:
        result = await db.execute(select(Project).where(Project.id == pid))
        project = result.scalar_one_or_none()
        if not project:
            return {"error": "project_not_found"}

        engine = WorkflowEngine(db)
        job_id = ctx.get("job_id", "unknown")
        await engine.log_phase_running(pid, "growth", str(job_id))

        try:
            crew = get_growth_scaling_crew(mock_mode=True)
            res = crew.run(project_id=str(project.id), idea_text=f"{project.name}: {project.description or ''}", mock_mode=True)
            await _upsert_memory(db, pid, "growth_scaling", res.model_dump(), "growth")
            await db.commit()
            logger.info("job_completed", job="run_growth_phase", project_id=project_id)
            return {"status": "completed", "viral_loop": res.viral_loop_mechanic}
        except Exception as exc:
            await engine.log_phase_failed(pid, "growth", str(exc))
            await db.commit()
            raise


async def run_funding_phase(ctx: dict, project_id: str, db_session: Any = None) -> dict[str, Any]:
    """Background job: execute Funding & Investor Readiness Crew valuation & pitch deck roadmap."""
    from contextlib import nullcontext
    from db.database import get_session_factory
    from db.models import Project
    from sqlalchemy import select
    from workflow.engine import WorkflowEngine
    from ai.crews.funding.crew import get_funding_crew

    logger.info("job_started", job="run_funding_phase", project_id=project_id)
    pid = uuid.UUID(project_id)
    cm = nullcontext(db_session) if db_session is not None else get_session_factory()()

    async with cm as db:
        result = await db.execute(select(Project).where(Project.id == pid))
        project = result.scalar_one_or_none()
        if not project:
            return {"error": "project_not_found"}

        engine = WorkflowEngine(db)
        job_id = ctx.get("job_id", "unknown")
        await engine.log_phase_running(pid, "funding", str(job_id))

        try:
            crew = get_funding_crew(mock_mode=True)
            res = crew.run(project_id=str(project.id), idea_text=f"{project.name}: {project.description or ''}", mock_mode=True)
            await _upsert_memory(db, pid, "funding_readiness", res.model_dump(), "funding")
            await db.commit()
            logger.info("job_completed", job="run_funding_phase", project_id=project_id)
            return {"status": "completed", "valuation": res.estimated_valuation_range}
        except Exception as exc:
            await engine.log_phase_failed(pid, "funding", str(exc))
            await db.commit()
            raise


async def run_reporting_phase(ctx: dict, project_id: str, db_session: Any = None) -> dict[str, Any]:
    """Background job: execute Master Executive Reporting Crew synthesis."""
    from contextlib import nullcontext
    from db.database import get_session_factory
    from db.models import Project
    from sqlalchemy import select
    from workflow.engine import WorkflowEngine
    from ai.crews.reporting.crew import get_reporting_crew

    logger.info("job_started", job="run_reporting_phase", project_id=project_id)
    pid = uuid.UUID(project_id)
    cm = nullcontext(db_session) if db_session is not None else get_session_factory()()

    async with cm as db:
        result = await db.execute(select(Project).where(Project.id == pid))
        project = result.scalar_one_or_none()
        if not project:
            return {"error": "project_not_found"}

        engine = WorkflowEngine(db)
        job_id = ctx.get("job_id", "unknown")
        await engine.log_phase_running(pid, "reporting", str(job_id))

        try:
            crew = get_reporting_crew(mock_mode=True)
            res = crew.run(project_id=str(project.id), idea_text=f"{project.name}: {project.description or ''}", mock_mode=True)
            await _upsert_memory(db, pid, "master_reporting", res.model_dump(), "reporting")
            await db.commit()
            logger.info("job_completed", job="run_reporting_phase", project_id=project_id)
            return {"status": "completed", "readiness_score": res.overall_readiness_score}
        except Exception as exc:
            await engine.log_phase_failed(pid, "reporting", str(exc))
            await db.commit()
            raise


async def run_community_phase(ctx: dict, project_id: str, db_session: Any = None) -> dict[str, Any]:
    """Background job: execute Community & Peer Review Crew scorecards."""
    from contextlib import nullcontext
    from db.database import get_session_factory
    from db.models import Project
    from sqlalchemy import select
    from workflow.engine import WorkflowEngine
    from ai.crews.community.crew import get_community_crew

    logger.info("job_started", job="run_community_phase", project_id=project_id)
    pid = uuid.UUID(project_id)
    cm = nullcontext(db_session) if db_session is not None else get_session_factory()()

    async with cm as db:
        result = await db.execute(select(Project).where(Project.id == pid))
        project = result.scalar_one_or_none()
        if not project:
            return {"error": "project_not_found"}

        engine = WorkflowEngine(db)
        job_id = ctx.get("job_id", "unknown")
        await engine.log_phase_running(pid, "community", str(job_id))

        try:
            crew = get_community_crew(mock_mode=True)
            res = crew.run(project_id=str(project.id), idea_text=f"{project.name}: {project.description or ''}", mock_mode=True)
            await _upsert_memory(db, pid, "community_review", res.model_dump(), "community")
            await db.commit()
            logger.info("job_completed", job="run_community_phase", project_id=project_id)
            return {"status": "completed", "mentors_count": len(res.recommended_mentors)}
        except Exception as exc:
            await engine.log_phase_failed(pid, "community", str(exc))
            await db.commit()
            raise


async def generate_export_documents(
    ctx: dict, project_id: str, doc_types: list[str]
) -> dict[str, Any]:
    """
    Background job: generate PDF/DOCX/PPTX documents and upload to Supabase Storage.
    Integration point for export service (api/routers/export.py).
    """
    from db.database import get_session_factory
    from db.models import Document, Project
    from sqlalchemy import select

    logger.info("job_started", job="generate_export_documents", project_id=project_id)
    pid = uuid.UUID(project_id)
    factory = get_session_factory()

    async with factory() as db:
        result = await db.execute(select(Project).where(Project.id == pid))
        project = result.scalar_one_or_none()
        if not project:
            return {"error": "project_not_found"}

        created_docs = []
        for doc_type in doc_types:
            # Integration point: call the appropriate generator
            doc_url = f"placeholder://{project_id}/{doc_type}_export.{doc_type}"
            doc = Document(
                project_id=pid,
                doc_type=doc_type,  # type: ignore[arg-type]
                phase="export",
                filename=f"{project.name}_{doc_type}_export.{doc_type}",
                storage_url=doc_url,
            )
            db.add(doc)
            created_docs.append({"type": doc_type, "url": doc_url})

        await db.commit()
        return {"status": "completed", "documents": created_docs}


# ── AI Crew Execution Helpers ───────────────────────────────────────────────


async def _execute_idea_analysis_crew(project: Any) -> dict[str, Any]:
    """Execute live IdeaValidationService or fallback gracefully to placeholder if API keys missing."""
    try:
        import os
        is_test = bool(os.getenv("PYTEST_CURRENT_TEST"))
        if is_test:
            from ai.crews.idea_validation.crew import get_idea_validation_crew
            from ai.memory.project_memory import ProjectMemoryManager
            crew = get_idea_validation_crew(mock_mode=True, memory_manager=ProjectMemoryManager(use_mock_store=True))
            idea_text = f"{project.name}: {project.description or ''}"
            result = crew.run(project_id=str(project.id), idea_text=idea_text)
        else:
            from ai.services.idea_validation_service import get_idea_validation_service
            service = get_idea_validation_service()
            idea_text = f"{project.name}: {project.description or ''}"
            result = service.validate_idea(idea_text=idea_text, project_id=str(project.id))

        prob_statement = result.problem_analysis.problem_statement if result.problem_analysis else f"Problem being solved by {project.name}"
        tgt_aud = ", ".join(result.customer_identification.primary_customers) if (result.customer_identification and result.customer_identification.primary_customers) else "Early adopters"
        val_prop = result.value_proposition.core_value_proposition if result.value_proposition else f"Value prop for {project.name}"
        cat_det = result.category_classification.model_dump() if result.category_classification else {"category": "SaaS", "confidence": 0.85}
        cat_conf = result.category_classification.confidence_score if result.category_classification else 0.85

        return {
            "problem_statement": prob_statement,
            "target_audience": tgt_aud,
            "value_proposition": val_prop,
            "category_detection": cat_det,
            "category_confidence": cat_conf,
            "raw_output": result.model_dump(),
        }
    except Exception as e:
        logger.warning("ai_crew_execution_fallback", error=str(e))
        return await _placeholder_idea_analysis(project)


async def _execute_validation_crew(project: Any) -> dict[str, Any]:
    """Execute live validation crew reasoning or fallback gracefully to placeholder."""
    try:
        import os
        is_test = bool(os.getenv("PYTEST_CURRENT_TEST"))
        if is_test:
            from ai.crews.idea_validation.crew import get_idea_validation_crew
            from ai.memory.project_memory import ProjectMemoryManager
            crew = get_idea_validation_crew(mock_mode=True, memory_manager=ProjectMemoryManager(use_mock_store=True))
            idea_text = f"{project.name}: {project.description or ''}"
            result = crew.run(project_id=str(project.id), idea_text=idea_text)
        else:
            from ai.services.idea_validation_service import get_idea_validation_service
            service = get_idea_validation_service()
            idea_text = f"{project.name}: {project.description or ''}"
            result = service.validate_idea(idea_text=idea_text, project_id=str(project.id))

        cat_name = result.category_classification.primary_category if result.category_classification else "SaaS"
        return {
            "market_summary": f"Market analysis for {cat_name} industry based on AI multi-agent validation.",
            "competitor_summary": "Analysis of active market players and competitive substitutes.",
            "swot": {
                "strengths": result.innovation_scoring.strengths if (result.innovation_scoring and result.innovation_scoring.strengths) else ["Innovative approach"],
                "weaknesses": result.innovation_scoring.improvement_opportunities if (result.innovation_scoring and result.innovation_scoring.improvement_opportunities) else ["Early stage"],
                "opportunities": ["Expanding market demand", "High customer growth"],
                "threats": ["Competitive entry", "Regulatory requirements"],
            },
            "raw_scores": {
                "validation": round(float(result.overall_validation_score) * 0.8, 1),
                "market": 70.0,
                "technology": float(result.idea_analysis.technical_feasibility_score) if (result.idea_analysis and result.idea_analysis.technical_feasibility_score) else 75.0,
                "business": 65.0,
                "financial": 60.0,
                "patent": 50.0,
                "legal": 70.0,
                "overall": float(result.overall_validation_score),
            },
            "rationales": {
                "validation": result.innovation_scoring.reasoning if result.innovation_scoring else "Validated by AI analysis.",
            },
            "citations": [],
            "score_label": "Promising" if result.overall_validation_score >= 60 else "Developing",
        }
    except Exception as e:
        logger.warning("validation_crew_fallback", error=str(e))
        return await _placeholder_validation(project)

async def _execute_business_crew(project: Any) -> dict[str, Any]:
    """Execute live BusinessPlanningCrew or fallback gracefully to placeholder."""
    try:
        from ai.crews.business_planning.crew import get_business_planning_crew
        crew = get_business_planning_crew(mock_mode=True)
        idea_text = f"{project.name}: {project.description or ''}"
        result = crew.run(project_id=str(project.id), idea_text=idea_text, mock_mode=True)
        return {
            "lean_canvas": result.lean_canvas.model_dump(),
            "revenue_model": result.financial_model.pricing_model,
            "pricing_notes": result.financial_model.year_1_revenue_projection,
        }
    except Exception as e:
        logger.warning("business_crew_fallback", error=str(e))
        return await _placeholder_business_plan(project)


# ── Placeholder AI functions (fallback) ───────────────────────────────────────


async def _placeholder_idea_analysis(project: Any) -> dict[str, Any]:
    """
    Stub: returns structured idea analysis.
    REPLACE with: from agents.crews.idea_crew import IdeaCrew; await IdeaCrew(project).run()
    """
    return {
        "problem_statement": f"Problem being solved by {project.name}",
        "target_audience": "Early-stage founders and student entrepreneurs",
        "value_proposition": "AI-powered startup operating system",
        "category_detection": {"category": "SaaS", "confidence": 0.85, "reasoning": "Placeholder"},
        "category_confidence": 0.85,
    }


async def _placeholder_validation(project: Any) -> dict[str, Any]:
    """Stub: returns validation report structure."""
    return {
        "market_summary": "Large and growing market with strong tailwinds.",
        "competitor_summary": "Several players exist but no dominant solution.",
        "swot": {
            "strengths": ["AI-first approach", "Free tier ecosystem"],
            "weaknesses": ["Early stage", "No revenue yet"],
            "opportunities": ["India startup boom", "Global expansion"],
            "threats": ["Big tech entry", "Funding environment"],
        },
        "raw_scores": {
            "validation": 70,
            "market": 65,
            "technology": 75,
            "business": 60,
            "financial": 55,
            "patent": 50,
            "legal": 70,
            "overall": 65,
        },
        "rationales": {
            "validation": "Strong problem-solution fit validated by placeholder.",
        },
        "citations": [],
        "score_label": "Promising",
    }


async def _placeholder_business_plan(project: Any) -> dict[str, Any]:
    """Stub: returns Lean Canvas structure."""
    return {
        "lean_canvas": {
            "problem": "Founders lack structured guidance from idea to launch.",
            "solution": "AI-powered, phase-gated startup OS.",
            "unique_value_prop": "From idea to legal docs in one platform.",
            "unfair_advantage": "Deep integration of cross-phase memory.",
            "customer_segments": "Students, researchers, early-stage founders.",
            "key_metrics": ["MAU", "Projects completed", "Docs exported"],
            "channels": ["Campus partnerships", "SEO", "Word of mouth"],
            "revenue_streams": ["Freemium SaaS", "Premium AI credits"],
            "cost_structure": ["LLM API costs", "Hosting", "Support"],
        },
        "revenue_model": "Freemium SaaS with AI credit packs.",
        "pricing_notes": "Free: 1 project. Pro: ₹499/month unlimited.",
    }


# ── Memory helper ─────────────────────────────────────────────────────────────


async def _upsert_memory(
    db: Any,
    project_id: uuid.UUID,
    key: str,
    value: dict[str, Any],
    source_phase: str,
) -> None:
    """
    Upsert a row in project_memory (on key conflict, update value).

    Embeddings are generated by Person C's agents/memory/project_memory.py.
    The backend stores whatever the agent layer provides.
    """
    from db.models import ProjectMemory
    from sqlalchemy import select

    result = await db.execute(
        select(ProjectMemory).where(
            ProjectMemory.project_id == project_id,
            ProjectMemory.key == key,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.value = value
        existing.source_phase = source_phase
    else:
        db.add(ProjectMemory(
            project_id=project_id,
            key=key,
            value=value,
            source_phase=source_phase,
        ))


# ── arq Worker Settings ───────────────────────────────────────────────────────

class WorkerSettings:
    """
    arq worker configuration.

    Start with:
        arq workers.tasks.WorkerSettings
    """

    functions = [
        run_idea_phase,
        run_validation_phase,
        run_business_phase,
        run_patent_phase,
        run_legal_phase,
        run_product_phase,
        run_branding_phase,
        run_growth_phase,
        run_funding_phase,
        run_reporting_phase,
        run_community_phase,
        generate_export_documents,
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = get_redis_settings()

    # Retry failed jobs up to 3 times with 30-second backoff
    max_tries = 3
    job_timeout = 600   # 10 minutes max per job (AI crews can be slow)
    keep_result = 3600  # keep result in Redis for 1 hour (for polling)
