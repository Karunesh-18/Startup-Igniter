"""Pydantic schemas for Growth & Scaling Crew outputs."""

from typing import List, Optional
from pydantic import BaseModel, Field


class GrowthScalingResult(BaseModel):
    """Unified result container for Growth & Scaling Crew."""

    project_id: str = Field(description="Project UUID string.")
    primary_acquisition_channels: List[str] = Field(default_factory=list, description="Primary customer acquisition channels.")
    viral_loop_mechanic: str = Field(description="Referral or viral growth mechanic.")
    retention_playbook: List[str] = Field(default_factory=list, description="User retention strategies.")
    target_kpis: List[str] = Field(default_factory=list, description="Target growth metrics.")
    confidence_score: float = Field(default=0.88, description="Confidence score (0.0 to 1.0).")
