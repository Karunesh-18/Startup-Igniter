"""LLM-as-judge qualitative scoring.

The judge is ALWAYS the fallback provider (Groq/OpenRouter), never the
self-hosted model under test — a model cannot grade its own homework, and
using the same backend for generation and judging would silently favor
whatever stylistic quirks that backend has.

Rubrics (training/eval/rubrics/<crew_dir>.yaml) define the criteria per crew
— e.g. Idea Validation's rubric asks whether the technical feasibility
rationale is substantive and specific to the idea, not generic boilerplate
that would apply to any startup.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from ai.llm.gateway import LLMGateway
from ai.llm.settings import LLMSettings
from ai.shared.constants import ModelTier
from pydantic import BaseModel, Field

RUBRICS_DIR = Path(__file__).resolve().parent / "rubrics"


class JudgeScore(BaseModel):
    """Structured judge output -- itself schema-validated through the same
    gateway machinery as every other call in this repo."""

    criterion_scores: Dict[str, int] = Field(description="Per-criterion score, 1-5, keyed by criterion name.")
    overall_score: int = Field(ge=1, le=5, description="Overall quality score, 1-5.")
    reasoning: str = Field(min_length=10, description="Brief justification for the scores.")


def load_rubric(crew_dir: str) -> Dict[str, Any]:
    path = RUBRICS_DIR / f"{crew_dir}.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"No rubric found for crew '{crew_dir}' at {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def judge_completion(
    *, idea_text: str, target_name: str, completion: Dict[str, Any], rubric: Dict[str, Any]
) -> JudgeScore:
    """Score one completion against its crew's rubric. Always uses the
    fallback provider at HEAVY tier -- judging quality is itself a
    structured-extraction-shaped task this pipeline is designed for."""
    settings = LLMSettings(LLM_BASE_URL=None)  # force fallback -- never judge with the model under test
    gateway = LLMGateway(settings=settings)

    criteria_text = "\n".join(f"- {c['name']}: {c['description']}" for c in rubric["criteria"])
    system_prompt = (
        "You are an impartial evaluator of AI-generated startup analysis output. "
        "Score strictly against the given criteria -- do not reward verbosity or "
        "confident-sounding language that isn't backed by the actual content."
    )
    user_prompt = (
        f"Original startup idea:\n{idea_text}\n\n"
        f"Agent under evaluation: {target_name}\n\n"
        f"Agent's output:\n{json.dumps(completion, indent=2)}\n\n"
        f"Evaluation criteria:\n{criteria_text}\n\n"
        "Score each criterion 1-5 (1=poor, 5=excellent), give an overall 1-5 "
        "score, and a brief reasoning."
    )

    return gateway.invoke_structured(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema_class=JudgeScore,
        tier=ModelTier.HEAVY,
    )
