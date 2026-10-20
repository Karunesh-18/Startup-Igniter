# Legal Summary

**Crew:** [Legal & Compliance](../phases/07-legal-and-compliance.md) (LGL) · **Role:** Legal Synthesis · **Status:** ⚪ SPECIFIED

## Implementation

**Not built.** `ai/crews/legal_compliance/tasks.py` returns a hardcoded literal
result for the whole Legal & Compliance crew — no LLM call, no per-agent
reasoning. This document describes the *intended* behavior so it can be
implemented against a real spec rather than invented at build time.

Building this agent means: a Pydantic output schema in `ai/schemas/`, a
system prompt in `ai/prompts/legal_compliance/`, and a `get_*_agent()` /
`run_*_agent()` pair following the pattern in
`ai/agents/idea_validation/startup_idea_analyzer.py` (the reference
implementation — see [Phase 07](../phases/07-legal-and-compliance.md)).

## Where this fits

Part of the **Legal & Compliance** crew (Compliance), agent 43 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
