"""LLM provider factory and model configuration for Groq and CrewAI."""

import os
from typing import Any, Dict, Optional, Union, TYPE_CHECKING
from pydantic import BaseModel, Field

from ai.shared.constants import DEFAULT_GROQ_MODELS, ModelTier
from ai.shared.errors import LLMProviderError, MissingAPIKeyError
from ai.shared.logger import ai_logger

# Optional CrewAI import check with type safety
HAS_CREWAI = False
CrewAILLM = None

try:
    from crewai import LLM as CrewAILLM  # type: ignore
    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False
    CrewAILLM = None


class LLMConfig(BaseModel):
    """Configuration settings for LLM invocation."""

    model_tier: ModelTier = Field(
        default=ModelTier.HEAVY,
        description="Execution tier (FAST for routing, HEAVY for deep analysis).",
    )
    model_name: str = Field(
        default=DEFAULT_GROQ_MODELS[ModelTier.HEAVY],
        description="Full LiteLLM model identifier string (e.g. groq/llama-3.3-70b-versatile).",
    )
    temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for LLM outputs.",
    )
    max_tokens: Optional[int] = Field(
        default=4096,
        ge=1,
        description="Maximum tokens to generate per response.",
    )
    top_p: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling parameter.",
    )
    timeout_seconds: float = Field(
        default=60.0,
        ge=1.0,
        description="Timeout duration in seconds for LLM call.",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Number of retry attempts on transient failure.",
    )


class LLMFactory:
    """Factory for instantiating and configuring LLMs for CrewAI agents."""

    @staticmethod
    def get_model_name(
        model_tier: Union[ModelTier, str],
        custom_model: Optional[str] = None,
    ) -> str:
        """Resolve full model name from tier or custom model string."""
        if custom_model:
            return custom_model if custom_model.startswith("groq/") else f"groq/{custom_model}"
        
        tier = ModelTier(model_tier) if isinstance(model_tier, str) else model_tier
        return DEFAULT_GROQ_MODELS.get(tier, DEFAULT_GROQ_MODELS[ModelTier.HEAVY])

    @classmethod
    def get_llm(
        cls,
        model_tier: Union[ModelTier, str] = ModelTier.HEAVY,
        temperature: float = 0.2,
        max_tokens: Optional[int] = 4096,
        api_key: Optional[str] = None,
        custom_model: Optional[str] = None,
        mock_mode: bool = False,
    ) -> Any:
        """Instantiate a configured CrewAI LLM instance backed by Groq.

        Args:
            model_tier: Model execution tier (FAST, HEAVY, REASONING).
            temperature: Generation temperature.
            max_tokens: Max output token limit.
            api_key: Optional explicit API key (falls back to GROQ_API_KEY env var).
            custom_model: Optional explicit model override.
            mock_mode: If True, returns mock config object for testing without API keys.

        Returns:
            CrewAI LLM instance or LLMConfig object.
        """
        # Resolve API Key from settings or environment
        from ai.config import get_ai_settings
        settings = get_ai_settings()
        groq_api_key = api_key or settings.groq_api_key or os.getenv("GROQ_API_KEY")
        if not groq_api_key and not mock_mode:
            raise MissingAPIKeyError(
                key_name="GROQ_API_KEY",
                provider_name="Groq",
            )

        model_name = cls.get_model_name(model_tier, custom_model)

        ai_logger.info(
            f"Initializing LLM: model={model_name}, temp={temperature}, mock={mock_mode}"
        )

        config = LLMConfig(
            model_tier=ModelTier(model_tier) if isinstance(model_tier, str) else model_tier,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if mock_mode:
            return config

        # If CrewAI is installed, instantiate native CrewAI LLM
        if HAS_CREWAI and CrewAILLM is not None:
            try:
                return CrewAILLM(
                    model=model_name,
                    api_key=groq_api_key,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as err:
                raise LLMProviderError(
                    f"Failed to instantiate CrewAI LLM '{model_name}': {str(err)}",
                    details={"model": model_name, "error": str(err)},
                ) from err

        # Fallback if CrewAI not yet installed
        return config


def call_live_llm(
    system_prompt: str,
    user_prompt: str,
    model_name: Optional[str] = None,
    temperature: float = 0.2,
    timeout: float = 45.0,
    max_retries: int = 8,
) -> str:
    """Execute live LLM completion call using OpenRouter (primary) or Groq with automatic rate limit retries."""
    import time
    import httpx
    from ai.config import get_ai_settings

    settings = get_ai_settings(reload=True)

    openrouter_key = os.getenv("OPENROUTER_API_KEY") or settings.openrouter_api_key
    groq_key = os.getenv("GROQ_API_KEY") or settings.groq_api_key

    if openrouter_key:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {openrouter_key}",
            "HTTP-Referer": "https://startup-igniter.ai",
            "X-Title": "Startup Igniter AI Engine",
            "Content-Type": "application/json",
        }
        if not model_name or "groq" in model_name or "versatile" in model_name or "instant" in model_name:
            primary_model = settings.openrouter_model_heavy
        else:
            primary_model = model_name
        fast_model = settings.openrouter_model_fast
        provider_label = "OpenRouter"
    elif groq_key:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json",
        }
        primary_model = (model_name or settings.groq_model_heavy).replace("groq/", "")
        fast_model = settings.groq_model_fast.replace("groq/", "")
        provider_label = "Groq"
    else:
        raise MissingAPIKeyError(
            key_name="OPENROUTER_API_KEY or GROQ_API_KEY",
            provider_name="OpenRouter / Groq",
        )

    httpx_timeout = httpx.Timeout(35.0, connect=10.0, read=35.0)

    for attempt in range(max_retries):
        target_model = primary_model if attempt < 2 else fast_model
        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": 4096,
        }
        if provider_label == "Groq":
            payload["response_format"] = {"type": "json_object"}
        try:
            with httpx.Client(timeout=httpx_timeout) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 429 or res.status_code == 503:
                    if attempt == max_retries - 1:
                        res.raise_for_status()
                    sleep_sec = 2.0 * (attempt + 1)
                    ai_logger.warning(
                        f"{provider_label} Rate Limit / Busy ({res.status_code} for '{target_model}'). "
                        f"Retrying in {sleep_sec:.1f}s (attempt {attempt + 1}/{max_retries})..."
                    )
                    time.sleep(sleep_sec)
                    continue
                res.raise_for_status()
                data = res.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content")
                if content and content.strip():
                    return content
                ai_logger.warning(
                    f"{provider_label} returned empty content for '{target_model}'. Retrying (attempt {attempt + 1}/{max_retries})..."
                )
                time.sleep(2.0)
        except httpx.HTTPStatusError as exc:
            err_msg = exc.response.text if exc.response is not None else str(exc)
            if attempt == max_retries - 1:
                ai_logger.error(f"{provider_label} HTTP error ({exc.response.status_code}): {err_msg}")
                raise
            sleep_sec = 2.0 * (attempt + 1)
            ai_logger.warning(
                f"{provider_label} HTTP {exc.response.status_code} ({err_msg}). Retrying in {sleep_sec:.1f}s (attempt {attempt + 1}/{max_retries})..."
            )
            time.sleep(sleep_sec)
        except httpx.RequestError as exc:
            if attempt == max_retries - 1:
                ai_logger.error(f"{provider_label} network request failed: {exc}")
                raise
            sleep_sec = 2.0 * (attempt + 1)
            ai_logger.warning(
                f"{provider_label} network request error ({exc}). Retrying in {sleep_sec:.1f}s (attempt {attempt + 1}/{max_retries})..."
            )
            time.sleep(sleep_sec)

    return ""

