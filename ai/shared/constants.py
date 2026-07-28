"""Shared constants, enums, score weights, and phase mappings for Startup Igniter AI system."""

from enum import Enum
from typing import Dict, List


class StartupPhase(str, Enum):
    """Supported workflow phases in Startup Igniter OS."""

    IDEA = "idea"
    MARKET_VALIDATION = "market_validation"
    PATENT_RESEARCH = "patent_research"
    BUSINESS_PLANNING = "business_planning"
    MVP = "mvp"
    LEGAL = "legal"
    LAUNCH = "launch"
    MEDICAL_COMPLIANCE = "medical_compliance"
    CLINICAL_VALIDATION = "clinical_validation"
    DEMAND_VALIDATION = "demand_validation"
    BUYER_VALIDATION = "buyer_validation"
    SELLER_VALIDATION = "seller_validation"
    REVENUE_MODEL = "revenue_model"


class StartupCategory(str, Enum):
    """System-seeded startup categories."""

    SAAS = "SaaS"
    HEALTHTECH = "HealthTech"
    FINTECH = "FinTech"
    D2C = "D2C"
    MARKETPLACE = "Marketplace"
    EDTECH = "EdTech"
    AGRITECH = "AgriTech"
    DEEPTECH = "DeepTech"
    CLIMATETECH = "ClimateTech"


# Dynamic default phase workflows per startup category
DEFAULT_CATEGORY_WORKFLOWS: Dict[str, List[StartupPhase]] = {
    StartupCategory.SAAS: [
        StartupPhase.IDEA,
        StartupPhase.MARKET_VALIDATION,
        StartupPhase.PATENT_RESEARCH,
        StartupPhase.BUSINESS_PLANNING,
        StartupPhase.MVP,
        StartupPhase.LEGAL,
        StartupPhase.LAUNCH,
    ],
    StartupCategory.HEALTHTECH: [
        StartupPhase.IDEA,
        StartupPhase.MARKET_VALIDATION,
        StartupPhase.MEDICAL_COMPLIANCE,
        StartupPhase.CLINICAL_VALIDATION,
        StartupPhase.BUSINESS_PLANNING,
        StartupPhase.LEGAL,
        StartupPhase.LAUNCH,
    ],
    StartupCategory.MARKETPLACE: [
        StartupPhase.IDEA,
        StartupPhase.DEMAND_VALIDATION,
        StartupPhase.BUYER_VALIDATION,
        StartupPhase.SELLER_VALIDATION,
        StartupPhase.REVENUE_MODEL,
        StartupPhase.MVP,
        StartupPhase.LAUNCH,
    ],
    # Default fallback workflow for unlisted or custom categories
    "default": [
        StartupPhase.IDEA,
        StartupPhase.MARKET_VALIDATION,
        StartupPhase.BUSINESS_PLANNING,
        StartupPhase.MVP,
        StartupPhase.LEGAL,
        StartupPhase.LAUNCH,
    ],
}


class ScoreDimension(str, Enum):
    """Dimensions for project multi-dimensional scoring."""

    VALIDATION = "validation"
    BUSINESS = "business"
    MARKET = "market"
    TECHNOLOGY = "technology"
    PATENT = "patent"
    FINANCIAL = "financial"
    LEGAL = "legal"
    OVERALL = "overall"


# Score dimension weights used for deterministic Python weighted sum computation (spec §6)
# Must sum to 1.0
DEFAULT_SCORE_WEIGHTS: Dict[ScoreDimension, float] = {
    ScoreDimension.VALIDATION: 0.20,
    ScoreDimension.MARKET: 0.20,
    ScoreDimension.BUSINESS: 0.15,
    ScoreDimension.TECHNOLOGY: 0.15,
    ScoreDimension.PATENT: 0.10,
    ScoreDimension.FINANCIAL: 0.10,
    ScoreDimension.LEGAL: 0.10,
}


class RiskType(str, Enum):
    """Categorization of risks detected during analysis."""

    MARKET = "market"
    TECHNICAL = "technical"
    FINANCIAL = "financial"
    LEGAL = "legal"
    TEAM = "team"
    EXECUTION = "execution"


class RiskSeverity(str, Enum):
    """Severity levels for risk assessments."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ModelTier(str, Enum):
    """LLM execution tiers for Groq routing."""

    FAST = "fast"          # llama-3.1-8b-instant (routing, classification, summarization)
    HEAVY = "heavy"        # llama-3.3-70b-versatile (deep reasoning, SWOT, risk, legal)
    REASONING = "reasoning" # deepseek-r1-distill-llama-70b (complex patent/research reasoning)


# Model mapping for Groq
DEFAULT_GROQ_MODELS: Dict[ModelTier, str] = {
    ModelTier.FAST: "groq/llama-3.1-8b-instant",
    ModelTier.HEAVY: "groq/llama-3.3-70b-versatile",
    ModelTier.REASONING: "groq/deepseek-r1-distill-llama-70b",
}


# Default embedding settings (spec §2: sentence-transformers/all-MiniLM-L6-v2)
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_EMBEDDING_DIMENSION = 384

# Default action budget per phase run to control LLM costs
DEFAULT_PHASE_ACTION_BUDGET = 10
DEFAULT_SIMILARITY_THRESHOLD = 0.75
DEFAULT_MEMORY_TOP_K = 5
