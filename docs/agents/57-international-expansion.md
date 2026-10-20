# International Expansion

**Crew:** [Growth & Scaling](../phases/10-growth-and-scaling.md) (GROW) · **Role:** Global Markets · **Status:** ⚪ SPECIFIED

## Implementation

**Not built.** `ai/crews/growth_scaling/tasks.py` returns a hardcoded literal
result for the whole Growth & Scaling crew — no LLM call, no per-agent
reasoning. This document describes the *intended* behavior so it can be
implemented against a real spec rather than invented at build time.

Building this agent means: a Pydantic output schema in `ai/schemas/`, a
system prompt in `ai/prompts/growth_scaling/`, and a `get_*_agent()` /
`run_*_agent()` pair following the pattern in
`ai/agents/idea_validation/startup_idea_analyzer.py` (the reference
implementation — see [Phase 10](../phases/10-growth-and-scaling.md)).

## Where this fits

Part of the **Growth & Scaling** crew (Scale), agent 57 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
