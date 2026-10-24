# Partnership Advisor

**Crew:** [Growth & Scaling](../phases/10-growth-and-scaling.md) (GROW) · **Role:** B2B Partnerships · **Status:** 🟢 IMPLEMENTED (crew-level)

## Implementation

This agent is a role inside the **Growth & Scaling** crew, which runs as one
structured LLM call (`ai/crews/spec_runner.py::run_spec_crew`) validated
against the crew's result schema in `ai/schemas/`. The agent is not a
separate call; this document and the
[Phase 10](../phases/10-growth-and-scaling.md) doc are part of the
crew's system prompt. Crew code: `ai/crews/growth_scaling/`.

## Where this fits

Part of the **Growth & Scaling** crew (Scale), agent 56 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
