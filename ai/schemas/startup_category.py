"""Pydantic schema for Startup Category Classifier output."""

from typing import List
from pydantic import BaseModel, Field, field_validator


class StartupCategoryClassification(BaseModel):
    """Structured Pydantic schema for StartupCategoryClassifier agent output."""

    primary_category: str = Field(
        ...,
        min_length=2,
        description="Primary startup category classification (e.g. AI, HealthTech, SaaS, FinTech).",
    )
    secondary_categories: List[str] = Field(
        default_factory=list,
        description="Secondary category tags if applicable.",
    )
    industry: str = Field(
        ...,
        min_length=2,
        description="Primary industry vertical (e.g. Healthcare, Agriculture, Financial Services).",
    )
    technology_domains: List[str] = Field(
        default_factory=list,
        description="Core technology domains involved (e.g. Computer Vision, Deep Learning, Cloud API).",
    )
    business_model: str = Field(
        ...,
        min_length=2,
        description="Business model structure (e.g., B2B, B2C, D2C, B2G, Marketplace, Subscription, Platform, Enterprise).",
    )
    revenue_model: str = Field(
        ...,
        min_length=2,
        description="Primary revenue model (e.g., Subscription, Freemium, Transaction Fee, Licensing, Usage Based).",
    )
    startup_stage: str = Field(
        ...,
        min_length=2,
        description="Current estimated startup stage (e.g., Idea, MVP, Prototype, Early Revenue, Growth, Scale).",
    )
    target_market: str = Field(
        ...,
        min_length=2,
        description="Target customer market segment description.",
    )
    confidence_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Classification confidence score rating from 0 to 100.",
    )
    reasoning: str = Field(
        ...,
        min_length=5,
        description="Concise rationale explaining the classification decision.",
    )

    @field_validator(
        "primary_category",
        "industry",
        "business_model",
        "revenue_model",
        "startup_stage",
        "target_market",
        "reasoning",
    )
    @classmethod
    def validate_non_empty_strings(cls, value: str) -> str:
        """Ensure string fields contain valid non-empty text."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("String field cannot be empty or blank whitespace.")
        return cleaned
