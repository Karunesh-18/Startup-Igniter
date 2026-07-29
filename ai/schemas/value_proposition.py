"""Pydantic schema for Value Proposition Analyzer output."""

from typing import List
from pydantic import BaseModel, Field, field_validator


class ValuePropositionAnalysis(BaseModel):
    """Structured Pydantic schema for ValuePropositionAnalyzer agent output."""

    core_value_proposition: str = Field(
        ...,
        min_length=5,
        description="Clear, 1-2 sentence core value proposition statement.",
    )
    unique_selling_proposition: str = Field(
        ...,
        min_length=5,
        description="Unique selling proposition (USP) highlighting the primary differentiator.",
    )
    functional_benefits: List[str] = Field(
        ...,
        min_length=1,
        description="Tangible functional benefits (e.g., faster diagnostic speed, automated reporting).",
    )
    emotional_benefits: List[str] = Field(
        default_factory=list,
        description="Psychological or emotional benefits (e.g., peace of mind, confidence in decisions).",
    )
    customer_outcomes: List[str] = Field(
        ...,
        min_length=1,
        description="Quantifiable customer outcomes and results (e.g. 50% faster diagnosis time).",
    )
    differentiators: List[str] = Field(
        default_factory=list,
        description="Key competitive differentiators and value moats.",
    )
    value_clarity_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Clarity rating of the value proposition from 0 (confusing) to 100 (crystal clear).",
    )
    customer_value_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Estimated customer value rating score from 0 to 100.",
    )
    confidence_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Analysis confidence rating score from 0 to 100.",
    )

    @field_validator("core_value_proposition", "unique_selling_proposition")
    @classmethod
    def validate_non_empty_strings(cls, value: str) -> str:
        """Ensure string fields are non-empty."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("String field cannot be empty or blank whitespace.")
        return cleaned

    @field_validator("functional_benefits", "customer_outcomes")
    @classmethod
    def validate_non_empty_lists(cls, items: List[str]) -> List[str]:
        """Ensure list contains non-empty items."""
        cleaned = [item.strip() for item in items if item and item.strip()]
        if not cleaned:
            raise ValueError("List field must contain at least one valid non-empty string item.")
        return cleaned
