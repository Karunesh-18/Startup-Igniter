"""Single source of truth for LLM backend configuration.

The only LLM backend is the self-hosted vLLM server (no paid APIs). This
module is the one place LLM settings are declared; ``ai/config.py::AISettings``
and ``backend/core/config.py::Settings`` both inherit ``LLMSettings``.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _locate_env_file() -> Optional[str]:
    """Find the workspace .env file, independent of ai.config (avoids a circular import
    since ai.config imports LLMSettings). Mirrors ai.config.find_env_file's search order.
    """
    candidates = [
        Path.cwd() / "backend" / ".env",
        Path.cwd() / "backend" / "env",
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[2] / "backend" / "env",
        Path(__file__).resolve().parents[2] / "backend" / ".env",
    ]
    for path in candidates:
        if path.is_file():
            return str(path)
    return None


class LLMSettings(BaseSettings):
    """Configuration for the self-hosted LLM gateway.

    Resolution order at call time is ``selfhosted -> mock``; mock is only
    reached when ``llm_allow_mock`` is true (default; prod should disable it).
    """

    model_config = SettingsConfigDict(
        env_file=_locate_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    # --- Self-hosted (DGX B200 / vLLM) -------------------------------------
    llm_base_url: Optional[str] = Field(
        default=None,
        alias="LLM_BASE_URL",
        description="OpenAI-compatible base URL for the self-hosted vLLM server, e.g. http://dgx-b200:47001/v1",
    )
    llm_api_key: Optional[str] = Field(
        default=None,
        alias="LLM_API_KEY",
        description="Bearer token for the self-hosted endpoint, if it requires one (vLLM does not by default).",
    )
    llm_model_heavy: str = Field(
        default="Qwen/Qwen3-32B",
        alias="LLM_MODEL_HEAVY",
        description="Self-hosted model name for ModelTier.HEAVY and ModelTier.REASONING.",
    )
    llm_model_fast: str = Field(
        default="Qwen/Qwen3-8B",
        alias="LLM_MODEL_FAST",
        description="Self-hosted model name for ModelTier.FAST.",
    )
    llm_base_url_fast: Optional[str] = Field(
        default=None,
        alias="LLM_BASE_URL_FAST",
        description=(
            "Optional separate base URL for ModelTier.FAST. vLLM serves one base "
            "model per process, so Qwen3-32B (HEAVY/REASONING) and Qwen3-8B (FAST) "
            "run as two separate servers (see training/serve/vllm_up.sh) -- content-"
            "based routing by model name isn't something a plain reverse proxy does "
            "cleanly, so the gateway picks the URL per tier directly instead. "
            "Defaults to LLM_BASE_URL when unset, i.e. one server answering both "
            "tiers still works unchanged."
        ),
    )
    llm_guided_decoding: bool = Field(
        default=True,
        alias="LLM_GUIDED_DECODING",
        description=(
            "Send response_format={'type':'json_schema', ...} to the self-hosted "
            "endpoint so vLLM grammar-constrains generation to the agent's schema."
        ),
    )

    # --- Behaviour -----------------------------------------------------------
    llm_allow_mock: bool = Field(
        default=True,
        alias="LLM_ALLOW_MOCK",
        description="Allow falling through to the offline mock provider. Production should set false.",
    )
    llm_default_timeout_seconds: float = Field(default=60.0, alias="LLM_TIMEOUT_SECONDS")
    llm_max_retries: int = Field(default=4, alias="LLM_MAX_RETRIES")
    llm_repair_attempts: int = Field(
        default=2,
        alias="LLM_REPAIR_ATTEMPTS",
        description="Bounded retries feeding validation errors back to the model on schema mismatch.",
    )

    @property
    def has_selfhosted(self) -> bool:
        return bool(self.llm_base_url)

    def selfhosted_base_url_for_tier(self, tier: "ModelTier") -> Optional[str]:
        """Resolve which self-hosted server answers a given tier.

        FAST uses `llm_base_url_fast` when set (Qwen3-8B's own vLLM server —
        see training/serve/vllm_up.sh, port 47002); everything else uses
        `llm_base_url` (Qwen3-32B, port 47001). Falls back to `llm_base_url`
        for FAST too when no separate URL is configured, so a single
        one-server setup keeps working unchanged.
        """
        from ai.shared.constants import ModelTier  # local import: avoids a hard dependency for callers that don't need it

        if tier == ModelTier.FAST and self.llm_base_url_fast:
            return self.llm_base_url_fast
        return self.llm_base_url

_llm_settings_instance: Optional[LLMSettings] = None


def get_llm_settings(reload: bool = False) -> LLMSettings:
    """Return the process-wide LLMSettings singleton.

    Unlike the old `call_live_llm`, this does NOT re-read from disk on every
    call — env vars are read once per process (or on explicit `reload=True`),
    matching how `backend/core/config.py::get_settings` already behaves.
    """
    global _llm_settings_instance
    if _llm_settings_instance is None or reload:
        _llm_settings_instance = LLMSettings()
    return _llm_settings_instance
