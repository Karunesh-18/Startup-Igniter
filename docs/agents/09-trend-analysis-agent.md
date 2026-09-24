# Trend Analysis Agent

**Crew:** [Market Research](../phases/02-market-research.md) (MKT) · **Role:** Market Trends · **Status:** 🟢 IMPLEMENTED

## Implementation

| | |
|---|---|
| Module | `ai/agents/market_research/trend_analysis_agent.py` |
| Backend role string | Senior Trend Analysis & Technology Futures Specialist |
| Output schema | [`TrendAnalysis`](../schemas/TrendAnalysis.json) |
| Prompt | `ai/prompts/market_research/*.md` |

This agent makes a real, self-hosted-model-backed LLM call through
[`ai.llm.gateway`](../architecture/0001-llm-gateway.md), validated against its
output schema with a bounded repair loop on schema mismatch.

## Where this fits

Part of the **Market Research** crew (Landscape), agent 9 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
