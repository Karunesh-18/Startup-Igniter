"""Pydantic schemas for Product Development Crew outputs."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MVPFeature(BaseModel):
    """Schema for individual MVP feature item."""

    feature_name: str = Field(description="Name of feature.")
    description: str = Field(description="Feature functionality summary.")
    priority: str = Field(default="Must Have", description="Must Have, Should Have, Could Have.")
    complexity: str = Field(default="Medium", description="Low, Medium, High engineering effort.")


class TechStackRecommendation(BaseModel):
    """Recommended tech stack components."""

    frontend: str = Field(description="Recommended frontend framework (e.g. Next.js / React).")
    backend: str = Field(description="Recommended backend framework (e.g. FastAPI / Node.js).")
    database: str = Field(description="Recommended database (e.g. PostgreSQL / Supabase).")
    hosting: str = Field(description="Recommended hosting cloud (e.g. Vercel / GCP).")
    ai_ml_tools: List[str] = Field(default_factory=list, description="AI models or frameworks.")


class ProductDevelopmentResult(BaseModel):
    """Unified result container for Product Development Crew."""

    project_id: str = Field(description="Project UUID string.")
    mvp_features: List[MVPFeature] = Field(default_factory=list, description="MVP feature roadmap.")
    tech_stack: TechStackRecommendation = Field(description="Tech stack recommendation.")
    architecture_overview: str = Field(description="System architecture description.")
    confidence_score: float = Field(default=0.85, description="Confidence score (0.0 to 1.0).")
