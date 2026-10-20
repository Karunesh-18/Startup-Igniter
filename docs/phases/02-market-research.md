# Phase 02: Market Research

**Status:** 🟢 IMPLEMENTED · **Crew ID:** 2 · **Domain:** Landscape · **Agents:** 7

## Purpose

Ground the idea validated in Phase 01 in an external market: size, stage,
competitors, trends, and customer personas. As of this migration, this is
also the first crew wired to real external research (Tavily + Exa + Zyte)
rather than pure LLM recall — see [Grounding](../architecture/0005-grounding-layer.md).

## Inputs

| Input | Source |
|---|---|
| `IdeaValidationResult` | Phase 01 output (required) |
| `ResearchBundle` (optional) | `ResearchManager.gather_market_research()` + `gather_competitor_research()`, merged — populated by `MarketResearchService` before the crew runs |

## Agent roster & task DAG

Sequential, 7 steps (`ai/crews/market_research/crew.py::MarketResearchCrew.run()`):

```
1. Market Research Analyst    → MarketResearchAnalysis   (grounded, if a bundle is present)
2. Industry Analysis Agent    → IndustryAnalysis
3. Trend Analysis Agent       → TrendAnalysis
4. Competitor Discovery       → CompetitorDiscovery
5. Competitor Comparison      → CompetitorComparison       (uses #4's discovered competitors)
6. Customer Persona Generator → CustomerPersona
7. TAM/SAM/SOM Estimator      → TAMSAMSOMAnalysis
```

| # | Agent | Doc | Schema |
|---|---|---|---|
| 1 | Market Research Analyst | [agent doc](../agents/07-market-research-analyst.md) | [`MarketResearchAnalysis`](../schemas/MarketResearchAnalysis.json) |
| 2 | Industry Analysis Agent | [agent doc](../agents/08-industry-analysis-agent.md) | [`IndustryAnalysis`](../schemas/IndustryAnalysis.json) |
| 3 | Trend Analysis Agent | [agent doc](../agents/09-trend-analysis-agent.md) | [`TrendAnalysis`](../schemas/TrendAnalysis.json) |
| 4 | Competitor Discovery | [agent doc](../agents/10-competitor-discovery.md) | [`CompetitorDiscovery`](../schemas/CompetitorDiscovery.json) |
| 5 | Competitor Comparison | [agent doc](../agents/11-competitor-comparison.md) | [`CompetitorComparison`](../schemas/CompetitorComparison.json) |
| 6 | Customer Persona Generator | [agent doc](../agents/12-customer-persona-generator.md) | [`CustomerPersona`](../schemas/CustomerPersona.json) |
| 7 | TAM/SAM/SOM Estimator | [agent doc](../agents/13-tam-sam-som-estimator.md) | [`TAMSAMSOMAnalysis`](../schemas/TAMSAMSOMAnalysis.json) |

Only agent 1 (Market Research Analyst) currently consumes the research
bundle — see [Grounding](../architecture/0005-grounding-layer.md) for why
that's the highest-value place to start and the natural next agent to extend.

## Output

`MarketResearchResult` — the 7 schemas above, plus a composite
`overall_market_score` computed from a mix of 0–1 and 0–10 scale confidence
inputs (see the scale-inconsistency note in [ADR 0004](../architecture/0004-taxonomy-conflict.md)
— this is the specific formula that mixes scales).

## Acceptance criteria

- All 7 sub-schemas validate.
- `citations` on `MarketResearchAnalysis` is non-empty when a research bundle
  was supplied, and the model was explicitly instructed not to invent
  sources when one wasn't (see the grounding prompt injection in
  `ai/agents/market_research/market_research_agent.py`).
- Writes to `project_memory` under `market_research` (and implicitly makes
  this phase's findings available to Phase 03).

## Failure modes

| Failure | Current behavior |
|---|---|
| `ResearchManager` fails entirely (all 3 providers down/misconfigured) | Caught in `MarketResearchService.run_market_research`, logged, crew proceeds **ungrounded** rather than failing the run. |
| One agent's schema validation fails after repair | Same as Phase 01 — propagates to a 500, losing the whole run. |
| `context.idea_validation` missing | `MarketResearchCrew.run()` raises `ValueError` immediately. |

## Mock mode

Unlike Phase 01, mock mode here is **per-agent**, not crew-wide: each
`run_*_agent()` function has its own `if mock_mode: raw_output = f"""{{...}}"""`
branch with a hand-written JSON literal, which is then still run through the
real `validate_agent_output()` — so mock mode exercises the parse+validate
path (unlike Phase 01's crew-level short-circuit), just not the actual LLM
call or the grounding injection.
