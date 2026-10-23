#!/usr/bin/env bash
# Run FIRST on the DGX (docs/ops/dgx-runbook.md step 1). Non-zero exit = do not proceed.
cd "$(dirname "$0")/.."
fail=0
ok()  { echo "OK   $*"; }
bad() { echo "FAIL $*"; fail=1; }

n=$(nvidia-smi -L 2>/dev/null | grep -c B200 || true)
if [ "$n" -ge 3 ]; then ok "$n x B200 visible"; else bad "expected B200 GPUs, nvidia-smi -L shows $n"; fi
echo "     (eyeball NVLink with: nvidia-smi topo -m)"

python - <<'PY' || fail=1
import sys, torch
cap = torch.cuda.get_device_capability() if torch.cuda.is_available() else None
cuda = tuple(map(int, (torch.version.cuda or "0.0").split(".")[:2]))
good = cap == (10, 0) and cuda >= (12, 8)
print("OK  " if good else "FAIL", f"torch {torch.__version__} cuda {torch.version.cuda} capability {cap} (need (10, 0), CUDA >= 12.8)")
sys.exit(0 if good else 1)
PY

for m in Qwen3-32B Qwen3-8B all-MiniLM-L6-v2; do
  if [ -f "bundle/models/$m/config.json" ]; then ok "model $m present"; else bad "bundle/models/$m missing"; fi
done
if [ -f bundle/SHA256SUMS ]; then
  if (cd bundle && sha256sum -c --quiet SHA256SUMS); then ok "bundle checksums match"; else bad "bundle checksum mismatch (re-run rsync)"; fi
else bad "bundle/SHA256SUMS missing"; fi

free=$(df -BG --output=avail . | tail -1 | tr -dc 0-9)
if [ "$free" -ge 100 ]; then ok "${free}G free disk"; else bad "only ${free}G free (need ~100G+ for checkpoints)"; fi
exit $fail
