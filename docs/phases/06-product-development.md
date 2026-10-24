# Phase 06: Product Development

**Status:** 🟢 IMPLEMENTED (crew-level) · **Crew ID:** 6 · **Domain:** Build · **Agents:** 6 (frontend) / 1 crew-level call

## Current behavior

Runs as one structured LLM call through `ai/crews/spec_runner.py::run_spec_crew` (heavy tier, 12000 max tokens). This phase doc plus the agent docs listed for the crew are the system prompt; the user prompt carries a digest of the prior crews' results and the shared numbered source pool. The reply is validated against the crew's result schema (`ai/schemas/`). The "agents" are roles the one call reasons through in turn, not separate calls. If the call fails the run continues and the report marks this crew unavailable. Claims from this crew's output are checked by the [evidence ledger](../architecture/0006-evidence-ledger-and-skeptic.md).

## Intended purpose

Turn the validated idea + feasibility assessment (Phase 04) into an MVP
feature roadmap, a concrete tech stack recommendation, and an architecture
overview a founder could hand to an engineer on day one.

## Existing schema

[`ProductDevelopmentResult`](../schemas/ProductDevelopmentResult.json):
- `mvp_features`: list of [`MVPFeature`](../schemas/MVPFeature.json)
  (name, description, priority: Must/Should/Could Have, complexity: Low/Med/High).
- `tech_stack`: [`TechStackRecommendation`](../schemas/TechStackRecommendation.json)
  (frontend, backend, database, hosting, ai_ml_tools).
- `architecture_overview`, `confidence_score`.

## Suggested agent split

| # | Agent | Doc | Natural schema target |
|---|---|---|---|
| 32 | MVP Feature Prioritizer | [agent doc](../agents/32-mvp-feature-prioritizer.md) | `mvp_features` |
| 33 | Tech Stack Advisor | [agent doc](../agents/33-tech-stack-advisor.md) | `tech_stack` |
| 34 | Product Roadmap Agent | [agent doc](../agents/34-product-roadmap-agent.md) | sequencing of `mvp_features` over time |
| 35 | Effort Estimator | [agent doc](../agents/35-effort-estimator.md) | `MVPFeature.complexity` justification |
| 36 | UX Recommendation Agent | [agent doc](../agents/36-ux-recommendation-agent.md) | new field needed — not in current schema |
| 37 | Product Dev Summary | [agent doc](../agents/37-product-dev-summary.md) | `architecture_overview` |

Building agent 36 for real requires extending `ProductDevelopmentResult`
with a UX-specific field (the current schema has no place for it) — a
concrete example of how "SPECIFIED" agents sometimes need schema work
before any prompt work.

## Inputs (once built)

`IdeaValidationResult` (Phase 01), `FeasibilityResult` (Phase 04, if
sequenced first).

## Failure modes (once built)

Same pattern as Phases 01-03.
