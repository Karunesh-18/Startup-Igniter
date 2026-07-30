import uuid
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from api.deps import decode_token_jwks_or_local, require_secret_key
from core.config import get_settings
from core.security import create_access_token


@pytest.mark.asyncio
async def test_supabase_config_settings():
    settings = get_settings()
    assert hasattr(settings, "SUPABASE_PUBLISHABLE_KEY")
    assert hasattr(settings, "SUPABASE_SECRET_KEY")
    assert hasattr(settings, "SUPABASE_JWKS_URL")


@pytest.mark.asyncio
async def test_decode_token_local_and_fallback():
    user_id = str(uuid.uuid4())
    token = create_access_token(user_id)

    payload = await decode_token_jwks_or_local(token)
    assert payload.get("sub") == user_id


@pytest.mark.asyncio
async def test_require_secret_key_valid():
    settings = get_settings()
    secret = settings.SUPABASE_SECRET_KEY or "test_secret_key"
    settings.SUPABASE_SECRET_KEY = secret

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=secret)
    res = await require_secret_key(credentials)
    assert res is True


@pytest.mark.asyncio
async def test_require_secret_key_invalid():
    settings = get_settings()
    settings.SUPABASE_SECRET_KEY = "valid_secret_key"

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_secret_key")
    with pytest.raises(HTTPException) as exc_info:
        await require_secret_key(credentials)
    assert exc_info.value.status_code == 401
