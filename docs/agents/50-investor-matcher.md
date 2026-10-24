# Investor Matcher

**Crew:** [Funding Readiness](../phases/09-funding-readiness.md) (FUND) · **Role:** Investor Fit · **Status:** 🟢 IMPLEMENTED (crew-level)

## Implementation

This agent is a role inside the **Funding Readiness** crew, which runs as one
structured LLM call (`ai/crews/spec_runner.py::run_spec_crew`) validated
against the crew's result schema in `ai/schemas/`. The agent is not a
separate call; this document and the
[Phase 09](../phases/09-funding-readiness.md) doc are part of the
crew's system prompt. Crew code: `ai/crews/funding/`.

## Where this fits

Part of the **Funding Readiness** crew (Capital), agent 50 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
