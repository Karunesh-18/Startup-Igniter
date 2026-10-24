"""Provider-agnostic LLM gateway: the one place that decides which backend
answers a call and enforces structured output.

Resolution order per call: selfhosted -> mock. Mock is only used when the
caller allows it AND settings.llm_allow_mock is true (LLM_ALLOW_MOCK; prod
should set false so an outage raises instead of returning placeholders).
"""

from typing import Optional, Type

from pydantic import BaseModel, ValidationError

from ai.llm.providers.base import BaseLLMProvider, ProviderRequestError, ProviderUnavailableError
from ai.llm.providers.mock import MockProvider
from ai.llm.providers.selfhosted import SelfHostedProvider
from ai.llm.settings import LLMSettings, get_llm_settings
from ai.llm.structured import build_repair_prompt, strip_think_blocks
from ai.shared.constants import ModelTier
from ai.shared.errors import LLMProviderError, MissingAPIKeyError
from ai.shared.logger import ai_logger
from ai.shared.progress import current_run
from ai.shared.output_validator import OutputValidationError, validate_output


# Every monetary figure the product shows is in Indian rupees.
CURRENCY_RULE = (
    "Currency: express every monetary figure in Indian rupees (use the symbol ₹, with lakh/crore for large "
    "amounts). If a source quotes another currency, convert at an approximate rate and keep the original in "
    "parentheses, e.g. ₹35,000 Cr ($4.2B)."
)


class LLMGateway:
    """Resolves a ModelTier + optional schema to a validated response."""

    def __init__(self, settings: Optional[LLMSettings] = None):
        self.settings = settings or get_llm_settings()
        self._selfhosted = SelfHostedProvider(self.settings)
        self._mock = MockProvider()

    def _model_for(self, tier: ModelTier) -> str:
        s = self.settings
        return s.llm_model_fast if tier == ModelTier.FAST else s.llm_model_heavy

    def _ordered_providers(self, allow_mock_fallback: bool):
        yield self._selfhosted
        if allow_mock_fallback and self.settings.llm_allow_mock:
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
        # Callers' hardcoded timeouts (45-60s) are too short for the 32B under shared load: use them as a floor.
        timeout = max(timeout or 0.0, self.settings.llm_default_timeout_seconds)
        run = current_run()
        label = schema_class.__name__ if schema_class else None
        if run and label:
            run.emit(type="agent", agent=label, status="start")
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
                    model="mock" if provider is self._mock else self._model_for(tier),
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
                    if run := current_run():
                        run.used_mock = True
                    ai_logger.warning(
                        "LLM call fell through to the mock provider — the self-hosted backend "
                        "was not configured/reachable. Set LLM_ALLOW_MOCK=false in production."
                    )
                if run and label:
                    run.emit(type="agent", agent=label, status="done")
                return strip_think_blocks(response.text)
            except ProviderUnavailableError:
                continue
            except ProviderRequestError as err:
                ai_logger.warning(f"Provider '{provider.name}' failed, falling through: {err}")
                continue

        raise MissingAPIKeyError(
            key_name="LLM_BASE_URL",
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

        system_prompt = f"{system_prompt}\n\n{CURRENCY_RULE}"
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
