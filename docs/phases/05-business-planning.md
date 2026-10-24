# Phase 05: Business Planning

**Status:** 🟢 IMPLEMENTED (crew-level) · **Crew ID:** 5 · **Domain:** Strategy · **Agents:** 6 (frontend) / 1 crew-level call

## Current behavior

Runs as one structured LLM call through `ai/crews/spec_runner.py::run_spec_crew` (heavy tier, 12000 max tokens). This phase doc plus the agent docs listed for the crew are the system prompt; the user prompt carries a digest of the prior crews' results and the shared numbered source pool. The reply is validated against the crew's result schema (`ai/schemas/`). The "agents" are roles the one call reasons through in turn, not separate calls. If the call fails the run continues and the report marks this crew unavailable. Claims from this crew's output are checked by the [evidence ledger](../architecture/0006-evidence-ledger-and-skeptic.md).

## Intended purpose

Turn the validated idea (Phase 01) + market data (Phase 02) into a Lean
Canvas, a financial model (pricing, CAC/LTV, year-1 revenue), and an
executive summary founders can act on immediately.

## Existing schema

[`BusinessPlanResult`](../schemas/BusinessPlanResult.json):
- `lean_canvas`: [`LeanCanvas`](../schemas/LeanCanvas.json) — problem,
  solution, UVP, unfair advantage, customer segments, key metrics, channels,
  cost structure, revenue streams (the standard 9-box Lean Canvas).
- `financial_model`: [`FinancialModel`](../schemas/FinancialModel.json) —
  pricing model, tiered price points, estimated CAC/LTV, year-1 revenue.
- `executive_summary`, `confidence_score`.

## Suggested agent split (if built per-agent, matching Phases 01-03's pattern)

| # | Agent | Doc | Natural schema target |
|---|---|---|---|
| 26 | Lean Canvas Agent | [agent doc](../agents/26-lean-canvas-agent.md) | `LeanCanvas` |
| 27 | Financial Model Agent | [agent doc](../agents/27-financial-model-agent.md) | `FinancialModel` (unit economics half) |
| 28 | Revenue Model Agent | [agent doc](../agents/28-revenue-model-agent.md) | `FinancialModel.price_points` / revenue streams |
| 29 | Cost Structure Agent | [agent doc](../agents/29-cost-structure-agent.md) | `LeanCanvas.cost_structure` |
| 30 | Pricing Strategy Agent | [agent doc](../agents/30-pricing-strategy-agent.md) | `FinancialModel.pricing_model` |
| 31 | Business Plan Summary | [agent doc](../agents/31-business-plan-summary.md) | `executive_summary` (synthesizes 26-30) |

Note agents 27–30 all target sub-pieces of the same `FinancialModel`
schema — building this crew likely means splitting `FinancialModel` further
(the way `LeanCanvas` and `FinancialModel` are already split out of one flat
result) rather than 4 agents racing to fill the same 5 fields.

## Inputs (once built)

`IdeaValidationResult` (Phase 01), `MarketResearchResult` (Phase 02) —
`TAMSAMSOMAnalysis` and `CompetitorComparison` in particular are the natural
grounding for the financial model's pricing and CAC/LTV estimates.

## Failure modes (once built)

Same pattern as Phases 01-03: schema validation with bounded repair,
citations where market data informs pricing claims.
