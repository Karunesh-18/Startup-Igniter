# Tech Stack Advisor

**Crew:** [Product Development](../phases/06-product-development.md) (PROD) · **Role:** Stack Selection · **Status:** ⚪ SPECIFIED

## Implementation

**Not built.** `ai/crews/product_development/tasks.py` returns a hardcoded literal
result for the whole Product Development crew — no LLM call, no per-agent
reasoning. This document describes the *intended* behavior so it can be
implemented against a real spec rather than invented at build time.

Building this agent means: a Pydantic output schema in `ai/schemas/`, a
system prompt in `ai/prompts/product_development/`, and a `get_*_agent()` /
`run_*_agent()` pair following the pattern in
`ai/agents/idea_validation/startup_idea_analyzer.py` (the reference
implementation — see [Phase 06](../phases/06-product-development.md)).

## Where this fits

Part of the **Product Development** crew (Build), agent 33 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
