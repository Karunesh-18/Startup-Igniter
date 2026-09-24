# Pricing Strategy Agent

**Crew:** [Business Planning](../phases/05-business-planning.md) (BIZ) · **Role:** Pricing Tiers · **Status:** ⚪ SPECIFIED

## Implementation

**Not built.** `ai/crews/business_planning/tasks.py` returns a hardcoded literal
result for the whole Business Planning crew — no LLM call, no per-agent
reasoning. This document describes the *intended* behavior so it can be
implemented against a real spec rather than invented at build time.

Building this agent means: a Pydantic output schema in `ai/schemas/`, a
system prompt in `ai/prompts/business_planning/`, and a `get_*_agent()` /
`run_*_agent()` pair following the pattern in
`ai/agents/idea_validation/startup_idea_analyzer.py` (the reference
implementation — see [Phase 05](../phases/05-business-planning.md)).

## Where this fits

Part of the **Business Planning** crew (Strategy), agent 30 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
