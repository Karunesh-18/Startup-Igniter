"""Pydantic schemas for Master Executive Reporting Crew outputs."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class MasterReportResult(BaseModel):
    """Unified result container for Master Executive Reporting Crew."""

    project_id: str = Field(description="Project UUID string.")
    project_name: str = Field(description="Startup project title.")
    executive_summary: str = Field(description="Master multi-phase summary report.")
    overall_readiness_score: float = Field(default=82.0, description="Overall startup readiness score (0-100).")
    phase_scores: Dict[str, float] = Field(default_factory=dict, description="Score map across all phases.")
    key_recommendations: List[str] = Field(default_factory=list, description="Actionable founder recommendations.")
    confidence_score: float = Field(default=0.90, description="Confidence score (0.0 to 1.0).")
