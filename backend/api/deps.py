"""
FastAPI dependency providers.

All reusable dependencies for route handlers live here.
Import with:
    from api.deps import get_current_user, require_project_access
"""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import decode_access_token
from db.database import get_db
from db.models import Project, ProjectMember, User

# ── Auth ──────────────────────────────────────────────────────────────────────

_bearer = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Validate the Bearer JWT and return the authenticated User.

    The JWT is either:
      a) Issued by our own API (core/security.py — SECRET_KEY signed).
      b) Issued by Supabase Auth (same JWT, validated via SECRET_KEY or Supabase JWKS).

    For v1, we validate against our own SECRET_KEY.  To accept Supabase-issued
    JWTs directly, swap `decode_access_token` for Supabase JWKS validation.

    Raises:
        401 if the token is missing, malformed, or expired.
        401 if the user record does not exist in our DB.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(credentials.credentials)
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    return user


# ── Project access ─────────────────────────────────────────────────────────────


async def get_project(
    project_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Project:
    """
    Load a project by UUID. Raises 404 if not found.
    """
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )
    return project


async def require_project_access(
    project: Annotated[Project, Depends(get_project)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Project:
    """
    Verify that the current user has at least viewer access to the project.

    Access rules:
      - Project owner (projects.user_id) always has full access.
      - project_members rows grant role-based access.

    Raises:
        403 if the user has no membership.
    """
    if project.user_id == current_user.id:
        return project

    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this project.",
        )
    return project


async def require_project_edit_access(
    project: Annotated[Project, Depends(get_project)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Project:
    """
    Verify that the current user has editor or owner access.

    Raises:
        403 if the user is a viewer-only member.
    """
    if project.user_id == current_user.id:
        return project

    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None or member.role == "viewer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You need editor or owner access to perform this action.",
        )
    return project


# ── Convenience type aliases ──────────────────────────────────────────────────

CurrentUser = Annotated[User, Depends(get_current_user)]
DB = Annotated[AsyncSession, Depends(get_db)]
OwnedProject = Annotated[Project, Depends(require_project_access)]
EditableProject = Annotated[Project, Depends(require_project_edit_access)]
