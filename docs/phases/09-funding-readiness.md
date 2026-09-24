# Phase 09: Funding Readiness

**Status:** ⚪ SPECIFIED (not built) · **Crew ID:** 9 · **Domain:** Capital · **Agents:** 5 (frontend) / 0 backend

## Current behavior

`ai/crews/funding/tasks.py` returns a hardcoded `FundingResult`.

## Intended purpose

Assess fundraising readiness: a pitch-deck slide structure, an estimated
valuation range, a fundraising target, a due-diligence checklist, and
matching investor types (angel / seed VC / micro VC).

## Existing schema

[`FundingResult`](../schemas/FundingResult.json): `pitch_deck_slides`,
`estimated_valuation_range`, `fundraising_target`, `investor_checklist`,
`investor_types`, `confidence_score`.

## Suggested agent split

| # | Agent | Doc | Natural schema target |
|---|---|---|---|
| 49 | Funding Readiness Agent | [agent doc](../agents/49-funding-readiness-agent.md) | `pitch_deck_slides`, `investor_checklist` |
| 50 | Investor Matcher | [agent doc](../agents/50-investor-matcher.md) | `investor_types` |
| 51 | Grant Discovery Agent | [agent doc](../agents/51-grant-discovery-agent.md) | new field needed (non-dilutive funding sources) |
| 52 | Valuation Advisor | [agent doc](../agents/52-valuation-advisor.md) | `estimated_valuation_range`, `fundraising_target` |
| 53 | Funding Summary | [agent doc](../agents/53-funding-summary.md) | synthesis across 49-52 |

## ⚠️ Investor matching vs. investor recommendation

Per the original spec: this is **recommendation, not real matching or
introduction** — `investor_types` should read as fit categories ("your stage
and sector suit micro-VCs focused on X"), not as a promise of an actual
warm introduction or a curated, verified investor database. A real
`investors` table with verified contacts is explicitly v2+ scope in the
original spec, out of scope for this crew.

## Inputs (once built)

`IdeaValidationResult` (Phase 01), `BusinessPlanResult` (Phase 05, for the
financial model informing valuation), `MarketResearchResult` (Phase 02, for
market-size-informed fundraising targets).

## Failure modes (once built)

Valuation figures are the highest-stakes hallucination risk in this crew —
`estimated_valuation_range` should always read as a rough band with an
explicit "not a formal valuation" caveat, never a precise number presented
with false confidence.
