# Customer Persona Generator

**Crew:** [Market Research](../phases/02-market-research.md) (MKT) · **Role:** Generate Personas · **Status:** 🟢 IMPLEMENTED

## Implementation

| | |
|---|---|
| Module | `ai/agents/market_research/customer_persona_generator.py` |
| Backend role string | Senior Customer Research & Persona Generation Specialist |
| Output schema | [`CustomerPersona`](../schemas/CustomerPersona.json) |
| Prompt | `ai/prompts/market_research/*.md` |

This agent makes a real, self-hosted-model-backed LLM call through
[`ai.llm.gateway`](../architecture/0001-llm-gateway.md), validated against its
output schema with a bounded repair loop on schema mismatch.

## Where this fits

Part of the **Market Research** crew (Landscape), agent 12 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
