"""Tests for the provider-agnostic LLM gateway (ai/llm/).

Uses pytest-httpx to stub the OpenAI-compatible HTTP layer so these run
without any real network access or API keys — exactly the "pytest with a
stubbed OpenAI-compatible server" verification called for in the migration
plan for Workstream A.
"""

import json

import httpx
import pytest
from pydantic import BaseModel, Field

from ai.llm.gateway import LLMGateway
from ai.llm.settings import LLMSettings
from ai.llm.structured import generate_mock_json, strip_think_blocks
from ai.shared.constants import ModelTier
from ai.shared.errors import MissingAPIKeyError


class _DummySchema(BaseModel):
    """Minimal schema used to exercise schema-aware code paths in isolation."""

    summary: str = Field(..., min_length=1)
    score: int = Field(..., ge=0, le=100)


def _openai_response(content: str) -> dict:
    return {"choices": [{"message": {"content": content}}]}


def test_selfhosted_is_tried_first_when_configured(httpx_mock):
    """With selfhosted configured, selfhosted answers the call (not mock)."""
    settings = LLMSettings(LLM_BASE_URL="http://dgx-b200:8000/v1")
    httpx_mock.add_response(
        url="http://dgx-b200:8000/v1/chat/completions",
        json=_openai_response('{"ok": true}'),
    )

    gw = LLMGateway(settings=settings)
    result = gw.invoke(system_prompt="sys", user_prompt="user", tier=ModelTier.HEAVY)

    assert result == '{"ok": true}'
    requests = httpx_mock.get_requests()
    assert len(requests) == 1
    assert requests[0].url.host == "dgx-b200"


def test_falls_through_to_mock_when_selfhosted_unreachable(httpx_mock):
    """A configured-but-unreachable self-hosted endpoint falls through to mock
    (LLM_ALLOW_MOCK defaults true) rather than surfacing a raw connection error."""
    settings = LLMSettings(LLM_BASE_URL="http://dgx-b200:8000/v1", LLM_MAX_RETRIES=1)
    httpx_mock.add_exception(
        httpx.ConnectError("connection refused"),
        url="http://dgx-b200:8000/v1/chat/completions",
    )

    gw = LLMGateway(settings=settings)
    result = gw.invoke(system_prompt="sys", user_prompt="user", tier=ModelTier.HEAVY, max_retries=1)

    assert json.loads(result)["mock"] is True


def test_raises_when_selfhosted_unreachable_and_llm_allow_mock_false(httpx_mock):
    """LLM_ALLOW_MOCK=false (production) turns an outage into a loud error."""
    settings = LLMSettings(LLM_BASE_URL="http://dgx-b200:8000/v1", LLM_MAX_RETRIES=1, LLM_ALLOW_MOCK=False)
    httpx_mock.add_exception(
        httpx.ConnectError("connection refused"),
        url="http://dgx-b200:8000/v1/chat/completions",
    )

    gw = LLMGateway(settings=settings)
    with pytest.raises(MissingAPIKeyError):
        gw.invoke(system_prompt="sys", user_prompt="user", max_retries=1)


def test_fast_tier_uses_separate_base_url_when_configured(httpx_mock):
    """Qwen3-32B and Qwen3-8B run as two separate vLLM servers (one base
    model per process) -- LLM_BASE_URL_FAST routes FAST-tier calls to the
    8B server while HEAVY/REASONING stay on the primary URL."""
    settings = LLMSettings(
        LLM_BASE_URL="http://dgx-b200:8001/v1",
        LLM_BASE_URL_FAST="http://dgx-b200:8002/v1",
    )
    httpx_mock.add_response(
        url="http://dgx-b200:8001/v1/chat/completions", json=_openai_response('{"served_by": "heavy"}')
    )
    httpx_mock.add_response(
        url="http://dgx-b200:8002/v1/chat/completions", json=_openai_response('{"served_by": "fast"}')
    )

    gw = LLMGateway(settings=settings)
    heavy_result = gw.invoke(system_prompt="sys", user_prompt="user", tier=ModelTier.HEAVY)
    fast_result = gw.invoke(system_prompt="sys", user_prompt="user", tier=ModelTier.FAST)

    assert heavy_result == '{"served_by": "heavy"}'
    assert fast_result == '{"served_by": "fast"}'


def test_fast_tier_falls_back_to_primary_url_when_no_separate_one_configured(httpx_mock):
    """A single-server setup (no LLM_BASE_URL_FAST) keeps working unchanged --
    both tiers hit the same base_url."""
    settings = LLMSettings(LLM_BASE_URL="http://dgx-b200:8000/v1", LLM_BASE_URL_FAST=None)
    httpx_mock.add_response(
        url="http://dgx-b200:8000/v1/chat/completions", json=_openai_response('{"ok": true}')
    )

    gw = LLMGateway(settings=settings)
    result = gw.invoke(system_prompt="sys", user_prompt="user", tier=ModelTier.FAST)

    assert result == '{"ok": true}'


def test_401_fails_fast_without_retrying(httpx_mock):
    """A 401 (invalid/revoked key) must not be retried -- retrying can never
    succeed, and doing it anyway wastes ~12s of exponential backoff on every
    single call (found while smoke-testing the training corpus generator
    against a real, since-revoked key)."""
    settings = LLMSettings(LLM_BASE_URL="http://dgx-b200:8000/v1", LLM_API_KEY="invalid", LLM_MAX_RETRIES=4)
    httpx_mock.add_response(
        url="http://dgx-b200:8000/v1/chat/completions",
        status_code=401,
        json={"error": {"message": "Invalid API Key"}},
    )

    gw = LLMGateway(settings=settings)
    result = gw.invoke(system_prompt="sys", user_prompt="user")  # falls through to mock

    assert result  # mock provider answered
    # Exactly one request was made -- no retries on a 401.
    assert len(httpx_mock.get_requests()) == 1


def test_429_still_retries_with_backoff(httpx_mock):
    """429 (rate limit) is the case retrying legitimately helps -- must not
    be caught by the same fast-fail path as 401/403/404/422."""
    settings = LLMSettings(LLM_BASE_URL="http://dgx-b200:8000/v1", LLM_MAX_RETRIES=2)
    httpx_mock.add_response(url="http://dgx-b200:8000/v1/chat/completions", status_code=429)
    httpx_mock.add_response(
        url="http://dgx-b200:8000/v1/chat/completions",
        json=_openai_response('{"ok": true}'),
    )

    gw = LLMGateway(settings=settings)
    result = gw.invoke(system_prompt="sys", user_prompt="user", max_retries=2)

    assert result == '{"ok": true}'
    assert len(httpx_mock.get_requests()) == 2


def test_falls_through_to_mock_when_nothing_configured():
    """No selfhosted -> mock provider answers rather than crashing."""
    settings = LLMSettings(LLM_BASE_URL=None, LLM_ALLOW_MOCK=True)
    gw = LLMGateway(settings=settings)
    result = gw.invoke(system_prompt="sys", user_prompt="user")
    assert result  # non-empty JSON text from MockProvider


def test_raises_missing_api_key_when_mock_disabled_and_nothing_configured():
    settings = LLMSettings(LLM_BASE_URL=None, LLM_ALLOW_MOCK=True)
    gw = LLMGateway(settings=settings)
    with pytest.raises(MissingAPIKeyError):
        gw.invoke(system_prompt="sys", user_prompt="user", allow_mock_fallback=False)


def test_schema_class_produces_json_schema_response_format_for_selfhosted(httpx_mock):
    """The self-hosted provider requests guided decoding via response_format
    when a schema_class is supplied — the core of the "structured output"
    half of Workstream A."""
    settings = LLMSettings(LLM_BASE_URL="http://dgx-b200:8000/v1", LLM_GUIDED_DECODING=True)
    httpx_mock.add_response(
        url="http://dgx-b200:8000/v1/chat/completions",
        json=_openai_response('{"summary": "ok", "score": 50}'),
    )

    gw = LLMGateway(settings=settings)
    gw.invoke(system_prompt="sys", user_prompt="user", schema_class=_DummySchema)

    sent_payload = json.loads(httpx_mock.get_requests()[0].content)
    assert sent_payload["response_format"]["type"] == "json_schema"
    assert sent_payload["response_format"]["json_schema"]["name"] == "_DummySchema"
    assert "score" in sent_payload["response_format"]["json_schema"]["schema"]["properties"]


def test_invoke_structured_repairs_on_validation_failure(httpx_mock):
    """First response is missing a required field; the gateway resends with the
    validation errors folded into the prompt and succeeds on the retry."""
    settings = LLMSettings(LLM_BASE_URL="http://dgx-b200:8000/v1")
    httpx_mock.add_response(
        url="http://dgx-b200:8000/v1/chat/completions",
        json=_openai_response('{"summary": "missing score"}'),
    )
    httpx_mock.add_response(
        url="http://dgx-b200:8000/v1/chat/completions",
        json=_openai_response('{"summary": "fixed", "score": 75}'),
    )

    gw = LLMGateway(settings=settings)
    result = gw.invoke_structured(
        system_prompt="sys", user_prompt="user", schema_class=_DummySchema, repair_attempts=1
    )

    assert isinstance(result, _DummySchema)
    assert result.score == 75
    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    second_request_body = json.loads(requests[1].content)
    assert "Validation errors" in second_request_body["messages"][1]["content"]


def test_invoke_structured_raises_after_exhausting_repair_attempts(httpx_mock):
    settings = LLMSettings(LLM_BASE_URL="http://dgx-b200:8000/v1")
    httpx_mock.add_response(
        url="http://dgx-b200:8000/v1/chat/completions",
        json=_openai_response('{"summary": "still missing score"}'),
    )
    httpx_mock.add_response(
        url="http://dgx-b200:8000/v1/chat/completions",
        json=_openai_response('{"summary": "still missing score"}'),
    )

    gw = LLMGateway(settings=settings)
    from ai.shared.errors import OutputValidationError

    with pytest.raises(OutputValidationError):
        gw.invoke_structured(
            system_prompt="sys", user_prompt="user", schema_class=_DummySchema, repair_attempts=1
        )


def test_strip_think_blocks_removes_reasoning():
    raw = "<think>let me reason about braces {like this}</think>{\"summary\": \"ok\", \"score\": 1}"
    assert strip_think_blocks(raw) == '{"summary": "ok", "score": 1}'


def test_strip_think_blocks_noop_without_think_tag():
    raw = '{"summary": "ok", "score": 1}'
    assert strip_think_blocks(raw) == raw


def test_generate_mock_json_conforms_to_schema():
    payload = generate_mock_json(_DummySchema)
    validated = _DummySchema.model_validate(payload)
    assert 0 <= validated.score <= 100


def test_generate_mock_json_self_corrects_custom_enum_validators():
    """Some real schemas (e.g. ProblemStatementAnalysis.problem_severity) use a
    plain `str` field plus a @field_validator raising "must be one of {...}"
    rather than a Literal type — generate_mock_json must still produce a
    validating payload for these, not just for ge/le-bounded numerics."""
    from ai.schemas.problem_statement import ProblemStatementAnalysis

    payload = generate_mock_json(ProblemStatementAnalysis)
    validated = ProblemStatementAnalysis.model_validate(payload)
    assert validated.problem_severity in {"low", "medium", "high", "critical"}
