# Innovation Scoring Engine

**Crew:** [Idea Validation](../phases/01-idea-validation.md) (IDEA) · **Role:** Innovation Score · **Status:** 🟢 IMPLEMENTED

## Implementation

| | |
|---|---|
| Module | `ai/agents/idea_validation/innovation_scoring_agent.py` |
| Backend role string | Innovation & Technology Differentiation Specialist |
| Output schema | [`InnovationScoreAnalysis`](../schemas/InnovationScoreAnalysis.json) |
| Prompt | `ai/prompts/idea_validation/*.md` |

This agent makes a real, self-hosted-model-backed LLM call through
[`ai.llm.gateway`](../architecture/0001-llm-gateway.md), validated against its
output schema with a bounded repair loop on schema mismatch.

## Where this fits

Part of the **Idea Validation** crew (Concept), agent 6 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
