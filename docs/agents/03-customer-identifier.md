# Customer Identifier

**Crew:** [Idea Validation](../phases/01-idea-validation.md) (IDEA) · **Role:** Target Users · **Status:** 🟢 IMPLEMENTED

## Implementation

| | |
|---|---|
| Module | `ai/agents/idea_validation/customer_identifier.py` |
| Backend role string | Target Audience & User Persona Strategist |
| Output schema | [`CustomerIdentification`](../schemas/CustomerIdentification.json) |
| Prompt | `ai/prompts/idea_validation/*.md` |

This agent makes a real, self-hosted-model-backed LLM call through
[`ai.llm.gateway`](../architecture/0001-llm-gateway.md), validated against its
output schema with a bounded repair loop on schema mismatch.

## Where this fits

Part of the **Idea Validation** crew (Concept), agent 3 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
