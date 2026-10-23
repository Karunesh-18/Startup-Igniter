"""Synthetic training corpus generator.

Crosses every SeedIdea (training/data/taxonomy.py) with every TrainingTarget
(training/data/agent_registry.py), calls the LLM gateway to produce a target
completion (the teacher is whatever LLM_BASE_URL points at -- on the DGX that is
the BASE Qwen3-32B before any adapter exists, i.e. self-distillation; the
schema validation + filter.py + docs/ops/eval.md gates are what keep quality up), validates it against the real schema, and writes one JSONL row
per example.

Usage:
    python -m training.data.generate --out training/data/corpus/raw.jsonl
    python -m training.data.generate --out /tmp/smoke.jsonl --mock --limit 3

Every row that fails schema validation is DROPPED, not repaired -- the
model must never train on a "fixed" bad example, since the fix itself may
have been mechanical rather than a genuinely better answer. See
docs/ops/training.md for the full corpus-quality rationale.
"""

import argparse
import json
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from ai.llm.gateway import get_gateway
from ai.shared.constants import ModelTier
from ai.shared.errors import OutputValidationError, StartupOSAIError
from ai.shared.logger import ai_logger
from training.data.agent_registry import CREW_PURPOSE, TrainingTarget, all_targets
from training.data.taxonomy import SEED_IDEAS, SeedIdea


def build_prompt(seed: SeedIdea, target: TrainingTarget) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for one (seed, target) pair.

    For implemented per-agent targets: pulls the REAL system prompt straight
    out of the agent factory's dict (the same `backstory` the live crew uses
    as its system_prompt at inference time).

    For specified crew-level targets: synthesizes a system prompt from the
    crew's stated purpose (agent_registry.CREW_PURPOSE) since no per-agent
    prompt file exists yet for crews 4-12.
    """
    if target.crew_level:
        system_prompt = (
            f"You are the {target.name.replace('_', ' ')} for a startup analysis pipeline. "
            f"{CREW_PURPOSE[target.crew_id]} Return pure JSON only, matching the required schema."
        )
    else:
        agent_dict = target.get_agent_fn(mock_mode=True)  # mock_mode=True: dict construction only, no network
        system_prompt = agent_dict["backstory"]

    user_prompt = (
        f"Startup idea ({seed.category}, {seed.quality_band.value} description):\n\n"
        f'"{seed.idea_text}"\n\n'
        "Analyze this proposal and return pure JSON matching the required schema. "
        "No markdown fences, no commentary outside the JSON object."
    )
    return system_prompt, user_prompt


def schema_for(target: TrainingTarget) -> Any:
    if target.crew_level:
        return target.schema_class
    agent_dict = target.get_agent_fn(mock_mode=True)
    return agent_dict["schema_class"]


def generate_one(seed: SeedIdea, target: TrainingTarget, *, mock: bool, tier: ModelTier) -> Optional[Dict[str, Any]]:
    """Generate and validate one training example. Returns None (dropped) on
    any failure -- never a partially-fixed row."""
    system_prompt, user_prompt = build_prompt(seed, target)
    schema_class = schema_for(target)

    try:
        result = get_gateway().invoke_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema_class=schema_class,
            tier=tier,
            allow_mock_fallback=mock,
        )
    except (OutputValidationError, StartupOSAIError) as err:
        ai_logger.warning(f"Dropped example (seed={seed.id}, target={target.name}): {err}")
        return None

    return {
        "id": str(uuid.uuid4()),
        "seed_id": seed.id,  # used by splits.py to split by IDEA, never by row
        "category": seed.category,
        "quality_band": seed.quality_band.value,
        "crew_id": target.crew_id,
        "agent_id": target.agent_id,
        "target_name": target.name,
        "schema_name": schema_class.__name__,
        "crew_level": target.crew_level,
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "completion": result.model_dump(),
        "generated_at": time.time(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="Output JSONL path.")
    parser.add_argument("--mock", action="store_true", help="Use the mock provider (no real API calls) -- for smoke-testing the pipeline itself.")
    parser.add_argument("--limit", type=int, default=None, help="Cap total examples generated (for smoke tests).")
    parser.add_argument("--tier", choices=["fast", "heavy", "reasoning"], default="heavy")
    args = parser.parse_args()

    tier = ModelTier(args.tier)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    dropped = 0
    with args.out.open("w", encoding="utf-8") as f:
        for target in all_targets():
            for seed in SEED_IDEAS:
                if args.limit and written >= args.limit:
                    break
                row = generate_one(seed, target, mock=args.mock, tier=tier)
                if row is None:
                    dropped += 1
                    continue
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                written += 1
            if args.limit and written >= args.limit:
                break

    print(f"Wrote {written} examples to {args.out} ({dropped} dropped on validation failure).")


if __name__ == "__main__":
    main()
