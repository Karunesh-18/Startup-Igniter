"""
SQLAlchemy async engine, session factory, and Base declarative class.

All models import `Base` from here.  The async session is injected into
FastAPI route handlers via the `get_db` dependency.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, MappedColumn
from sqlalchemy import MetaData

from core.config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)

# ── Naming convention (Alembic-friendly) ─────────────────────────────────────
NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


# ── Engine (singleton per process) ───────────────────────────────────────────
def _create_engine():
    settings = get_settings()
    if not settings.DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy backend/.env.example → backend/.env "
            "and fill in your Supabase connection string."
        )
    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.is_development,   # SQL logging in dev
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,             # detect stale connections
    )


_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = _create_engine()
    return _engine


# ── Session factory ───────────────────────────────────────────────────────────
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _async_session_factory


# ── FastAPI dependency ────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async database session for use in route handlers.

    Usage::

        @router.get("/")
        async def handler(db: AsyncSession = Depends(get_db)):
            ...
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def close_db() -> None:
    """Dispose the engine connection pool (called on app shutdown)."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        logger.info("database_engine_disposed")
