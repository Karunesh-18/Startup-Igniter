#!/usr/bin/env bash
# Stop the servers started by vllm_up.sh.
cd "$(dirname "$0")/../.."
for f in logs/vllm-*.pid; do
  if [ -f "$f" ]; then kill "$(cat "$f")" 2>/dev/null || true; rm -f "$f"; fi
done
echo stopped
