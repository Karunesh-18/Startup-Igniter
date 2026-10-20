# Market Research Analyst

**Crew:** [Market Research](../phases/02-market-research.md) (MKT) · **Role:** Market Overview · **Status:** 🟢 IMPLEMENTED

## Implementation

| | |
|---|---|
| Module | `ai/agents/market_research/market_research_agent.py` |
| Backend role string | Senior Market Research & Industry Analysis Specialist |
| Output schema | [`MarketResearchAnalysis`](../schemas/MarketResearchAnalysis.json) |
| Prompt | `ai/prompts/market_research/*.md` |

This agent makes a real, self-hosted-model-backed LLM call through
[`ai.llm.gateway`](../architecture/0001-llm-gateway.md), validated against its
output schema with a bounded repair loop on schema mismatch.

## Where this fits

Part of the **Market Research** crew (Landscape), agent 7 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
