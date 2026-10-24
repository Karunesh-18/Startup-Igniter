#!/usr/bin/env bash
# Corpus -> LoRA adapters for crews 1-3 on the DGX.
# Needs vllm_up.sh running first: the teacher is base Qwen3-32B on :47001 (generation goes
# through the gateway, so LLM_BASE_URL must point at it). Serving is stopped before
# training so axolotl gets the GPUs.
# Usage: bash scripts/train_all.sh [8b|32b]     (default 8b; DRY_RUN=1 prints steps)
set -euo pipefail
cd "$(dirname "$0")/.."
SIZE="${1:-8b}"
run() { echo "+ $*"; if [ "${DRY_RUN:-0}" != 1 ]; then "$@"; fi; }
export LLM_BASE_URL="${LLM_BASE_URL:-http://localhost:47001/v1}" LLM_ALLOW_MOCK=false
C=training/data/corpus
mkdir -p "$C" logs

run python -m training.data.generate --out "$C/raw.jsonl"
run python -m training.data.filter --in "$C/raw.jsonl" --out "$C/filtered.jsonl"

declare -A CREW_ID=([idea_validation]=1 [market_research]=2 [research_patent]=3)
for crew in "${!CREW_ID[@]}"; do
  d="$C/$crew"
  mkdir -p "$d"
  if [ "${DRY_RUN:-0}" != 1 ]; then
    python - "$C/filtered.jsonl" "${CREW_ID[$crew]}" "$d/filtered.jsonl" <<'PY'
import json, sys
src, cid, dst = sys.argv[1], int(sys.argv[2]), sys.argv[3]
with open(src, encoding="utf-8") as f, open(dst, "w", encoding="utf-8") as o:
    for line in f:
        if json.loads(line)["crew_id"] == cid:
            o.write(line)
PY
  fi
  run python -m training.data.splits --in "$d/filtered.jsonl" --out-dir "$d"
  for s in train val; do
    run python -m training.data.to_chat_format --in "$d/$s.jsonl" --out "$d/$s.chat.jsonl"
  done
done

run bash training/serve/vllm_down.sh   # free the GPUs
for crew in "${!CREW_ID[@]}"; do
  tmp="logs/train-$SIZE-$crew.yaml"
  sed "s#idea_validation#$crew#g" "training/configs/qwen3-$SIZE-lora.yaml" > "$tmp"
  run accelerate launch -m axolotl.cli.train "$tmp"
done
echo "Adapters in training/adapters/qwen3-$SIZE/*. Run docs/ops/eval.md gates, then bash training/serve/vllm_up.sh (auto-attaches them)."
