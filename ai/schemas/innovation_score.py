"""Pydantic schema for Innovation Scoring Agent output."""

from typing import List
from pydantic import BaseModel, Field, field_validator


class InnovationScoreAnalysis(BaseModel):
    """Structured Pydantic schema for InnovationScoringAgent output."""

    overall_innovation_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Composite overall innovation rating score from 0 to 100.",
    )
    innovation_level: str = Field(
        ...,
        description="Categorical innovation level ('Very Low', 'Low', 'Moderate', 'High', 'Exceptional').",
    )
    novelty_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Core concept novelty rating score from 0 to 100.",
    )
    technology_innovation_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Technical and architectural innovation score from 0 to 100.",
    )
    business_model_innovation_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Business and revenue model innovation rating from 0 to 100.",
    )
    problem_originality_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Originality score of the target problem being solved from 0 to 100.",
    )
    differentiation_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Competitive differentiation and moat score from 0 to 100.",
    )
    strengths: List[str] = Field(
        ...,
        min_length=1,
        description="Key innovation strengths of the proposal.",
    )
    improvement_opportunities: List[str] = Field(
        default_factory=list,
        description="Areas where innovation or differentiation could be enhanced.",
    )
    reasoning: str = Field(
        ...,
        min_length=5,
        description="Detailed rationale explaining score allocations and innovation breakdown.",
    )
    confidence_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Analysis confidence rating score from 0 to 100.",
    )

    @field_validator("reasoning")
    @classmethod
    def validate_non_empty_reasoning(cls, value: str) -> str:
        """Ensure reasoning is non-empty string."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("reasoning field cannot be blank whitespace.")
        return cleaned

    @field_validator("strengths")
    @classmethod
    def validate_non_empty_strengths(cls, items: List[str]) -> List[str]:
        """Ensure strengths list contains non-empty items."""
        cleaned = [item.strip() for item in items if item and item.strip()]
        if not cleaned:
            raise ValueError("strengths must contain at least one valid non-empty string item.")
        return cleaned
