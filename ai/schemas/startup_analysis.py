"""Pydantic schema for unified end-to-end Startup Analysis result (Crew 1 + Crew 2)."""

from typing import Optional
from pydantic import BaseModel, Field

from ai.schemas.idea_validation import IdeaValidationResult
from ai.schemas.market_research import MarketResearchResult


class StartupAnalysisResult(BaseModel):
    """Unified master analysis output combining Idea Validation (Crew 1) and Market Research (Crew 2)."""

    project_id: str = Field(
        ...,
        description="Unique identifier for the startup project.",
    )
    startup_idea_text: str = Field(
        ...,
        description="Original raw startup idea proposal text submitted by the user.",
    )
    idea_validation: IdeaValidationResult = Field(
        ...,
        description="Complete output result from Idea Validation Crew (Crew 1).",
    )
    market_research: Optional[MarketResearchResult] = Field(
        default=None,
        description="Complete output result from Market Research Crew (Crew 2), if executed successfully.",
    )
    overall_summary: str = Field(
        ...,
        description="Comprehensive executive summary synthesizing findings from both Idea Validation and Market Research.",
    )
    overall_readiness_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Dynamic weighted composite readiness score from 0.0 to 100.0.",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Average confidence score across both crews from 0.0 to 1.0.",
    )
    status: str = Field(
        default="success",
        description="Overall pipeline execution status ('success', 'partial_failure', 'failure').",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error details if a phase encountered a failure.",
    )
