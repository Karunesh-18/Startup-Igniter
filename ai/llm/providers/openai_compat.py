"""Fallback providers: Groq and OpenRouter.

These are the two providers the codebase already used exclusively. They now
sit behind the self-hosted provider as an explicit fallback rather than the
only option, per the migration decision to demote hosted APIs without
breaking the pipeline while the DGX is unreachable.

Behavioural note vs. the old `call_live_llm`: neither provider silently
downgrades to a smaller "fast" model on later retry attempts anymore. That
behaviour answered a request for a specific model with a different, weaker
one and reported success — a clean failure is more honest and lets the
gateway's own fallback chain (selfhosted -> groq/openrouter -> mock) do the
degrading explicitly, where it's visible in logs.
"""

from typing import Any, Dict, Optional, Type

from pydantic import BaseModel

from ai.llm.providers.base import BaseLLMProvider, LLMResponse, ProviderUnavailableError
from ai.llm.providers.openai_http import chat_completion
from ai.llm.settings import LLMSettings


class GroqProvider(BaseLLMProvider):
    """Groq's OpenAI-compatible endpoint."""

    name = "groq"
    BASE_URL = "https://api.groq.com/openai/v1"

    def __init__(self, settings: LLMSettings):
        self.settings = settings

    def is_configured(self) -> bool:
        return self.settings.has_groq

    def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float = 0.2,
        max_tokens: Optional[int] = 4096,
        timeout: float = 60.0,
        max_retries: int = 4,
        schema_class: Optional[Type[BaseModel]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        if not self.is_configured():
            raise ProviderUnavailableError("GroqProvider has no GROQ_API_KEY configured.", details={"provider": self.name})

        headers = {
            "Authorization": f"Bearer {self.settings.groq_api_key}",
            "Content-Type": "application/json",
        }
        # Groq supports json_object mode (not full json_schema); still meaningfully
        # better than nothing when the self-hosted path with true schema-guided
        # decoding is unavailable.
        response_format = {"type": "json_object"} if schema_class is not None else None
        model_name = model.replace("groq/", "")

        text = chat_completion(
            base_url=self.BASE_URL,
            headers=headers,
            model=model_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            max_retries=max_retries,
            response_format=response_format,
            provider_label="Groq",
        )
        return LLMResponse(text=text, provider=self.name, model=model_name)


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter's OpenAI-compatible endpoint."""

    name = "openrouter"
    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, settings: LLMSettings):
        self.settings = settings

    def is_configured(self) -> bool:
        return self.settings.has_openrouter

    def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float = 0.2,
        max_tokens: Optional[int] = 4096,
        timeout: float = 60.0,
        max_retries: int = 4,
        schema_class: Optional[Type[BaseModel]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        if not self.is_configured():
            raise ProviderUnavailableError(
                "OpenRouterProvider has no OPENROUTER_API_KEY configured.", details={"provider": self.name}
            )

        headers = {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "HTTP-Referer": "https://startup-igniter.ai",
            "X-Title": "Startup Igniter AI Engine",
            "Content-Type": "application/json",
        }

        text = chat_completion(
            base_url=self.BASE_URL,
            headers=headers,
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            max_retries=max_retries,
            response_format=None,  # OpenRouter's json_schema support varies by upstream model; rely on the repair loop
            provider_label="OpenRouter",
        )
        return LLMResponse(text=text, provider=self.name, model=model)
