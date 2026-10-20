"""Pydantic schemas for Branding & Marketing Crew outputs."""

from typing import List, Optional
from pydantic import BaseModel, Field


class BrandingMarketingResult(BaseModel):
    """Unified result container for Branding & Marketing Crew."""

    project_id: str = Field(description="Project UUID string.")
    brand_name_suggestions: List[str] = Field(default_factory=list, description="Suggested brand names.")
    tagline: str = Field(description="Core brand tagline.")
    brand_positioning: str = Field(description="Brand positioning strategy.")
    copywriting_angles: List[str] = Field(default_factory=list, description="High-converting messaging angles.")
    launch_channel_strategy: List[str] = Field(default_factory=list, description="GTM launch channels.")
    confidence_score: float = Field(default=0.88, description="Confidence score (0.0 to 1.0).")
