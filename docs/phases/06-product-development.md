# Phase 06: Product Development

**Status:** ⚪ SPECIFIED (not built) · **Crew ID:** 6 · **Domain:** Build · **Agents:** 6 (frontend) / 0 backend

## Current behavior

`ai/crews/product_development/tasks.py` returns a hardcoded
`ProductDevelopmentResult`.

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
