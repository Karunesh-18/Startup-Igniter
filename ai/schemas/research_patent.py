"""Pydantic schemas for research patent analysis."""

from typing import List, Optional
from pydantic import BaseModel, Field


class PatentAnalysis(BaseModel):
    """Schema representing patent research and prior-art analysis."""

    project_id: str = Field(description="Project UUID string.")
    patent_number: Optional[str] = Field(default=None, description="Patent or application number.")
    title: str = Field(description="Title of patent or prior art.")
    abstract: Optional[str] = Field(default=None, description="Abstract summary.")
    similarity_score: float = Field(default=0.0, description="Prior-art similarity score.")
    inventors: List[str] = Field(default_factory=list, description="List of inventors.")
    key_claims: List[str] = Field(default_factory=list, description="Key patent claims.")
