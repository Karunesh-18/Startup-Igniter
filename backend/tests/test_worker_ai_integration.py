import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Project, User
from workers.tasks import run_idea_phase, run_validation_phase


@pytest.mark.asyncio
async def test_worker_run_idea_phase_execution(db: AsyncSession, test_user: dict):
    """Verify run_idea_phase background worker executes and populates DB rows."""
    user = test_user["user"]

    project = Project(
        id=uuid.uuid4(),
        user_id=user.id,
        name="AI Medical Diagnostics Assistant",
        description="Autonomous AI agent analyzing medical scans and clinical reports.",
        current_phase="idea",
    )
    db.add(project)
    await db.commit()

    ctx = {"job_id": "test_job_123"}
    res = await run_idea_phase(ctx, str(project.id), db_session=db)

    assert res.get("status") == "completed"
    assert "idea_id" in res


@pytest.mark.asyncio
async def test_worker_run_validation_phase_execution(db: AsyncSession, test_user: dict):
    """Verify run_validation_phase background worker executes after idea phase completion."""
    user = test_user["user"]

    project = Project(
        id=uuid.uuid4(),
        user_id=user.id,
        name="FinTech Micro-Lending Platform",
        description="P2P micro-lending app for college student founders.",
        current_phase="idea",
    )
    db.add(project)
    await db.commit()

    ctx = {"job_id": "test_job_456"}
    # Run idea phase first so gate passes
    await run_idea_phase(ctx, str(project.id), db_session=db)

    val_res = await run_validation_phase(ctx, str(project.id), db_session=db)
    assert val_res.get("status") == "completed"
    assert "total_score" in val_res
