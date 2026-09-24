# Startup Idea Analyzer

**Crew:** [Idea Validation](../phases/01-idea-validation.md) (IDEA) · **Role:** Core Analysis · **Status:** 🟢 IMPLEMENTED

## Implementation

| | |
|---|---|
| Module | `ai/agents/idea_validation/startup_idea_analyzer.py` |
| Backend role string | Senior Startup Architect & Feasibility Lead |
| Output schema | [`StartupIdeaAnalysis`](../schemas/StartupIdeaAnalysis.json) |
| Prompt | `ai/prompts/idea_validation/*.md` |

This agent makes a real, self-hosted-model-backed LLM call through
[`ai.llm.gateway`](../architecture/0001-llm-gateway.md), validated against its
output schema with a bounded repair loop on schema mismatch.

## Where this fits

Part of the **Idea Validation** crew (Concept), agent 1 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
