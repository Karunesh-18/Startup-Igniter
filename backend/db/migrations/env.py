"""
Alembic env.py — configures the migration environment.

Key behaviours:
- Reads DATABASE_URL_SYNC (psycopg2 DSN) from application settings.
- Imports all ORM models so Alembic can auto-detect schema changes.
- Supports both online (live DB) and offline (SQL script) modes.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# ── Make the backend/ package importable ─────────────────────────────────────
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

# ── Load application settings ─────────────────────────────────────────────────
from core.config import get_settings  # noqa: E402
from db.database import Base  # noqa: E402
import db.models  # noqa: E402, F401  — must import to register models on Base

settings = get_settings()

# ── Alembic Config object ─────────────────────────────────────────────────────
config = context.config

# Wire logging config from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Inject the sync DSN so Alembic can create a sync engine
config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL_SYNC
    or "postgresql+psycopg2://postgres:password@localhost:5432/postgres",
)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode — emits SQL to stdout/file.
    Useful for generating migration scripts to send to a DBA.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Include schema-level objects (pgvector extension, etc.)
        include_schemas=False,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode — connects to the live database.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
