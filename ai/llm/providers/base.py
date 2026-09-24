"""Provider interface shared by every LLM backend the gateway can call."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel

from ai.shared.errors import LLMProviderError


@dataclass
class LLMResponse:
    """Raw text result from a provider call, plus provenance for logging/eval."""

    text: str
    provider: str
    model: str


class ProviderUnavailableError(LLMProviderError):
    """Raised when a provider is not configured (no base_url/key) — gateway should
    skip straight to the next stage in the resolution chain without retrying."""


class ProviderRequestError(LLMProviderError):
    """Raised when a configured provider was attempted but failed (network error,
    exhausted retries, non-2xx). Gateway falls through to the next stage."""


class BaseLLMProvider(ABC):
    """A single LLM backend (self-hosted vLLM, Groq, OpenRouter, mock, ...)."""

    name: str = "base"

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if this provider has enough config to attempt a call."""

    @abstractmethod
    def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str,
        tier: Any = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = 4096,
        timeout: float = 60.0,
        max_retries: int = 4,
        schema_class: Optional[Type[BaseModel]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """Execute a chat completion and return raw text (not yet parsed/validated).

        Args:
            tier: The ModelTier the caller asked for (typed as `Any` here to
                avoid a hard import of ai.shared.constants in this base module).
                Most providers ignore it (`model` is already resolved); only
                SelfHostedProvider currently uses it, to pick between two
                separate vLLM servers when LLM_BASE_URL_FAST is configured.
            schema_class: When provided and the provider supports guided decoding,
                the provider SHOULD constrain generation to this Pydantic schema's
                JSON Schema via response_format. Providers that don't support it
                (e.g. plain OpenRouter passthrough) silently ignore it — the
                gateway's repair loop is what makes that safe.
        """
