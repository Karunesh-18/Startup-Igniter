"""
Test configuration and fixtures.

Uses pytest-asyncio with an in-memory SQLite DB for fast unit tests.
Integration tests against a real Postgres DB can be enabled by setting
TEST_DATABASE_URL in the environment.
"""

import asyncio
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.main import app
from api.deps import get_db
from core.config import get_settings
from core.security import create_access_token
from db.database import Base
import db.models  # noqa — register models

# ── Test engine (SQLite in-memory) ────────────────────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
)

TestSessionFactory = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Create all tables once per test session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a fresh DB session per test, rolled back after each test."""
    async with TestSessionFactory() as session:
        try:
            yield session
            await session.rollback()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Async test client with the test DB injected.
    """
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db: AsyncSession):
    """Create a test user and return the user + JWT token."""
    from db.models import User
    from core.security import hash_password

    user = User(
        id=uuid.uuid4(),
        email="test@startup-os.dev",
        name="Test Founder",
        role="student",
        bio=hash_password("testpass123"),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(subject=user.id, extra_claims={"role": user.role})
    return {"user": user, "token": token}


@pytest_asyncio.fixture
async def auth_headers(test_user) -> dict[str, str]:
    """Return Authorization header dict for authenticated requests."""
    return {"Authorization": f"Bearer {test_user['token']}"}
