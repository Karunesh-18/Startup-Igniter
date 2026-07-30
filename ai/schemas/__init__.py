"""Pydantic schemas package for AI module structured outputs."""

from ai.schemas.context import (
    BusinessPlanningContext,
    FeasibilityContext,
    IdeaValidationContext,
    MarketResearchContext,
    ResearchPatentContext,
)
from ai.schemas.customer_identifier import CustomerIdentification
from ai.schemas.idea_validation import IdeaValidationResult, StartupIdeaAnalysis
from ai.schemas.innovation_score import InnovationScoreAnalysis
from ai.schemas.market_research import (
    CompetitorComparison,
    CompetitorDiscovery,
    CompetitorInfo,
    CustomerPersona,
    IndustryAnalysis,
    MarketResearchAnalysis,
    MarketResearchResult,
    PersonaProfile,
    TAMSAMSOMAnalysis,
    TrendAnalysis,
)
from ai.schemas.problem_statement import ProblemStatementAnalysis
from ai.schemas.startup_analysis import StartupAnalysisResult
from ai.schemas.startup_category import StartupCategoryClassification
from ai.schemas.value_proposition import ValuePropositionAnalysis

__all__ = [
    "StartupIdeaAnalysis",
    "ProblemStatementAnalysis",
    "CustomerIdentification",
    "ValuePropositionAnalysis",
    "StartupCategoryClassification",
    "InnovationScoreAnalysis",
    "IdeaValidationResult",
    "MarketResearchAnalysis",
    "IndustryAnalysis",
    "TrendAnalysis",
    "CompetitorInfo",
    "CompetitorDiscovery",
    "CompetitorComparison",
    "PersonaProfile",
    "CustomerPersona",
    "TAMSAMSOMAnalysis",
    "MarketResearchResult",
    "StartupAnalysisResult",
    "IdeaValidationContext",
    "MarketResearchContext",
    "ResearchPatentContext",
    "FeasibilityContext",
    "BusinessPlanningContext",
]
