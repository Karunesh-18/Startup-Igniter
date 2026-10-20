# Research Paper Analyzer

**Crew:** [Research & Patent](../phases/03-research-and-patent.md) (R&D) · **Role:** Academic Research · **Status:** 🟢 IMPLEMENTED

## Implementation

| | |
|---|---|
| Module | `ai/agents/research_patent/research_paper_analyzer_agent.py` |
| Backend role string | Academic & Scientific Research Literature Specialist |
| Output schema | [`ResearchPaperAnalysis`](../schemas/ResearchPaperAnalysis.json) |
| Prompt | `ai/prompts/research_patent/*.md` |

This agent makes a real, self-hosted-model-backed LLM call through
[`ai.llm.gateway`](../architecture/0001-llm-gateway.md), validated against its
output schema with a bounded repair loop on schema mismatch.

## Where this fits

Part of the **Research & Patent** crew (IP), agent 15 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
