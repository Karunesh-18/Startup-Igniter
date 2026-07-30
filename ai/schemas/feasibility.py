"""Pydantic schemas for Feasibility Crew outputs."""

from typing import List, Optional
from pydantic import BaseModel, Field


class FeasibilityResult(BaseModel):
    """Unified result container for Feasibility Crew."""

    project_id: str = Field(description="Project UUID string.")
    technical_feasibility_score: float = Field(default=80.0, description="Technical feasibility score (0-100).")
    operational_feasibility_score: float = Field(default=85.0, description="Operational feasibility score (0-100).")
    financial_feasibility_score: float = Field(default=75.0, description="Financial feasibility score (0-100).")
    key_risks: List[str] = Field(default_factory=list, description="Key feasibility risk factors.")
    mitigation_strategies: List[str] = Field(default_factory=list, description="Risk mitigation strategies.")
    executive_summary: str = Field(description="Feasibility summary text.")
    confidence_score: float = Field(default=0.88, description="Confidence score (0.0 to 1.0).")
