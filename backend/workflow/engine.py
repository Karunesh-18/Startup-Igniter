"""
Workflow Engine — phase gating logic for Startup OS projects.

Responsibilities:
1. Determine the current phase of a project.
2. Check whether a phase is complete (has the required output rows).
3. Advance a project to the next phase in its category's workflow.
4. Gate API access: raise an error if a caller tries to run a phase
   that is not yet unlocked.

Design goals:
- Simple: no external state-machine library — a JSON array in
  `startup_categories.workflow` is enough for v1.
- Deterministic: phase completion is decided by checking that specific
  output rows exist in the DB, not by trusting client state.
- Auditable: every transition is written to `phase_log`.

Phase completion criteria:
  idea       → idea_analysis row exists AND problem_statement is not null
  validation → validation_reports row exists AND total_score is not null
  patent     → patent_research_reports row exists for this project
  business   → business_plans row exists AND lean_canvas is not null
  legal      → legal_checklists row exists for this project
  export     → documents row exists for this project (any doc type)

Usage::

    engine = WorkflowEngine(db)
    status = await engine.get_phase_status(project)
    await engine.advance_phase(project)
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from core.logging import get_logger
from db.models import (
    BusinessPlan,
    Document,
    IdeaAnalysis,
    LegalChecklist,
    PatentResearchReport,
    PhaseLog,
    Project,
    StartupCategory,
    ValidationReport,
)

logger = get_logger(__name__)

# ── Ordered list of all possible phases ───────────────────────────────────────
ALL_PHASES: list[str] = ["idea", "validation", "patent", "business", "legal", "export"]

# ── Default workflow (used when no category is assigned) ──────────────────────
DEFAULT_WORKFLOW: list[str] = ["idea", "validation", "business", "legal", "export"]


class PhaseNotUnlockedError(Exception):
    """Raised when a caller attempts to run a phase that is not yet available."""

    def __init__(self, phase: str, current_phase: str) -> None:
        super().__init__(
            f"Phase '{phase}' is not unlocked. Current phase: '{current_phase}'. "
            f"Complete the preceding phases first."
        )
        self.phase = phase
        self.current_phase = current_phase


class PhaseAlreadyCompleteError(Exception):
    """Raised when trying to advance beyond the last phase."""

    def __init__(self, phase: str) -> None:
        super().__init__(f"Phase '{phase}' is already the last phase in the workflow.")
        self.phase = phase


class WorkflowEngine:
    """
    Encapsulates all phase progression logic for a project.

    All methods are async and require an active SQLAlchemy AsyncSession.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Public API ────────────────────────────────────────────────────────

    async def get_workflow(self, project: Project) -> list[str]:
        """
        Return the ordered phase list for this project's category.

        Falls back to DEFAULT_WORKFLOW if the category has no workflow defined.
        """
        if project.category_id is None:
            return DEFAULT_WORKFLOW

        result = await self._db.execute(
            select(StartupCategory).where(StartupCategory.id == project.category_id)
        )
        category: StartupCategory | None = result.scalar_one_or_none()
        if category is None or not category.workflow:
            return DEFAULT_WORKFLOW

        return list(category.workflow)

    async def get_phase_status(self, project: Project) -> dict[str, Any]:
        """
        Return a full status snapshot for all phases in this project's workflow.

        Returns:
            {
                "current_phase": str,
                "workflow": [str, ...],
                "phases": {
                    "<phase>": {
                        "status": "completed" | "current" | "locked",
                        "completed_at": ISO str | null,
                    },
                    ...
                }
            }
        """
        workflow = await self.get_workflow(project)
        current_idx = self._phase_index(workflow, project.current_phase)

        phases: dict[str, dict] = {}
        for idx, phase in enumerate(workflow):
            if idx < current_idx:
                # Completed phase — look up the log entry
                completed_at = await self._get_phase_completed_at(project.id, phase)
                phases[phase] = {
                    "status": "completed",
                    "completed_at": completed_at.isoformat() if completed_at else None,
                }
            elif idx == current_idx:
                phases[phase] = {"status": "current", "completed_at": None}
            else:
                phases[phase] = {"status": "locked", "completed_at": None}

        return {
            "current_phase": project.current_phase,
            "workflow": workflow,
            "phases": phases,
        }

    async def is_phase_complete(self, project: Project, phase: str) -> bool:
        """
        Check whether a phase has its required output rows in the DB.

        This is the authoritative completion check — do NOT rely on
        `current_phase` alone to determine whether a phase ran successfully.
        """
        checker = {
            "idea": self._check_idea_complete,
            "validation": self._check_validation_complete,
            "patent": self._check_patent_complete,
            "business": self._check_business_complete,
            "legal": self._check_legal_complete,
            "export": self._check_export_complete,
        }.get(phase)

        if checker is None:
            logger.warning("unknown_phase_in_completion_check", phase=phase)
            return False

        return await checker(project.id)

    async def assert_phase_unlocked(self, project: Project, phase: str) -> None:
        """
        Raise PhaseNotUnlockedError if `phase` is not yet reachable.

        A phase is reachable if every phase before it in the workflow is complete.
        """
        workflow = await self.get_workflow(project)
        target_idx = self._phase_index(workflow, phase)
        current_idx = self._phase_index(workflow, project.current_phase)

        if target_idx > current_idx:
            raise PhaseNotUnlockedError(phase, project.current_phase)

    async def advance_phase(self, project: Project) -> str:
        """
        Move the project to the next phase in its workflow.

        Pre-condition: the current phase must be complete (checked here).
        Post-condition: `project.current_phase` is updated and a PhaseLog
                        row is written for the newly entered phase.

        Returns:
            The name of the new current phase.

        Raises:
            PhaseAlreadyCompleteError if already on the last phase.
            ValueError if the current phase is not yet complete.
        """
        workflow = await self.get_workflow(project)
        current_idx = self._phase_index(workflow, project.current_phase)

        if current_idx >= len(workflow) - 1:
            raise PhaseAlreadyCompleteError(project.current_phase)

        # Confirm current phase is actually complete
        is_done = await self.is_phase_complete(project, project.current_phase)
        if not is_done:
            raise ValueError(
                f"Cannot advance: phase '{project.current_phase}' is not yet complete. "
                f"Run the AI pipeline for this phase first."
            )

        # Mark current phase as completed in the log
        await self._mark_phase_completed(project.id, project.current_phase)

        # Advance
        next_phase = workflow[current_idx + 1]
        project.current_phase = next_phase  # type: ignore[assignment]

        # Log entry for the newly entered phase
        await self._log_phase_start(project.id, next_phase)

        await self._db.flush()
        logger.info(
            "phase_advanced",
            project_id=str(project.id),
            from_phase=workflow[current_idx],
            to_phase=next_phase,
        )
        return next_phase

    async def log_phase_running(self, project_id: uuid.UUID, phase: str, task_id: str) -> None:
        """Write a 'running' entry when an async AI job starts."""
        log = PhaseLog(
            project_id=project_id,
            phase=phase,
            status="running",  # type: ignore[arg-type]
            task_id=task_id,
            started_at=datetime.now(timezone.utc),
        )
        self._db.add(log)
        await self._db.flush()

    async def log_phase_failed(
        self,
        project_id: uuid.UUID,
        phase: str,
        error: str,
    ) -> None:
        """Write a 'failed' entry when an AI job errors out."""
        log = PhaseLog(
            project_id=project_id,
            phase=phase,
            status="failed",  # type: ignore[arg-type]
            error_message=error,
            completed_at=datetime.now(timezone.utc),
        )
        self._db.add(log)
        await self._db.flush()

    # ── Phase completion checkers ─────────────────────────────────────────

    async def _check_idea_complete(self, project_id: uuid.UUID) -> bool:
        result = await self._db.execute(
            select(IdeaAnalysis).where(
                and_(
                    IdeaAnalysis.project_id == project_id,
                    IdeaAnalysis.problem_statement.isnot(None),
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def _check_validation_complete(self, project_id: uuid.UUID) -> bool:
        result = await self._db.execute(
            select(ValidationReport).where(
                and_(
                    ValidationReport.project_id == project_id,
                    ValidationReport.total_score.isnot(None),
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def _check_patent_complete(self, project_id: uuid.UUID) -> bool:
        result = await self._db.execute(
            select(PatentResearchReport).where(
                PatentResearchReport.project_id == project_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def _check_business_complete(self, project_id: uuid.UUID) -> bool:
        result = await self._db.execute(
            select(BusinessPlan).where(
                and_(
                    BusinessPlan.project_id == project_id,
                    BusinessPlan.lean_canvas.isnot(None),
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def _check_legal_complete(self, project_id: uuid.UUID) -> bool:
        result = await self._db.execute(
            select(LegalChecklist).where(LegalChecklist.project_id == project_id)
        )
        return result.scalar_one_or_none() is not None

    async def _check_export_complete(self, project_id: uuid.UUID) -> bool:
        result = await self._db.execute(
            select(Document).where(Document.project_id == project_id)
        )
        return result.scalar_one_or_none() is not None

    # ── Phase log helpers ─────────────────────────────────────────────────

    async def _log_phase_start(self, project_id: uuid.UUID, phase: str) -> None:
        log = PhaseLog(
            project_id=project_id,
            phase=phase,
            status="pending",  # type: ignore[arg-type]
            started_at=datetime.now(timezone.utc),
        )
        self._db.add(log)

    async def _mark_phase_completed(self, project_id: uuid.UUID, phase: str) -> None:
        result = await self._db.execute(
            select(PhaseLog)
            .where(
                and_(
                    PhaseLog.project_id == project_id,
                    PhaseLog.phase == phase,
                    PhaseLog.completed_at.is_(None),
                )
            )
            .order_by(PhaseLog.started_at.desc())
        )
        log = result.scalar_one_or_none()
        if log:
            log.status = "completed"  # type: ignore[assignment]
            log.completed_at = datetime.now(timezone.utc)
        else:
            # Create a completed entry if no pending log exists
            completed_log = PhaseLog(
                project_id=project_id,
                phase=phase,
                status="completed",  # type: ignore[arg-type]
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )
            self._db.add(completed_log)

    async def _get_phase_completed_at(
        self,
        project_id: uuid.UUID,
        phase: str,
    ) -> datetime | None:
        result = await self._db.execute(
            select(PhaseLog)
            .where(
                and_(
                    PhaseLog.project_id == project_id,
                    PhaseLog.phase == phase,
                    PhaseLog.status == "completed",
                )
            )
            .order_by(PhaseLog.completed_at.desc())
        )
        log = result.scalar_one_or_none()
        return log.completed_at if log else None

    # ── Internal helpers ──────────────────────────────────────────────────

    @staticmethod
    def _phase_index(workflow: list[str], phase: str) -> int:
        try:
            return workflow.index(phase)
        except ValueError:
            # Phase not in workflow — treat as index 0
            logger.warning("phase_not_in_workflow", phase=phase, workflow=workflow)
            return 0
