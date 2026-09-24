#!/usr/bin/env bash
# Launch the two vLLM servers this pipeline's gateway expects:
#   HEAVY/REASONING tier -> Qwen3-32B, TP=2 (4 replicas of TP=2 across 8 GPUs)
#   FAST tier            -> Qwen3-8B,  TP=1
#
# See docs/ops/serving.md for the full topology rationale (why TP=2 not 4 or
# 8, why two separate servers rather than one multiplexed one, and the
# Blackwell/CUDA version constraints to check FIRST).
#
# Usage: bash training/serve/vllm_up.sh
set -euo pipefail

MODEL_HEAVY="${LLM_MODEL_HEAVY:-Qwen/Qwen3-32B}"
MODEL_FAST="${LLM_MODEL_FAST:-Qwen/Qwen3-8B}"
ADAPTERS_DIR="${ADAPTERS_DIR:-./training/adapters}"

# --- HEAVY/REASONING: Qwen3-32B on GPUs 0-1 (TP=2) --------------------------
CUDA_VISIBLE_DEVICES=0,1 python -m vllm.entrypoints.openai.api_server \
  --model "${MODEL_HEAVY}" \
  --tensor-parallel-size 2 \
  --dtype bfloat16 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.90 \
  --guided-decoding-backend xgrammar \
  --enable-lora \
  --lora-modules \
    idea_validation="${ADAPTERS_DIR}/qwen3-32b/idea_validation" \
    market_research="${ADAPTERS_DIR}/qwen3-32b/market_research" \
    research_patent="${ADAPTERS_DIR}/qwen3-32b/research_patent" \
  --max-lora-rank 32 \
  --port 8001 \
  > logs/vllm-heavy.log 2>&1 &

echo "Qwen3-32B (HEAVY/REASONING) starting on port 8001, PID $!"

# --- FAST: Qwen3-8B on GPUs 2-2 (TP=1) --------------------------------------
CUDA_VISIBLE_DEVICES=2 python -m vllm.entrypoints.openai.api_server \
  --model "${MODEL_FAST}" \
  --tensor-parallel-size 1 \
  --dtype bfloat16 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.90 \
  --guided-decoding-backend xgrammar \
  --enable-lora \
  --lora-modules \
    idea_validation="${ADAPTERS_DIR}/qwen3-8b/idea_validation" \
    market_research="${ADAPTERS_DIR}/qwen3-8b/market_research" \
    research_patent="${ADAPTERS_DIR}/qwen3-8b/research_patent" \
  --max-lora-rank 16 \
  --port 8002 \
  > logs/vllm-fast.log 2>&1 &

echo "Qwen3-8B (FAST) starting on port 8002, PID $!"

# GPUs 3-7 (5x B200) stay free for training jobs (see training/configs/*.yaml)
# and/or additional replicas once load-testing shows single-replica
# throughput is the bottleneck (see docs/ops/serving.md's scaling notes).

echo ""
echo "Point the gateway at these directly -- no router needed:"
echo "  LLM_BASE_URL=http://<this-host>:8001/v1       (HEAVY/REASONING, Qwen3-32B)"
echo "  LLM_BASE_URL_FAST=http://<this-host>:8002/v1  (FAST, Qwen3-8B)"
