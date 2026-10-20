# Innovation Gap Identifier

**Crew:** [Research & Patent](../phases/03-research-and-patent.md) (R&D) · **Role:** Innovation Gaps · **Status:** 🟢 IMPLEMENTED

## Implementation

| | |
|---|---|
| Module | `ai/agents/research_patent/innovation_gap_identifier_agent.py` |
| Backend role string | Chief Innovation Officer & Strategic Gap Specialist |
| Output schema | [`InnovationGapAnalysis`](../schemas/InnovationGapAnalysis.json) |
| Prompt | `ai/prompts/research_patent/*.md` |

This agent makes a real, self-hosted-model-backed LLM call through
[`ai.llm.gateway`](../architecture/0001-llm-gateway.md), validated against its
output schema with a bounded repair loop on schema mismatch.

## Where this fits

Part of the **Research & Patent** crew (IP), agent 16 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
