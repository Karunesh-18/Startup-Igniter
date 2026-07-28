"""
Core application configuration — reads from environment variables.

All settings have safe defaults for local development. In production every
value MUST be supplied via environment or a .env file (never hardcoded).
"""

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────
    APP_NAME: str = "Startup OS API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    SECRET_KEY: str = Field(default="dev-insecure-secret-change-me", min_length=32)
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: str | list) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ── Database (Supabase / PostgreSQL) ─────────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    DATABASE_URL: str = ""          # asyncpg DSN
    DATABASE_URL_SYNC: str = ""     # psycopg2 DSN (Alembic only)

    # ── Redis (Upstash) ───────────────────────────────────────────────────
    UPSTASH_REDIS_REST_URL: str = ""
    UPSTASH_REDIS_REST_TOKEN: str = ""

    # ── Groq ──────────────────────────────────────────────────────────────
    GROQ_API_KEY: str = ""
    GROQ_MODEL_HEAVY: str = "llama-3.3-70b-versatile"
    GROQ_MODEL_FAST: str = "llama-3.1-8b-instant"

    # ── Search ────────────────────────────────────────────────────────────
    TAVILY_API_KEY: str = ""
    EXA_API_KEY: str = ""
    ZYTE_API_KEY: str = ""

    # ── Research APIs ─────────────────────────────────────────────────────
    SEMANTIC_SCHOLAR_API_KEY: str = ""
    OPENALEX_EMAIL: str = ""

    # ── Storage ───────────────────────────────────────────────────────────
    STORAGE_BUCKET: str = "documents"

    # ── Rate Limiting ─────────────────────────────────────────────────────
    # Maximum AI pipeline invocations per project per 24 h
    AI_CALL_BUDGET_PER_PROJECT: int = 10

    # ── Redis cache TTLs (seconds) ────────────────────────────────────────
    CACHE_MARKET_TTL: int = 60 * 60 * 72   # 3 days
    CACHE_COMPETITOR_TTL: int = 60 * 60 * 24  # 1 day

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()
