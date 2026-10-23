#!/usr/bin/env bash
# Launch the two vLLM servers the gateway expects (see docs/ops/serving.md):
#   HEAVY/REASONING -> Qwen3-32B, TP=2, GPUs 0-1, port 47001
#   FAST            -> Qwen3-8B,  TP=1, GPU 2,    port 47002
# Offline: weights come from bundle/models (see scripts/fetch_models.py).
# LoRA adapters are attached only if their directory exists, so this works
# before any training has happened.
#
# Usage: bash training/serve/vllm_up.sh        (DRY_RUN=1 prints commands only)
set -euo pipefail
cd "$(dirname "$0")/../.."

MODELS_DIR="${MODELS_DIR:-$PWD/bundle/models}"
ADAPTERS_DIR="${ADAPTERS_DIR:-$PWD/training/adapters}"
NAME_HEAVY="${LLM_MODEL_HEAVY:-Qwen/Qwen3-32B}"
NAME_FAST="${LLM_MODEL_FAST:-Qwen/Qwen3-8B}"
PATH_HEAVY="${MODEL_PATH_HEAVY:-$MODELS_DIR/Qwen3-32B}"
PATH_FAST="${MODEL_PATH_FAST:-$MODELS_DIR/Qwen3-8B}"
GPUS_HEAVY="${GPUS_HEAVY:-0,1}"; TP_HEAVY="${TP_HEAVY:-2}"
GPUS_FAST="${GPUS_FAST:-2}"
CREWS=(idea_validation market_research research_patent)

export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
mkdir -p logs

# The guided-decoding flag changed across vLLM versions; pass it only if this build has it.
# Newer builds enable structured outputs by default, so nothing is needed there.
GUIDED=()
if [ "${DRY_RUN:-0}" != 1 ] && python -m vllm.entrypoints.openai.api_server --help=all 2>/dev/null | grep -q -- '--guided-decoding-backend'; then
  GUIDED=(--guided-decoding-backend xgrammar)
fi

launch() {  # name gpus tp model_path served_name port lora_rank adapter_subdir
  local name=$1 gpus=$2 tp=$3 mpath=$4 served=$5 port=$6 rank=$7 sub=$8
  if [ "${DRY_RUN:-0}" != 1 ] && [ ! -f "$mpath/config.json" ]; then
    echo "ERROR: model not found at $mpath (copy the bundle first)"; exit 1
  fi
  local lora=() mods=() crew
  for crew in "${CREWS[@]}"; do
    if [ -f "$ADAPTERS_DIR/$sub/$crew/adapter_config.json" ]; then mods+=("$crew=$ADAPTERS_DIR/$sub/$crew"); fi
  done
  if [ ${#mods[@]} -gt 0 ]; then lora=(--enable-lora --max-lora-rank "$rank" --lora-modules "${mods[@]}"); fi
  local cmd=(python -m vllm.entrypoints.openai.api_server --model "$mpath" --served-model-name "$served"
    --tensor-parallel-size "$tp" --dtype bfloat16 --max-model-len 8192 --gpu-memory-utilization "${GPU_UTIL:-0.90}"
    "${GUIDED[@]}" "${lora[@]}" --host "${VLLM_HOST:-127.0.0.1}" --port "$port")
  echo "[$name] GPUs=$gpus port=$port adapters=${#mods[@]}"
  if [ "${DRY_RUN:-0}" = 1 ]; then echo "  CUDA_VISIBLE_DEVICES=$gpus ${cmd[*]}"; return; fi
  CUDA_VISIBLE_DEVICES=$gpus nohup "${cmd[@]}" > "logs/vllm-$name.log" 2>&1 &
  echo $! > "logs/vllm-$name.pid"
}

launch heavy "$GPUS_HEAVY" "$TP_HEAVY" "$PATH_HEAVY" "$NAME_HEAVY" 47001 32 qwen3-32b
launch fast  "$GPUS_FAST"  1           "$PATH_FAST"  "$NAME_FAST"  47002 16 qwen3-8b
if [ "${DRY_RUN:-0}" = 1 ]; then exit 0; fi

for port in 47001 47002; do
  printf "waiting for :%s " "$port"
  up=0
  for _ in $(seq 1 120); do
    if curl -sf "http://localhost:$port/health" >/dev/null; then up=1; break; fi
    printf "."; sleep 10
  done
  if [ "$up" = 1 ]; then echo " up"; else echo; echo "ERROR: :$port not healthy after 20 min, see logs/vllm-*.log"; exit 1; fi
done
echo "Ready. LLM_BASE_URL=http://localhost:47001/v1  LLM_BASE_URL_FAST=http://localhost:47002/v1"
echo "GPUs 3-7 are free for training (scripts/train_all.sh)."
