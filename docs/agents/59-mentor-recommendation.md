# Mentor Recommendation

**Crew:** [Community & Ecosystem](../phases/11-community-and-ecosystem.md) (COMM) · **Role:** Mentor Matching · **Status:** ⚪ SPECIFIED

## Implementation

**Not built.** `ai/crews/community/tasks.py` returns a hardcoded literal
result for the whole Community & Ecosystem crew — no LLM call, no per-agent
reasoning. This document describes the *intended* behavior so it can be
implemented against a real spec rather than invented at build time.

Building this agent means: a Pydantic output schema in `ai/schemas/`, a
system prompt in `ai/prompts/community/`, and a `get_*_agent()` /
`run_*_agent()` pair following the pattern in
`ai/agents/idea_validation/startup_idea_analyzer.py` (the reference
implementation — see [Phase 11](../phases/11-community-and-ecosystem.md)).

## Where this fits

Part of the **Community & Ecosystem** crew (Network), agent 59 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
