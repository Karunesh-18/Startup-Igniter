"""Provider-agnostic LLM gateway.

Replaces the single hardcoded Groq/OpenRouter call path in
``ai.shared.llm_provider`` with a resolvable chain of providers:

    selfhosted (DGX B200 / vLLM, OpenAI-compatible)
        -> fallback (Groq or OpenRouter, OpenAI-compatible)
        -> mock (offline, deterministic)

See ``ai/llm/gateway.py`` for the public entry point.
"""

from ai.llm.gateway import LLMGateway, get_gateway, invoke

__all__ = ["LLMGateway", "get_gateway", "invoke"]
