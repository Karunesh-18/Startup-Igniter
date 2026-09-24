# Phase 03: Research & Patent

**Status:** 🟢 IMPLEMENTED · **Crew ID:** 3 · **Domain:** IP · **Agents:** 6 in the frontend taxonomy, **7 in the actual backend**

## A real discrepancy, documented rather than hidden

The frontend lists 6 agents for this crew (ids 14–19). The backend
(`ai/agents/research_patent/`) implements **7**: everything the frontend
lists, plus `existing_solution_analyzer_agent.py` — see
[`docs/agents/67-existing-solution-analyzer.md`](../agents/67-existing-solution-analyzer.md)
and [ADR 0004](../architecture/0004-taxonomy-conflict.md). This doc describes
the real 7-step backend flow.

## Purpose

Assess the idea's IP landscape: prior art, academic research, existing
commercial/open-source solutions, innovation gaps, technology readiness
(TRL), and IP strategy — then synthesize all of it into one executive
summary. This is Zyte's primary reason for existing in this project: global
patent offices have no unified free API (see
[Grounding](../architecture/0005-grounding-layer.md)).

## Inputs

| Input | Source |
|---|---|
| `IdeaValidationResult` | Phase 01 output (required) |
| `MarketResearchResult` | Phase 02 output (optional — enriches the prompt with industry/market-stage context) |
| `ResearchBundle` (optional) | `ResearchManager.gather_patent_research()` — Zyte scrapes of Google Patents / Espacenet / WIPO Patentscope / India IP, merged with Exa's semantic patent search |

## Agent roster & task DAG

Sequential, 7 steps (`ai/crews/research_patent/crew.py::ResearchPatentCrew.run()`):

```
1. Patent Search Agent            → PatentAnalysis            (grounded via Zyte + Exa)
2. Research Paper Analyzer        → ResearchPaperAnalysis
3. Existing Solution Analyzer     → ExistingSolutionAnalysis   (not in the frontend's 66 — see above)
4. Innovation Gap Identifier      → InnovationGapAnalysis
5. Technology Readiness Assessor  → TechnologyReadiness
6. IP Strategy Architect          → IPStrategy
7. R&D Summary Agent              → ResearchPatentResult       (synthesizes 1-6 + context)
```

| # | Agent | Doc | Schema |
|---|---|---|---|
| 1 | Prior Art Search Agent | [agent doc](../agents/14-prior-art-search-agent.md) | [`PatentAnalysis`](../schemas/PatentAnalysis.json) |
| 2 | Research Paper Analyzer | [agent doc](../agents/15-research-paper-analyzer.md) | [`ResearchPaperAnalysis`](../schemas/ResearchPaperAnalysis.json) |
| — | Existing Solution Analyzer (unlisted) | [agent doc](../agents/67-existing-solution-analyzer.md) | [`ExistingSolutionAnalysis`](../schemas/ExistingSolutionAnalysis.json) |
| 3 | Innovation Gap Identifier | [agent doc](../agents/16-innovation-gap-identifier.md) | [`InnovationGapAnalysis`](../schemas/InnovationGapAnalysis.json) |
| 4 | Technology Readiness Assessor | [agent doc](../agents/17-technology-readiness-assessor.md) | [`TechnologyReadiness`](../schemas/TechnologyReadiness.json) |
| 5 | IP Strategy Architect | [agent doc](../agents/18-ip-strategy-architect.md) | [`IPStrategy`](../schemas/IPStrategy.json) |
| 6 | R&D Summary Agent | [agent doc](../agents/19-r-and-d-summary-agent.md) | [`ResearchPatentResult`](../schemas/ResearchPatentResult.json) |

## Output

`ResearchPatentResult` — the final summary agent's synthesis, carrying
`overall_novelty_score`, `trl_level`, `confidence_score`, and strategic
recommendations, plus the 6 sub-analyses above nested in the crew context.

## Acceptance criteria

- All 7 steps validate against their schema.
- `PatentAnalysis.citations` non-empty when the Zyte scrape returned real
  content (see the `has_grounding` check in `patent_search_agent.py`).
- Note: `PatentAnalysis` retains legacy flat fields (`patent_number`,
  `title`, `key_claims`, etc.) from an earlier schema shape that the real
  agent never populates — don't rely on them; use `existing_patent_summary`,
  `patentability_assessment`, and the other agent-populated fields instead
  (this is exactly the mistake a stale unit test made — see the fix in the
  Workstream C commit).

## Failure modes

| Failure | Current behavior |
|---|---|
| Zyte scrape of a patent office fails (network, layout change) | `_scrape_targets` catches per-source, logs, continues with the remaining 3 sources — never sinks the whole bundle. |
| `ResearchManager.gather_patent_research` fails entirely | Caught in `ResearchPatentService`, logged, crew proceeds ungrounded. |
| One agent's schema validation fails after repair | Propagates to a 500 (same pattern as Phases 01–02). |

## Mock mode

Same per-agent pattern as Phase 02: each `run_*_agent()` has its own
hand-written mock JSON branch, still validated through the real schema.
