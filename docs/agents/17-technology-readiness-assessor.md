# Technology Readiness Assessor

**Crew:** [Research & Patent](../phases/03-research-and-patent.md) (R&D) · **Role:** TRL Evaluation · **Status:** 🟢 IMPLEMENTED

## Implementation

| | |
|---|---|
| Module | `ai/agents/research_patent/technology_readiness_agent.py` |
| Backend role string | Chief Technology Officer & System Architecture Specialist |
| Output schema | [`TechnologyReadiness`](../schemas/TechnologyReadiness.json) |
| Prompt | `ai/prompts/research_patent/*.md` |

This agent makes a real, self-hosted-model-backed LLM call through
[`ai.llm.gateway`](../architecture/0001-llm-gateway.md), validated against its
output schema with a bounded repair loop on schema mismatch.

## Where this fits

Part of the **Research & Patent** crew (IP), agent 17 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
