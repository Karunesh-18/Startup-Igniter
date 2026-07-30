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
from ai.schemas.research_patent import (
    ExistingSolutionAnalysis,
    InnovationGapAnalysis,
    IPStrategy,
    PatentAnalysis,
    ResearchPaperAnalysis,
    ResearchPatentResult,
    TechnologyReadiness,
)
from ai.schemas.startup_analysis import StartupAnalysisResult
from ai.schemas.startup_category import StartupCategoryClassification
from ai.schemas.value_proposition import ValuePropositionAnalysis

from ai.schemas.branding_marketing import BrandingMarketingResult
from ai.schemas.business_plan import BusinessPlanResult, FinancialModel, LeanCanvas
from ai.schemas.community import CommunityResult
from ai.schemas.feasibility import FeasibilityResult
from ai.schemas.funding import FundingResult
from ai.schemas.growth_scaling import GrowthScalingResult
from ai.schemas.legal_compliance import ComplianceItem, LegalComplianceResult, LegalDocumentDraft
from ai.schemas.product_development import MVPFeature, ProductDevelopmentResult, TechStackRecommendation
from ai.schemas.reporting import MasterReportResult
from ai.schemas.research_patent import PatentAnalysis

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
    "PatentAnalysis",
    "ResearchPaperAnalysis",
    "ExistingSolutionAnalysis",
    "InnovationGapAnalysis",
    "TechnologyReadiness",
    "IPStrategy",
    "ResearchPatentResult",
    "IdeaValidationContext",
    "MarketResearchContext",
    "ResearchPatentContext",
    "FeasibilityContext",
    "BusinessPlanningContext",
    "LeanCanvas",
    "FinancialModel",
    "BusinessPlanResult",
    "ComplianceItem",
    "LegalDocumentDraft",
    "LegalComplianceResult",
    "MVPFeature",
    "TechStackRecommendation",
    "ProductDevelopmentResult",
    "PatentAnalysis",
    "FeasibilityResult",
    "BrandingMarketingResult",
    "GrowthScalingResult",
    "FundingResult",
    "MasterReportResult",
    "CommunityResult",
]
