"""Download every model the DGX needs into bundle/models/ (run on a machine with internet).

    python scripts/fetch_models.py            # all
    python scripts/fetch_models.py Qwen/Qwen3-8B

Resumable: re-run after an interruption. Writes bundle/SHA256SUMS when done.
"""
import hashlib
import sys
from pathlib import Path

from huggingface_hub import snapshot_download

BUNDLE = Path(__file__).resolve().parents[1] / "bundle"
MODELS = ["Qwen/Qwen3-32B", "Qwen/Qwen3-8B", "sentence-transformers/all-MiniLM-L6-v2"]
# safetensors + tokenizer/config only; skip duplicate .bin/.onnx/.gguf weights
PATTERNS = ["*.safetensors", "*.json", "*.txt", "*.model", "*.tiktoken", "*.jinja"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    for repo in sys.argv[1:] or MODELS:
        dest = BUNDLE / "models" / repo.split("/")[-1]
        print(f"==> {repo} -> {dest}", flush=True)
        snapshot_download(repo, local_dir=dest, allow_patterns=PATTERNS)
    sums = BUNDLE / "SHA256SUMS"
    with sums.open("w", newline="\n") as out:
        for f in sorted((BUNDLE).rglob("*")):
            if f.is_file() and f != sums and ".cache" not in f.parts and f.parent.name != "wheels_tmp":
                out.write(f"{sha256(f)}  {f.relative_to(BUNDLE).as_posix()}\n")
    print("done; checksums in", sums)


if __name__ == "__main__":
    main()
