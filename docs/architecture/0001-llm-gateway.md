# ADR 0001: Provider-agnostic LLM gateway

**Status:** Implemented · **Date:** 2026-09-24

## Context

Before this migration, `ai/shared/llm_provider.py::call_live_llm` hardcoded
two provider URLs (`https://openrouter.ai/api/v1/chat/completions` and
`https://api.groq.com/openai/v1/chat/completions`) and picked between them by
which environment variable happened to be set. There was no way to point the
pipeline at a self-hosted model, no structured-output support beyond Groq's
`json_object` mode, and a silent behavior where retry attempts 2+ swapped to
a smaller "fast" model without telling the caller.

The user has an NVIDIA DGX B200 and wants inference cost to stop scaling
with token usage. The DGX is not reachable yet, so the pipeline needs to
keep working against hosted providers in the interim, with the self-hosted
path preferred the moment it's configured.

## Decision

A new `ai/llm/` package resolves every LLM call through an explicit chain:

```
selfhosted (DGX B200 / vLLM)  →  fallback (Groq or OpenRouter)  →  mock
```

Each stage is skipped if unconfigured (`is_configured() == False`); a
configured stage that fails after its own retries falls through to the next
one, logged at WARNING so a real outage is never silent. `ai/shared/llm_provider.py::call_live_llm`
is now a thin, signature-compatible shim over `LLMGateway.invoke()`, so all
~20 existing call sites kept working through the migration and moved
incrementally to passing `schema_class=`/`tier=` directly.

**Structured output.** `LLMGateway.invoke_structured()` requests
JSON-schema-guided decoding (`response_format: {"type": "json_schema", ...}`)
from the self-hosted provider — vLLM's xgrammar/outlines backend
grammar-constrains generation to the Pydantic schema, which is strictly
stronger than the previous approach of spelling out field names in prose.
Groq gets its own `json_object` mode (its actual capability); OpenRouter and
the mock provider get no structural help, relying on the bounded repair loop
below. Qwen3/DeepSeek-style `<think>...</think>` reasoning blocks are
stripped before parsing.

**Repair loop.** On `OutputValidationError`, `invoke_structured` resends the
same prompt with the model's own bad output and the exact field errors
appended, bounded by `LLM_REPAIR_ATTEMPTS` (default 2). Previously, one bad
field anywhere in a 20-call pipeline run raised straight through to the bare
`except Exception` in `backend/api/routers/analysis.py`, losing every
already-completed crew's work.

**Model resolution.** `LLMGateway._model_for(provider, tier)` resolves the
right model name for *whichever provider actually answers the call* — the
pre-migration code hardcoded `settings.groq_model_heavy` in some call sites
and `settings.openrouter_model_heavy` in others, regardless of which
provider was actually configured.

## Consequences

- Removed `LLMFactory` entirely. It only ever returned an inert `LLMConfig`
  object nothing consumed (CrewAI was never installed — see
  [ADR 0002](0002-crewai-removal.md)), while also hard-requiring
  `GROQ_API_KEY` even on the OpenRouter path and shipping a
  `get_llm(tier=...)` signature that 7 call sites got wrong (never caught
  because those callers use `run_*_agent()`, not `get_*_agent()`).
- `LLM_BACKEND` is not itself a setting — the chain is driven by which of
  `LLM_BASE_URL` / `GROQ_API_KEY` / `OPENROUTER_API_KEY` is actually set,
  plus `LLM_FALLBACK_BACKEND` (`auto`/`groq`/`openrouter`/`none`) to force a
  specific fallback choice.
- `ai/config.py::AISettings` and `backend/core/config.py::Settings` both now
  inherit `ai/llm/settings.py::LLMSettings` instead of each keeping their
  own copy — the two had already drifted (OpenRouter was primary in code but
  missing from `backend/core/config.py` and `backend/.env.example` entirely).

## Known limitations

- The repair loop is per-call. A pipeline run is still all-or-nothing at the
  crew level: if repair is exhausted for one agent, the whole multi-crew run
  fails. Making a single agent's failure degrade gracefully (skip + flag,
  rather than fail the run) is a reasonable next step once more crews are
  built (see the note in [Phase 12](../phases/12-executive-reporting.md)).
- `MockProvider`'s schema-conformant dummy generator
  (`ai.llm.structured.generate_mock_json`) self-corrects against simple
  `@field_validator`-raised enum constraints by parsing the validator's own
  error message, but has no general mechanism for arbitrary custom
  validation logic — a validator with more complex cross-field logic could
  still exhaust the mock's 5 self-correction passes and return a
  non-validating payload. This only affects the mock fallback path (nothing
  configured), never the real selfhosted/Groq/OpenRouter paths.
