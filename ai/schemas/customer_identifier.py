"""Pydantic schema for Customer Identifier output."""

from typing import List
from pydantic import BaseModel, Field, field_validator


class CustomerIdentification(BaseModel):
    """Structured Pydantic schema for CustomerIdentifier agent output."""

    primary_customers: List[str] = Field(
        ...,
        min_length=1,
        description="Primary target customers who buy or pay for the solution.",
    )
    secondary_customers: List[str] = Field(
        default_factory=list,
        description="Secondary target customers or secondary buyer personas.",
    )
    end_users: List[str] = Field(
        default_factory=list,
        description="Actual end users who use the product day-to-day.",
    )
    decision_makers: List[str] = Field(
        default_factory=list,
        description="Key decision makers involved in purchasing or procurement.",
    )
    customer_segments: List[str] = Field(
        ...,
        min_length=1,
        description="Core customer segment categories (e.g. B2B Hospitals, Private Clinics).",
    )
    demographics: List[str] = Field(
        default_factory=list,
        description="Demographic or firmographic characteristics of target users.",
    )
    geographic_markets: List[str] = Field(
        default_factory=list,
        description="Primary geographic markets or regional focus areas.",
    )
    industries: List[str] = Field(
        default_factory=list,
        description="Target industry verticals or sectors.",
    )
    pain_points: List[str] = Field(
        default_factory=list,
        description="Core pain points experienced by target customers.",
    )
    customer_needs: List[str] = Field(
        ...,
        min_length=1,
        description="Essential customer needs and requirements.",
    )
    motivations: List[str] = Field(
        default_factory=list,
        description="Key purchasing motivations and value drivers.",
    )
    adoption_barriers: List[str] = Field(
        default_factory=list,
        description="Potential barriers to customer adoption or purchase.",
    )
    willingness_to_pay: str = Field(
        ...,
        description="Estimated willingness to pay rating or level ('low', 'medium', 'high', or detailed description).",
    )
    confidence_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confidence score rating from 0 to 100.",
    )

    @field_validator("primary_customers", "customer_segments", "customer_needs")
    @classmethod
    def validate_non_empty_lists(cls, items: List[str]) -> List[str]:
        """Ensure list contains non-empty string items."""
        cleaned = [item.strip() for item in items if item and item.strip()]
        if not cleaned:
            raise ValueError("List field must contain at least one valid non-empty string item.")
        return cleaned

    @field_validator("willingness_to_pay")
    @classmethod
    def validate_willingness_to_pay(cls, value: str) -> str:
        """Validate willingness_to_pay is non-empty."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("willingness_to_pay cannot be empty or blank whitespace.")
        return cleaned
