# Serving: vLLM topology

## Topology

Two separate vLLM server processes (vLLM serves one base model per process —
there is no way to multiplex Qwen3-32B and Qwen3-8B behind one process):

| Server | Model | GPUs | TP | Port | Purpose |
|---|---|---|---|---|---|
| `vllm-heavy` | Qwen3-32B | 0-1 | 2 | 8001 | `ModelTier.HEAVY` + `ModelTier.REASONING` |
| `vllm-fast` | Qwen3-8B | 2 | 1 | 8002 | `ModelTier.FAST` |

GPUs 3-7 (5 of 8) stay free for training jobs (see [training.md](training.md))
and/or additional inference replicas once load-testing shows a real need.

**Why TP=2 for the 32B model, not TP=1/4/8?** At bf16, Qwen3-32B's weights
are ~64GB — comfortably fits on a single B200 (180GB) memory-wise, so TP=1
would work. TP=2 is chosen for latency: splitting attention/MLP computation
across 2 GPUs roughly halves per-token latency for a model this size,
without the diminishing returns and cross-GPU communication overhead TP=4/8
would add for a model that doesn't need that much sharding. **This is a
reasoned starting point, not a benchmarked one** — see
[dgx-runbook.md](dgx-runbook.md)'s "known unknowns."

**Why the gateway doesn't need a router in front of these two ports**: see
`ai/llm/settings.py::LLMSettings.selfhosted_base_url_for_tier` — the gateway
picks `LLM_BASE_URL` vs `LLM_BASE_URL_FAST` per tier itself, since a plain
reverse proxy can't cleanly route on a JSON body's `"model"` field without
scripting. Set both env vars and there's nothing else to run.

## LoRA adapter hot-swap

Both servers launch with `--enable-lora` and `--lora-modules` pointing at
`training/adapters/<model>/<crew_dir>/` (see
[ADR 0003](../architecture/0003-qwen3-base-models.md) for why adapters are
per-crew, not per-agent). `training/serve/adapters.yaml` is the registry of
which adapters exist and their training provenance — keep
`vllm_up.sh`/`compose.yaml`'s `--lora-modules` flags in sync with it.

A crew without a trained adapter yet (the 9 specified crews) simply isn't
listed — vLLM serves the base model unadapted for any request that doesn't
name one of the configured LoRA modules, which is the correct behavior for
an untrained crew (no adapter is strictly better than a wrong one).

## Guided decoding

Both servers run `--guided-decoding-backend xgrammar` — this is what makes
`ai.llm.providers.openai_http.build_json_schema_response_format`'s
`response_format: {"type": "json_schema", ...}` actually constrain
generation (see [ADR 0001](../architecture/0001-llm-gateway.md)). Confirm
this flag survives whatever vLLM version is actually installed once
[dgx-runbook.md](dgx-runbook.md)'s capability check pins one — guided
decoding backend flags have changed name across vLLM versions.

## Precision

Both configs launch with `--dtype bfloat16`. B200 supports FP8 and NVFP4
natively — moving to FP8 serving is a legitimate next step for
throughput/memory, but **only after** validating that FP8 doesn't regress
[eval.md](eval.md)'s schema-validity/groundedness gates versus the bf16
baseline. This mirrors the general principle in
[ADR 0003](../architecture/0003-qwen3-base-models.md): measure before
committing to a precision change, don't assume it's free.

## Scaling notes

If load testing shows single-replica throughput is the bottleneck: the 5
free GPUs (3-7) can run additional replicas of either server behind a
load-balancer-aware gateway change (today's gateway assumes one URL per
tier, not a pool) — that's a real code change to
`ai/llm/settings.py`/`ai/llm/providers/selfhosted.py`, not just a deployment
change, and should wait for actual measured throughput pressure rather than
being built speculatively.
