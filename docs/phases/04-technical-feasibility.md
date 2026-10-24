# Phase 04: Technical Feasibility

**Status:** 🟢 IMPLEMENTED (crew-level) · **Crew ID:** 4 · **Domain:** Engineering · **Agents:** 6 (frontend) / 1 crew-level call

## Current behavior

Runs as one structured LLM call through `ai/crews/spec_runner.py::run_spec_crew` (heavy tier, 12000 max tokens). This phase doc plus the agent docs listed for the crew are the system prompt; the user prompt carries a digest of the prior crews' results and the shared numbered source pool. The reply is validated against the crew's result schema (`ai/schemas/`). The "agents" are roles the one call reasons through in turn, not separate calls. If the call fails the run continues and the report marks this crew unavailable. Claims from this crew's output are checked by the [evidence ledger](../architecture/0006-evidence-ledger-and-skeptic.md).

## Intended purpose

Assess whether the idea (Phase 01) and its business model (Phase 05, once
built) can actually be engineered: architecture risk, infrastructure needs,
scalability limits, and security posture.

## A structural note before building this

The existing schema is **crew-level, not per-agent**: one `FeasibilityResult`
with flat fields, not 6 independent Pydantic models the way Phases 01–03
have. The frontend's 6 "agents" (Feasibility Analyzer, Architecture
Recommender, Infrastructure Planner, Scalability Assessment, Security
Assessment, Feasibility Summary) are a **UI-level grouping concept**, not 6
backend LLM calls today. Building this crew for real means choosing one of:

1. **Match Phases 01–03's pattern**: split `FeasibilityResult` into 6
   sub-schemas, one real LLM call each, synthesized by a 6th "summary" call
   — most consistent with the rest of the pipeline, most expensive (6 calls).
2. **One call, structured richly**: keep `FeasibilityResult` as the single
   schema, one real LLM call filling all fields at once, and treat the "6
   agents" as purely a documentation/UI fiction — cheaper, less consistent
   with Phases 01–03's architecture.

Given the pipeline standardized on option 1 for the first 20 agents (and the
per-crew adapter design in [ADR 0003](../architecture/0003-qwen3-base-models.md)
assumes crew-level training data, not agent-level), **option 1 is the
recommended default** unless a specific reason favors otherwise.

## Existing schema

[`FeasibilityResult`](../schemas/FeasibilityResult.json) —
`technical_feasibility_score`, `operational_feasibility_score`,
`financial_feasibility_score` (all 0–100), `key_risks`,
`mitigation_strategies`, `executive_summary`, `confidence_score`.

## Inputs (once built)

`IdeaValidationResult` (Phase 01, required), `ProductDevelopmentResult`
(Phase 06, if sequenced after it — check `startup_categories.workflow` for
the category's actual phase order).

## Agent roster (frontend taxonomy)

| # | Agent | Doc |
|---|---|---|
| 20 | Feasibility Analyzer | [agent doc](../agents/20-feasibility-analyzer.md) |
| 21 | Architecture Recommender | [agent doc](../agents/21-architecture-recommender.md) |
| 22 | Infrastructure Planner | [agent doc](../agents/22-infrastructure-planner.md) |
| 23 | Scalability Assessment | [agent doc](../agents/23-scalability-assessment.md) |
| 24 | Security Assessment | [agent doc](../agents/24-security-assessment.md) |
| 25 | Feasibility Summary | [agent doc](../agents/25-feasibility-summary.md) |

## Failure modes (once built)

Design for the same pattern as Phases 01–03: schema validation with a
bounded repair loop, grounding failures logged and non-fatal, one bad
sub-agent should not lose the whole multi-crew run (worth revisiting the
current all-or-nothing 500 behavior — see [ADR 0001](../architecture/0001-llm-gateway.md)'s
"Known limitations" section — before scaling to 12 crews of failure surface).
