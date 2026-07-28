"""Pydantic schema for Problem Statement Analyzer output."""

from typing import List
from pydantic import BaseModel, Field, field_validator


class ProblemStatementAnalysis(BaseModel):
    """Structured Pydantic schema for ProblemStatementAnalyzer output."""

    problem_statement: str = Field(
        ...,
        min_length=10,
        description="Clear, concise formulation of the core problem being analyzed.",
    )
    affected_users: List[str] = Field(
        ...,
        min_length=1,
        description="User groups or personas impacted by this problem.",
    )
    root_causes: List[str] = Field(
        ...,
        min_length=1,
        description="Underlying root causes giving rise to the problem.",
    )
    existing_solutions: List[str] = Field(
        default_factory=list,
        description="Current manual workarounds or existing solutions employed today.",
    )
    solution_gaps: List[str] = Field(
        ...,
        min_length=1,
        description="Deficiencies, gaps, or limitations in current solutions.",
    )
    problem_severity: str = Field(
        ...,
        description="Severity level of the pain point ('low', 'medium', 'high', 'critical').",
    )
    urgency_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Market urgency score rating from 0 (nice-to-have) to 100 (critical hair-on-fire).",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Analysis confidence rating score between 0.00 and 1.00.",
    )

    @field_validator("problem_statement")
    @classmethod
    def validate_non_empty_statement(cls, value: str) -> str:
        """Ensure problem statement is non-empty string."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("problem_statement cannot be blank whitespace.")
        return cleaned

    @field_validator("problem_severity")
    @classmethod
    def validate_severity_level(cls, value: str) -> str:
        """Standardize and validate severity string."""
        valid_levels = {"low", "medium", "high", "critical"}
        cleaned = value.strip().lower()
        if cleaned not in valid_levels:
            raise ValueError(f"problem_severity must be one of {valid_levels}, got '{value}'")
        return cleaned
