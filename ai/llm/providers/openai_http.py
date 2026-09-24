"""Shared OpenAI-compatible chat-completions client.

Self-hosted vLLM, Groq, and OpenRouter all speak the same `/chat/completions`
shape. This is the one retry ladder every real provider uses, so fixing a bug
here (timeout handling, retry backoff, empty-content detection) fixes it
everywhere instead of in three copy-pasted implementations.
"""

import time
from typing import Any, Dict, Optional, Type

import httpx
from pydantic import BaseModel

from ai.llm.providers.base import LLMResponse, ProviderRequestError
from ai.shared.logger import ai_logger

# Client errors where retrying literally cannot help: an invalid/revoked key
# (401/403), a malformed request the same payload will always fail (400/422),
# or a URL/model that doesn't exist (404). 429 (rate limit) and 5xx (server-side,
# often transient) are handled by the retry-with-backoff path above instead.
_NON_RETRYABLE_STATUS_CODES = frozenset({400, 401, 403, 404, 422})


def build_json_schema_response_format(schema_class: Type[BaseModel]) -> Dict[str, Any]:
    """Build an OpenAI/vLLM-style json_schema response_format from a Pydantic model.

    vLLM (xgrammar/outlines backend) and OpenAI both accept this shape to
    grammar-constrain generation, which is strictly stronger than asking
    nicely in the prompt for "pure JSON matching fields: a, b, c".
    """
    schema = schema_class.model_json_schema()
    # vLLM's guided-decoding backends are stricter than OpenAI's about
    # `additionalProperties` — disallow extra keys so the grammar stays tight.
    schema.setdefault("additionalProperties", False)
    return {
        "type": "json_schema",
        "json_schema": {
            "name": schema_class.__name__,
            "schema": schema,
            "strict": True,
        },
    }


def chat_completion(
    *,
    base_url: str,
    headers: Dict[str, str],
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_tokens: Optional[int] = 4096,
    timeout: float = 60.0,
    max_retries: int = 4,
    response_format: Optional[Dict[str, Any]] = None,
    provider_label: str = "openai-compatible",
) -> str:
    """POST one chat completion with bounded retries. Returns raw message content.

    Unlike the legacy `call_live_llm`, this:
      - honours the caller's `timeout` instead of a hardcoded 35s
      - never silently swaps to a smaller model on later attempts — a caller
        asked for a specific model and getting a worse one back with no
        signal is worse than a clean failure
      - raises ProviderRequestError on exhaustion instead of returning ""
        (an empty string that later fails JSON parsing with a confusing
        error is strictly worse than a clear "this provider failed")
    """
    url = f"{base_url.rstrip('/')}/chat/completions"
    httpx_timeout = httpx.Timeout(timeout, connect=min(10.0, timeout))

    payload: Dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if response_format is not None:
        payload["response_format"] = response_format

    last_error: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=httpx_timeout) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code in (429, 503):
                    if attempt == max_retries - 1:
                        res.raise_for_status()
                    sleep_sec = 2.0 * (attempt + 1)
                    ai_logger.warning(
                        f"{provider_label} rate-limited/busy ({res.status_code}) for '{model}'. "
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
                    f"{provider_label} returned empty content for '{model}'. "
                    f"Retrying (attempt {attempt + 1}/{max_retries})..."
                )
                time.sleep(1.5)
        except httpx.HTTPStatusError as exc:
            last_error = exc
            err_msg = exc.response.text if exc.response is not None else str(exc)
            status = exc.response.status_code if exc.response is not None else None
            if status in _NON_RETRYABLE_STATUS_CODES:
                # An invalid/revoked key, a malformed request, or a missing
                # resource will not succeed on retry -- failing fast here is
                # the fix for a real bug found during corpus generation: this
                # used to retry a 401 three times with exponential backoff
                # (~12s wasted) on every single call before falling through.
                ai_logger.error(
                    f"{provider_label} HTTP {status} (non-retryable): {err_msg}"
                )
                break
            if attempt == max_retries - 1:
                ai_logger.error(f"{provider_label} HTTP error ({status}): {err_msg}")
                break
            sleep_sec = 2.0 * (attempt + 1)
            ai_logger.warning(
                f"{provider_label} HTTP {status} ({err_msg}). "
                f"Retrying in {sleep_sec:.1f}s (attempt {attempt + 1}/{max_retries})..."
            )
            time.sleep(sleep_sec)
        except httpx.RequestError as exc:
            last_error = exc
            if attempt == max_retries - 1:
                ai_logger.error(f"{provider_label} network request failed: {exc}")
                break
            sleep_sec = 2.0 * (attempt + 1)
            ai_logger.warning(
                f"{provider_label} network request error ({exc}). "
                f"Retrying in {sleep_sec:.1f}s (attempt {attempt + 1}/{max_retries})..."
            )
            time.sleep(sleep_sec)

    raise ProviderRequestError(
        f"{provider_label} exhausted {max_retries} attempts calling model '{model}'.",
        details={"provider": provider_label, "model": model, "error": str(last_error) if last_error else None},
    )
