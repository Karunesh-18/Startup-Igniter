# Brand & Marketing Agent

**Crew:** [Branding & Marketing](../phases/08-branding-and-marketing.md) (BRND) · **Role:** Brand Positioning · **Status:** ⚪ SPECIFIED

## Implementation

**Not built.** `ai/crews/branding_marketing/tasks.py` returns a hardcoded literal
result for the whole Branding & Marketing crew — no LLM call, no per-agent
reasoning. This document describes the *intended* behavior so it can be
implemented against a real spec rather than invented at build time.

Building this agent means: a Pydantic output schema in `ai/schemas/`, a
system prompt in `ai/prompts/branding_marketing/`, and a `get_*_agent()` /
`run_*_agent()` pair following the pattern in
`ai/agents/idea_validation/startup_idea_analyzer.py` (the reference
implementation — see [Phase 08](../phases/08-branding-and-marketing.md)).

## Where this fits

Part of the **Branding & Marketing** crew (Identity), agent 44 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
