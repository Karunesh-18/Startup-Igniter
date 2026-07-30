"""Pydantic schemas for research patent analysis across Crew 3."""

from typing import List, Optional
from pydantic import BaseModel, Field


class PatentAnalysis(BaseModel):
    """Schema representing patent research and prior-art analysis."""

    project_id: Optional[str] = Field(default=None, description="Project UUID string.")
    patent_number: Optional[str] = Field(default=None, description="Patent or application number.")
    title: Optional[str] = Field(default="Prior-Art Patent Analysis", description="Title of patent or prior art.")
    abstract: Optional[str] = Field(default=None, description="Abstract summary.")
    similarity_score: float = Field(default=0.0, description="Prior-art similarity score.")
    inventors: List[str] = Field(default_factory=list, description="List of inventors.")
    key_claims: List[str] = Field(default_factory=list, description="Key patent claims.")

    # Agent output fields
    existing_patent_summary: str = Field(default="", description="Summary of existing patents and prior art.")
    patent_landscape: str = Field(default="", description="Overview of patent density and filing volume.")
    major_patent_holders: List[str] = Field(default_factory=list, description="Top enterprise and academic assignees.")
    related_technology_domains: List[str] = Field(default_factory=list, description="IPC/CPC Technical classification domains.")
    patent_activity_level: str = Field(default="High", description="Activity level (Low, Moderate, High).")
    potential_patent_conflicts: List[str] = Field(default_factory=list, description="Identified IP conflict observations.")
    white_space_opportunities: List[str] = Field(default_factory=list, description="Unclaimed technological white spaces.")
    patentability_assessment: str = Field(default="", description="Evaluation of concept patentability.")
    freedom_to_operate_observations: List[str] = Field(default_factory=list, description="Freedom to operate observations.")
    innovation_opportunities: List[str] = Field(default_factory=list, description="Actionable differentiation vectors.")
    patent_risks: List[str] = Field(default_factory=list, description="Identified IP risks or patent thicket threats.")
    novelty_assessment: str = Field(default="", description="Qualitative assessment of technical novelty.")
    confidence_score: float = Field(default=0.85, description="Confidence score (0.0-1.0).")


class ResearchPaperAnalysis(BaseModel):
    """Schema representing academic research paper & scientific literature analysis."""

    key_research_papers: List[str] = Field(default_factory=list, description="Foundational and benchmark research papers.")
    state_of_the_art_methods: List[str] = Field(default_factory=list, description="State-of-the-art algorithms and models.")
    academic_innovations: List[str] = Field(default_factory=list, description="Recent theoretical breakthroughs.")
    open_problems: List[str] = Field(default_factory=list, description="Unsolved academic research problems.")
    technical_limitations: List[str] = Field(default_factory=list, description="Computational or algorithmic bottlenecks.")
    emerging_research_trends: List[str] = Field(default_factory=list, description="Emerging research directions.")
    academic_novelty_score: float = Field(default=80.0, description="Academic novelty rating (0-100).")
    confidence_score: float = Field(default=0.88, description="Confidence score (0.0-1.0).")
    reasoning_summary: str = Field(default="", description="Detailed reasoning summary.")
    recommendations: List[str] = Field(default_factory=list, description="Strategic recommendations.")


class ExistingSolutionAnalysis(BaseModel):
    """Schema representing commercial product, startup, and open-source landscape evaluation."""

    existing_startups: List[str] = Field(default_factory=list, description="Relevant venture-backed startups.")
    commercial_products: List[str] = Field(default_factory=list, description="Established commercial products.")
    enterprise_software: List[str] = Field(default_factory=list, description="Legacy enterprise suites.")
    open_source_projects: List[str] = Field(default_factory=list, description="Key open-source projects / repos.")
    existing_technologies: List[str] = Field(default_factory=list, description="Core technologies / stacks.")
    market_maturity: str = Field(default="Growing", description="Market maturity stage.")
    solution_gaps: List[str] = Field(default_factory=list, description="Deficiencies and functional gaps in current solutions.")
    confidence_score: float = Field(default=0.90, description="Confidence score (0.0-1.0).")
    reasoning_summary: str = Field(default="", description="Summary of product landscape analysis.")
    recommendations: List[str] = Field(default_factory=list, description="Strategic product positioning recommendations.")


class InnovationGapAnalysis(BaseModel):
    """Schema representing technical, product, customer, and market gap identification."""

    technical_gaps: List[str] = Field(default_factory=list, description="Engineering or algorithmic capability gaps.")
    product_gaps: List[str] = Field(default_factory=list, description="Product workflow or UI/UX gaps.")
    customer_gaps: List[str] = Field(default_factory=list, description="Underserved customer segment pain points.")
    market_gaps: List[str] = Field(default_factory=list, description="Unexploited business model market gaps.")
    innovation_opportunities: List[str] = Field(default_factory=list, description="High-leverage technical innovation opportunities.")
    differentiation_opportunities: List[str] = Field(default_factory=list, description="Defensible differentiation moats.")
    overall_gap_score: float = Field(default=85.0, description="Innovation gap score (0-100).")
    confidence_score: float = Field(default=0.89, description="Confidence score (0.0-1.0).")
    reasoning_summary: str = Field(default="", description="Rationale synthesizing all gaps.")
    recommendations: List[str] = Field(default_factory=list, description="Actionable product and moat recommendations.")


class TechnologyReadiness(BaseModel):
    """Schema representing Technology Readiness Level (TRL) and feasibility assessment."""

    trl_level: int = Field(default=3, description="TRL rating from 1 to 9.")
    trl_stage_name: str = Field(default="TRL 3: Proof of Concept", description="Human-readable TRL stage name.")
    technical_feasibility_assessment: str = Field(default="", description="Feasibility evaluation.")
    infrastructure_complexity: str = Field(default="Moderate", description="Complexity level (Low, Moderate, High, Extreme).")
    engineering_complexity: str = Field(default="High", description="Engineering complexity (Low, Moderate, High, Extreme).")
    technology_dependencies: List[str] = Field(default_factory=list, description="Third-party frameworks and infrastructure dependencies.")
    scalability_assessment: str = Field(default="", description="Assessment of system scalability bottlenecks.")
    development_risks: List[str] = Field(default_factory=list, description="Key technical execution risks.")
    estimated_time_to_mvp_months: int = Field(default=4, description="Estimated months to functional MVP.")
    confidence_score: float = Field(default=0.88, description="Confidence score (0.0-1.0).")
    reasoning_summary: str = Field(default="", description="Detailed technical rationale.")
    recommendations: List[str] = Field(default_factory=list, description="Engineering and infrastructure derisking recommendations.")


class IPStrategy(BaseModel):
    """Schema representing intellectual property protection strategy and portfolio roadmap."""

    patent_strategy_recommendations: List[str] = Field(default_factory=list, description="Priority patent filing recommendations.")
    trade_secret_opportunities: List[str] = Field(default_factory=list, description="Proprietary trade secret protections.")
    copyright_protection_areas: List[str] = Field(default_factory=list, description="Source code and design copyright areas.")
    licensing_considerations: List[str] = Field(default_factory=list, description="Commercial API and open-source licensing considerations.")
    defensive_ip_tactics: List[str] = Field(default_factory=list, description="Defensive publication and moat tactics.")
    open_source_strategy: str = Field(default="Open-core model", description="Open-source vs proprietary licensing model strategy.")
    ip_defensibility_score: float = Field(default=82.0, description="IP defensibility score (0-100).")
    confidence_score: float = Field(default=0.90, description="Confidence score (0.0-1.0).")
    reasoning_summary: str = Field(default="", description="IP portfolio rationale.")
    recommendations: List[str] = Field(default_factory=list, description="Actionable IP steps.")


class ResearchPatentResult(BaseModel):
    """Unified master output model for Research & Patent Analysis Crew (Crew 3)."""

    project_id: str = Field(description="Unique project UUID string identifier.")
    startup_idea_text: str = Field(default="", description="Submitted raw startup proposal text.")
    patent_analysis: Optional[PatentAnalysis] = Field(default=None, description="Prior-art patent search analysis.")
    research_paper_analysis: Optional[ResearchPaperAnalysis] = Field(default=None, description="Academic literature analysis.")
    existing_solution_analysis: Optional[ExistingSolutionAnalysis] = Field(default=None, description="Commercial & open-source landscape evaluation.")
    innovation_gap_analysis: Optional[InnovationGapAnalysis] = Field(default=None, description="Technical, product, customer & market gap analysis.")
    technology_readiness: Optional[TechnologyReadiness] = Field(default=None, description="TRL rating & technical feasibility assessment.")
    ip_strategy: Optional[IPStrategy] = Field(default=None, description="Intellectual property strategy & roadmap.")
    overall_novelty_score: float = Field(default=85.0, description="Composite novelty score (0-100).")
    trl_level: int = Field(default=3, description="Master TRL level (1-9).")
    confidence_score: float = Field(default=0.88, description="Average confidence score (0.0-1.0).")
    executive_summary: str = Field(default="", description="Executive summary synthesizing all research & IP findings.")
    strategic_recommendations: List[str] = Field(default_factory=list, description="Top strategic recommendations.")
    status: str = Field(default="success", description="Execution status ('success' | 'failed').")
