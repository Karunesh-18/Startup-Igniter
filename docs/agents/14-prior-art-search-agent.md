# Prior Art Search Agent

**Crew:** [Research & Patent](../phases/03-research-and-patent.md) (R&D) · **Role:** Patent Landscape · **Status:** 🟢 IMPLEMENTED

## Implementation

| | |
|---|---|
| Module | `ai/agents/research_patent/patent_search_agent.py` |
| Backend role string | Patent & Intellectual Property Research Specialist |
| Output schema | [`PatentAnalysis`](../schemas/PatentAnalysis.json) |
| Prompt | `ai/prompts/research_patent/*.md` |

This agent makes a real, self-hosted-model-backed LLM call through
[`ai.llm.gateway`](../architecture/0001-llm-gateway.md), validated against its
output schema with a bounded repair loop on schema mismatch.

## Where this fits

Part of the **Research & Patent** crew (IP), agent 14 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
