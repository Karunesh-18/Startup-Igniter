# Eval: per-agent rubrics and promotion gating

## What gets measured

`training/eval/harness.py` runs every `TrainingTarget`
(`training/data/agent_registry.py`) against a set of seed ideas and a chosen
backend (`selfhosted`, `fallback`, or `mock`), measuring per target:

1. **Schema-validity rate** — raw compliance, with the gateway's repair loop
   *disabled* (`repair_attempts=0`) so this measures the model's own
   compliance, not the gateway rescuing it.
2. **Numeric-range compliance** — every numeric field with a declared
   `ge`/`le` bound actually lands in range. This is the check that would
   have caught the pre-migration 0–1 vs 0–100 vs 0–10 scale inconsistency
   (see [ADR 0004](../architecture/0004-taxonomy-conflict.md)) at the
   per-field level, before it corrupts downstream composite-score
   arithmetic.
3. **List-field fill rate** — list fields are non-empty, not just technically
   satisfying a `min_length=1` with a placeholder.
4. **Judge-scored quality** (`training/eval/judge.py`) — a qualitative
   rubric score from an independent LLM judge (always the fallback provider,
   never the model under test — a model cannot grade its own homework).
   Rubrics live in `training/eval/rubrics/<crew_dir>.yaml`, one per crew,
   each with 3–4 criteria specific to that crew's actual failure modes (see
   e.g. `research_patent.yaml`'s `groundedness` criterion, which exists
   specifically because patent-holder hallucination is this pipeline's
   highest-stakes failure surface).

## Establishing the baseline (do this FIRST)

Before any fine-tune exists, record a baseline against the fallback
provider:

```bash
python -m training.eval.harness --tier heavy --backend fallback \
    --out training/eval/results/baseline.json
```

This is not optional pre-work — without it, there is nothing to prove a
fine-tuned model is actually an improvement over what the pipeline already
does today. [ADR 0003](../architecture/0003-qwen3-base-models.md)'s Qwen3
choice was made on published benchmarks precisely because this baseline
couldn't be measured against a real candidate in the development
environment; closing that loop once the DGX is reachable is this doc's job.

## Promotion gating

```bash
python -m training.eval.harness --tier heavy --backend selfhosted \
    --out training/eval/results/qwen3-32b-v1.json
python -m training.eval.report \
    --baseline training/eval/results/baseline.json \
    --candidate training/eval/results/qwen3-32b-v1.json
```

`training/eval/report.py` enforces hard gates (see the file for the exact
thresholds — currently 90% minimum schema-validity, 95% minimum
numeric-range compliance, no more than 5 percentage points of regression
vs. baseline on any target). A candidate failing **any** gate is not
promoted, full stop — these are pipeline-breaking failure modes
([ADR 0001](../architecture/0001-llm-gateway.md)'s repair loop has bounded
attempts; a model with a high raw failure rate will exhaust it often enough
to matter), not soft quality preferences to average away.

## What promotion actually changes

A promoted model/adapter combination becomes the new
`LLM_MODEL_HEAVY`/`LLM_MODEL_FAST` (or the new LoRA adapter path in
`training/serve/adapters.yaml`) — update those, restart the vLLM server(s)
per [serving.md](serving.md), and re-run the eval harness against the live
endpoint as a final smoke check before considering the promotion complete.

## Judge cost and reliability

The judge makes one additional LLM call per evaluated example (always
against the fallback provider). For a full eval run across all 28 current
targets × N seed ideas, budget for `28 * N` extra fallback-provider calls —
this is a real, ongoing cost of running eval, not a one-time setup cost, and
should scale with how often promotions are actually attempted, not run on
every commit.
