# IP Strategy Architect

**Crew:** [Research & Patent](../phases/03-research-and-patent.md) (R&D) · **Role:** IP Protection · **Status:** 🟢 IMPLEMENTED

## Implementation

| | |
|---|---|
| Module | `ai/agents/research_patent/intellectual_property_strategy_agent.py` |
| Backend role string | Chief IP Counsel & Strategic Patent Strategist |
| Output schema | [`IPStrategy`](../schemas/IPStrategy.json) |
| Prompt | `ai/prompts/research_patent/*.md` |

This agent makes a real, self-hosted-model-backed LLM call through
[`ai.llm.gateway`](../architecture/0001-llm-gateway.md), validated against its
output schema with a bounded repair loop on schema mismatch.

## Where this fits

Part of the **Research & Patent** crew (IP), agent 18 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
