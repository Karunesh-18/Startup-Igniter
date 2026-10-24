# Financial Model Agent

**Crew:** [Business Planning](../phases/05-business-planning.md) (BIZ) · **Role:** Unit Economics · **Status:** 🟢 IMPLEMENTED (crew-level)

## Implementation

This agent is a role inside the **Business Planning** crew, which runs as one
structured LLM call (`ai/crews/spec_runner.py::run_spec_crew`) validated
against the crew's result schema in `ai/schemas/`. The agent is not a
separate call; this document and the
[Phase 05](../phases/05-business-planning.md) doc are part of the
crew's system prompt. Crew code: `ai/crews/business_planning/`.

## Where this fits

Part of the **Business Planning** crew (Strategy), agent 27 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
