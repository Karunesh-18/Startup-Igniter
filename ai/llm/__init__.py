"""Provider-agnostic LLM gateway.

Provider chain:

    selfhosted (DGX B200 / vLLM, OpenAI-compatible)
        -> mock (offline, deterministic; only if LLM_ALLOW_MOCK=true)

See ``ai/llm/gateway.py`` for the public entry point.
"""

from ai.llm.gateway import LLMGateway, get_gateway, invoke

__all__ = ["LLMGateway", "get_gateway", "invoke"]
