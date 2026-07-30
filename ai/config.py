"""Startup Igniter AI Subsystem Master Configuration.

Provides centralized management for LLM providers, environment variables,
memory settings, CrewAI framework parameters, and shared system constants.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from ai.shared.constants import (
    DEFAULT_EMBEDDING_DIMENSION,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_PHASE_ACTION_BUDGET,
    ModelTier,
    StartupCategory,
    StartupPhase,
)
from ai.shared.errors import ConfigurationError, MissingAPIKeyError
from ai.shared.logger import setup_ai_logger
from ai.shared.memory_config import VectorMemoryConfig


def find_env_file() -> Optional[str]:
    """Locate workspace environment file (.env or backend/env)."""
    possible_paths = [
        Path.cwd() / "backend" / ".env",
        Path.cwd() / "backend" / "env",
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent / "backend" / "env",
        Path(__file__).resolve().parent.parent / "backend" / ".env",
    ]
    for path in possible_paths:
        if path.is_file():
            return str(path)
    return None


class AISettings(BaseSettings):
    """Central configuration for Startup Igniter AI Engine."""

    model_config = SettingsConfigDict(
        env_file=find_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Environment & App Settings ---
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # --- Groq LLM Provider ---
    groq_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    groq_model_heavy: str = Field(
        default="llama-3.3-70b-versatile", alias="GROQ_MODEL_HEAVY"
    )
    groq_model_fast: str = Field(
        default="llama-3.1-8b-instant", alias="GROQ_MODEL_FAST"
    )

    # --- OpenRouter LLM Provider ---
    openrouter_api_key: Optional[str] = Field(default=None, alias="OPENROUTER_API_KEY")
    openrouter_model_heavy: str = Field(
        default="meta-llama/llama-3.3-70b-instruct", alias="OPENROUTER_MODEL_HEAVY"
    )
    openrouter_model_fast: str = Field(
        default="meta-llama/llama-3.1-8b-instruct", alias="OPENROUTER_MODEL_FAST"
    )

    # --- Search & Scraping APIs ---
    tavily_api_key: Optional[str] = Field(default=None, alias="TAVILY_API_KEY")
    exa_api_key: Optional[str] = Field(default=None, alias="EXA_API_KEY")
    zyte_api_key: Optional[str] = Field(default=None, alias="ZYTE_API_KEY")

    # --- Supabase Database & Memory ---
    supabase_url: Optional[str] = Field(default=None, alias="SUPABASE_URL")
    supabase_service_role_key: Optional[str] = Field(
        default=None, alias="SUPABASE_SERVICE_ROLE_KEY"
    )

    # --- Redis / Upstash Queue ---
    upstash_redis_rest_url: Optional[str] = Field(
        default=None, alias="UPSTASH_REDIS_REST_URL"
    )
    upstash_redis_rest_token: Optional[str] = Field(
        default=None, alias="UPSTASH_REDIS_REST_TOKEN"
    )

    # --- CrewAI Framework Global Settings ---
    crewai_verbose: bool = Field(default=True, alias="CREWAI_VERBOSE")
    crewai_telemetry_opt_out: bool = Field(
        default=True, alias="CREWAI_TELEMETRY_OPT_OUT"
    )
    crewai_max_rpm: int = Field(default=60, alias="CREWAI_MAX_RPM")

    # --- Budget & Limits ---
    phase_action_budget: int = Field(
        default=DEFAULT_PHASE_ACTION_BUDGET, alias="PHASE_ACTION_BUDGET"
    )

    # --- Memory Configuration ---
    memory_config: VectorMemoryConfig = Field(
        default_factory=VectorMemoryConfig
    )

    def validate_api_keys(self, raise_on_missing: bool = False) -> Dict[str, bool]:
        """Audit status of configured API keys.

        Args:
            raise_on_missing: If True, raises MissingAPIKeyError for required Groq key.

        Returns:
            Dict mapping key name to presence status boolean.
        """
        status = {
            "GROQ_API_KEY": bool(self.groq_api_key and self.groq_api_key != "your-groq-api-key"),
            "TAVILY_API_KEY": bool(self.tavily_api_key),
            "EXA_API_KEY": bool(self.exa_api_key),
            "ZYTE_API_KEY": bool(self.zyte_api_key),
            "SUPABASE_URL": bool(self.supabase_url),
        }

        if raise_on_missing and not status["GROQ_API_KEY"]:
            raise MissingAPIKeyError(
                key_name="GROQ_API_KEY",
                provider_name="Groq",
            )

        return status

    def setup_environment(self) -> None:
        """Apply AI environment variables to OS process level (e.g. for CrewAI/LiteLLM)."""
        if self.groq_api_key:
            os.environ["GROQ_API_KEY"] = self.groq_api_key
        if self.tavily_api_key:
            os.environ["TAVILY_API_KEY"] = self.tavily_api_key
        if self.crewai_telemetry_opt_out:
            os.environ["OTEL_SDK_DISABLED"] = "true"


# Global singleton settings cache
_ai_settings_instance: Optional[AISettings] = None


def get_ai_settings(reload: bool = False) -> AISettings:
    """Retrieve or initialize global AI settings instance."""
    global _ai_settings_instance
    if _ai_settings_instance is None or reload:
        try:
            _ai_settings_instance = AISettings()
            _ai_settings_instance.setup_environment()
            setup_ai_logger(log_level=_ai_settings_instance.log_level)
        except Exception as err:
            raise ConfigurationError(
                f"Failed to load AI settings: {str(err)}",
                details={"error": str(err)},
            ) from err
    return _ai_settings_instance
