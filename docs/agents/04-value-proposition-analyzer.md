# Value Proposition Analyzer

**Crew:** [Idea Validation](../phases/01-idea-validation.md) (IDEA) · **Role:** Value Analysis · **Status:** 🟢 IMPLEMENTED

## Implementation

| | |
|---|---|
| Module | `ai/agents/idea_validation/value_proposition_analyzer.py` |
| Backend role string | Value Proposition & Competitive Advantage Specialist |
| Output schema | [`ValuePropositionAnalysis`](../schemas/ValuePropositionAnalysis.json) |
| Prompt | `ai/prompts/idea_validation/*.md` |

This agent makes a real, self-hosted-model-backed LLM call through
[`ai.llm.gateway`](../architecture/0001-llm-gateway.md), validated against its
output schema with a bounded repair loop on schema mismatch.

## Where this fits

Part of the **Idea Validation** crew (Concept), agent 4 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
