"""Streaming chat against the self-hosted vLLM server (OpenAI-compatible SSE)."""

import json
from typing import Dict, Iterator, List

import httpx

from ai.llm.settings import get_llm_settings
from ai.llm.structured import strip_think_blocks
from ai.shared.constants import ModelTier
from ai.shared.errors import MissingAPIKeyError


def stream_chat(
    messages: List[Dict[str, str]], tier: ModelTier = ModelTier.HEAVY, max_tokens: int = 900, temperature: float = 0.5
) -> Iterator[str]:
    """Yield content deltas. Thinking is disabled (chat should answer, not deliberate)."""
    s = get_llm_settings()
    if not s.has_selfhosted:
        raise MissingAPIKeyError(key_name="LLM_BASE_URL", provider_name="self-hosted LLM")
    headers = {"Content-Type": "application/json"}
    if s.llm_api_key:
        headers["Authorization"] = f"Bearer {s.llm_api_key}"
    payload = {
        "model": s.llm_model_fast if tier == ModelTier.FAST else s.llm_model_heavy,
        "messages": messages, "stream": True, "temperature": temperature, "max_tokens": max_tokens,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    url = f"{s.selfhosted_base_url_for_tier(tier).rstrip('/')}/chat/completions"
    in_think = False
    with httpx.stream("POST", url, headers=headers, json=payload, timeout=httpx.Timeout(120, connect=10)) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                return
            delta = (json.loads(data)["choices"][0].get("delta") or {}).get("content")
            if not delta:
                continue
            # Belt and braces: drop a <think> block if the server emits one anyway.
            if "<think>" in delta:
                in_think = True
            if not in_think:
                yield delta
            if "</think>" in delta:
                in_think = False
                tail = strip_think_blocks(delta)
                if tail:
                    yield tail
