# ADR 0003: Qwen3-32B / Qwen3-8B as the self-hosted base models

**Status:** Decided, not yet trained (DGX not reachable) · **Date:** 2026-09-24

## Context

The pipeline's `ModelTier` enum (`ai/shared/constants.py`) already had a
3-tier shape — `FAST` (routing/classification), `HEAVY` (deep reasoning),
`REASONING` (complex multi-step reasoning) — mapped to Groq's
`llama-3.1-8b-instant` / `llama-3.3-70b-versatile` /
`deepseek-r1-distill-llama-70b`. A self-hosted replacement needs to fill the
same 3 roles without requiring 3 separately-trained model families.

Constraints as given:
- 32GB of model weights is not downloadable in the current environment —
  base-model selection had to be decided without downloading or running it.
- The DGX B200 (8× ~180GB HBM3e ≈ 1.4TB total) is not reachable yet.
- Local dev happens on a 6GB RTX 3060 laptop GPU — nowhere near enough for
  either candidate at full precision.

## Decision

- **`ModelTier.HEAVY` and `ModelTier.REASONING` → Qwen3-32B**
- **`ModelTier.FAST` → Qwen3-8B**

Both served from vLLM with `--enable-lora` for per-crew adapters (see
[docs/ops/serving.md](../ops/serving.md)), on 8×B200 — memory is not the
constraint at this scale (32B and 8B both fit with enormous headroom), so
the split exists for *latency/cost* reasons: FAST-tier calls (classification,
structural extraction) don't need a 32B model's latency, and the existing
`ModelTier` enum already assumed this two-speed shape.

**Why Qwen3, not Llama 3.3 70B (closest to today's behavior)?**
- Native reasoning-mode support (`<think>` blocks) that the gateway's
  `strip_think_blocks` was built to handle — Qwen3 is designed for exactly
  the FAST/HEAVY-vs-deep-reasoning split this pipeline already has.
- Strong instruction-following and JSON-schema adherence in independent
  benchmarks, which matters more here than raw parameter count: every one of
  this pipeline's ~20 (eventually 66) LLM calls is a structured-extraction
  task over supplied context (the idea text, upstream phase outputs,
  research bundle snippets) — not open-ended generation. A well-instructed
  32B doing extraction over supplied context is a reasonable match for a
  70B's general capability on this specific task shape, which is also why
  [ADR 0005](0005-grounding-layer.md)'s grounding work matters: the model's
  job is increasingly "structure this supplied information correctly," not
  "recall a fact from training."
- Apache 2.0 licensing, no usage restrictions.

**Why not benchmark first and decide later?** The user explicitly asked for
code now, given no ability to download and run either candidate in this
environment. This decision is therefore made on published benchmarks and
architectural fit, not measurement — [docs/ops/eval.md](../ops/eval.md)'s
harness exists specifically to validate or overturn this choice once the DGX
is reachable, before committing to a full fine-tune.

## Consequences

- `ai/llm/settings.py::LLMSettings.llm_model_heavy` defaults to
  `"Qwen/Qwen3-32B"`, `llm_model_fast` to `"Qwen/Qwen3-8B"` — override via
  `LLM_MODEL_HEAVY`/`LLM_MODEL_FAST` if a different model is deployed.
- The training pipeline ([docs/ops/training.md](../ops/training.md)) targets
  these two specific model architectures for its LoRA/QLoRA configs.
- Adapter granularity is **per-crew (12), not per-agent (66)** — a 66-way
  split would starve each adapter's training set and multiply serving
  complexity for no benefit, since an agent's identity already arrives via
  its system prompt, not via a separately-trained adapter.

## Reversibility

This is a config change, not an architectural one: swapping
`LLM_MODEL_HEAVY`/`LLM_MODEL_FAST` to a different self-hosted model requires
no code change to `ai/llm/`, only to the training configs and re-running the
eval harness. If eval results once the DGX is reachable don't support this
choice, switching is cheap.
