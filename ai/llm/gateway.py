"""Provider-agnostic LLM gateway: the one place that decides which backend
answers a call and enforces structured output.

Resolution order per call: selfhosted -> fallback (Groq/OpenRouter) -> mock.
Each stage is skipped if unconfigured; a configured stage that fails after
its own retries falls through to the next one (logged, never silent in a way
that would hide a real outage from someone reading logs).
"""

from typing import Optional, Type

from pydantic import BaseModel, ValidationError

from ai.llm.providers.base import BaseLLMProvider, ProviderRequestError, ProviderUnavailableError
from ai.llm.providers.mock import MockProvider
from ai.llm.providers.openai_compat import GroqProvider, OpenRouterProvider
from ai.llm.providers.selfhosted import SelfHostedProvider
from ai.llm.settings import LLMSettings, get_llm_settings
from ai.llm.structured import build_repair_prompt, strip_think_blocks
from ai.shared.constants import ModelTier
from ai.shared.errors import LLMProviderError, MissingAPIKeyError
from ai.shared.logger import ai_logger
from ai.shared.output_validator import OutputValidationError, validate_output


class LLMGateway:
    """Resolves a ModelTier + optional schema to a validated response."""

    def __init__(self, settings: Optional[LLMSettings] = None):
        self.settings = settings or get_llm_settings()
        self._selfhosted = SelfHostedProvider(self.settings)
        self._groq = GroqProvider(self.settings)
        self._openrouter = OpenRouterProvider(self.settings)
        self._mock = MockProvider()

    def _fallback_provider(self) -> Optional[BaseLLMProvider]:
        choice = self.settings.resolve_fallback_backend()
        if choice == "groq":
            return self._groq
        if choice == "openrouter":
            return self._openrouter
        return None

    def _model_for(self, provider: BaseLLMProvider, tier: ModelTier) -> str:
        """Resolve the right model name for whichever backend answers this call.

        This is the fix for the pre-existing inconsistency where idea_validation
        and market_research agents hardcoded `settings.groq_model_heavy` while
        research_patent agents hardcoded `settings.openrouter_model_heavy` —
        whichever provider actually ends up serving the call now gets its own
        correct model name, regardless of which tier the caller asked for.
        """
        s = self.settings
        if provider is self._selfhosted:
            return s.llm_model_fast if tier == ModelTier.FAST else s.llm_model_heavy
        if provider is self._groq:
            return s.groq_model_fast if tier == ModelTier.FAST else s.groq_model_heavy
        if provider is self._openrouter:
            return s.openrouter_model_fast if tier == ModelTier.FAST else s.openrouter_model_heavy
        return "mock"

    def _ordered_providers(self, allow_mock_fallback: bool):
        yield self._selfhosted
        fallback = self._fallback_provider()
        if fallback is not None:
            yield fallback
        if allow_mock_fallback:
            yield self._mock

    def invoke(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        tier: ModelTier = ModelTier.HEAVY,
        temperature: float = 0.2,
        max_tokens: Optional[int] = 4096,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        schema_class: Optional[Type[BaseModel]] = None,
        allow_mock_fallback: bool = True,
    ) -> str:
        """Return raw text from whichever provider answers first in the chain.

        Raises MissingAPIKeyError if every stage (including mock, if disabled)
        is unavailable or fails — mirrors the old call_live_llm contract so
        existing callers' error handling keeps working unchanged.
        """
        timeout = timeout if timeout is not None else self.settings.llm_default_timeout_seconds
        max_retries = max_retries if max_retries is not None else self.settings.llm_max_retries

        attempted = []
        for provider in self._ordered_providers(allow_mock_fallback):
            if not provider.is_configured():
                continue
            attempted.append(provider.name)
            try:
                response = provider.complete(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model=self._model_for(provider, tier),
                    tier=tier,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout,
                    max_retries=max_retries,
                    schema_class=schema_class,
                )
                if provider is not self._mock:
                    ai_logger.info(f"LLM call served by '{provider.name}' (tier={tier.value}, model={response.model})")
                else:
                    ai_logger.warning(
                        "LLM call fell through to the mock provider — no self-hosted or "
                        "fallback backend was configured/reachable. This should not happen "
                        "outside local dev/CI."
                    )
                return strip_think_blocks(response.text)
            except ProviderUnavailableError:
                continue
            except ProviderRequestError as err:
                ai_logger.warning(f"Provider '{provider.name}' failed, falling through: {err}")
                continue

        raise MissingAPIKeyError(
            key_name="LLM_BASE_URL, GROQ_API_KEY, or OPENROUTER_API_KEY",
            provider_name=f"LLM gateway (attempted: {attempted or 'none configured'})",
        )

    def invoke_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema_class: Type[BaseModel],
        tier: ModelTier = ModelTier.HEAVY,
        temperature: float = 0.2,
        max_tokens: Optional[int] = 4096,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        repair_attempts: Optional[int] = None,
        allow_mock_fallback: bool = True,
    ) -> BaseModel:
        """Invoke, parse, validate, and — on schema failure — retry with the
        validation errors fed back to the model, bounded by `repair_attempts`.

        This replaces the current behaviour where one bad field raises
        OutputValidationError straight out of a 20-call, multi-minute pipeline
        run (backend/api/routers/analysis.py's bare `except Exception`).
        """
        repair_attempts = repair_attempts if repair_attempts is not None else self.settings.llm_repair_attempts

        current_user_prompt = user_prompt
        last_raw: Optional[str] = None
        last_error: Optional[OutputValidationError] = None

        for attempt in range(repair_attempts + 1):
            raw = self.invoke(
                system_prompt=system_prompt,
                user_prompt=current_user_prompt,
                tier=tier,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
                max_retries=max_retries,
                schema_class=schema_class,
                allow_mock_fallback=allow_mock_fallback,
            )
            try:
                return validate_output(raw, schema_class)
            except OutputValidationError as err:
                last_raw, last_error = raw, err
                if attempt < repair_attempts:
                    ai_logger.warning(
                        f"{schema_class.__name__} validation failed on attempt {attempt + 1}"
                        f"/{repair_attempts + 1}; retrying with a repair prompt."
                    )
                    current_user_prompt = build_repair_prompt(
                        user_prompt, raw, err.details.get("field_errors", [])
                    )

        assert last_error is not None  # loop always runs at least once
        raise last_error


_gateway_instance: Optional[LLMGateway] = None


def get_gateway(reload: bool = False) -> LLMGateway:
    """Process-wide LLMGateway singleton."""
    global _gateway_instance
    if _gateway_instance is None or reload:
        _gateway_instance = LLMGateway()
    return _gateway_instance


def invoke(**kwargs) -> str:
    """Module-level convenience wrapper over get_gateway().invoke(...)."""
    return get_gateway().invoke(**kwargs)
