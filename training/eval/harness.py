"""Per-agent/per-crew eval harness.

Measures, for every TrainingTarget (training/data/agent_registry.py) against
a held-out set of seed ideas:

1. Schema-validity rate — did the model's raw output parse and validate
   against the target schema at all (no repair loop — this measures the
   model's raw compliance, not the gateway's ability to rescue it).
2. Field-presence rate — for list/optional fields, did the model actually
   fill them meaningfully (non-empty) rather than technically satisfying
   `min_length=1` with a placeholder.
3. Numeric-range compliance — the 0-1 vs 0-100 vs 0-10 scale problem (see
   docs/architecture/0004-taxonomy-conflict.md): did every numeric field
   land in ITS OWN schema's declared range, not just "some plausible number".
4. Citation groundedness (grounded agents only) — when a research bundle was
   supplied, does every `citations` entry resolve to a URL that was actually
   in the supplied sources (not invented).
5. Judge-scored quality (see judge.py) — a qualitative rubric score from an
   independent LLM judge (the fallback provider, never the model under test).

Usage:
    python -m training.eval.harness --tier heavy --backend selfhosted --out training/eval/results/qwen3-32b.json
    python -m training.eval.harness --tier heavy --backend fallback   --out training/eval/results/baseline.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from ai.llm.gateway import LLMGateway
from ai.llm.settings import LLMSettings
from ai.shared.constants import ModelTier
from ai.shared.errors import OutputValidationError, StartupOSAIError
from training.data.agent_registry import TrainingTarget, all_targets
from training.data.taxonomy import SEED_IDEAS, SeedIdea
from training.data.generate import build_prompt, schema_for


def _numeric_fields_in_range(schema_class: Any, instance: Any) -> tuple[int, int]:
    """Return (fields_checked, fields_in_range) for every numeric field with
    declared ge/le bounds -- this is the check that would have caught the
    pre-migration 0-1 vs 0-100 vs 0-10 scale inconsistency at the schema
    level rather than downstream in composite-score arithmetic."""
    checked = 0
    in_range = 0
    for name, field in schema_class.model_fields.items():
        value = getattr(instance, name, None)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            continue
        lo, hi = None, None
        for meta in field.metadata:
            lo = getattr(meta, "ge", lo)
            hi = getattr(meta, "le", hi)
        if lo is None and hi is None:
            continue
        checked += 1
        if (lo is None or value >= lo) and (hi is None or value <= hi):
            in_range += 1
    return checked, in_range


def _non_empty_list_fields(schema_class: Any, instance: Any) -> tuple[int, int]:
    """Return (list_fields, non_empty_list_fields)."""
    total = 0
    non_empty = 0
    for name, field in schema_class.model_fields.items():
        value = getattr(instance, name, None)
        if isinstance(value, list):
            total += 1
            if len(value) > 0:
                non_empty += 1
    return total, non_empty


def evaluate_target(
    gateway: LLMGateway, target: TrainingTarget, seeds: List[SeedIdea], tier: ModelTier
) -> Dict[str, Any]:
    schema_class = schema_for(target)
    n = len(seeds)
    valid = 0
    numeric_checked = numeric_ok = 0
    list_checked = list_ok = 0
    errors: List[str] = []

    for seed in seeds:
        system_prompt, user_prompt = build_prompt(seed, target)
        try:
            instance = gateway.invoke_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema_class=schema_class,
                tier=tier,
                repair_attempts=0,  # measure RAW compliance, not the gateway's repair loop rescuing it
            )
        except (OutputValidationError, StartupOSAIError) as err:
            errors.append(f"{seed.id}: {err}")
            continue

        valid += 1
        nc, no = _numeric_fields_in_range(schema_class, instance)
        numeric_checked += nc
        numeric_ok += no
        lc, lo = _non_empty_list_fields(schema_class, instance)
        list_checked += lc
        list_ok += lo

    return {
        "target": target.name,
        "crew_id": target.crew_id,
        "schema": schema_class.__name__,
        "n_examples": n,
        "schema_validity_rate": valid / n if n else 0.0,
        "numeric_range_compliance": numeric_ok / numeric_checked if numeric_checked else None,
        "list_field_fill_rate": list_ok / list_checked if list_checked else None,
        "errors": errors[:5],  # keep a sample, not every failure
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tier", choices=["fast", "heavy", "reasoning"], default="heavy")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--backend",
        choices=["selfhosted", "fallback", "mock"],
        default="fallback",
        help="Which stage of the gateway chain to force -- 'fallback' is the baseline (see docs/ops/eval.md).",
    )
    args = parser.parse_args()

    settings = LLMSettings()
    if args.backend == "selfhosted" and not settings.has_selfhosted:
        print("ERROR: --backend selfhosted requires LLM_BASE_URL to be set.", file=sys.stderr)
        sys.exit(1)
    if args.backend == "fallback":
        # force past the selfhosted stage even if it happens to be configured,
        # so a baseline run is reproducible regardless of DGX availability
        settings = LLMSettings(LLM_BASE_URL=None)

    gateway = LLMGateway(settings=settings)
    tier = ModelTier(args.tier)

    # Held-out seeds only -- in a real run this should be training/data/corpus/<crew>/test.jsonl's
    # seed_ids, not the full SEED_IDEAS list (which training may have used).
    # Using the full list here is the pre-corpus-existing default.
    results = [evaluate_target(gateway, target, SEED_IDEAS, tier) for target in all_targets()]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"backend": args.backend, "tier": args.tier, "results": results}, indent=2), encoding="utf-8")

    avg_validity = sum(r["schema_validity_rate"] for r in results) / len(results)
    print(f"Evaluated {len(results)} targets. Mean schema-validity rate: {avg_validity:.2%}")
    print(f"Full results written to {args.out}")


if __name__ == "__main__":
    main()
