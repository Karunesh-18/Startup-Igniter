"""Train/val/test splitting -- by SEED IDEA, never by row.

Splitting by row would let paraphrases/near-variants of the same underlying
idea land in both train and test (e.g. the same seed idea generating one
example for the Startup Idea Analyzer and one for the Problem Statement
Analyzer, both derived from identical input text) -- that inflates eval
scores by testing on data the model has effectively already seen. Splitting
by `seed_id` guarantees every example from one idea lands entirely on one
side of the split.
"""

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterator, List

DEFAULT_SPLIT = {"train": 0.7, "val": 0.15, "test": 0.15}


def split_by_seed(
    rows: List[dict], ratios: Dict[str, float] = None, seed: int = 42
) -> Dict[str, List[dict]]:
    ratios = ratios or DEFAULT_SPLIT
    assert abs(sum(ratios.values()) - 1.0) < 1e-6, "split ratios must sum to 1.0"

    by_seed: Dict[str, List[dict]] = defaultdict(list)
    for row in rows:
        by_seed[row["seed_id"]].append(row)

    seed_ids = sorted(by_seed.keys())  # sorted first for determinism, then shuffled
    random.Random(seed).shuffle(seed_ids)

    n = len(seed_ids)
    n_train = round(n * ratios["train"])
    n_val = round(n * ratios["val"])

    train_ids = set(seed_ids[:n_train])
    val_ids = set(seed_ids[n_train : n_train + n_val])
    test_ids = set(seed_ids[n_train + n_val :])

    result: Dict[str, List[dict]] = {"train": [], "val": [], "test": []}
    for sid, rows_for_seed in by_seed.items():
        if sid in train_ids:
            result["train"].extend(rows_for_seed)
        elif sid in val_ids:
            result["val"].extend(rows_for_seed)
        else:
            result["test"].extend(rows_for_seed)

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in", dest="input", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    def read_rows() -> Iterator[dict]:
        with args.input.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)

    rows = list(read_rows())
    splits = split_by_seed(rows, seed=args.seed)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for split_name, split_rows in splits.items():
        out_path = args.out_dir / f"{split_name}.jsonl"
        with out_path.open("w", encoding="utf-8") as f:
            for row in split_rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        n_seeds = len({r["seed_id"] for r in split_rows})
        print(f"{split_name}: {len(split_rows)} examples from {n_seeds} seed ideas -> {out_path}")


if __name__ == "__main__":
    main()
