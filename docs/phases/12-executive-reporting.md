# Phase 12: Executive Reporting

**Status:** 🟢 IMPLEMENTED (crew-level) · **Crew ID:** 12 · **Domain:** Synthesis · **Agents:** 5 (frontend) / 1 crew-level call

## Current behavior

Runs as one structured LLM call through `ai/crews/spec_runner.py::run_spec_crew` (heavy tier, 12000 max tokens). This phase doc plus the agent docs listed for the crew are the system prompt; the user prompt carries a digest of the prior crews' results and the shared numbered source pool. The reply is validated against the crew's result schema (`ai/schemas/`). The "agents" are roles the one call reasons through in turn, not separate calls. If the call fails the run continues and the report marks this crew unavailable. Claims from this crew's output are checked by the [evidence ledger](../architecture/0006-evidence-ledger-and-skeptic.md).

## Intended purpose

The final crew: synthesize every prior phase's output into one executive
summary, an overall readiness score, a 12-month roadmap, a 30-60-90 day
action plan, and an investor-ready master report — the deliverable the
whole pipeline builds toward.

## Existing schema

[`MasterReportResult`](../schemas/MasterReportResult.json): `project_name`,
`executive_summary`, `overall_readiness_score` (0–100), `phase_scores`
(dict of phase name → score), `key_recommendations`, `confidence_score`.

## Suggested agent split

| # | Agent | Doc | Natural schema target |
|---|---|---|---|
| 62 | Master Reporting Agent | [agent doc](../agents/62-master-reporting-agent.md) | `executive_summary` |
| 63 | Readiness Scoring Agent | [agent doc](../agents/63-readiness-scoring-agent.md) | `overall_readiness_score`, `phase_scores` |
| 64 | Roadmap Generator | [agent doc](../agents/64-roadmap-generator.md) | new field needed (12-month roadmap) |
| 65 | Action Plan Generator | [agent doc](../agents/65-action-plan-generator.md) | new field needed (30-60-90 day plan) |
| 66 | Final Report Generator | [agent doc](../agents/66-final-report-generator.md) | synthesizes 62-65 into the exportable document |

## ⚠️ This is the one crew where the scoring guardrail matters most

Per every score-related guardrail already honored in Phases 01–02:
**`overall_readiness_score` and `phase_scores` must be a deterministic,
Python-computed weighted sum over the sub-scores already produced by every
other phase — never an LLM free-generating a single number.** The
`DEFAULT_SCORE_WEIGHTS` machinery already exists in
`ai/shared/constants.py` for exactly this; Readiness Scoring Agent's actual
job should be to select/justify weights and flag which phases were
skipped/ungrounded, not to invent the number itself.

## Inputs (once built)

Every prior phase's output — this crew necessarily runs last, and its
quality is bounded by how many of Phases 04–11 actually exist. Today, an
honest v1 of this crew can only meaningfully synthesize Phases 01–03; the
`Final Report Generator` should say so explicitly rather than presenting a
report that implies full-pipeline coverage it can't back up until crews
04–11 are built.

## Failure modes (once built)

If a required upstream phase's output is missing (crew not run, or failed),
this crew must degrade gracefully — report on what's available and flag
the gap — rather than either failing outright or silently fabricating the
missing section.
