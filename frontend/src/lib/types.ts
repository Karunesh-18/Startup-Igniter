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

// ─── Crews 4-12 ──────────────────────────────────────────────
// Mirrors ai/schemas/{feasibility,business_plan,product_development,
// legal_compliance,branding_marketing,funding,growth_scaling,community,
// reporting}.py. Every field is optional on purpose: these crews are new and
// their schemas are still moving, and the UI renders them through one
// generic renderer (results/GenericCrew.tsx), so a renamed or missing field
// degrades to "not shown" instead of a crash.

export interface FeasibilityResult {
  project_id?: string;
  technical_feasibility_score?: number; // 0-100
  operational_feasibility_score?: number; // 0-100
  financial_feasibility_score?: number; // 0-100
  key_risks?: string[];
  mitigation_strategies?: string[];
  executive_summary?: string;
  confidence_score?: number; // 0-1
}

export interface BusinessPlanResult {
  project_id?: string;
  lean_canvas?: {
    problem?: string;
    solution?: string;
    unique_value_proposition?: string;
    unfair_advantage?: string;
    customer_segments?: string;
    key_metrics?: string[];
    channels?: string[];
    cost_structure?: string[];
    revenue_streams?: string[];
  };
  financial_model?: {
    pricing_model?: string;
    price_points?: Record<string, string>;
    estimated_cac?: string | null;
    estimated_ltv?: string | null;
  };
  executive_summary?: string;
  confidence_score?: number;
}

export interface ProductDevelopmentResult {
  project_id?: string;
  mvp_features?: { feature_name?: string; description?: string; priority?: string; complexity?: string }[];
  tech_stack?: { frontend?: string; backend?: string; database?: string; hosting?: string; ai_ml_tools?: string[] };
  architecture_overview?: string;
  confidence_score?: number;
}

export interface LegalDocumentDraft {
  document_type?: string;
  title?: string;
  content?: string;
  disclaimer?: string;
}

export interface LegalComplianceResult {
  project_id?: string;
  compliance_checklist?: {
    category?: string;
    title?: string;
    description?: string;
    is_mandatory?: boolean;
    regulatory_body?: string | null;
  }[];
  draft_nda?: LegalDocumentDraft | null;
  draft_founder_agreement?: LegalDocumentDraft | null;
  overall_summary?: string;
  confidence_score?: number;
}

export interface BrandingMarketingResult {
  project_id?: string;
  brand_name_suggestions?: string[];
  tagline?: string;
  brand_positioning?: string;
  copywriting_angles?: string[];
  launch_channel_strategy?: string[];
  confidence_score?: number;
}

export interface FundingResult {
  project_id?: string;
  pitch_deck_slides?: string[];
  estimated_valuation_range?: string;
  fundraising_target?: string;
  investor_checklist?: string[];
  investor_types?: string[];
  confidence_score?: number;
}

export interface GrowthScalingResult {
  project_id?: string;
  primary_acquisition_channels?: string[];
  viral_loop_mechanic?: string;
  retention_playbook?: string[];
  target_kpis?: string[];
  confidence_score?: number;
}

export interface CommunityResult {
  project_id?: string;
  peer_review_scorecard?: Record<string, number>;
  community_feedback_summary?: string;
  recommended_mentors?: string[];
  confidence_score?: number;
}

export interface MasterReportResult {
  project_id?: string;
  project_name?: string;
  executive_summary?: string;
  overall_readiness_score?: number; // 0-100
  phase_scores?: Record<string, number>;
  key_recommendations?: string[];
  confidence_score?: number;
}

// ─── Master Combined Result ───────────────────────────────────

export interface AnalysisResult {
  project_id: string;
  idea_text: string;
  status: 'success' | 'failed';
  ai_generated: boolean;
  /** 0-10 from the 3-crew pipeline; may become 0-100 — normalise with toPercent(). */
  overall_readiness_score: number;
  executive_summary?: string;
  strategic_recommendations?: string[];
  idea_validation?: IdeaValidationResult;
  market_research?: MarketResearchResult;
  research_patent?: ResearchPatentResult;
  feasibility?: FeasibilityResult;
  business_planning?: BusinessPlanResult;
  product_development?: ProductDevelopmentResult;
  legal_compliance?: LegalComplianceResult;
  branding_marketing?: BrandingMarketingResult;
  funding?: FundingResult;
  growth_scaling?: GrowthScalingResult;
  community?: CommunityResult;
  reporting?: MasterReportResult;
  error?: string;
}

// ─── Streaming progress (POST /api/v1/analysis/run/stream) ────
// One JSON object per newline-delimited line — see
// backend/api/routers/analysis.py::_stream_analysis for the producer.
// Granularity is per crew: one crew_complete per crew, carrying that crew's
// result object so the UI can preview it before the final `result` line.

export type KnownCrewKey =
  | 'idea_validation'
  | 'market_research'
  | 'research_patent'
  | 'feasibility'
  | 'business_planning'
  | 'product_development'
  | 'legal_compliance'
  | 'branding_marketing'
  | 'funding'
  | 'growth_scaling'
  | 'community'
  | 'reporting';

/** Known keys autocomplete; any other string is still accepted (backend keys are provisional). */
export type StreamCrewKey = KnownCrewKey | (string & {});

export interface StreamStartedEvent {
  type: 'started';
  project_id: string;
  crews: string[];
}

export interface StreamCrewCompleteEvent {
  type: 'crew_complete';
  crew: StreamCrewKey;
  label: string;
  result?: unknown;
}

export interface StreamResultEvent {
  type: 'result';
  result: AnalysisResult;
}

export interface StreamErrorEvent {
  type: 'error';
  project_id?: string;
  error: string;
}

export type StreamEvent =
  | StreamStartedEvent
  | StreamCrewCompleteEvent
  | StreamResultEvent
  | StreamErrorEvent;
