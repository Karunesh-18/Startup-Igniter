# Existing Solution Analyzer

**Crew:** [Research & Patent](../phases/03-research-and-patent.md) (R&D) · **Role:** Commercial Landscape Analysis · **Status:** 🟢 IMPLEMENTED (not in the frontend's 66)

## Implementation

| | |
|---|---|
| Module | `ai/agents/research_patent/existing_solution_analyzer_agent.py` |
| Backend role string | Commercial Solution & Open-Source Landscape Specialist |
| Output schema | [`ExistingSolutionAnalysis`](../schemas/ExistingSolutionAnalysis.json) |

## A real inconsistency, not a doc error

This is a genuine 7th agent in the Research & Patent crew's backend
(`ai/agents/research_patent/`) with no corresponding entry in
`frontend/src/data/crews.ts`'s 66-agent list — the frontend lists 6 agents
for this crew (ids 14-19), the backend implements 7. See
[ADR 0004: taxonomy conflict](../architecture/0004-taxonomy-conflict.md).
