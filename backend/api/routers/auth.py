"""
Auth router — user registration, login (JWT issuance), profile management.

Supabase Auth is the primary identity provider. This router handles:
  - POST /auth/register  — create a user shadow record in our DB after Supabase signup
  - POST /auth/login     — validate credentials and issue our own JWT
  - GET  /auth/me        — return the authenticated user's profile
  - PATCH /auth/me       — update name, bio, role

For a frontend using Supabase Auth SDK directly, the /login route is optional
(Supabase handles it). We include it for API clients / testing.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import CurrentUser, DB
from core.security import create_access_token, hash_password, verify_password
from db.models import User

router = APIRouter(prefix="/auth", tags=["Auth"])


# ── Schemas ───────────────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    """Request body for user registration."""

    email: EmailStr
    name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(
        default="student",
        pattern="^(student|working_professional|graduate|researcher|faculty)$",
    )

    model_config = {"json_schema_extra": {"example": {
        "email": "founder@example.com",
        "name": "Arjun Sharma",
        "password": "securepass123",
        "role": "student",
    }}}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str


class UserProfile(BaseModel):
    id: str
    email: str
    name: str
    role: str
    bio: str | None
    avatar_url: str | None

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    bio: str | None = Field(default=None, max_length=2000)
    role: str | None = Field(
        default=None,
        pattern="^(student|working_professional|graduate|researcher|faculty)$",
    )
    avatar_url: str | None = None


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(body: RegisterRequest, db: DB) -> TokenResponse:
    """
    Create a new user account.

    - Checks that the email is not already registered.
    - Hashes the password with bcrypt.
    - Returns a JWT access token immediately (no email verification for v1).

    Note: In production, this should be gated by Supabase Auth confirmation.
    """
    # Check email uniqueness
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        id=uuid.uuid4(),
        email=body.email,
        name=body.name,
        role=body.role,  # type: ignore[arg-type]
        # Store hashed password in bio temporarily — use a dedicated column in a real app.
        # For Supabase Auth integration, passwords live in Supabase, not here.
        bio=hash_password(body.password),  # TEMPORARY for demo auth
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(subject=user.id, extra_claims={"role": user.role})
    return TokenResponse(access_token=token, user_id=str(user.id))


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive a JWT",
)
async def login(body: LoginRequest, db: DB) -> TokenResponse:
    """
    Validate credentials and issue a JWT access token.

    Uses the local bcrypt-hashed password (stored in bio field for demo).
    In production, delegate to Supabase Auth's /auth/v1/token endpoint.
    """
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or not (user.bio and verify_password(body.password, user.bio)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(subject=user.id, extra_claims={"role": user.role})
    return TokenResponse(access_token=token, user_id=str(user.id))


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Get the authenticated user's profile",
)
async def get_me(current_user: CurrentUser) -> UserProfile:
    """Return the profile of the currently authenticated user."""
    return UserProfile(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        bio=None,  # don't expose the hashed password stored in bio
        avatar_url=current_user.avatar_url,
    )


@router.patch(
    "/me",
    response_model=UserProfile,
    summary="Update profile",
)
async def update_me(
    body: UpdateProfileRequest,
    current_user: CurrentUser,
    db: DB,
) -> UserProfile:
    """Partially update the authenticated user's profile."""
    if body.name is not None:
        current_user.name = body.name  # type: ignore[assignment]
    if body.role is not None:
        current_user.role = body.role  # type: ignore[assignment]
    if body.avatar_url is not None:
        current_user.avatar_url = body.avatar_url  # type: ignore[assignment]
    # Note: bio update excluded to avoid overwriting hashed password in demo

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)

    return UserProfile(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        bio=None,
        avatar_url=current_user.avatar_url,
    )
