// ============================================================
// Startup Igniter AI — TypeScript interfaces for all AI crews
// Mirrors the Python Pydantic schemas from the ai/ module.
// ============================================================

// ─── Crew 1: Idea Validation ────────────────────────────────

export interface StartupIdeaAnalysis {
  summary: string;
  startup_category?: string;
  operational_pillars: string[];
  technical_feasibility_score: number;
  rationale: string;
  key_assumptions: string[];
  strengths: string[];
  weaknesses: string[];
}

export interface ProblemStatementAnalysis {
  problem_statement: string;
  affected_users: string[];
  root_causes: string[];
  existing_solutions: string[];
  solution_gaps: string[];
  problem_severity: 'low' | 'medium' | 'high' | 'critical';
  urgency_score: number;
  confidence_score: number;
}

export interface CustomerIdentification {
  primary_customers: string[];
  secondary_customers: string[];
  end_users: string[];
  decision_makers: string[];
  customer_segments: string[];
  demographics: string[];
  geographic_markets: string[];
  pain_points: string[];
  customer_needs: string[];
  motivations: string[];
  willingness_to_pay: string;
  confidence_score: number;
}

export interface ValuePropositionAnalysis {
  core_value_proposition: string;
  unique_selling_proposition: string;
  functional_benefits: string[];
  emotional_benefits: string[];
  customer_outcomes: string[];
  differentiators: string[];
  value_clarity_score: number;
  customer_value_score: number;
  confidence_score: number;
}

export interface StartupCategoryClassification {
  primary_category: string;
  secondary_categories: string[];
  industry: string;
  technology_domains: string[];
  business_model: string;
  revenue_model: string;
  startup_stage: string;
  target_market: string;
  confidence_score: number;
  reasoning: string;
}

export interface InnovationScoreAnalysis {
  overall_innovation_score: number;
  innovation_level: string;
  novelty_score: number;
  technology_innovation_score: number;
  business_model_innovation_score: number;
  problem_originality_score: number;
  differentiation_score: number;
  strengths: string[];
  improvement_opportunities: string[];
  reasoning: string;
  confidence_score: number;
}

export interface IdeaValidationResult {
  project_id: string;
  idea_text: string;
  idea_analysis: StartupIdeaAnalysis;
  problem_analysis: ProblemStatementAnalysis;
  customer_identification: CustomerIdentification;
  value_proposition: ValuePropositionAnalysis;
  category_classification: StartupCategoryClassification;
  innovation_scoring: InnovationScoreAnalysis;
  overall_validation_score: number;
  status?: string;
}

// ─── Crew 2: Market Research ─────────────────────────────────

export interface MarketResearchAnalysis {
  market_overview: string;
  industry_overview: string;
  market_stage: string;
  market_maturity: string;
  market_size_summary: string;
  market_demand: string;
  market_opportunities: string[];
  market_challenges: string[];
  growth_drivers: string[];
  market_risks: string[];
  future_outlook: string;
  confidence_score: number;
}

export interface IndustryAnalysis {
  industry_name: string;
  sector: string;
  industry_growth_rate: string;
  market_drivers: string[];
  regulatory_factors: string[];
  technology_shifts: string[];
  competitive_landscape_summary: string;
  cagr_percentage: number;
  key_players: string[];
  confidence_score: number;
}

export interface TrendAnalysis {
  technology_trends: string[];
  consumer_trends: string[];
  macro_economic_trends: string[];
  emerging_threats: string[];
  future_opportunities: string[];
  trend_velocity: string;
  market_drivers: string[];
  adoption_barriers: string[];
  confidence_score: number;
}

export interface CompetitorInfo {
  name: string;
  website?: string;
  description: string;
  key_features: string[];
  pricing_model: string;
  strengths: string[];
  weaknesses: string[];
}

export interface CompetitorDiscovery {
  direct_competitors: CompetitorInfo[];
  indirect_competitors: string[];
  market_leaders: string[];
  startup_challengers: string[];
  competition_intensity: string;
  market_fragmentation: string;
  barrier_to_entry: string;
  confidence_score: number;
}

export interface CompetitorComparison {
  competitive_matrix: Record<string, unknown>;
  feature_comparison: Record<string, string[]>;
  pricing_comparison: Record<string, string>;
  overall_competitive_score: number;
  strategic_advantages: string[];
  vulnerabilities: string[];
  confidence_score: number;
}

export interface PersonaProfile {
  persona_name: string;
  persona_type: string;
  age_range: string;
  gender: string;
  occupation: string;
  education_level: string;
  income_range: string;
  goals: string[];
  frustrations: string[];
  tech_savviness: string;
  buying_behavior: string;
  preferred_channels: string[];
}

export interface CustomerPersona {
  primary_persona: PersonaProfile;
  secondary_personas: PersonaProfile[];
  buying_decision_factors: string[];
  customer_journey_stages: string[];
  target_audience_summary: string;
  confidence_score: number;
}

export interface TAMSAMSOMAnalysis {
  tam_value: string;
  sam_value: string;
  som_value: string;
  tam_description: string;
  sam_description: string;
  som_description: string;
  methodology: string;
  assumptions: string[];
  growth_projections: string[];
  target_geographies: string[];
  confidence_score: number;
}

export interface MarketResearchResult {
  project_id: string;
  market_research?: MarketResearchAnalysis;
  industry_analysis?: IndustryAnalysis;
  trend_analysis?: TrendAnalysis;
  competitor_discovery?: CompetitorDiscovery;
  competitor_comparison?: CompetitorComparison;
  customer_persona?: CustomerPersona;
  tam_sam_som?: TAMSAMSOMAnalysis;
  overall_market_score?: number;
  confidence_score?: number;
  status?: string;
}

// ─── Crew 3: Research & Patent ───────────────────────────────

export interface PatentAnalysis {
  existing_patent_summary?: string;
  patent_landscape?: string;
  major_patent_holders?: string[];
  related_technology_domains?: string[];
  patent_activity_level?: 'Low' | 'Moderate' | 'High' | 'Very High';
  potential_patent_conflicts?: string[];
  white_space_opportunities?: string[];
  patentability_assessment?: string;
  freedom_to_operate_observations?: string[];
  innovation_opportunities?: string[];
  patent_risks?: string[];
  novelty_assessment?: string;
  confidence_score?: number;
  // legacy fields from feat/research-integrations
  patent_number?: string;
  title?: string;
  abstract?: string;
  similarity_score?: number;
  inventors?: string[];
  key_claims?: string[];
}

export interface ResearchPaperAnalysis {
  key_research_papers: string[];
  state_of_the_art_methods: string[];
  academic_innovations: string[];
  open_problems: string[];
  technical_limitations: string[];
  emerging_research_trends: string[];
  academic_novelty_score: number;
  confidence_score: number;
  reasoning_summary: string;
  recommendations: string[];
}

export interface ExistingSolutionAnalysis {
  existing_startups: string[];
  commercial_products: string[];
  enterprise_software: string[];
  open_source_projects: string[];
  existing_technologies: string[];
  market_maturity: 'Emerging' | 'Growing' | 'Mature' | 'Saturated';
  solution_gaps: string[];
  confidence_score: number;
  reasoning_summary: string;
  recommendations: string[];
}

export interface InnovationGapAnalysis {
  technical_gaps: string[];
  product_gaps: string[];
  customer_gaps: string[];
  market_gaps: string[];
  innovation_opportunities: string[];
  differentiation_opportunities: string[];
  overall_gap_score: number;
  confidence_score: number;
  reasoning_summary: string;
  recommendations: string[];
}

export interface TechnologyReadiness {
  trl_level: number;
  trl_stage_name: string;
  technical_feasibility_assessment: string;
  infrastructure_complexity: 'Low' | 'Moderate' | 'High' | 'Extreme';
  engineering_complexity: 'Low' | 'Moderate' | 'High' | 'Extreme';
  technology_dependencies: string[];
  scalability_assessment: string;
  development_risks: string[];
  estimated_time_to_mvp_months: number;
  confidence_score: number;
  reasoning_summary: string;
  recommendations: string[];
}

export interface IPStrategy {
  patent_strategy_recommendations: string[];
  trade_secret_opportunities: string[];
  copyright_protection_areas: string[];
  licensing_considerations: string[];
  defensive_ip_tactics: string[];
  open_source_strategy: string;
  ip_defensibility_score: number;
  confidence_score: number;
  reasoning_summary: string;
  recommendations: string[];
}

export interface ResearchPatentResult {
  project_id: string;
  startup_idea_text?: string;
  patent_analysis?: PatentAnalysis;
  research_paper_analysis?: ResearchPaperAnalysis;
  existing_solution_analysis?: ExistingSolutionAnalysis;
  innovation_gap_analysis?: InnovationGapAnalysis;
  technology_readiness?: TechnologyReadiness;
  ip_strategy?: IPStrategy;
  overall_novelty_score?: number;
  trl_level?: number;
  confidence_score?: number;
  executive_summary?: string;
  strategic_recommendations?: string[];
  status?: string;
}

// ─── Master Combined Result ───────────────────────────────────

export interface AnalysisResult {
  project_id: string;
  idea_text: string;
  status: 'success' | 'failed';
  ai_generated: boolean;
  overall_readiness_score: number;
  executive_summary?: string;
  strategic_recommendations?: string[];
  idea_validation?: IdeaValidationResult;
  market_research?: MarketResearchResult;
  research_patent?: ResearchPatentResult;
  error?: string;
}

// ─── Crew Progress Tracking ───────────────────────────────────

export interface AgentStep {
  id: number;
  name: string;
  crew: number;
  crewName: string;
  status: 'pending' | 'running' | 'done';
  progress: number;
}
