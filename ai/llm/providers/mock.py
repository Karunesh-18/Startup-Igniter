"""Offline provider: no network calls, deterministic schema-conformant output.

This is the last stage of the resolution chain (selfhosted -> fallback ->
mock) and also what `LLM_BACKEND=mock` forces directly for CI/tests. Most
agents already have their own hand-written mock JSON branches that bypass
the gateway entirely when `mock_mode=True` is passed at the call site (see
e.g. ai/agents/market_research/market_research_agent.py) — this provider is
the safety net for callers that reach the gateway without a bespoke mock
branch of their own, and for the eval harness baseline.
"""

import json
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel

from ai.llm.providers.base import BaseLLMProvider, LLMResponse
from ai.llm.structured import generate_mock_json


class MockProvider(BaseLLMProvider):
    """Always configured; never makes a network call."""

    name = "mock"

    def is_configured(self) -> bool:
        return True

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
        if schema_class is not None:
            payload: Dict[str, Any] = generate_mock_json(schema_class)
        else:
            payload = {"result": "mock response", "mock": True}
        return LLMResponse(text=json.dumps(payload), provider=self.name, model="mock")
