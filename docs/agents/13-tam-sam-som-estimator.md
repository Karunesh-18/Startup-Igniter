# TAM/SAM/SOM Estimator

**Crew:** [Market Research](../phases/02-market-research.md) (MKT) · **Role:** Market Sizing · **Status:** 🟢 IMPLEMENTED

## Implementation

| | |
|---|---|
| Module | `ai/agents/market_research/tam_sam_som_estimator.py` |
| Backend role string | Senior Financial & Market Sizing Specialist |
| Output schema | [`TAMSAMSOMAnalysis`](../schemas/TAMSAMSOMAnalysis.json) |
| Prompt | `ai/prompts/market_research/*.md` |

This agent makes a real, self-hosted-model-backed LLM call through
[`ai.llm.gateway`](../architecture/0001-llm-gateway.md), validated against its
output schema with a bounded repair loop on schema mismatch.

## Where this fits

Part of the **Market Research** crew (Landscape), agent 13 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
