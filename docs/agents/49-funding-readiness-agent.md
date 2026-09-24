# Funding Readiness Agent

**Crew:** [Funding Readiness](../phases/09-funding-readiness.md) (FUND) · **Role:** Pitch Deck · **Status:** ⚪ SPECIFIED

## Implementation

**Not built.** `ai/crews/funding/tasks.py` returns a hardcoded literal
result for the whole Funding Readiness crew — no LLM call, no per-agent
reasoning. This document describes the *intended* behavior so it can be
implemented against a real spec rather than invented at build time.

Building this agent means: a Pydantic output schema in `ai/schemas/`, a
system prompt in `ai/prompts/funding/`, and a `get_*_agent()` /
`run_*_agent()` pair following the pattern in
`ai/agents/idea_validation/startup_idea_analyzer.py` (the reference
implementation — see [Phase 09](../phases/09-funding-readiness.md)).

## Where this fits

Part of the **Funding Readiness** crew (Capital), agent 49 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
