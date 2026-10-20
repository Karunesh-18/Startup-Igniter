"""Aggregate harness.py results and decide whether a model is safe to promote.

A model is a candidate for serving in place of the current one only if it
does not regress on any of the hard gates below relative to the current
baseline (see docs/ops/eval.md for the full promotion procedure, including
why the FIRST comparison must always be against the fallback-provider
baseline recorded before any fine-tune exists).

Usage:
    python -m training.eval.report --baseline training/eval/results/baseline.json \\
        --candidate training/eval/results/qwen3-32b.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Windows consoles default to cp1252, which can't encode the checkmark/cross
# glyphs below (a real crash hit while smoke-testing this script) -- force
# UTF-8 stdout so this runs the same on Windows, Linux, and CI regardless of
# the host's default locale.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Hard gates -- a candidate failing ANY of these is not promoted, regardless
# of how it scores elsewhere. These thresholds are intentionally strict:
# schema validity failures are pipeline-breaking (see docs/architecture/0001-llm-gateway.md's
# repair loop -- a raw validity rate this low would exhaust repair attempts
# often enough to matter), not just a quality nit.
MIN_SCHEMA_VALIDITY_RATE = 0.90
MIN_NUMERIC_RANGE_COMPLIANCE = 0.95
MAX_REGRESSION_VS_BASELINE = 0.05  # a candidate may not score more than 5pp worse than baseline on any target


def load_results(path: Path) -> Dict[str, Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {r["target"]: r for r in data["results"]}


def evaluate_gates(baseline: Dict[str, Dict[str, Any]], candidate: Dict[str, Dict[str, Any]]) -> List[str]:
    """Return a list of gate failures (empty list == promote)."""
    failures: List[str] = []

    for target_name, cand in candidate.items():
        if cand["schema_validity_rate"] < MIN_SCHEMA_VALIDITY_RATE:
            failures.append(
                f"{target_name}: schema_validity_rate {cand['schema_validity_rate']:.2%} "
                f"< minimum {MIN_SCHEMA_VALIDITY_RATE:.2%}"
            )

        if cand["numeric_range_compliance"] is not None and cand["numeric_range_compliance"] < MIN_NUMERIC_RANGE_COMPLIANCE:
            failures.append(
                f"{target_name}: numeric_range_compliance {cand['numeric_range_compliance']:.2%} "
                f"< minimum {MIN_NUMERIC_RANGE_COMPLIANCE:.2%}"
            )

        base = baseline.get(target_name)
        if base is not None:
            regression = base["schema_validity_rate"] - cand["schema_validity_rate"]
            if regression > MAX_REGRESSION_VS_BASELINE:
                failures.append(
                    f"{target_name}: schema_validity_rate regressed {regression:.2%} vs baseline "
                    f"(baseline {base['schema_validity_rate']:.2%}, candidate {cand['schema_validity_rate']:.2%})"
                )

    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    args = parser.parse_args()

    baseline = load_results(args.baseline)
    candidate = load_results(args.candidate)

    failures = evaluate_gates(baseline, candidate)

    if failures:
        print(f"❌ NOT PROMOTABLE — {len(failures)} gate failure(s):")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"✅ PROMOTABLE — all {len(candidate)} targets pass every gate vs baseline.")
        sys.exit(0)


if __name__ == "__main__":
    main()
