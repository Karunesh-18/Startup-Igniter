"""Pydantic schema for Market Research Analysis agent output."""

from typing import Any, List
from pydantic import BaseModel, Field, field_validator


class MarketResearchAnalysis(BaseModel):
    """Structured Pydantic schema for MarketResearchAgent output."""

    market_overview: str = Field(
        ...,
        min_length=5,
        description="High-level assessment and overview of the target market landscape.",
    )
    industry_overview: str = Field(
        ...,
        min_length=5,
        description="Overview of the broader industry vertical and sector dynamics.",
    )
    market_stage: str = Field(
        ...,
        description="Stage of the market (e.g. Emerging, Growth, Mature, Declining).",
    )
    market_maturity: str = Field(
        ...,
        description="Maturity level of the market (e.g. Early Stage, Growth Stage, Highly Mature).",
    )
    market_size_summary: str = Field(
        ...,
        description="Qualitative summary of market size and growth potential.",
    )
    market_demand: str = Field(
        ...,
        description="Current and projected trajectory of market demand (e.g. High Demand, Accelerating).",
    )
    market_opportunities: List[str] = Field(
        ...,
        min_length=1,
        description="Key market opportunities driving potential startup expansion.",
    )
    market_challenges: List[str] = Field(
        ...,
        min_length=1,
        description="Core operational, regulatory, or structural challenges in this market.",
    )
    growth_drivers: List[str] = Field(
        ...,
        min_length=1,
        description="Primary macro and micro drivers pushing market growth.",
    )
    market_risks: List[str] = Field(
        ...,
        min_length=1,
        description="Major market and macro risks associated with entering this sector.",
    )
    future_outlook: str = Field(
        ...,
        description="Future trajectory and 3-5 year outlook for the market.",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score rating strictly between 0.0 and 1.0.",
    )

    @field_validator("confidence_score", mode="before")
    @classmethod
    def normalize_confidence_score(cls, value: Any) -> float:
        """Ensure confidence score is normalized to a float between 0.0 and 1.0."""
        try:
            val = float(value)
            if val > 1.0 and val <= 100.0:
                return round(val / 100.0, 2)
            return round(val, 2)
        except (ValueError, TypeError):
            raise ValueError("confidence_score must be a valid float value between 0.0 and 1.0.")

    @field_validator(
        "market_overview",
        "industry_overview",
        "market_stage",
        "market_maturity",
        "market_size_summary",
        "market_demand",
        "future_outlook",
    )
    @classmethod
    def validate_non_empty_strings(cls, value: str) -> str:
        """Ensure string fields contain meaningful non-whitespace text."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("String field cannot be empty or blank whitespace.")
        return cleaned

    @field_validator(
        "market_opportunities",
        "market_challenges",
        "growth_drivers",
        "market_risks",
    )
    @classmethod
    def validate_non_empty_lists(cls, items: List[str]) -> List[str]:
        """Ensure list contains non-empty string items."""
        cleaned = [item.strip() for item in items if item and item.strip()]
        if not cleaned:
            raise ValueError("List field must contain at least one valid non-empty string item.")
        return cleaned


class IndustryAnalysis(BaseModel):
    """Structured Pydantic schema for IndustryAnalysisAgent output."""

    industry_name: str = Field(
        ...,
        min_length=2,
        description="Formal name of the industry vertical.",
    )
    industry_description: str = Field(
        ...,
        min_length=5,
        description="Detailed description of the industry landscape.",
    )
    industry_classification: str = Field(
        ...,
        description="Standard industry classification taxonomy or sector grouping.",
    )
    industry_lifecycle_stage: str = Field(
        ...,
        description="Lifecycle stage of the industry (e.g. Emerging, Growth, Mature, Consolidation).",
    )
    industry_maturity: str = Field(
        ...,
        description="Maturity level rating of the overall industry.",
    )
    industry_growth_rate: str = Field(
        ...,
        description="Estimated qualitative or quantitative industry CAGR/growth rate trajectory.",
    )
    industry_drivers: List[str] = Field(
        ...,
        min_length=1,
        description="Core macro and technological drivers spurring industry progression.",
    )
    industry_challenges: List[str] = Field(
        ...,
        min_length=1,
        description="Structural or economic challenges facing companies in this industry.",
    )
    entry_barriers: List[str] = Field(
        ...,
        min_length=1,
        description="Key barriers to entry for new market entrants.",
    )
    regulatory_environment: str = Field(
        ...,
        description="Overview of regulatory complexity, compliance requirements, and government oversight.",
    )
    technology_adoption: str = Field(
        ...,
        description="Level and speed of modern technology adoption across industry incumbents.",
    )
    innovation_level: str = Field(
        ...,
        description="Current innovation intensity and rate of technological disruption.",
    )
    investment_activity: str = Field(
        ...,
        description="Venture capital, private equity, and corporate M&A investment activity level.",
    )
    future_outlook: str = Field(
        ...,
        description="Comprehensive 3-5 year future industry outlook.",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score rating strictly between 0.0 and 1.0.",
    )

    @field_validator("confidence_score", mode="before")
    @classmethod
    def normalize_confidence_score(cls, value: Any) -> float:
        """Ensure confidence score is normalized to a float between 0.0 and 1.0."""
        try:
            val = float(value)
            if val > 1.0 and val <= 100.0:
                return round(val / 100.0, 2)
            return round(val, 2)
        except (ValueError, TypeError):
            raise ValueError("confidence_score must be a valid float value between 0.0 and 1.0.")

    @field_validator(
        "industry_name",
        "industry_description",
        "industry_classification",
        "industry_lifecycle_stage",
        "industry_maturity",
        "industry_growth_rate",
        "regulatory_environment",
        "technology_adoption",
        "innovation_level",
        "investment_activity",
        "future_outlook",
    )
    @classmethod
    def validate_non_empty_strings(cls, value: str) -> str:
        """Ensure string fields contain meaningful non-whitespace text."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("String field cannot be empty or blank whitespace.")
        return cleaned

    @field_validator("industry_drivers", "industry_challenges", "entry_barriers")
    @classmethod
    def validate_non_empty_lists(cls, items: List[str]) -> List[str]:
        """Ensure list contains non-empty string items."""
        cleaned = [item.strip() for item in items if item and item.strip()]
        if not cleaned:
            raise ValueError("List field must contain at least one valid non-empty string item.")
        return cleaned


class TrendAnalysis(BaseModel):
    """Structured Pydantic schema for TrendAnalysisAgent output."""

    current_trends: List[str] = Field(
        ...,
        min_length=1,
        description="Current active trends influencing the target industry vertical.",
    )
    emerging_trends: List[str] = Field(
        ...,
        min_length=1,
        description="Emerging early-stage trends shaping the future of the sector.",
    )
    technology_trends: List[str] = Field(
        ...,
        min_length=1,
        description="Key technological advancements and digital transformation trends.",
    )
    consumer_behavior_trends: List[str] = Field(
        ...,
        min_length=1,
        description="Shifts in customer expectations, buying habits, and usage behavior.",
    )
    regulatory_trends: List[str] = Field(
        ...,
        min_length=1,
        description="Evolving legal, compliance, policy, and governance trends.",
    )
    investment_trends: List[str] = Field(
        ...,
        min_length=1,
        description="Venture funding, capital deployment, and investor focus trends.",
    )
    sustainability_trends: List[str] = Field(
        ...,
        min_length=1,
        description="ESG, environmental impact, and sustainability trends.",
    )
    future_predictions: List[str] = Field(
        ...,
        min_length=1,
        description="Key predictions and projections for the industry over the next 3-5 years.",
    )
    opportunities_from_trends: List[str] = Field(
        ...,
        min_length=1,
        description="Strategic opportunities created by these macro and tech trends.",
    )
    risks_from_trends: List[str] = Field(
        ...,
        min_length=1,
        description="Potential risks, disruption threats, or vulnerabilities introduced by trends.",
    )
    trend_stability: str = Field(
        ...,
        description="Assessment of trend longevity and stability (e.g. Highly Stable, Volatile, Sustained Long-Term).",
    )
    trend_relevance: str = Field(
        ...,
        description="Relevance rating and impact magnitude of trends on the specific startup proposal.",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score rating strictly between 0.0 and 1.0.",
    )

    @field_validator("confidence_score", mode="before")
    @classmethod
    def normalize_confidence_score(cls, value: Any) -> float:
        """Ensure confidence score is normalized to a float between 0.0 and 1.0."""
        try:
            val = float(value)
            if val > 1.0 and val <= 100.0:
                return round(val / 100.0, 2)
            return round(val, 2)
        except (ValueError, TypeError):
            raise ValueError("confidence_score must be a valid float value between 0.0 and 1.0.")

    @field_validator("trend_stability", "trend_relevance")
    @classmethod
    def validate_non_empty_strings(cls, value: str) -> str:
        """Ensure string fields contain meaningful non-whitespace text."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("String field cannot be empty or blank whitespace.")
        return cleaned

    @field_validator(
        "current_trends",
        "emerging_trends",
        "technology_trends",
        "consumer_behavior_trends",
        "regulatory_trends",
        "investment_trends",
        "sustainability_trends",
        "future_predictions",
        "opportunities_from_trends",
        "risks_from_trends",
    )
    @classmethod
    def validate_non_empty_lists(cls, items: List[str]) -> List[str]:
        """Ensure list contains non-empty string items."""
        cleaned = [item.strip() for item in items if item and item.strip()]
        if not cleaned:
            raise ValueError("List field must contain at least one valid non-empty string item.")
        return cleaned


class CompetitorInfo(BaseModel):
    """Structured information for an identified competitor entity."""

    name: str = Field(
        ...,
        min_length=1,
        description="Formal name of the competitor organization or product.",
    )
    category: str = Field(
        ...,
        description="Competitor category classification (e.g., Direct, Indirect, Emerging, Incumbent).",
    )
    description: str = Field(
        ...,
        description="Short summary description of the competitor's market position and value prop.",
    )
    target_market: str = Field(
        ...,
        description="Target customer segment or geographic market served by this competitor.",
    )
    primary_offering: str = Field(
        ...,
        description="Core product, platform, or service offered by this competitor.",
    )

    @field_validator("name", "category", "description", "target_market", "primary_offering")
    @classmethod
    def validate_non_empty_strings(cls, value: str) -> str:
        """Ensure string fields contain non-whitespace text."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("CompetitorInfo field cannot be empty or blank whitespace.")
        return cleaned


class CompetitorDiscovery(BaseModel):
    """Structured Pydantic schema for CompetitorDiscoveryAgent output."""

    direct_competitors: List[CompetitorInfo] = Field(
        ...,
        min_length=1,
        description="List of direct competitors offering similar core solutions.",
    )
    indirect_competitors: List[CompetitorInfo] = Field(
        ...,
        default_factory=list,
        description="List of indirect competitors solving similar problems through alternative methods.",
    )
    emerging_competitors: List[CompetitorInfo] = Field(
        ...,
        default_factory=list,
        description="List of early-stage startups or emerging market entrants.",
    )
    market_leaders: List[str] = Field(
        ...,
        min_length=1,
        description="Established market leaders and dominant industry incumbents.",
    )
    startup_challengers: List[str] = Field(
        ...,
        min_length=1,
        description="High-growth startup challengers disrupting the sector.",
    )
    alternative_solutions: List[str] = Field(
        ...,
        min_length=1,
        description="Non-software, manual, or legacy alternative solutions used by customers.",
    )
    competition_intensity: str = Field(
        ...,
        description="Overall market competition intensity (e.g. Low, Moderate, High, Fierce).",
    )
    major_competitor_count: int = Field(
        ...,
        ge=0,
        description="Estimated count of major active competitors in the primary segment.",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score rating strictly between 0.0 and 1.0.",
    )

    @field_validator("confidence_score", mode="before")
    @classmethod
    def normalize_confidence_score(cls, value: Any) -> float:
        """Ensure confidence score is normalized to a float between 0.0 and 1.0."""
        try:
            val = float(value)
            if val > 1.0 and val <= 100.0:
                return round(val / 100.0, 2)
            return round(val, 2)
        except (ValueError, TypeError):
            raise ValueError("confidence_score must be a valid float value between 0.0 and 1.0.")

    @field_validator("competition_intensity")
    @classmethod
    def validate_non_empty_strings(cls, value: str) -> str:
        """Ensure string fields contain meaningful non-whitespace text."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("String field cannot be empty or blank whitespace.")
        return cleaned

    @field_validator("market_leaders", "startup_challengers", "alternative_solutions")
    @classmethod
    def validate_non_empty_lists(cls, items: List[str]) -> List[str]:
        """Ensure list contains non-empty string items."""
        cleaned = [item.strip() for item in items if item and item.strip()]
        if not cleaned:
            raise ValueError("List field must contain at least one valid non-empty string item.")
        return cleaned


class CompetitorComparison(BaseModel):
    """Structured Pydantic schema for CompetitorComparisonAgent output."""

    startup_position: str = Field(
        ...,
        min_length=5,
        description="Assessment of the startup's current market position relative to competitors.",
    )
    competitive_advantages: List[str] = Field(
        ...,
        min_length=1,
        description="Key strategic advantages and unique moats held by the startup.",
    )
    competitive_weaknesses: List[str] = Field(
        ...,
        min_length=1,
        description="Key competitive vulnerabilities or gaps relative to established incumbents.",
    )
    feature_comparison: List[str] = Field(
        ...,
        min_length=1,
        description="High-level comparison points of key feature capabilities vs competitors.",
    )
    technology_comparison: str = Field(
        ...,
        description="Comparison of technological stack, AI depth, and architecture vs competitors.",
    )
    customer_focus_comparison: str = Field(
        ...,
        description="Comparison of target customer segment focus and user alignment vs competitors.",
    )
    pricing_strategy_comparison: str = Field(
        ...,
        description="High-level pricing model and cost structure comparison vs market alternatives.",
    )
    innovation_comparison: str = Field(
        ...,
        description="Innovation pace and technological novelty comparison vs incumbents.",
    )
    market_positioning: str = Field(
        ...,
        description="Strategic positioning statement and value vector relative to existing players.",
    )
    competitive_gap: List[str] = Field(
        ...,
        min_length=1,
        description="Unserved market needs or feature voids left open by existing competitors.",
    )
    differentiation_opportunities: List[str] = Field(
        ...,
        min_length=1,
        description="Clear opportunities for the startup to carve out a distinct competitive position.",
    )
    overall_competitive_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Overall rating score of the startup's competitive strength from 0.0 to 10.0.",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score rating strictly between 0.0 and 1.0.",
    )

    @field_validator("confidence_score", mode="before")
    @classmethod
    def normalize_confidence_score(cls, value: Any) -> float:
        """Ensure confidence score is normalized to a float between 0.0 and 1.0."""
        try:
            val = float(value)
            if val > 1.0 and val <= 100.0:
                return round(val / 100.0, 2)
            return round(val, 2)
        except (ValueError, TypeError):
            raise ValueError("confidence_score must be a valid float value between 0.0 and 1.0.")

    @field_validator("overall_competitive_score", mode="before")
    @classmethod
    def normalize_overall_score(cls, value: Any) -> float:
        """Ensure overall competitive score is normalized between 0.0 and 10.0."""
        try:
            val = float(value)
            if val > 10.0 and val <= 100.0:
                return round(val / 10.0, 2)
            return round(val, 2)
        except (ValueError, TypeError):
            raise ValueError("overall_competitive_score must be a valid float value between 0.0 and 10.0.")

    @field_validator(
        "startup_position",
        "technology_comparison",
        "customer_focus_comparison",
        "pricing_strategy_comparison",
        "innovation_comparison",
        "market_positioning",
    )
    @classmethod
    def validate_non_empty_strings(cls, value: str) -> str:
        """Ensure string fields contain meaningful non-whitespace text."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("String field cannot be empty or blank whitespace.")
        return cleaned

    @field_validator(
        "competitive_advantages",
        "competitive_weaknesses",
        "feature_comparison",
        "competitive_gap",
        "differentiation_opportunities",
    )
    @classmethod
    def validate_non_empty_lists(cls, items: List[str]) -> List[str]:
        """Ensure list contains non-empty string items."""
        cleaned = [item.strip() for item in items if item and item.strip()]
        if not cleaned:
            raise ValueError("List field must contain at least one valid non-empty string item.")
        return cleaned


class PersonaProfile(BaseModel):
    """Detailed target customer persona profile."""

    persona_name: str = Field(
        ...,
        min_length=1,
        description="Fictional persona identifier name (e.g., Enterprise CTO Elena).",
    )
    persona_type: str = Field(
        ...,
        description="Type category of persona (e.g. Primary Buyer, End User, Decision Maker).",
    )
    age_range: str = Field(
        ...,
        description="Target age demographic bracket (e.g., 30-45).",
    )
    gender: str = Field(
        ...,
        description="Gender breakdown or 'All / Gender Neutral'.",
    )
    occupation: str = Field(
        ...,
        description="Primary job title or professional role.",
    )
    education_level: str = Field(
        ...,
        description="Highest educational attainment.",
    )
    income_range: str = Field(
        ...,
        description="Income bracket or corporate budget range.",
    )
    location: str = Field(
        ...,
        description="Geographic region or urbanization environment.",
    )
    digital_literacy: str = Field(
        ...,
        description="Digital literacy level (e.g., High, Moderate, Expert).",
    )
    technical_skill_level: str = Field(
        ...,
        description="Technical proficiency and software adoption skill level.",
    )
    goals: List[str] = Field(
        ...,
        min_length=1,
        description="Primary professional or personal goals.",
    )
    motivations: List[str] = Field(
        ...,
        min_length=1,
        description="Core driving motivations for seeking a solution.",
    )
    pain_points: List[str] = Field(
        ...,
        min_length=1,
        description="Key frustrations and operational pain points experienced.",
    )
    challenges: List[str] = Field(
        ...,
        min_length=1,
        description="Main obstacles blocking goal achievement.",
    )
    daily_activities: List[str] = Field(
        ...,
        min_length=1,
        description="Typical daily workflow and operational activities.",
    )
    buying_behavior: str = Field(
        ...,
        description="Purchasing habits, evaluation speed, and approval process.",
    )
    decision_factors: List[str] = Field(
        ...,
        min_length=1,
        description="Key criteria influencing purchasing decision (e.g., ROI, Ease of Use, Security).",
    )
    preferred_platforms: List[str] = Field(
        ...,
        min_length=1,
        description="Preferred software platforms, OS, and ecosystems.",
    )
    communication_channels: List[str] = Field(
        ...,
        min_length=1,
        description="Preferred channels for marketing and support (e.g., Email, LinkedIn, Slack).",
    )
    device_usage: List[str] = Field(
        ...,
        min_length=1,
        description="Primary hardware devices used (e.g., Desktop Mac/PC, Mobile iOS).",
    )
    expected_features: List[str] = Field(
        ...,
        min_length=1,
        description="Must-have product capabilities expected by this persona.",
    )
    price_sensitivity: str = Field(
        ...,
        description="Price sensitivity rating (e.g., Low - Value Driven, Moderate, High - Budget Constrained).",
    )
    adoption_readiness: str = Field(
        ...,
        description="Readiness to adopt new technology (e.g., Innovator, Early Adopter, Pragmatist).",
    )
    customer_lifetime_value: str = Field(
        ...,
        description="Estimated qualitative or quantitative Customer Lifetime Value (CLV) potential.",
    )

    @field_validator(
        "persona_name",
        "persona_type",
        "age_range",
        "gender",
        "occupation",
        "education_level",
        "income_range",
        "location",
        "digital_literacy",
        "technical_skill_level",
        "buying_behavior",
        "price_sensitivity",
        "adoption_readiness",
        "customer_lifetime_value",
    )
    @classmethod
    def validate_non_empty_strings(cls, value: str) -> str:
        """Ensure string fields contain non-whitespace text."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("PersonaProfile field cannot be empty or blank whitespace.")
        return cleaned

    @field_validator(
        "goals",
        "motivations",
        "pain_points",
        "challenges",
        "daily_activities",
        "decision_factors",
        "preferred_platforms",
        "communication_channels",
        "device_usage",
        "expected_features",
    )
    @classmethod
    def validate_non_empty_lists(cls, items: List[str]) -> List[str]:
        """Ensure list contains non-empty string items."""
        cleaned = [item.strip() for item in items if item and item.strip()]
        if not cleaned:
            raise ValueError("List field must contain at least one valid non-empty string item.")
        return cleaned


class CustomerPersona(BaseModel):
    """Structured Pydantic schema for CustomerPersonaGenerator agent output."""

    primary_persona: PersonaProfile = Field(
        ...,
        description="Core target customer persona profile.",
    )
    secondary_personas: List[PersonaProfile] = Field(
        default_factory=list,
        description="Secondary or supporting customer persona profiles.",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score rating strictly between 0.0 and 1.0.",
    )

    @field_validator("confidence_score", mode="before")
    @classmethod
    def normalize_confidence_score(cls, value: Any) -> float:
        """Ensure confidence score is normalized to a float between 0.0 and 1.0."""
        try:
            val = float(value)
            if val > 1.0 and val <= 100.0:
                return round(val / 100.0, 2)
            return round(val, 2)
        except (ValueError, TypeError):
            raise ValueError("confidence_score must be a valid float value between 0.0 and 1.0.")


class TAMSAMSOMAnalysis(BaseModel):
    """Structured Pydantic schema for TAMSAMSOMEstimator agent output."""

    tam_description: str = Field(
        ...,
        description="Detailed description of Total Addressable Market (TAM).",
    )
    tam_value: str = Field(
        ...,
        description="Estimated monetary value of TAM (e.g. '$45.2 Billion').",
    )
    sam_description: str = Field(
        ...,
        description="Detailed description of Serviceable Addressable Market (SAM).",
    )
    sam_value: str = Field(
        ...,
        description="Estimated monetary value of SAM (e.g. '$6.8 Billion').",
    )
    som_description: str = Field(
        ...,
        description="Detailed description of Serviceable Obtainable Market (SOM).",
    )
    som_value: str = Field(
        ...,
        description="Estimated monetary value of SOM (e.g. '$120 Million').",
    )
    methodology: str = Field(
        ...,
        description="Methodology and assumptions used for market sizing calculation.",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score rating strictly between 0.0 and 1.0.",
    )

    @field_validator("confidence_score", mode="before")
    @classmethod
    def normalize_confidence_score(cls, value: Any) -> float:
        """Ensure confidence score is normalized to a float between 0.0 and 1.0."""
        try:
            val = float(value)
            if val > 1.0 and val <= 100.0:
                return round(val / 100.0, 2)
            return round(val, 2)
        except (ValueError, TypeError):
            raise ValueError("confidence_score must be a valid float value between 0.0 and 1.0.")

    @field_validator(
        "tam_description",
        "tam_value",
        "sam_description",
        "sam_value",
        "som_description",
        "som_value",
        "methodology",
    )
    @classmethod
    def validate_non_empty_strings(cls, value: str) -> str:
        """Ensure string fields contain non-whitespace text."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("TAMSAMSOMAnalysis field cannot be empty or blank whitespace.")
        return cleaned


class MarketResearchResult(BaseModel):
    """Unified master output model combining all 7 Market Research Crew task analyses."""

    project_id: str = Field(..., description="Unique project UUID identifier.")
    market_research: MarketResearchAnalysis = Field(..., description="Task 1: Market Research Overview.")
    industry_analysis: IndustryAnalysis = Field(..., description="Task 2: Industry Analysis.")
    trend_analysis: TrendAnalysis = Field(..., description="Task 3: Trend Analysis.")
    competitor_discovery: CompetitorDiscovery = Field(..., description="Task 4: Competitor Discovery.")
    competitor_comparison: CompetitorComparison = Field(..., description="Task 5: Competitor Comparison.")
    customer_persona: CustomerPersona = Field(..., description="Task 6: Customer Persona Profiles.")
    tam_sam_som: TAMSAMSOMAnalysis = Field(..., description="Task 7: TAM SAM SOM Market Sizing.")
    overall_summary: str = Field(..., description="Comprehensive synthesized overall market research executive summary.")
    overall_market_score: float = Field(..., ge=0.0, le=100.0, description="Dynamically calculated market opportunity score (0.0 to 100.0).")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence rating across all market research tasks (0.0 to 1.0).")






