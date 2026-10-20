# Phase 01: Idea Validation

**Status:** 🟢 IMPLEMENTED · **Crew ID:** 1 · **Domain:** Concept · **Agents:** 6

The first and most mature crew in the pipeline. Every agent here makes a real
LLM call (via [`ai.llm.gateway`](../architecture/0001-llm-gateway.md)) and
every output is validated against a Pydantic schema before the crew moves on.

## Purpose

Take a raw, unstructured startup pitch (a few sentences to a paragraph) and
turn it into a structured assessment: what it is, what problem it solves,
who it's for, why it's valuable, what category it belongs to, and how
innovative it is — each backed by its own schema, not a single monolithic
"analyze this idea" call.

## Inputs

| Input | Source |
|---|---|
| `idea_text` | Raw user submission, 10–5000 chars (`AnalysisRequest.idea_text`) |
| `project_id` | Optional; generated if absent |

No prior phase output is required — this is always the entry point.

## Agent roster & task DAG

Runs **sequentially**, each step's output feeding the next step's prompt as
context (not parallel — see [ADR 0001](../architecture/0001-llm-gateway.md)
for why sequential-with-context beats independent parallel calls here):

```
1. Startup Idea Analyzer       → StartupIdeaAnalysis
2. Problem Statement Analyzer  → ProblemStatementAnalysis   (uses #1's summary)
3. Customer Identifier         → CustomerIdentification     (uses #2's problem statement)
4. Value Proposition Analyzer  → ValuePropositionAnalysis   (uses #3's primary customers)
5. Category Classifier         → StartupCategoryClassification
6. Innovation Scoring Engine   → InnovationScoreAnalysis    (uses #5's category)
```

Source: `ai/crews/idea_validation/crew.py::IdeaValidationCrew.run()`.

| # | Agent | Doc | Schema |
|---|---|---|---|
| 1 | Startup Idea Analyzer | [agent doc](../agents/01-startup-idea-analyzer.md) | [`StartupIdeaAnalysis`](../schemas/StartupIdeaAnalysis.json) |
| 2 | Problem Statement Analyzer | [agent doc](../agents/02-problem-statement-analyzer.md) | [`ProblemStatementAnalysis`](../schemas/ProblemStatementAnalysis.json) |
| 3 | Customer Identifier | [agent doc](../agents/03-customer-identifier.md) | [`CustomerIdentification`](../schemas/CustomerIdentification.json) |
| 4 | Value Proposition Analyzer | [agent doc](../agents/04-value-proposition-analyzer.md) | [`ValuePropositionAnalysis`](../schemas/ValuePropositionAnalysis.json) |
| 5 | Category Classifier | [agent doc](../agents/05-category-classifier.md) | [`StartupCategoryClassification`](../schemas/StartupCategoryClassification.json) |
| 6 | Innovation Scoring Engine | [agent doc](../agents/06-innovation-scoring-engine.md) | [`InnovationScoreAnalysis`](../schemas/InnovationScoreAnalysis.json) |

## Output

`IdeaValidationResult` — the 6 schemas above, plus a **deterministic, Python-computed**
composite score (never LLM-computed, per the original spec's guardrail):

```python
overall_validation_score = round(
    0.20 * idea_model.technical_feasibility_score
  + 0.20 * problem_model.urgency_score
  + 0.20 * value_model.customer_value_score
  + 0.15 * category_model.confidence_score
  + 0.25 * innovation_model.overall_innovation_score,
    2,
)
```

⚠️ **Known scale inconsistency** (see [ADR 0004](../architecture/0004-taxonomy-conflict.md)):
`category_model.confidence_score` is 0–100, while every other input to this
formula is also nominally 0–100 *except* several other schemas elsewhere in
the pipeline use 0.0–1.0 for the same concept. This formula happens to be
internally consistent; the inconsistency bites when comparing scores *across*
phases (e.g. Market Research's `confidence_score` is 0.0–1.0).

## Acceptance criteria

- All 6 sub-schemas validate (or a bounded repair-loop retry succeeds — see
  [`ai.llm.gateway.LLMGateway.invoke_structured`](../architecture/0001-llm-gateway.md)).
- `overall_validation_score` is within `[0, 100]`.
- Every step writes to `project_memory` under a stable key (`idea_analysis`,
  `problem_analysis`, `customer_analysis`, `value_proposition`,
  `category_classification`, `innovation_scoring`) so later phases (Market
  Research, Research & Patent) can read this phase's findings back out.

## Failure modes

| Failure | Current behavior | 
|---|---|
| One agent's output fails schema validation after repair attempts | `OutputValidationError` propagates up through the crew, the service, to the bare `except Exception` in `backend/api/routers/analysis.py` → HTTP 500. The whole run (including any already-completed crews) is lost. |
| LLM call itself fails (network, rate limit) after gateway fallback exhausted | `MissingAPIKeyError` / provider error propagates the same way. |
| `idea_text` too short/long | Caught earlier by `AnalysisRequest` validation (10–5000 chars) — never reaches this crew. |

## Mock mode

`IdeaValidationCrew.run(mock_mode=True)` short-circuits **before any LLM
call** and returns a fixed, hand-written result (`ai/crews/idea_validation/crew.py`
lines ~157–232). Useful for UI development and CI, but note it exercises
none of the actual prompt/schema/gateway code path — a schema drift here
would not be caught by testing only in mock mode.
