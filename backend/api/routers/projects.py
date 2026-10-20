"""
Projects router — CRUD for startup projects.

Endpoints:
  POST   /projects                         Create a new project
  GET    /projects                         List current user's projects
  GET    /projects/{project_id}            Get project details
  PATCH  /projects/{project_id}            Update name/tagline/description/category
  DELETE /projects/{project_id}            Delete a project (owner only)

  GET    /projects/{project_id}/members          List members
  POST   /projects/{project_id}/members          Invite a member
  PATCH  /projects/{project_id}/members/{uid}    Change member role
  DELETE /projects/{project_id}/members/{uid}    Remove a member

  GET    /projects/{project_id}/phase-status     Get workflow status
  POST   /projects/{project_id}/advance-phase    Advance to next phase
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import CurrentUser, DB, EditableProject, OwnedProject
from db.models import Project, ProjectMember, StartupCategory, User
from workflow.engine import (
    PhaseAlreadyCompleteError,
    PhaseNotUnlockedError,
    WorkflowEngine,
)

router = APIRouter(prefix="/projects", tags=["Projects"])


# ── Schemas ───────────────────────────────────────────────────────────────────


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    tagline: str | None = Field(default=None, max_length=500)
    description: str | None = None
    category_slug: str | None = None

    model_config = {"json_schema_extra": {"example": {
        "name": "EduMatch AI",
        "tagline": "AI-powered student-mentor matching platform",
        "description": "Connects students with relevant mentors using semantic matching.",
        "category_slug": "edtech",
    }}}


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=300)
    tagline: str | None = Field(default=None, max_length=500)
    description: str | None = None
    category_slug: str | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    tagline: str | None
    description: str | None
    current_phase: str
    category_name: str | None
    category_slug: str | None
    ai_calls_used: int
    ai_calls_budget: int
    created_at: str

    model_config = {"from_attributes": True}


class MemberResponse(BaseModel):
    user_id: str
    email: str
    name: str
    role: str
    joined_at: str


class InviteMemberRequest(BaseModel):
    email: str
    role: str = Field(default="viewer", pattern="^(editor|viewer)$")


class UpdateMemberRoleRequest(BaseModel):
    role: str = Field(pattern="^(editor|viewer)$")


class PhaseStatusResponse(BaseModel):
    current_phase: str
    workflow: list[str]
    phases: dict[str, dict]


# ── Helper ────────────────────────────────────────────────────────────────────


async def _resolve_category(slug: str | None, db: AsyncSession) -> uuid.UUID | None:
    if not slug:
        return None
    result = await db.execute(
        select(StartupCategory).where(StartupCategory.slug == slug)
    )
    cat = result.scalar_one_or_none()
    if cat is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown category slug: '{slug}'",
        )
    return cat.id


def _project_to_response(project: Project, category: StartupCategory | None) -> ProjectResponse:
    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        tagline=project.tagline,
        description=project.description,
        current_phase=project.current_phase,
        category_name=category.name if category else None,
        category_slug=category.slug if category else None,
        ai_calls_used=project.ai_calls_used,
        ai_calls_budget=project.ai_calls_budget,
        created_at=project.created_at.isoformat(),
    )


# ── Project CRUD ──────────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
)
async def create_project(
    body: ProjectCreate,
    current_user: CurrentUser,
    db: DB,
) -> ProjectResponse:
    """
    Create a new startup project owned by the authenticated user.

    The project starts in the 'idea' phase automatically.
    An optional `category_slug` assigns a predefined workflow.
    """
    from core.config import get_settings
    settings = get_settings()

    category_id = await _resolve_category(body.category_slug, db)

    project = Project(
        id=uuid.uuid4(),
        user_id=current_user.id,
        category_id=category_id,
        name=body.name,
        tagline=body.tagline,
        description=body.description,
        current_phase="idea",
        ai_calls_budget=settings.AI_CALL_BUDGET_PER_PROJECT,
    )
    db.add(project)

    # Create owner membership record
    db.add(ProjectMember(
        id=uuid.uuid4(),
        project_id=project.id,
        user_id=current_user.id,
        role="owner",
    ))

    # Write initial phase log entry
    from workflow.engine import WorkflowEngine
    engine = WorkflowEngine(db)
    await engine._log_phase_start(project.id, "idea")

    await db.commit()
    await db.refresh(project)

    category = None
    if category_id:
        result = await db.execute(select(StartupCategory).where(StartupCategory.id == category_id))
        category = result.scalar_one_or_none()

    return _project_to_response(project, category)


@router.get(
    "",
    response_model=list[ProjectResponse],
    summary="List current user's projects",
)
async def list_projects(current_user: CurrentUser, db: DB) -> list[ProjectResponse]:
    """
    Return all projects owned by or shared with the authenticated user.
    """
    # Projects the user owns
    result = await db.execute(
        select(Project).where(Project.user_id == current_user.id).order_by(Project.created_at.desc())
    )
    projects = list(result.scalars().all())

    # Projects shared with this user
    member_result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.user_id == current_user.id,
            ProjectMember.role != "owner",
        )
    )
    member_rows = list(member_result.scalars().all())
    shared_ids = {m.project_id for m in member_rows}
    owned_ids = {p.id for p in projects}

    for shared_id in shared_ids - owned_ids:
        r = await db.execute(select(Project).where(Project.id == shared_id))
        proj = r.scalar_one_or_none()
        if proj:
            projects.append(proj)

    responses = []
    for project in projects:
        category = None
        if project.category_id:
            cr = await db.execute(select(StartupCategory).where(StartupCategory.id == project.category_id))
            category = cr.scalar_one_or_none()
        responses.append(_project_to_response(project, category))

    return responses


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project details",
)
async def get_project_detail(
    project: OwnedProject,
    db: DB,
) -> ProjectResponse:
    """Return full details for a specific project."""
    category = None
    if project.category_id:
        result = await db.execute(
            select(StartupCategory).where(StartupCategory.id == project.category_id)
        )
        category = result.scalar_one_or_none()
    return _project_to_response(project, category)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project details",
)
async def update_project(
    body: ProjectUpdate,
    project: EditableProject,
    db: DB,
) -> ProjectResponse:
    """Update project name, tagline, description, or category."""
    if body.name is not None:
        project.name = body.name  # type: ignore[assignment]
    if body.tagline is not None:
        project.tagline = body.tagline  # type: ignore[assignment]
    if body.description is not None:
        project.description = body.description  # type: ignore[assignment]
    if body.category_slug is not None:
        project.category_id = await _resolve_category(body.category_slug, db)

    db.add(project)
    await db.commit()
    await db.refresh(project)

    category = None
    if project.category_id:
        result = await db.execute(
            select(StartupCategory).where(StartupCategory.id == project.category_id)
        )
        category = result.scalar_one_or_none()

    return _project_to_response(project, category)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project (owner only)",
)
async def delete_project(
    project: OwnedProject,
    current_user: CurrentUser,
    db: DB,
) -> None:
    """
    Permanently delete a project and all its data (cascade).

    Only the project owner can delete a project.
    """
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner can delete a project.",
        )
    await db.delete(project)
    await db.commit()


# ── Member management ─────────────────────────────────────────────────────────


@router.get(
    "/{project_id}/members",
    response_model=list[MemberResponse],
    summary="List project members",
)
async def list_members(project: OwnedProject, db: DB) -> list[MemberResponse]:
    result = await db.execute(
        select(ProjectMember, User)
        .join(User, User.id == ProjectMember.user_id)
        .where(ProjectMember.project_id == project.id)
    )
    rows = result.all()
    return [
        MemberResponse(
            user_id=str(member.user_id),
            email=user.email,
            name=user.name,
            role=member.role,
            joined_at=member.joined_at.isoformat(),
        )
        for member, user in rows
    ]


@router.post(
    "/{project_id}/members",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite a user to the project",
)
async def invite_member(
    body: InviteMemberRequest,
    project: EditableProject,
    current_user: CurrentUser,
    db: DB,
) -> MemberResponse:
    """
    Invite a registered user to the project by email.

    The invited user must already have an account.
    """
    result = await db.execute(select(User).where(User.email == body.email))
    invited_user = result.scalar_one_or_none()
    if not invited_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No user found with email: {body.email}",
        )

    # Check not already a member
    existing = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == invited_user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This user is already a project member.",
        )

    member = ProjectMember(
        id=uuid.uuid4(),
        project_id=project.id,
        user_id=invited_user.id,
        role=body.role,  # type: ignore[arg-type]
        invited_by=current_user.id,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)

    return MemberResponse(
        user_id=str(invited_user.id),
        email=invited_user.email,
        name=invited_user.name,
        role=member.role,
        joined_at=member.joined_at.isoformat(),
    )


@router.patch(
    "/{project_id}/members/{user_id}",
    response_model=MemberResponse,
    summary="Update a member's role",
)
async def update_member_role(
    user_id: uuid.UUID,
    body: UpdateMemberRoleRequest,
    project: EditableProject,
    current_user: CurrentUser,
    db: DB,
) -> MemberResponse:
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can change roles.")

    result = await db.execute(
        select(ProjectMember, User)
        .join(User, User.id == ProjectMember.user_id)
        .where(ProjectMember.project_id == project.id, ProjectMember.user_id == user_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Member not found.")

    member, user = row
    member.role = body.role  # type: ignore[assignment]
    db.add(member)
    await db.commit()
    await db.refresh(member)

    return MemberResponse(
        user_id=str(user.id),
        email=user.email,
        name=user.name,
        role=member.role,
        joined_at=member.joined_at.isoformat(),
    )


@router.delete(
    "/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member from the project",
)
async def remove_member(
    user_id: uuid.UUID,
    project: EditableProject,
    current_user: CurrentUser,
    db: DB,
) -> None:
    if user_id == project.user_id:
        raise HTTPException(status_code=400, detail="Cannot remove the project owner.")

    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found.")

    await db.delete(member)
    await db.commit()


# ── Phase management ──────────────────────────────────────────────────────────


@router.get(
    "/{project_id}/phase-status",
    response_model=PhaseStatusResponse,
    summary="Get workflow phase status",
)
async def get_phase_status(project: OwnedProject, db: DB) -> PhaseStatusResponse:
    """
    Return the full phase progression map for this project.

    Frontend uses this to:
      - Render the progress stepper.
      - Determine which phase panels to unlock.
      - Show completion timestamps.
    """
    engine = WorkflowEngine(db)
    status_data = await engine.get_phase_status(project)
    return PhaseStatusResponse(**status_data)


@router.post(
    "/{project_id}/advance-phase",
    response_model=PhaseStatusResponse,
    summary="Advance the project to the next phase",
)
async def advance_phase(
    project: EditableProject,
    db: DB,
) -> PhaseStatusResponse:
    """
    Advance the project's current phase to the next one in the workflow.

    Pre-conditions:
      - The current phase must be complete (has required DB output rows).
      - The project must not already be on the last phase.

    Returns the updated phase status map.
    """
    engine = WorkflowEngine(db)
    try:
        await engine.advance_phase(project)
    except PhaseAlreadyCompleteError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PhaseNotUnlockedError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    status_data = await engine.get_phase_status(project)
    return PhaseStatusResponse(**status_data)
