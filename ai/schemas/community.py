"""Pydantic schemas for Community Crew outputs."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class CommunityResult(BaseModel):
    """Unified result container for Community & Peer Review Crew."""

    project_id: str = Field(description="Project UUID string.")
    peer_review_scorecard: Dict[str, float] = Field(default_factory=dict, description="Peer review feedback scores.")
    community_feedback_summary: str = Field(description="Synthesized feedback from founder network.")
    recommended_mentors: List[str] = Field(default_factory=list, description="Target mentor profiles.")
    confidence_score: float = Field(default=0.88, description="Confidence score (0.0 to 1.0).")
