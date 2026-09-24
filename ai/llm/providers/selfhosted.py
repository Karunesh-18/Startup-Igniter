"""Self-hosted, OpenAI-compatible provider — the DGX B200 / vLLM target.

Not reachable at the time of writing (per the user: "DGX not available yet").
This provider is written against a configurable `base_url` so it works
identically against:
  - a future vLLM server on the DGX serving Qwen3-32B / Qwen3-8B
  - a local stub server for development (anything speaking the same API
    shape — vLLM, llama.cpp's server, or a hand-rolled FastAPI stub)

It is simply unconfigured (`is_configured() == False`) until `LLM_BASE_URL`
is set, at which point the gateway starts trying it first.
"""

from typing import Any, Dict, Optional, Type

from pydantic import BaseModel

from ai.llm.providers.base import BaseLLMProvider, LLMResponse, ProviderUnavailableError
from ai.llm.providers.openai_http import build_json_schema_response_format, chat_completion
from ai.llm.settings import LLMSettings


class SelfHostedProvider(BaseLLMProvider):
    """OpenAI-compatible client for a self-hosted vLLM deployment."""

    name = "selfhosted"

    def __init__(self, settings: LLMSettings):
        self.settings = settings

    def is_configured(self) -> bool:
        return self.settings.has_selfhosted

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
        if not self.is_configured():
            raise ProviderUnavailableError(
                "SelfHostedProvider has no LLM_BASE_URL configured.",
                details={"provider": self.name},
            )

        headers = {"Content-Type": "application/json"}
        if self.settings.llm_api_key:
            headers["Authorization"] = f"Bearer {self.settings.llm_api_key}"

        response_format = None
        if schema_class is not None and self.settings.llm_guided_decoding:
            response_format = build_json_schema_response_format(schema_class)

        base_url = self.settings.selfhosted_base_url_for_tier(tier) if tier is not None else self.settings.llm_base_url

        text = chat_completion(
            base_url=base_url,  # type: ignore[arg-type]
            headers=headers,
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            max_retries=max_retries,
            response_format=response_format,
            provider_label="selfhosted",
        )
        return LLMResponse(text=text, provider=self.name, model=model)
