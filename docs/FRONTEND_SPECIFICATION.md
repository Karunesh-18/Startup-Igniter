# Startup Igniter AI — Frontend Architecture & UI Specification

This document provides the complete, authoritative specification for designing, building, and integrating the frontend application for **Startup Igniter AI**. It details the design system, API interfaces, data schemas, UI components, state management, and real-time execution flows for all three AI crews (**Crew 1: Idea Validation**, **Crew 2: Market Research**, and **Crew 3: Research & Patent Analysis**).

---

## 1. Executive Product Overview & Design System

Startup Igniter AI is an enterprise-grade multi-agent AI engine that evaluates startup proposals across 20 specialized agents grouped into 3 strategic crews.

### 🎨 Design System & Aesthetics
- **Theme**: Dark Mode Glassmorphism with deep space slate background (`#0b0f19`), subtle gradient borders, and frosted glass cards (`backdrop-filter: blur(16px)`).
- **Primary Accent Colors**:
  - Neon Cyan (`#00f2fe` / `#4facfe`) for Primary Actions & Crew 1 (Idea Validation).
  - Electric Violet (`#7f00ff` / `#e100ff`) for Crew 2 (Market Research).
  - Emerald Green (`#00b09b` / `#96c93d`) for Crew 3 (Research & Patent) & TRL Readiness.
  - Amber Orange (`#f6d365` / `#fda085`) for Warnings & Risks.
- **Typography**: Google Fonts — **Inter** for UI controls/body text and **Outfit** for headers, score badges, and metrics.
- **Micro-Animations**: Framer Motion / CSS transitions for smooth card expansion, score gauge animations, and live agent execution progress bars.

---

## 2. API Endpoints & Service Integration

The frontend communicates with the backend via REST API or WebSocket/SSE endpoints.

### API Base URL
`http://localhost:8000/api/v1` (configured via `VITE_API_BASE_URL` or `NEXT_PUBLIC_API_BASE_URL`).

### Key API Routes

| Endpoint | Method | Payload | Returns | Description |
| :--- | :--- | :--- | :--- | :--- |
| `/analysis/workflow` | `POST` | `{ "idea_text": str, "project_id"?: str, "mock_mode"?: bool }` | `StartupAnalysisResult` | Runs full multi-crew workflow (Crew 1 -> Crew 2 -> Crew 3). Proposal entered **ONLY ONCE**. |
| `/crews/idea-validation` | `POST` | `{ "idea_text": str, "project_id"?: str, "mock_mode"?: bool }` | `IdeaValidationResult` | Runs Crew 1 only (6 Agents). |
| `/crews/market-research` | `POST` | `{ "idea_validation": IdeaValidationResult, "project_id"?: str, "mock_mode"?: bool }` | `MarketResearchResult` | Runs Crew 2 only (7 Agents). |
| `/crews/research-patent` | `POST` | `{ "idea_validation": IdeaValidationResult, "market_research"?: MarketResearchResult, "project_id"?: str, "mock_mode"?: bool }` | `ResearchPatentResult` | Runs Crew 3 only (7 Agents). |
| `/projects/{project_id}/memory` | `GET` | — | `Dict[str, Any]` | Fetches all stored memory artifacts from `ProjectMemoryManager`. |

---

## 3. Data Schemas for UI Rendering

### Master Pipeline Result (`StartupAnalysisResult`)

```typescript
interface StartupAnalysisResult {
  project_id: string;
  startup_idea_text: string;
  overall_readiness_score: number; // 0.0 to 100.0 (Weighted Average)
  executive_summary: string;
  strategic_recommendations: string[];
  validation: IdeaValidationResult;
  market_research: MarketResearchResult;
  research_patent?: ResearchPatentResult;
  status: "success" | "failed";
  error_message?: string | null;
}
```

---

### Crew 1: Idea Validation Schemas (`IdeaValidationResult`)

```typescript
interface IdeaValidationResult {
  project_id: string;
  idea_text: string;
  idea_analysis: StartupIdeaAnalysis;
  problem_analysis: ProblemStatementAnalysis;
  customer_identification: CustomerIdentification;
  value_proposition: ValuePropositionAnalysis;
  category_classification: StartupCategoryClassification;
  innovation_scoring: InnovationScoreAnalysis;
  overall_validation_score: number; // 0.0 to 100.0
  status: string;
}

interface StartupIdeaAnalysis {
  summary: string;
  startup_category?: string;
  operational_pillars: string[];
  technical_feasibility_score: number; // 0-100
  rationale: string;
  key_assumptions: string[];
  strengths: string[];
  weaknesses: string[];
}

interface ProblemStatementAnalysis {
  problem_statement: string;
  affected_users: string[];
  root_causes: string[];
  existing_solutions: string[];
  solution_gaps: string[];
  problem_severity: "low" | "medium" | "high" | "critical";
  urgency_score: number; // 0-100
  confidence_score: number; // 0.0-1.0
}

interface CustomerIdentification {
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

interface ValuePropositionAnalysis {
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

interface StartupCategoryClassification {
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

interface InnovationScoreAnalysis {
  overall_innovation_score: number; // 0-100
  innovation_level: string; // "Very Low" | "Low" | "Moderate" | "High" | "Exceptional"
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
```

---

### Crew 2: Market Research Schemas (`MarketResearchResult`)

```typescript
interface MarketResearchResult {
  project_id: string;
  market_research: MarketResearchAnalysis;
  industry_analysis: IndustryAnalysis;
  trend_analysis: TrendAnalysis;
  competitor_discovery: CompetitorDiscovery;
  competitor_comparison: CompetitorComparison;
  customer_persona: CustomerPersona;
  tam_sam_som: TAMSAMSOMAnalysis;
  overall_market_score: number; // 0.0 to 100.0
  confidence_score: number; // 0.0 to 1.0
  status: string;
}

interface MarketResearchAnalysis {
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

interface IndustryAnalysis {
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

interface TrendAnalysis {
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

interface CompetitorDiscovery {
  direct_competitors: CompetitorInfo[];
  indirect_competitors: string[];
  market_leaders: string[];
  startup_challengers: string[];
  competition_intensity: string;
  market_fragmentation: string;
  barrier_to_entry: string;
  confidence_score: number;
}

interface CompetitorInfo {
  name: string;
  website?: string;
  description: string;
  key_features: string[];
  pricing_model: string;
  strengths: string[];
  weaknesses: string[];
}

interface CompetitorComparison {
  competitive_matrix: Record<string, any>;
  feature_comparison: Record<string, string[]>;
  pricing_comparison: Record<string, string>;
  positioning_map: Record<string, any>;
  overall_competitive_score: number; // 0.0 to 10.0
  strategic_advantages: string[];
  vulnerabilities: string[];
  confidence_score: number;
}

interface CustomerPersona {
  primary_persona: PersonaProfile;
  secondary_personas: PersonaProfile[];
  buying_decision_factors: string[];
  customer_journey_stages: string[];
  target_audience_summary: string;
  confidence_score: number;
}

interface PersonaProfile {
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

interface TAMSAMSOMAnalysis {
  tam_value: string; // e.g. "$50 Billion"
  sam_value: string; // e.g. "$5 Billion"
  som_value: string; // e.g. "$250 Million"
  tam_description: string;
  sam_description: string;
  som_description: string;
  methodology: string;
  assumptions: string[];
  growth_projections: string[];
  target_geographies: string[];
  confidence_score: number;
}
```

---

### Crew 3: Research & Patent Analysis Schemas (`ResearchPatentResult`)

```typescript
interface ResearchPatentResult {
  project_id: string;
  startup_idea_text: string;
  patent_analysis: PatentAnalysis;
  research_paper_analysis: ResearchPaperAnalysis;
  existing_solution_analysis: ExistingSolutionAnalysis;
  innovation_gap_analysis: InnovationGapAnalysis;
  technology_readiness: TechnologyReadiness;
  ip_strategy: IPStrategy;
  overall_novelty_score: number; // 0.0 to 100.0
  trl_level: number; // 1 to 9
  confidence_score: number; // 0.0 to 1.0
  executive_summary: string;
  strategic_recommendations: string[];
  status: string;
}

interface PatentAnalysis {
  existing_patent_summary: string;
  patent_landscape: string;
  major_patent_holders: string[];
  related_technology_domains: string[];
  patent_activity_level: "Low" | "Moderate" | "High" | "Very High";
  potential_patent_conflicts: string[];
  white_space_opportunities: string[];
  patentability_assessment: string;
  freedom_to_operate_observations: string[];
  innovation_opportunities: string[];
  patent_risks: string[];
  novelty_assessment: string;
  confidence_score: number;
}

interface ResearchPaperAnalysis {
  key_research_papers: string[];
  state_of_the_art_methods: string[];
  academic_innovations: string[];
  open_problems: string[];
  technical_limitations: string[];
  emerging_research_trends: string[];
  academic_novelty_score: number; // 0-100
  confidence_score: number;
  reasoning_summary: string;
  recommendations: string[];
}

interface ExistingSolutionAnalysis {
  existing_startups: string[];
  commercial_products: string[];
  enterprise_software: string[];
  open_source_projects: string[];
  existing_technologies: string[];
  market_maturity: "Emerging" | "Growing" | "Mature" | "Saturated";
  solution_gaps: string[];
  confidence_score: number;
  reasoning_summary: string;
  recommendations: string[];
}

interface InnovationGapAnalysis {
  technical_gaps: string[];
  product_gaps: string[];
  customer_gaps: string[];
  market_gaps: string[];
  innovation_opportunities: string[];
  differentiation_opportunities: string[];
  overall_gap_score: number; // 0-100
  confidence_score: number;
  reasoning_summary: string;
  recommendations: string[];
}

interface TechnologyReadiness {
  trl_level: number; // 1 to 9
  trl_stage_name: string; // e.g. "TRL 3: Analytical Proof of Concept"
  technical_feasibility_assessment: string;
  infrastructure_complexity: "Low" | "Moderate" | "High" | "Extreme";
  engineering_complexity: "Low" | "Moderate" | "High" | "Extreme";
  technology_dependencies: string[];
  scalability_assessment: string;
  development_risks: string[];
  estimated_time_to_mvp_months: number;
  confidence_score: number;
  reasoning_summary: string;
  recommendations: string[];
}

interface IPStrategy {
  patent_strategy_recommendations: string[];
  trade_secret_opportunities: string[];
  copyright_protection_areas: string[];
  licensing_considerations: string[];
  defensive_ip_tactics: string[];
  open_source_strategy: string;
  ip_defensibility_score: number; // 0-100
  confidence_score: number;
  reasoning_summary: string;
  recommendations: string[];
}
```

---

## 4. UI Page Breakdown & Component Architecture

The frontend application consists of 5 core screens/views:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        STARTUP IGNITER AI NAVBAR                       │
│ [Logo] Startup Igniter AI     [Projects] [New Analysis] [Settings]    │
└────────────────────────────────────────────────────────────────────────┘
                                   │
 ┌─────────────────────────────────┴────────────────────────────────────┐
 │ 1. PROPOSAL ENTRY SCREEN (Hero Input Box + Preset Domain Examples)  │
 └─────────────────────────────────┬────────────────────────────────────┘
                                   │ (Submits Proposal ONCE)
 ┌─────────────────────────────────v────────────────────────────────────┐
 │ 2. LIVE AGENT EXECUTION STEPPER (20 Agents across 3 Crews Stream)    │
 └─────────────────────────────────┬────────────────────────────────────┘
                                   │ (Execution Complete)
 ┌─────────────────────────────────v────────────────────────────────────┐
 │ 3. MASTER EXECUTIVE DASHBOARD                                        │
 │    ┌──────────────────────────┐  ┌─────────────────────────────────┐ │
 │    │ Overall Readiness Donut  │  │ Executive Summary Card          │ │
 │    │       87.3 / 100         │  │ Strategic Recommendations List  │ │
 │    └──────────────────────────┘  └─────────────────────────────────┘ │
 ├──────────────────────────────────────────────────────────────────────┤
 │ TAB NAVIGATION:                                                      │
 │ [Overview]  [Idea Validation]  [Market Research]  [Research & Patent]  │
 ├──────────────────────────────────────────────────────────────────────┤
 │ 4. DYNAMIC TAB DETAILS VIEW                                          │
 │    - Idea Validation: Problem Severity, Customer Matrix, Innovation  │
 │    - Market Research: TAM/SAM/SOM Cards, Competitors, Trend Velocity │
 │    - Research & Patent: Patent Density, SOTA Papers, TRL Meter (1-9) │
 └──────────────────────────────────────────────────────────────────────┘
```

---

### View 1: Proposal Input & Hero Screen
- **Input Control**: Large multi-line textarea with auto-expand capability.
- **Single Entry Point Rule**: Emphasizes that the user types their idea **only once**.
- **Domain Presets**: Clickable quick-fill chips for common verticals (AI Dev Tools, HealthTech Remote Monitoring, Warehouse Robotics, AgriTech Drone Spraying, FinTech Micro-Lending).
- **Execution Mode Toggle**: Switch between `Live AI Execution` and `Mock Fast Test`.

---

### View 2: Live Agent Execution Stepper
Displays real-time execution animation through the 20 AI agents:

```text
[✓] CREW 1: IDEA VALIDATION CREW (6/6 Completed - Score: 92.1/100)
    ✓ StartupIdeaAnalyzer
    ✓ ProblemStatementAnalyzer
    ✓ CustomerIdentifier
    ✓ ValuePropositionAnalyzer
    ✓ StartupCategoryClassifier
    ✓ InnovationScoringAgent

[⚡] CREW 2: MARKET RESEARCH CREW (4/7 Running...)
    ✓ MarketResearchAgent
    ✓ IndustryAnalysisAgent
    ✓ TrendAnalysisAgent
    ➜ CompetitorDiscoveryAgent (Analyzing 3 direct competitors...)
    ○ CompetitorComparisonAgent
    ○ CustomerPersonaGenerator
    ○ TAMSAMSOMEstimator

[ ] CREW 3: RESEARCH & PATENT CREW (0/7 Pending)
```

---

### View 3: Master Executive Dashboard
- **Overall Readiness Gauge**: Animated radial donut chart displaying `overall_readiness_score` (0.0 to 100.0).
- **Crew Sub-Scores Breakdown Cards**:
  - `Idea Validation Score`: e.g. 92.1 / 100 (Cyan)
  - `Market Research Score`: e.g. 82.5 / 100 (Violet)
  - `Research & Novelty Score`: e.g. 90.5 / 100 (Emerald)
  - `Technology Readiness (TRL)`: e.g. Level 3 (Proof of Concept)
- **Executive Summary Card**: Markdown rendered synthesis.
- **Top Strategic Recommendations**: Prioritized action checklist with status icons.

---

### View 4: Tabbed Deep-Dive Views

#### Tab A: Idea Validation
- **Problem Severity Radar**: Urgency score gauge and severity badge (`Critical` / `High`).
- **Target Customer Matrix**: Interactive pills for primary/secondary customers, decision-makers, and pain points.
- **Value Proposition Comparison**: Core value prop banner + USP differentiators list.
- **Innovation Breakdown**: Bar chart comparing Novelty, Technological Leap, Defensibility, and Market Disruption.

#### Tab B: Market Research
- **TAM / SAM / SOM Financial Cards**:
  - `TAM` (Total Addressable Market): e.g. $13.4 Billion (3-card grid with descriptions).
  - `SAM` (Serviceable Addressable Market): e.g. $1.2 Billion.
  - `SOM` (Serviceable Obtainable Market): e.g. $50 Million.
- **Competitor Comparison Table**: Interactive matrix comparing Direct Competitors, Pricing Models, Strengths, and Weaknesses.
- **Trend Velocity Metrics**: Technology, consumer, and macro trends with trend velocity badge (`High Acceleration`).

#### Tab C: Research & Patent Analysis
- **Patent Activity Gauge**: Density meter (`Low` | `Moderate` | `High` | `Very High`) + Major Patent Assignee Chips (IBM, Microsoft, Google).
- **Academic SOTA Paper Feed**: Cards displaying key research literature, state-of-the-art benchmarks, and open research problems.
- **Technology Readiness Level (TRL) Meter**: Interactive 1-to-9 milestone pipeline highlighting current TRL stage, engineering complexity, and estimated months to MVP.
- **IP Protection Roadmap**: Multi-layered strategy breakdown (Provisional Utility Patents, Trade Secrets, Copyright, Open-Source Dual-Licensing).

---

## 5. Technology Stack & Implementation Guidelines

- **Framework**: Next.js 14 (App Router) or Vite + React 18 + TypeScript.
- **Styling**: Vanilla CSS / CSS Modules with custom design tokens or Tailwind CSS (if explicitly configured).
- **UI Components**: Radix UI / Lucide React icons / Recharts or Tremor for score charts and TAM/SAM/SOM financial visualizations.
- **State Management**: Zustand or TanStack Query (React Query) for caching project memory and polling agent progress.
- **Export Capabilities**: PDF Report Generation (via `react-pdf` or `html2pdf.js`) and JSON raw download.

---

## 6. Frontend Verification Checklist

- [ ] Startup idea proposal is prompted **ONLY ONCE** on initial load.
- [ ] Submitting proposal executes full multi-crew workflow without asking for re-entry.
- [ ] Scores are correctly clamped and displayed:
  - Overall Readiness (0.0 to 100.0)
  - Validation Score (0.0 to 100.0)
  - Market Score (0.0 to 100.0)
  - Novelty Score (0.0 to 100.0)
  - TRL Level (1 to 9)
- [ ] Competitor comparison table handles dynamic competitor arrays without breaking layout.
- [ ] TAM/SAM/SOM values render formatted currency strings (`$13.4 Billion`).
- [ ] TRL meter accurately reflects active TRL level (e.g. TRL 3 highlighted).
- [ ] UI is fully responsive across Desktop, Tablet, and Mobile screens.
