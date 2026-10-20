"""Pydantic schemas for Funding & Investor Readiness Crew outputs."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class FundingResult(BaseModel):
    """Unified result container for Funding & Investor Readiness Crew."""

    project_id: str = Field(description="Project UUID string.")
    pitch_deck_slides: List[str] = Field(default_factory=list, description="10-slide pitch deck structure.")
    estimated_valuation_range: str = Field(description="Estimated pre-money valuation range.")
    fundraising_target: str = Field(description="Target capital raising amount.")
    investor_checklist: List[str] = Field(default_factory=list, description="Due diligence readiness checklist.")
    investor_types: List[str] = Field(default_factory=list, description="Angel, Seed VC, Micro VC targets.")
    confidence_score: float = Field(default=0.88, description="Confidence score (0.0 to 1.0).")
