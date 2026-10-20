"""Pydantic schemas for Business Planning Crew outputs (Lean Canvas & BMC)."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LeanCanvas(BaseModel):
    """Schema representing Lean Canvas business model data."""

    problem: str = Field(description="Top 3 problems being addressed.")
    solution: str = Field(description="Top 3 features offering solutions.")
    unique_value_proposition: str = Field(description="Clear, compelling message explaining uniqueness.")
    unfair_advantage: str = Field(description="Thing that cannot be easily copied or bought.")
    customer_segments: str = Field(description="Target customers and early adopters.")
    key_metrics: List[str] = Field(default_factory=list, description="Key activities measured.")
    channels: List[str] = Field(default_factory=list, description="Pathways to reach customers.")
    cost_structure: List[str] = Field(default_factory=list, description="Fixed and variable costs.")
    revenue_streams: List[str] = Field(default_factory=list, description="Revenue models and pricing.")


class FinancialModel(BaseModel):
    """Schema representing financial projections and pricing strategy."""

    pricing_model: str = Field(description="Subscription, pay-per-use, or freemium model.")
    price_points: Dict[str, str] = Field(default_factory=dict, description="Tiered pricing breakdown.")
    estimated_cac: Optional[str] = Field(default=None, description="Estimated Customer Acquisition Cost.")
    estimated_ltv: Optional[str] = Field(default=None, description="Estimated Customer Lifetime Value.")
    year_1_revenue_projection: Optional[str] = Field(default=None, description="Year 1 revenue target.")


class BusinessPlanResult(BaseModel):
    """Unified result container for Business Planning Crew."""

    project_id: str = Field(description="Project UUID string.")
    lean_canvas: LeanCanvas = Field(description="Structured Lean Canvas model.")
    financial_model: FinancialModel = Field(description="Financial model projections.")
    executive_summary: str = Field(description="Synthesized business summary.")
    confidence_score: float = Field(default=0.85, description="Confidence score (0.0 to 1.0).")
