#!/usr/bin/env bash
# One-time DGX environment setup (needs internet for pip only; model weights come from bundle/).
# Creates .venv with Python 3.12 via uv, installs vllm (pulls a Blackwell-capable torch),
# axolotl for training, and this repo's training tooling.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
[ -d .venv ] || uv venv --python 3.12 .venv
. .venv/bin/activate
uv pip install vllm --torch-backend=auto      # picks the CUDA build matching the driver
uv pip install axolotl accelerate peft datasets
uv pip install -e training/
uv pip install -r <(python - <<'PY'
import tomllib; print("\n".join(tomllib.load(open("backend/pyproject.toml","rb"))["project"]["dependencies"]))
PY
)
python -c "import torch,vllm;print('torch',torch.__version__,'cuda',torch.version.cuda,'vllm',vllm.__version__)"
echo "Next: bash scripts/dgx_preflight.sh"
