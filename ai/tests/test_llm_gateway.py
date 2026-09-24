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
    """With both selfhosted and Groq configured, selfhosted answers the call."""
    settings = LLMSettings(LLM_BASE_URL="http://dgx-b200:8000/v1", GROQ_API_KEY="gsk_test")
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


def test_falls_through_to_groq_when_selfhosted_unreachable(httpx_mock):
    """A configured-but-unreachable self-hosted endpoint falls through to Groq
    rather than surfacing a raw connection error to the caller."""
    settings = LLMSettings(
        LLM_BASE_URL="http://dgx-b200:8000/v1",
        GROQ_API_KEY="gsk_test",
        LLM_MAX_RETRIES=1,
    )
    httpx_mock.add_exception(
        httpx.ConnectError("connection refused"),
        url="http://dgx-b200:8000/v1/chat/completions",
    )
    httpx_mock.add_response(
        url="https://api.groq.com/openai/v1/chat/completions",
        json=_openai_response('{"served_by": "groq"}'),
    )

    gw = LLMGateway(settings=settings)
    result = gw.invoke(system_prompt="sys", user_prompt="user", tier=ModelTier.HEAVY, max_retries=1)

    assert result == '{"served_by": "groq"}'


def test_falls_through_to_mock_when_nothing_configured():
    """No selfhosted, no fallback keys -> mock provider answers rather than crashing."""
    settings = LLMSettings(LLM_BASE_URL=None, GROQ_API_KEY=None, OPENROUTER_API_KEY=None)
    gw = LLMGateway(settings=settings)
    result = gw.invoke(system_prompt="sys", user_prompt="user")
    assert result  # non-empty JSON text from MockProvider


def test_raises_missing_api_key_when_mock_disabled_and_nothing_configured():
    settings = LLMSettings(LLM_BASE_URL=None, GROQ_API_KEY=None, OPENROUTER_API_KEY=None)
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


def test_groq_uses_json_object_mode_not_json_schema(httpx_mock):
    """Groq only supports json_object mode, not full json_schema — the gateway
    must not send a response_format shape Groq will reject."""
    settings = LLMSettings(LLM_BASE_URL=None, GROQ_API_KEY="gsk_test")
    httpx_mock.add_response(
        url="https://api.groq.com/openai/v1/chat/completions",
        json=_openai_response('{"summary": "ok", "score": 50}'),
    )

    gw = LLMGateway(settings=settings)
    gw.invoke(system_prompt="sys", user_prompt="user", schema_class=_DummySchema)

    sent_payload = json.loads(httpx_mock.get_requests()[0].content)
    assert sent_payload["response_format"] == {"type": "json_object"}


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
