"""Pydantic schemas for crew execution Context objects across Startup Igniter."""

from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field

from ai.schemas.idea_validation import IdeaValidationResult
from ai.schemas.market_research import (
    CompetitorComparison,
    CompetitorDiscovery,
    CustomerPersona,
    IndustryAnalysis,
    MarketResearchAnalysis,
    MarketResearchResult,
    TAMSAMSOMAnalysis,
    TrendAnalysis,
)
from ai.schemas.research_patent import PatentAnalysis
from ai.shared.research.research_bundle import ResearchBundle


class IdeaValidationContext(BaseModel):
    """Context container passed through Idea Validation Crew execution."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    project_id: str = Field(description="Unique project UUID string identifier.")
    idea_text: str = Field(description="Submitted raw startup proposal text.")
    result: Optional[IdeaValidationResult] = Field(
        default=None,
        description="Validated IdeaValidationResult model populated upon crew completion.",
    )


class MarketResearchContext(BaseModel):
    """Context container passed through Market Research Crew execution."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    project_id: str = Field(description="Unique project UUID string identifier.")
    idea_validation: IdeaValidationResult = Field(
        description="Validated IdeaValidationResult output from Crew 1."
    )
    market_research: Optional[MarketResearchAnalysis] = Field(
        default=None,
        description="High-level MarketResearchAnalysis output populated by MarketResearchAgent.",
    )
    industry_analysis: Optional[IndustryAnalysis] = Field(
        default=None,
        description="IndustryAnalysis output populated by IndustryAnalysisAgent.",
    )
    trend_analysis: Optional[TrendAnalysis] = Field(
        default=None,
        description="TrendAnalysis output populated by TrendAnalysisAgent.",
    )
    competitor_discovery: Optional[CompetitorDiscovery] = Field(
        default=None,
        description="CompetitorDiscovery output populated by CompetitorDiscoveryAgent.",
    )
    competitor_comparison: Optional[CompetitorComparison] = Field(
        default=None,
        description="CompetitorComparison output populated by CompetitorComparisonAgent.",
    )
    customer_persona: Optional[CustomerPersona] = Field(
        default=None,
        description="CustomerPersona output populated by CustomerPersonaGenerator.",
    )
    tam_sam_som: Optional[TAMSAMSOMAnalysis] = Field(
        default=None,
        description="TAMSAMSOMAnalysis output populated by TAMSAMSOMEstimator.",
    )
    research_bundle: Optional[ResearchBundle] = Field(
        default=None,
        description="Optional external research bundle from ResearchManager (Tavily/Exa/Zyte).",
    )


class ResearchPatentContext(BaseModel):
    """Context container passed through Research & Patent Crew execution."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    project_id: str = Field(description="Unique project UUID string identifier.")
    idea_validation: IdeaValidationResult = Field(
        description="Validated IdeaValidationResult output from Crew 1."
    )
    market_research_context: Optional[MarketResearchContext] = Field(
        default=None,
        description="Populated MarketResearchContext output from Crew 2.",
    )
    research_bundle: Optional[ResearchBundle] = Field(
        default=None,
        description="Optional external research bundle from ResearchManager (Tavily/Exa/Zyte).",
    )
    patent_research: Optional[Any] = Field(default=None)


class FeasibilityContext(BaseModel):
    """Context container passed through Feasibility Crew execution."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    project_id: str = Field(description="Unique project UUID string identifier.")
    idea_validation: IdeaValidationResult = Field(
        description="Validated IdeaValidationResult output from Crew 1."
    )
    feasibility_analysis: Optional[Any] = Field(default=None)


class BusinessPlanningContext(BaseModel):
    """Context container passed through Business Planning Crew execution."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    project_id: str = Field(description="Unique project UUID string identifier.")
    idea_validation: IdeaValidationResult = Field(
        description="Validated IdeaValidationResult output from Crew 1."
    )
    business_plan: Optional[Any] = Field(default=None)
