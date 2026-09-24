"""Single source of truth for LLM backend configuration.

Historically ``ai/config.py::AISettings`` and ``backend/core/config.py::Settings``
each declared their own copy of the LLM env vars (``GROQ_*``, ``OPENROUTER_*``)
and drifted — OpenRouter was primary in code but missing from
``backend/.env.example`` and from ``backend/core/config.py`` entirely. This
module is the one place new LLM settings are declared; both config classes
import ``LLMSettings`` rather than re-declaring fields.
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
    """Configuration for the self-hosted-first LLM gateway.

    Resolution order at call time is ``selfhosted -> fallback -> mock``,
    each stage skipped if its preconditions are not met (no base_url/key,
    or the connection fails and a fallback is configured).
    """

    model_config = SettingsConfigDict(
        env_file=_locate_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    # --- Self-hosted (DGX B200 / vLLM) -------------------------------------
    # Not reachable yet at time of writing; every call gracefully falls
    # through to `llm_fallback_backend` when this is unset or unreachable.
    llm_base_url: Optional[str] = Field(
        default=None,
        alias="LLM_BASE_URL",
        description="OpenAI-compatible base URL for the self-hosted vLLM server, e.g. http://dgx-b200:8000/v1",
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

    # --- Fallback (existing hosted providers) ------------------------------
    # 'groq' | 'openrouter' | 'none'. Auto-detected from whichever key is
    # present if left as 'auto'.
    llm_fallback_backend: str = Field(default="auto", alias="LLM_FALLBACK_BACKEND")

    groq_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    groq_model_heavy: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL_HEAVY")
    groq_model_fast: str = Field(default="llama-3.1-8b-instant", alias="GROQ_MODEL_FAST")

    openrouter_api_key: Optional[str] = Field(default=None, alias="OPENROUTER_API_KEY")
    openrouter_model_heavy: str = Field(
        default="meta-llama/llama-3.3-70b-instruct", alias="OPENROUTER_MODEL_HEAVY"
    )
    openrouter_model_fast: str = Field(
        default="meta-llama/llama-3.1-8b-instruct", alias="OPENROUTER_MODEL_FAST"
    )

    # --- Behaviour -----------------------------------------------------------
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
        see training/serve/vllm_up.sh, port 8002); everything else uses
        `llm_base_url` (Qwen3-32B, port 8001). Falls back to `llm_base_url`
        for FAST too when no separate URL is configured, so a single
        one-server setup keeps working unchanged.
        """
        from ai.shared.constants import ModelTier  # local import: avoids a hard dependency for callers that don't need it

        if tier == ModelTier.FAST and self.llm_base_url_fast:
            return self.llm_base_url_fast
        return self.llm_base_url

    @property
    def has_groq(self) -> bool:
        return bool(self.groq_api_key and self.groq_api_key not in ("", "your-groq-api-key"))

    @property
    def has_openrouter(self) -> bool:
        return bool(self.openrouter_api_key)

    def resolve_fallback_backend(self) -> Optional[str]:
        """Return 'groq', 'openrouter', or None per `llm_fallback_backend` and configured keys."""
        choice = (self.llm_fallback_backend or "auto").lower()
        if choice == "none":
            return None
        if choice == "groq":
            return "groq" if self.has_groq else None
        if choice == "openrouter":
            return "openrouter" if self.has_openrouter else None
        # auto: prefer OpenRouter (matches historical behaviour: it was primary in call_live_llm)
        if self.has_openrouter:
            return "openrouter"
        if self.has_groq:
            return "groq"
        return None


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
