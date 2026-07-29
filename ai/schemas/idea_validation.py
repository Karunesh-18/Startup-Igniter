"""Pydantic schemas for Idea Validation phase output validation."""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from ai.schemas.customer_identifier import CustomerIdentification
from ai.schemas.innovation_score import InnovationScoreAnalysis
from ai.schemas.problem_statement import ProblemStatementAnalysis
from ai.schemas.startup_category import StartupCategoryClassification
from ai.schemas.value_proposition import ValuePropositionAnalysis


class StartupIdeaAnalysis(BaseModel):
    """Structured Pydantic schema for Startup Idea Analyzer output."""

    summary: str = Field(
        ...,
        min_length=5,
        description="Concise synthesis summary of the core startup proposal concept.",
    )
    startup_category: Optional[str] = Field(
        default=None,
        description="Primary industry vertical/category classification if identified.",
    )
    operational_pillars: List[str] = Field(
        ...,
        min_length=1,
        description="Core operational/technical pillars required to build the startup.",
    )
    technical_feasibility_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Feasibility score rating from 0 (impossible) to 100 (highly feasible).",
    )
    rationale: str = Field(
        ...,
        min_length=10,
        description="Detailed technical feasibility rationale and explanation.",
    )
    key_assumptions: List[str] = Field(
        default_factory=list,
        description="Critical underlying assumptions that require market/tech validation.",
    )
    strengths: List[str] = Field(
        default_factory=list,
        description="Key architectural, technical, or market strengths of the proposal.",
    )
    weaknesses: List[str] = Field(
        default_factory=list,
        description="Potential operational, data, or technical weaknesses/risks.",
    )

    @field_validator("summary", "rationale")
    @classmethod
    def validate_non_empty_strings(cls, value: str) -> str:
        """Ensure string fields contain meaningful non-whitespace text."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty or blank whitespace.")
        return cleaned

    @field_validator("operational_pillars")
    @classmethod
    def validate_non_empty_pillars(cls, pillars: List[str]) -> List[str]:
        """Ensure operational pillars list contains non-empty items."""
        cleaned = [p.strip() for p in pillars if p and p.strip()]
        if not cleaned:
            raise ValueError("operational_pillars must contain at least one valid pillar item.")
        return cleaned


class IdeaValidationResult(BaseModel):
    """Combined structured Pydantic schema for full Idea Validation Crew results."""

    project_id: str = Field(..., description="Unique project identifier.")
    idea_text: str = Field(..., description="Original raw startup proposal text.")
    idea_analysis: StartupIdeaAnalysis
    problem_analysis: ProblemStatementAnalysis
    customer_identification: CustomerIdentification
    value_proposition: ValuePropositionAnalysis
    category_classification: StartupCategoryClassification
    innovation_scoring: InnovationScoreAnalysis
    overall_validation_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Weighted composite validation score from 0.0 to 100.0.",
    )
