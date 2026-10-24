# Phase 11: Community & Ecosystem

**Status:** 🟢 IMPLEMENTED (crew-level) · **Crew ID:** 11 · **Domain:** Network · **Agents:** 4 (frontend) / 1 crew-level call

## Current behavior

Runs as one structured LLM call through `ai/crews/spec_runner.py::run_spec_crew` (heavy tier, 12000 max tokens). This phase doc plus the agent docs listed for the crew are the system prompt; the user prompt carries a digest of the prior crews' results and the shared numbered source pool. The reply is validated against the crew's result schema (`ai/schemas/`). The "agents" are roles the one call reasons through in turn, not separate calls. If the call fails the run continues and the report marks this crew unavailable. Claims from this crew's output are checked by the [evidence ledger](../architecture/0006-evidence-ledger-and-skeptic.md).

## Intended purpose

Surface peer-review feedback, a synthesized community-feedback summary,
recommended mentors, and (per the frontend's agent list) accelerator and
regional-ecosystem recommendations.

## Existing schema

[`CommunityResult`](../schemas/CommunityResult.json):
`peer_review_scorecard` (dict of category → float score),
`community_feedback_summary`, `recommended_mentors`, `confidence_score`.

## Suggested agent split

| # | Agent | Doc | Natural schema target |
|---|---|---|---|
| 58 | Community Peer Review Agent | [agent doc](../agents/58-community-peer-review-agent.md) | `peer_review_scorecard`, `community_feedback_summary` |
| 59 | Mentor Recommendation | [agent doc](../agents/59-mentor-recommendation.md) | `recommended_mentors` |
| 60 | Accelerator Recommender | [agent doc](../agents/60-accelerator-recommender.md) | new field needed (accelerator program fit) |
| 61 | Startup Ecosystem Agent | [agent doc](../agents/61-startup-ecosystem-agent.md) | new field needed (regional hub / E-Cell recommendations) |

Per the original spec's "personalized ecosystem recommendations" use case:
this should be grounded with real, current program data (Brave Search /
Tavily), not invented from parametric memory — accelerator cohorts, regional
E-Cell programs, and grant deadlines change yearly and a fine-tuned model's
training-time knowledge will be stale by the time it's deployed.

## ⚠️ "Peer review" needs a real data source

`peer_review_scorecard` implies actual peer feedback exists somewhere (the
community forum, per the original spec's later milestones) — this crew has
no meaningful output until either the forum exists or this field is
re-scoped to mean something an LLM can legitimately assess alone (e.g. a
structured self-assessment rubric rather than claimed "peer" data).

## Inputs (once built)

`StartupCategoryClassification` (Phase 01, for community/hub relevance),
`users.role` (student/professional/researcher — for role-appropriate mentor
and accelerator matching, per the original spec).

## Failure modes (once built)

Same schema-validation pattern as other SPECIFIED crews.
