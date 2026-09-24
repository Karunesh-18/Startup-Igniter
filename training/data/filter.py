"""Quality filtering for the raw generated corpus.

Schema validity is already enforced at generation time (generate.py drops
any row that fails `model_validate` rather than writing it) — this stage
handles what generation-time validation can't catch:

1. Near-duplicate removal (MinHash over the completion JSON) — the fallback
   provider tends to produce very similar phrasing across different seed
   ideas in the same category, and training on near-duplicates wastes
   capacity and encourages memorization of phrasing over the underlying task.
2. Length bounds — reject completions that are suspiciously short (a
   truncated or degenerate response that happened to still validate against
   the schema, e.g. every list field satisfying `min_length=1` with a single
   two-word placeholder-shaped string) or suspiciously long (runaway
   generation, more common on `mock_mode` misconfiguration than real models,
   but worth guarding regardless).
"""

import argparse
import json
from pathlib import Path
from typing import Iterator

from datasketch import MinHash, MinHashLSH

MIN_COMPLETION_CHARS = 80
MAX_COMPLETION_CHARS = 8000
MINHASH_NUM_PERM = 128
MINHASH_THRESHOLD = 0.85  # rows above this Jaccard similarity are considered near-duplicates


def _shingles(text: str, k: int = 5) -> set[str]:
    """Character k-shingles -- robust to minor wording differences that word-level
    shingling would treat as completely different."""
    text = text.lower()
    return {text[i : i + k] for i in range(max(len(text) - k + 1, 1))}


def _minhash_for(text: str) -> MinHash:
    mh = MinHash(num_perm=MINHASH_NUM_PERM)
    for shingle in _shingles(text):
        mh.update(shingle.encode("utf-8"))
    return mh


def _length_ok(completion: dict) -> bool:
    length = len(json.dumps(completion, ensure_ascii=False))
    return MIN_COMPLETION_CHARS <= length <= MAX_COMPLETION_CHARS


def filter_corpus(rows: Iterator[dict]) -> Iterator[dict]:
    """Yield rows that pass length bounds and are not a near-duplicate of an
    earlier row FOR THE SAME (target_name) — duplicate detection is scoped
    per-agent since two different agents legitimately producing similarly-
    shaped JSON for the same seed idea is not the problem being solved here.
    """
    lsh = MinHashLSH(threshold=MINHASH_THRESHOLD, num_perm=MINHASH_NUM_PERM)
    seen_count = 0
    kept = 0
    dropped_length = 0
    dropped_duplicate = 0

    for row in rows:
        seen_count += 1
        if not _length_ok(row["completion"]):
            dropped_length += 1
            continue

        key = f"{row['target_name']}::{row['id']}"
        completion_text = json.dumps(row["completion"], sort_keys=True, ensure_ascii=False)
        mh = _minhash_for(f"{row['target_name']}::{completion_text}")

        near_dupes = lsh.query(mh)
        if near_dupes:
            dropped_duplicate += 1
            continue

        lsh.insert(key, mh)
        kept += 1
        yield row

    import sys

    print(
        f"filter_corpus: {seen_count} in, {kept} kept, "
        f"{dropped_length} dropped (length), {dropped_duplicate} dropped (near-duplicate)",
        file=sys.stderr,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in", dest="input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    def read_rows() -> Iterator[dict]:
        with args.input.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for row in filter_corpus(read_rows()):
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
