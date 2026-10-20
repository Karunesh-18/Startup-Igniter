# Phase 05: Business Planning

**Status:** ⚪ SPECIFIED (not built) · **Crew ID:** 5 · **Domain:** Strategy · **Agents:** 6 (frontend) / 0 backend

## Current behavior

`ai/crews/business_planning/tasks.py` returns a hardcoded `BusinessPlanResult`.
The schema module (`ai/schemas/business_plan.py`) is more developed than most
stub crews — it already has **two** nested sub-schemas (`LeanCanvas`,
`FinancialModel`), which maps more naturally onto a multi-agent split than
the single-flat-schema crews (04, 06–12).

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
