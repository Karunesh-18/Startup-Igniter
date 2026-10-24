# DGX B200 Runbook

## Quickstart

Weights are pre-downloaded on a PC (`python scripts/fetch_models.py` -> `bundle/`), so the DGX only
needs internet for pip.

```bash
rsync -avP --partial ./ user@dgx:~/Startup-Igniter/   # repo + bundle/ (resumable)
# BACKUP: skip bundle/ in the rsync and instead run, after dgx_setup.sh: bash scripts/dgx_fetch_models.sh
cd ~/Startup-Igniter
bash scripts/dgx_setup.sh            # uv + Python 3.12 venv + vllm/axolotl/backend deps
. .venv/bin/activate
bash scripts/dgx_preflight.sh        # B200 + CUDA>=12.8 + models + checksums; STOP if it fails
bash training/serve/vllm_up.sh       # 32B on :47001 (GPUs 0-1), 8B on :47002 (GPU 2); adapters attach only if trained
cp backend/.env.example backend/.env # fill Supabase/Upstash/SECRET_KEY; set LLM_ALLOW_MOCK=false
bash scripts/dgx_smoke.sh            # real text on both tiers + structured output
# Optional, later: corpus + LoRA training for crews 1-3, teacher = base 32B
bash scripts/train_all.sh 8b
```

Everything below is the detailed reference.

**Status:** Serving has been run. Qwen3-32B (heavy) and Qwen3-8B (fast) run under vLLM on the shared host
on ports 47001 and 47002 and are reached from the dev PC through an SSH tunnel (host, ports and tunnel command are in
the repo's `CLAUDE.md`). Training and the eval baseline have not been run.

## 1. Capability check (do this FIRST, before anything else)

B200 is `sm_100` (Blackwell). Many pinned CUDA/PyTorch/vLLM/flash-attention
versions silently lack `sm_100` kernels and either fail to build or (worse)
build successfully but silently fall back to a slow, unoptimized code path.

```bash
nvidia-smi                              # confirm 8x B200 visible, driver version
nvcc --version                          # need CUDA 12.8+
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_capability())"
# torch.cuda.get_device_capability() must report (10, 0) for sm_100
```

If `get_device_capability()` doesn't report `(10, 0)`, or `nvcc` reports
below 12.8, **stop here** — do not proceed to training or serving until the
driver/CUDA/PyTorch stack is confirmed B200-compatible. Installing a version
that merely "runs" without erroring is not the same as running on the actual
tensor cores this GPU has.

## 2. First boot checklist

1. Confirm all 8 GPUs are visible and healthy: `nvidia-smi --query-gpu=index,name,memory.total,temperature.gpu --format=csv`
2. Confirm NVLink/NVSwitch topology (matters for FSDP full-SFT and
   tensor-parallel serving): `nvidia-smi topo -m`
3. Confirm the model weights download path: `Qwen/Qwen3-32B` and
   `Qwen/Qwen3-8B` from Hugging Face — **32GB+ combined, budget the download
   time and disk space before the first run** (this is the exact constraint
   that blocked base-model verification during code development — see
   [ADR 0003](../architecture/0003-qwen3-base-models.md)).
4. Install training deps: `pip install -e training/` (see
   `training/pyproject.toml` — `torch`/`vllm` versions there are provisional
   until step 1's capability check confirms exact compatible pins).
5. Run a 1-step smoke run on a tiny stand-in model (NOT Qwen3) to validate
   the training harness itself works on this hardware before spending time
   on a real model:
   ```bash
   # Point qwen3-8b-lora.yaml's base_model at a small public model temporarily
   # (e.g. Qwen/Qwen2.5-0.5B) and run 1 step -- validates axolotl + FSDP +
   # the corpus format, without waiting on an 8B/32B download first.
   ```

## 3. Bringing up inference serving

Once step 1 passes: see [serving.md](serving.md) and
`training/serve/vllm_up.sh`.

## 4. Bringing up training

Once step 1 passes and a real corpus exists (see [training.md](training.md)):
`accelerate launch -m axolotl.cli.train training/configs/qwen3-32b-lora.yaml`

## 5. Connecting the gateway

Set on the backend (`backend/.env`, see `backend/.env.example`):
```
LLM_BASE_URL=http://<dgx-host>:47001/v1
LLM_BASE_URL_FAST=http://<dgx-host>:47002/v1   # only if FAST runs as a separate server
```
Verify with:
```bash
python -c "
from ai.llm.gateway import get_gateway
from ai.shared.constants import ModelTier
print(get_gateway().invoke(system_prompt='test', user_prompt='say OK', tier=ModelTier.FAST))
"
```
If this returns real text (not a `[MOCK]`-prefixed placeholder and not a
`MissingAPIKeyError`), the self-hosted path is live end-to-end.

## Known unknowns (fill in once the DGX is actually reachable)

- Exact vLLM version with confirmed `sm_100` support at the time of bring-up
  (vLLM's Blackwell support was landing rapidly at time of writing — pin the
  exact tested version here once confirmed, don't trust this doc's
  `pyproject.toml` placeholder pin).
- Actual first-token latency and throughput numbers for Qwen3-32B TP=2 vs
  TP=4 vs TP=8 — [serving.md](serving.md)'s TP=2 recommendation is a
  reasoned starting point, not a benchmarked one.
- Real wall-clock training time for the LoRA/full-SFT configs in
  [training.md](training.md) — currently unvalidated estimates.
