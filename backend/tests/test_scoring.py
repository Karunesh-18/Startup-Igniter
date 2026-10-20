"""
Tests for the deterministic scoring module.
"""

import pytest
from workflow.scoring import (
    DIMENSION_WEIGHTS,
    ScoreResult,
    compute_weighted_score,
    score_label,
)


def test_weights_sum_to_one():
    """Scoring weights must sum to exactly 1.0."""
    assert abs(sum(DIMENSION_WEIGHTS.values()) - 1.0) < 1e-9


def test_perfect_score():
    """All dimensions at 100 → total = 100."""
    raw = {dim: 100.0 for dim in DIMENSION_WEIGHTS}
    result = compute_weighted_score(raw)
    assert result.total == 100.0


def test_zero_score():
    """All dimensions at 0 → total = 0."""
    raw = {dim: 0.0 for dim in DIMENSION_WEIGHTS}
    result = compute_weighted_score(raw)
    assert result.total == 0.0


def test_partial_score():
    """Compute weighted sum manually for a partial set."""
    raw = {
        "validation": 80,
        "market": 60,
        "technology": 70,
        "business": 50,
        "financial": 40,
        "patent": 30,
        "legal": 90,
        "overall": 65,
    }
    result = compute_weighted_score(raw)

    expected = (
        80 * 0.20 + 60 * 0.20 + 70 * 0.15 + 50 * 0.15
        + 40 * 0.10 + 30 * 0.10 + 90 * 0.05 + 65 * 0.05
    )
    assert abs(result.total - round(expected, 2)) < 0.01


def test_missing_dimensions_defaulted_to_50():
    """Missing dimensions are replaced with 50 (neutral)."""
    raw = {"validation": 80}  # only one dimension
    result = compute_weighted_score(raw)
    assert "validation" in result.breakdown
    assert len(result.missing_dimensions) == len(DIMENSION_WEIGHTS) - 1


def test_clamping():
    """Values above 100 are clamped to 100, below 0 clamped to 0."""
    raw = {dim: 150 if dim == "market" else -10 for dim in DIMENSION_WEIGHTS}
    result = compute_weighted_score(raw)
    # market clamped to 100, others clamped to 0
    assert result.raw_scores == {dim: 150 if dim == "market" else -10 for dim in DIMENSION_WEIGHTS}
    # Weighted sum uses clamped values
    expected_market_contribution = 100 * DIMENSION_WEIGHTS["market"]
    assert result.breakdown["market"] == round(expected_market_contribution, 4)


def test_score_labels():
    """score_label returns correct label for boundary values."""
    assert score_label(0) == "Very Early Stage"
    assert score_label(29) == "Very Early Stage"
    assert score_label(30) == "Early Stage"
    assert score_label(49) == "Early Stage"
    assert score_label(50) == "Developing"
    assert score_label(64) == "Developing"
    assert score_label(65) == "Promising"
    assert score_label(79) == "Promising"
    assert score_label(80) == "Investment-Ready"
    assert score_label(100) == "Investment-Ready"


def test_to_dict():
    """ScoreResult.to_dict() returns expected keys."""
    raw = {dim: 50.0 for dim in DIMENSION_WEIGHTS}
    result = compute_weighted_score(raw)
    d = result.to_dict()
    assert "total" in d
    assert "breakdown" in d
    assert "raw_scores" in d
    assert "missing_dimensions" in d
