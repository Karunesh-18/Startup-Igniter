"""Supabase JWT verification (asymmetric, via the project's JWKS).

Supabase signs access tokens with a project key published at
SUPABASE_JWKS_URL (ES256 on current projects). Tokens signed by our own
SECRET_KEY (core.security) are accepted too: the API mints those for
service-to-service use and tests. Anything else is rejected; claims are never
trusted unverified.
"""

import asyncio
import uuid
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import get_settings
from core.security import decode_access_token

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    """The authenticated caller. `id` is the Supabase auth user id."""

    id: uuid.UUID
    email: str | None = None


@lru_cache
def _jwks_client(url: str) -> jwt.PyJWKClient:
    # PyJWKClient caches fetched keys and refetches on an unknown `kid`.
    return jwt.PyJWKClient(url, cache_keys=True, lifespan=3600, timeout=10)


def _verify_supabase(token: str) -> dict:
    settings = get_settings()
    url = settings.SUPABASE_JWKS_URL or (
        f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json" if settings.SUPABASE_URL else ""
    )
    if not url:
        raise jwt.InvalidTokenError("Supabase JWKS is not configured")
    key = _jwks_client(url).get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        key.key,
        algorithms=["ES256", "RS256"],
        audience="authenticated",
        options={"require": ["exp", "sub"]},
    )


async def verify_token(token: str) -> dict:
    """Return verified claims, or raise jwt.InvalidTokenError / JWTError."""
    try:
        return decode_access_token(token)
    except Exception:  # noqa: BLE001 -- not one of ours; try Supabase
        return await asyncio.to_thread(_verify_supabase, token)


async def current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Principal:
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED, "Could not validate credentials.", headers={"WWW-Authenticate": "Bearer"}
    )
    if credentials is None:
        raise unauthorized
    try:
        claims = await verify_token(credentials.credentials)
        return Principal(id=uuid.UUID(claims["sub"]), email=claims.get("email"))
    except Exception:  # noqa: BLE001 -- any verification failure is a 401
        raise unauthorized


CurrentPrincipal = Annotated[Principal, Depends(current_principal)]
