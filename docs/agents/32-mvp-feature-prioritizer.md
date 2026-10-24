# MVP Feature Prioritizer

**Crew:** [Product Development](../phases/06-product-development.md) (PROD) · **Role:** Feature Scope · **Status:** 🟢 IMPLEMENTED (crew-level)

## Implementation

This agent is a role inside the **Product Development** crew, which runs as one
structured LLM call (`ai/crews/spec_runner.py::run_spec_crew`) validated
against the crew's result schema in `ai/schemas/`. The agent is not a
separate call; this document and the
[Phase 06](../phases/06-product-development.md) doc are part of the
crew's system prompt. Crew code: `ai/crews/product_development/`.

## Where this fits

Part of the **Product Development** crew (Build), agent 32 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
