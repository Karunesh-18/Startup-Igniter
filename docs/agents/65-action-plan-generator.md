# Action Plan Generator

**Crew:** [Executive Reporting](../phases/12-executive-reporting.md) (RPT) · **Role:** 30-60-90 Day Plan · **Status:** ⚪ SPECIFIED

## Implementation

**Not built.** `ai/crews/reporting/tasks.py` returns a hardcoded literal
result for the whole Executive Reporting crew — no LLM call, no per-agent
reasoning. This document describes the *intended* behavior so it can be
implemented against a real spec rather than invented at build time.

Building this agent means: a Pydantic output schema in `ai/schemas/`, a
system prompt in `ai/prompts/reporting/`, and a `get_*_agent()` /
`run_*_agent()` pair following the pattern in
`ai/agents/idea_validation/startup_idea_analyzer.py` (the reference
implementation — see [Phase 12](../phases/12-executive-reporting.md)).

## Where this fits

Part of the **Executive Reporting** crew (Synthesis), agent 65 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
