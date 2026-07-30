"""Pydantic schema definitions for Crew 3 (Research & Patent Analysis Crew)."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class PatentAnalysis(BaseModel):
    """Pydantic schema for structured output of PatentSearchAgent."""

    existing_patent_summary: str = Field(
        description="Comprehensive summary of existing patents and prior art in the target technology domain.",
    )
    patent_landscape: str = Field(
        description="High-level overview of global patent landscape density, trends, and key innovation clusters.",
    )
    major_patent_holders: List[str] = Field(
        min_length=1,
        description="List of key enterprise, academic, or institutional patent assignees and market leaders.",
    )
    related_technology_domains: List[str] = Field(
        min_length=1,
        description="Key technological IPC/CPC classification domains related to the startup proposal.",
    )
    patent_activity_level: str = Field(
        description="Current filing volume and activity level (e.g. 'Low', 'Moderate', 'High', 'Very High').",
    )
    potential_patent_conflicts: List[str] = Field(
        default_factory=list,
        description="Analytical identification of potential patent overlap or intellectual property friction areas.",
    )
    white_space_opportunities: List[str] = Field(
        min_length=1,
        description="Unclaimed technological white spaces, unpatented feature gaps, and novel architectural vectors.",
    )
    patentability_assessment: str = Field(
        description="Evaluation of the core technical concept's potential patentability (novelty, non-obviousness).",
    )
    freedom_to_operate_observations: List[str] = Field(
        min_length=1,
        description="Preliminary analytical observations regarding freedom-to-operate (FTO) and IP commercialization safety.",
    )
    innovation_opportunities: List[str] = Field(
        min_length=1,
        description="Actionable technical differentiation vectors that increase IP protection strength.",
    )
    patent_risks: List[str] = Field(
        min_length=1,
        description="Identified intellectual property risks, patent thickets, or dominant assignee moat threats.",
    )
    novelty_assessment: str = Field(
        description="Overall qualitative assessment of technical novelty relative to public state-of-the-art.",
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0) indicating reliability of the patent landscape analysis.",
    )

    @field_validator("existing_patent_summary", "patent_landscape", "patentability_assessment", "novelty_assessment")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        if not v or len(v.strip()) < 10:
            raise ValueError("Field must contain at least 10 characters of descriptive analysis.")
        return v.strip()

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence_score(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence_score must be between 0.0 and 1.0")
        return round(float(v), 2)


class ResearchPaperAnalysis(BaseModel):
    """Pydantic schema for structured output of ResearchPaperAnalyzerAgent."""

    key_research_papers: List[str] = Field(
        min_length=1,
        description="Key academic papers, publications, and foundational literature in the domain.",
    )
    state_of_the_art_methods: List[str] = Field(
        min_length=1,
        description="Current state-of-the-art algorithms, models, and technical benchmarks.",
    )
    academic_innovations: List[str] = Field(
        min_length=1,
        description="Recent scientific breakthroughs and academic theoretical advancements.",
    )
    open_problems: List[str] = Field(
        min_length=1,
        description="Unsolved academic research problems and technical challenges identified in literature.",
    )
    technical_limitations: List[str] = Field(
        min_length=1,
        description="Known computational, algorithmic, or scaling limitations of state-of-the-art methods.",
    )
    emerging_research_trends: List[str] = Field(
        min_length=1,
        description="Emerging research vectors and frontier exploration topics.",
    )
    academic_novelty_score: int = Field(
        ge=0,
        le=100,
        description="Academic novelty score rating from 0 to 100 relative to published literature.",
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0) for research paper analysis.",
    )
    reasoning_summary: str = Field(
        description="Structured reasoning summary synthesizing state-of-the-art research findings.",
    )
    recommendations: List[str] = Field(
        min_length=1,
        description="Strategic recommendations for bridging academic research into production software.",
    )

    @field_validator("reasoning_summary")
    @classmethod
    def validate_reasoning(cls, v: str) -> str:
        if not v or len(v.strip()) < 10:
            raise ValueError("reasoning_summary must contain at least 10 characters.")
        return v.strip()


class ExistingSolutionAnalysis(BaseModel):
    """Pydantic schema for structured output of ExistingSolutionAnalyzerAgent."""

    existing_startups: List[str] = Field(
        default_factory=list,
        description="Key venture-backed startups offering related commercial solutions.",
    )
    commercial_products: List[str] = Field(
        min_length=1,
        description="Established commercial products and enterprise software suites.",
    )
    enterprise_software: List[str] = Field(
        default_factory=list,
        description="Legacy enterprise software platforms operating in the space.",
    )
    open_source_projects: List[str] = Field(
        default_factory=list,
        description="Relevant open-source repositories, frameworks, and developer tools.",
    )
    existing_technologies: List[str] = Field(
        min_length=1,
        description="Core underlying technologies utilized by existing solutions.",
    )
    market_maturity: str = Field(
        description="Commercial market maturity (e.g., 'Emerging', 'Growing', 'Mature', 'Saturated').",
    )
    solution_gaps: List[str] = Field(
        min_length=1,
        description="Key feature, performance, or accessibility gaps in current commercial offerings.",
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0) for existing solution analysis.",
    )
    reasoning_summary: str = Field(
        description="Structured summary of the existing solution landscape.",
    )
    recommendations: List[str] = Field(
        min_length=1,
        description="Strategic recommendations for out-positioning existing market offerings.",
    )


class InnovationGapAnalysis(BaseModel):
    """Pydantic schema for structured output of InnovationGapIdentifierAgent."""

    technical_gaps: List[str] = Field(
        min_length=1,
        description="Unsolved engineering or technical capability gaps.",
    )
    product_gaps: List[str] = Field(
        min_length=1,
        description="User experience, feature, or workflow product gaps.",
    )
    customer_gaps: List[str] = Field(
        min_length=1,
        description="Underserved customer segment pain points.",
    )
    market_gaps: List[str] = Field(
        min_length=1,
        description="Unexploited business model or market positioning opportunities.",
    )
    innovation_opportunities: List[str] = Field(
        min_length=1,
        description="High-leverage innovation vectors available to the startup.",
    )
    differentiation_opportunities: List[str] = Field(
        min_length=1,
        description="Key differentiation moats separating the proposal from existing options.",
    )
    overall_gap_score: int = Field(
        ge=0,
        le=100,
        description="Overall innovation gap score (0 to 100) indicating size of unclaimed opportunity.",
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0) for innovation gap identification.",
    )
    reasoning_summary: str = Field(
        description="Structured synthesis of technical, product, customer, and market gaps.",
    )
    recommendations: List[str] = Field(
        min_length=1,
        description="Actionable recommendations to capitalize on identified innovation gaps.",
    )


class TechnologyReadiness(BaseModel):
    """Pydantic schema for structured output of TechnologyReadinessAgent."""

    trl_level: int = Field(
        ge=1,
        le=9,
        description="Estimated Technology Readiness Level (TRL 1: Basic Principles to TRL 9: Proven System).",
    )
    trl_stage_name: str = Field(
        description="Official TRL stage name (e.g. 'TRL 3: Proof of Concept', 'TRL 6: Prototype Verified').",
    )
    technical_feasibility_assessment: str = Field(
        description="Comprehensive technical feasibility evaluation.",
    )
    infrastructure_complexity: str = Field(
        description="Infrastructure and cloud operational complexity rating (Low, Moderate, High, Extreme).",
    )
    engineering_complexity: str = Field(
        description="Software and system engineering complexity rating (Low, Moderate, High, Extreme).",
    )
    technology_dependencies: List[str] = Field(
        min_length=1,
        description="Critical third-party APIs, hardware, or model dependencies required to operate.",
    )
    scalability_assessment: str = Field(
        description="System architecture scalability and bottleneck assessment.",
    )
    development_risks: List[str] = Field(
        min_length=1,
        description="Key technical development and execution risks.",
    )
    estimated_time_to_mvp_months: int = Field(
        ge=1,
        le=60,
        description="Estimated development timeline to functional MVP in months.",
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0) for TRL estimation.",
    )
    reasoning_summary: str = Field(
        description="Detailed technical rationale supporting TRL rating and feasibility analysis.",
    )
    recommendations: List[str] = Field(
        min_length=1,
        description="Engineering recommendations to derisk technical development and reach MVP faster.",
    )


class IPStrategy(BaseModel):
    """Pydantic schema for structured output of IntellectualPropertyStrategyAgent."""

    patent_strategy_recommendations: List[str] = Field(
        min_length=1,
        description="Actionable patent filing strategies (utility patents, provisional filings, global PCT).",
    )
    trade_secret_opportunities: List[str] = Field(
        min_length=1,
        description="Proprietary algorithms, training datasets, or trade secrets to keep confidential.",
    )
    copyright_protection_areas: List[str] = Field(
        min_length=1,
        description="Software codebase, UI design, and documentation copyright protection areas.",
    )
    licensing_considerations: List[str] = Field(
        min_length=1,
        description="Inbound/outbound licensing, commercial API terms, and IP monetization models.",
    )
    defensive_ip_tactics: List[str] = Field(
        min_length=1,
        description="Defensive publication, prior art establishment, and IP moat expansion tactics.",
    )
    open_source_strategy: str = Field(
        description="Open-source licensing strategy (e.g., dual-licensing, open-core, Apache 2.0).",
    )
    ip_defensibility_score: int = Field(
        ge=0,
        le=100,
        description="Overall IP defensibility score (0 to 100) indicating long-term competitive moat strength.",
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0) for IP strategy recommendations.",
    )
    reasoning_summary: str = Field(
        description="Structured rationale for IP portfolio construction.",
    )
    recommendations: List[str] = Field(
        min_length=1,
        description="Prioritized roadmap of immediate IP protection actions.",
    )


class ResearchPatentResult(BaseModel):
    """Master composite result model for the complete Research & Patent Analysis Crew (Crew 3)."""

    project_id: str = Field(description="Unique project UUID string identifier.")
    startup_idea_text: str = Field(description="Original submitted startup proposal text.")
    patent_analysis: PatentAnalysis = Field(
        description="Patent landscape, prior art, assignees, and white space assessment."
    )
    research_paper_analysis: ResearchPaperAnalysis = Field(
        description="Academic literature, state-of-the-art benchmarks, and scientific innovations."
    )
    existing_solution_analysis: ExistingSolutionAnalysis = Field(
        description="Commercial products, startups, open-source projects, and market maturity."
    )
    innovation_gap_analysis: InnovationGapAnalysis = Field(
        description="Technical, product, customer, and market gap identification."
    )
    technology_readiness: TechnologyReadiness = Field(
        description="TRL level estimation, engineering complexity, and development roadmap."
    )
    ip_strategy: IPStrategy = Field(
        description="Patent strategy, trade secrets, open-source strategy, and IP defensibility."
    )
    overall_novelty_score: float = Field(
        ge=0.0,
        le=100.0,
        description="Composite overall novelty & defensibility score (0.0 to 100.0).",
    )
    trl_level: int = Field(
        ge=1,
        le=9,
        description="Master TRL level rating (1 to 9).",
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall average confidence rating score (0.0 to 1.0).",
    )
    executive_summary: str = Field(
        description="High-level executive summary of research, novelty, TRL, and IP protection.",
    )
    strategic_recommendations: List[str] = Field(
        min_length=1,
        description="Top actionable strategic recommendations for technical and IP execution.",
    )
    status: str = Field(default="success", description="Crew execution status string.")
    error_message: Optional[str] = Field(default=None, description="Execution error message if failed.")

    @field_validator("overall_novelty_score")
    @classmethod
    def validate_novelty_score(cls, v: float) -> float:
        return round(float(v), 1)

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        return round(float(v), 2)
