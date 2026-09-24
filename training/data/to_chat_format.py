"""Convert generate.py's row shape into axolotl's `messages` chat format.

generate.py/filter.py/splits.py all work with a flat row shape
({system_prompt, user_prompt, completion, ...metadata}) because that's the
natural shape for schema validation and dedup. axolotl's `chat_template`
dataset type expects a `messages: [{role, content}, ...]` list instead. This
is a separate, final step (not folded into splits.py) so the flat shape
stays available for the eval harness, which wants the metadata columns
splits.py's output preserves.

Usage:
    python -m training.data.to_chat_format \\
        --in training/data/corpus/idea_validation/train.jsonl \\
        --out training/data/corpus/idea_validation/train.chat.jsonl
"""

import argparse
import json
from pathlib import Path
from typing import Iterator


def to_chat_row(row: dict) -> dict:
    return {
        "messages": [
            {"role": "system", "content": row["system_prompt"]},
            {"role": "user", "content": row["user_prompt"]},
            {"role": "assistant", "content": json.dumps(row["completion"], ensure_ascii=False)},
        ]
    }


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
    count = 0
    with args.out.open("w", encoding="utf-8") as f:
        for row in read_rows():
            f.write(json.dumps(to_chat_row(row), ensure_ascii=False) + "\n")
            count += 1
    print(f"Wrote {count} chat-format rows to {args.out}")


if __name__ == "__main__":
    main()
