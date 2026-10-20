"""
Multi-dimensional startup readiness scoring — computed in Python, not by the LLM.

Architecture note (spec §3, implementation_plan §scoring):
  - The LLM produces *sub-ratings* per dimension (0-100) with written justification.
  - This module computes the *weighted sum* deterministically from those sub-ratings.
  - This makes scores reproducible, auditable, and hallucination-proof.

Dimensions and weights (must sum to 1.0):
  validation    0.20   Does the problem exist and is the solution viable?
  market        0.20   Market size, growth rate, and competition density.
  technology    0.15   Technical feasibility and innovation degree.
  business      0.15   Revenue model clarity and unit economics.
  financial     0.10   Funding needs vs. bootstrappability.
  patent        0.10   Prior-art risk and IP defensibility.
  legal         0.05   Regulatory burden and compliance complexity.
  overall       0.05   Holistic / sanity-check dimension.

Usage::

    from workflow.scoring import compute_weighted_score, DIMENSION_WEIGHTS

    # llm_scores is a dict returned by the AI crew:
    # {"validation": 75, "market": 60, ...}
    result = compute_weighted_score(llm_scores)
    # result.total       → float (0-100)
    # result.breakdown   → dict of {dim: weighted_contribution}
"""

from dataclasses import dataclass, field
from typing import Any

# ── Weight table ──────────────────────────────────────────────────────────────
DIMENSION_WEIGHTS: dict[str, float] = {
    "validation": 0.20,
    "market": 0.20,
    "technology": 0.15,
    "business": 0.15,
    "financial": 0.10,
    "patent": 0.10,
    "legal": 0.05,
    "overall": 0.05,
}

assert abs(sum(DIMENSION_WEIGHTS.values()) - 1.0) < 1e-9, (
    "Scoring weights must sum to exactly 1.0"
)


@dataclass
class ScoreResult:
    """
    Result of `compute_weighted_score`.

    Attributes:
        total: Weighted sum (0-100, two decimal places).
        breakdown: Per-dimension contribution after weighting.
        raw_scores: Original LLM-provided sub-ratings (0-100).
        missing_dimensions: Dimensions in the weight table but absent from
                            `raw_scores` (defaulted to 50 = neutral).
    """

    total: float
    breakdown: dict[str, float]
    raw_scores: dict[str, float]
    missing_dimensions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "breakdown": self.breakdown,
            "raw_scores": self.raw_scores,
            "missing_dimensions": self.missing_dimensions,
        }


def compute_weighted_score(
    raw_scores: dict[str, float | int],
    weights: dict[str, float] | None = None,
) -> ScoreResult:
    """
    Compute the weighted readiness score from LLM sub-ratings.

    Args:
        raw_scores: Dict mapping dimension names to raw LLM scores (0-100).
                    Extra dimensions not in the weight table are ignored.
        weights: Optional custom weight table. Defaults to DIMENSION_WEIGHTS.

    Returns:
        ScoreResult with total, breakdown, raw_scores, missing_dimensions.
    """
    weights = weights or DIMENSION_WEIGHTS
    missing: list[str] = []
    breakdown: dict[str, float] = {}
    total = 0.0

    for dimension, weight in weights.items():
        if dimension not in raw_scores:
            missing.append(dimension)
            raw_value = 50.0  # neutral default when dimension is missing
        else:
            raw_value = float(raw_scores[dimension])
            # Clamp to [0, 100]
            raw_value = max(0.0, min(100.0, raw_value))

        weighted = raw_value * weight
        breakdown[dimension] = round(weighted, 4)
        total += weighted

    return ScoreResult(
        total=round(total, 2),
        breakdown=breakdown,
        raw_scores={k: float(v) for k, v in raw_scores.items()},
        missing_dimensions=missing,
    )


def score_label(total: float) -> str:
    """
    Return a human-readable label for a total score.

    Args:
        total: Score value between 0 and 100.

    Returns:
        One of: "Very Early Stage", "Early Stage", "Developing",
                "Promising", "Investment-Ready"
    """
    if total < 30:
        return "Very Early Stage"
    if total < 50:
        return "Early Stage"
    if total < 65:
        return "Developing"
    if total < 80:
        return "Promising"
    return "Investment-Ready"
