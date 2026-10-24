# Final Report Generator

**Crew:** [Executive Reporting](../phases/12-executive-reporting.md) (RPT) · **Role:** Investor Pack · **Status:** 🟢 IMPLEMENTED (crew-level)

## Implementation

This agent is a role inside the **Executive Reporting** crew, which runs as one
structured LLM call (`ai/crews/spec_runner.py::run_spec_crew`) validated
against the crew's result schema in `ai/schemas/`. The agent is not a
separate call; this document and the
[Phase 12](../phases/12-executive-reporting.md) doc are part of the
crew's system prompt. Crew code: `ai/crews/reporting/`.

## Where this fits

Part of the **Executive Reporting** crew (Synthesis), agent 66 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
