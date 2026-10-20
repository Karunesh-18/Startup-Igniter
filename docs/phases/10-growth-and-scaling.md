# Phase 10: Growth & Scaling

**Status:** ⚪ SPECIFIED (not built) · **Crew ID:** 10 · **Domain:** Scale · **Agents:** 4 (frontend) / 0 backend

## Current behavior

`ai/crews/growth_scaling/tasks.py` returns a hardcoded `GrowthScalingResult`.

## Intended purpose

Recommend customer acquisition channels, a viral/referral growth mechanic,
a retention playbook, and target growth KPIs for post-launch scaling.

## Existing schema

[`GrowthScalingResult`](../schemas/GrowthScalingResult.json):
`primary_acquisition_channels`, `viral_loop_mechanic`, `retention_playbook`,
`target_kpis`, `confidence_score`.

## Suggested agent split

Only 4 agents (the smallest crew, alongside Community & Ecosystem) — no
dedicated "summary" agent in the frontend taxonomy.

| # | Agent | Doc | Natural schema target |
|---|---|---|---|
| 54 | Growth Scaling Agent | [agent doc](../agents/54-growth-scaling-agent.md) | `primary_acquisition_channels`, `target_kpis` |
| 55 | Expansion Planner | [agent doc](../agents/55-expansion-planner.md) | new field needed (market-expansion sequencing) |
| 56 | Partnership Advisor | [agent doc](../agents/56-partnership-advisor.md) | new field needed (B2B partnership targets) |
| 57 | International Expansion | [agent doc](../agents/57-international-expansion.md) | new field needed (target geographies) |

Notably `viral_loop_mechanic` and `retention_playbook` — both already in the
schema — have no agent explicitly assigned to them in the frontend's 4-agent
list, while 3 of the 4 listed agents (Expansion Planner, Partnership
Advisor, International Expansion) target fields that **don't exist yet**.
Building this crew for real requires reconciling the schema to the agent
roster (or vice versa) before writing any prompts — a concrete instance of
the general pattern flagged in [ADR 0004](../architecture/0004-taxonomy-conflict.md).

## Inputs (once built)

`MarketResearchResult` (Phase 02), `FundingResult` (Phase 09, growth
strategy is usually funding-stage-dependent).

## Failure modes (once built)

Same schema-validation pattern as other SPECIFIED crews, once the schema
itself is reconciled to the agent roster above.
