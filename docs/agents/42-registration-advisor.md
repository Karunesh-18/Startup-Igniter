# Registration Advisor

**Crew:** [Legal & Compliance](../phases/07-legal-and-compliance.md) (LGL) · **Role:** Incorporation · **Status:** 🟢 IMPLEMENTED (crew-level)

## Implementation

This agent is a role inside the **Legal & Compliance** crew, which runs as one
structured LLM call (`ai/crews/spec_runner.py::run_spec_crew`) validated
against the crew's result schema in `ai/schemas/`. The agent is not a
separate call; this document and the
[Phase 07](../phases/07-legal-and-compliance.md) doc are part of the
crew's system prompt. Crew code: `ai/crews/legal_compliance/`.

## Where this fits

Part of the **Legal & Compliance** crew (Compliance), agent 42 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
