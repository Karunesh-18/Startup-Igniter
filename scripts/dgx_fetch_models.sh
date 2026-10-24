#!/usr/bin/env bash
# BACKUP path: download the weights directly on the DGX instead of rsync-ing bundle/ from a PC.
# Same destination (bundle/models/) and same checksum file, so vllm_up.sh and dgx_preflight.sh
# work unchanged. Resumable: just re-run after an interruption. Needs the venv from dgx_setup.sh.
# Optional: export HF_TOKEN=... for higher rate limits.
set -euo pipefail
cd "$(dirname "$0")/.."
export HF_XET_HIGH_PERFORMANCE=1   # saturate the link on fast connections
python scripts/fetch_models.py "$@"
