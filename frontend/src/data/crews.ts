export type CrewStatus = 'idle' | 'active' | 'syncing' | 'complete';

export interface Crew {
  id: number;
  name: string;
  short: string;
  domain: string;
  color: string;
  color2: string;
  icon: string;
  agents: Agent[];
}

export interface Agent {
  id: number;
  name: string;
  role: string;
  crew: number;
}

export const CREWS: Crew[] = [
  {
    id: 1, name: 'Idea Validation', short: 'IDEA', domain: 'Concept',
    color: '#2d7ff9', color2: '#6366f1', icon: 'Lightbulb',
    agents: [
      { id: 1, name: 'Hypothesis Scanner', role: 'Assumptions', crew: 1 },
      { id: 2, name: 'Problem Decoder', role: 'Pain Points', crew: 1 },
      { id: 3, name: 'Market Fit Analyst', role: 'TAM/SAM', crew: 1 },
      { id: 4, name: 'Risk Assessor', role: 'Viability', crew: 1 },
      { id: 5, name: 'Trend Mapper', role: 'Timing', crew: 1 },
      { id: 6, name: 'Uniqueness Probe', role: 'Differentiation', crew: 1 },
    ],
  },
  {
    id: 2, name: 'Market Research', short: 'MKT', domain: 'Landscape',
    color: '#14b8a6', color2: '#2d7ff9', icon: 'Globe',
    agents: [
      { id: 7, name: 'Segment Cartographer', role: 'Segments', crew: 2 },
      { id: 8, name: 'Demand Forecaster', role: 'Demand', crew: 2 },
      { id: 9, name: 'Persona Architect', role: 'ICP', crew: 2 },
      { id: 10, name: 'Competitor Scout', role: 'Landscape', crew: 2 },
      { id: 11, name: 'Pricing Analyst', role: 'WTP', crew: 2 },
      { id: 12, name: 'Channel Strategist', role: 'Distribution', crew: 2 },
    ],
  },
  {
    id: 3, name: 'Research & Patent', short: 'R&D', domain: 'IP',
    color: '#8b5cf6', color2: '#6366f1', icon: 'FlaskConical',
    agents: [
      { id: 13, name: 'Prior Art Miner', role: 'Patents', crew: 3 },
      { id: 14, name: 'Literature Crawler', role: 'Papers', crew: 3 },
      { id: 15, name: 'Patent Drafter', role: 'Claims', crew: 3 },
      { id: 16, name: 'Tech Scout', role: 'Frontier', crew: 3 },
      { id: 17, name: 'Innovation Mapper', role: 'White Space', crew: 3 },
      { id: 18, name: 'Citation Tracker', role: 'Impact', crew: 3 },
    ],
  },
  {
    id: 4, name: 'Technical Feasibility', short: 'TECH', domain: 'Engineering',
    color: '#6366f1', color2: '#8b5cf6', icon: 'Cpu',
    agents: [
      { id: 19, name: 'Stack Optimizer', role: 'Architecture', crew: 4 },
      { id: 20, name: 'Scalability Prober', role: 'Scale', crew: 4 },
      { id: 21, name: 'Security Sentinel', role: 'Threats', crew: 4 },
      { id: 22, name: 'Latency Engineer', role: 'Performance', crew: 4 },
      { id: 23, name: 'Build Estimator', role: 'Timeline', crew: 4 },
      { id: 24, name: 'Integration Mapper', role: 'APIs', crew: 4 },
    ],
  },
  {
    id: 5, name: 'Business Planning', short: 'BIZ', domain: 'Strategy',
    color: '#fb923c', color2: '#ec4899', icon: 'Briefcase',
    agents: [
      { id: 25, name: 'Model Designer', role: 'Revenue', crew: 5 },
      { id: 26, name: 'Unit Economist', role: 'Economics', crew: 5 },
      { id: 27, name: 'Scenario Planner', role: 'Forecast', crew: 5 },
      { id: 28, name: 'Milestone Architect', role: 'Roadmap', crew: 5 },
      { id: 29, name: 'Partnership Scout', role: 'Alliances', crew: 5 },
      { id: 30, name: 'Risk Hedger', role: 'Mitigation', crew: 5 },
    ],
  },
  {
    id: 6, name: 'Product Development', short: 'PROD', domain: 'Build',
    color: '#ec4899', color2: '#fb923c', icon: 'Boxes',
    agents: [
      { id: 31, name: 'Feature Prioritizer', role: 'Scope', crew: 6 },
      { id: 32, name: 'UX Synthesizer', role: 'Flows', crew: 6 },
      { id: 33, name: 'Prototype Forge', role: 'MVP', crew: 6 },
      { id: 34, name: 'Quality Gatekeeper', role: 'QA', crew: 6 },
      { id: 35, name: 'Roadmap Sequencer', role: 'Releases', crew: 6 },
      { id: 36, name: 'Design System Keeper', role: 'Consistency', crew: 6 },
    ],
  },
  {
    id: 7, name: 'Legal', short: 'LGL', domain: 'Compliance',
    color: '#10b981', color2: '#14b8a6', icon: 'Scale',
    agents: [
      { id: 37, name: 'Structure Advisor', role: 'Entity', crew: 7 },
      { id: 38, name: 'Contract Drafter', role: 'Agreements', crew: 7 },
      { id: 39, name: 'IP Protector', role: 'Trademarks', crew: 7 },
      { id: 40, name: 'Privacy Guardian', role: 'GDPR', crew: 7 },
      { id: 41, name: 'Compliance Mapper', role: 'Regulation', crew: 7 },
      { id: 42, name: 'Equity Architect', role: 'Cap Table', crew: 7 },
    ],
  },
  {
    id: 8, name: 'Branding', short: 'BRND', domain: 'Identity',
    color: '#ec4899', color2: '#8b5cf6', icon: 'Sparkles',
    agents: [
      { id: 43, name: 'Narrative Sculptor', role: 'Story', crew: 8 },
      { id: 44, name: 'Visual Identity Forge', role: 'Logo', crew: 8 },
      { id: 45, name: 'Voice Tuner', role: 'Tone', crew: 8 },
      { id: 46, name: 'Positioning Strategist', role: 'Mind', crew: 8 },
      { id: 47, name: 'Color Theorist', role: 'Palette', crew: 8 },
      { id: 48, name: 'Asset Librarian', role: 'Library', crew: 8 },
    ],
  },
  {
    id: 9, name: 'Funding', short: 'FUND', domain: 'Capital',
    color: '#fb923c', color2: '#10b981', icon: 'Banknote',
    agents: [
      { id: 49, name: 'Round Strategist', role: 'Stages', crew: 9 },
      { id: 50, name: 'Valuation Modeler', role: 'Worth', crew: 9 },
      { id: 51, name: 'Investor Matcher', role: 'Fit', crew: 9 },
      { id: 52, name: 'Pitch Deck Composer', role: 'Narrative', crew: 9 },
      { id: 53, name: 'Term Sheet Negotiator', role: 'Terms', crew: 9 },
      { id: 54, name: 'Dilution Optimizer', role: 'Equity', crew: 9 },
    ],
  },
  {
    id: 10, name: 'Growth', short: 'GROW', domain: 'Scale',
    color: '#14b8a6', color2: '#10b981', icon: 'TrendingUp',
    agents: [
      { id: 55, name: 'Growth Loop Designer', role: 'Loops', crew: 10 },
      { id: 56, name: 'Funnel Optimizer', role: 'Conversion', crew: 10 },
      { id: 57, name: 'Retention Engineer', role: 'Churn', crew: 10 },
      { id: 58, name: 'Viral Coefficient Tuner', role: 'Referral', crew: 10 },
      { id: 59, name: 'Expansion Mapper', role: 'Markets', crew: 10 },
      { id: 60, name: 'Lifecycle Orchestrator', role: 'Journeys', crew: 10 },
    ],
  },
  {
    id: 11, name: 'Community', short: 'COMM', domain: 'Network',
    color: '#2d7ff9', color2: '#14b8a6', icon: 'Users',
    agents: [
      { id: 61, name: 'Audience Cultivator', role: 'Tribe', crew: 11 },
      { id: 62, name: 'Content Engine', role: 'Stories', crew: 11 },
      { id: 63, name: 'Ambassador Recruiter', role: 'Advocacy', crew: 11 },
      { id: 64, name: 'Discord Architect', role: 'Spaces', crew: 11 },
      { id: 65, name: 'Event Orchestrator', role: 'Gatherings', crew: 11 },
      { id: 66, name: 'Feedback Synthesizer', role: 'Listening', crew: 11 },
    ],
  },
  {
    id: 12, name: 'Final Report', short: 'RPT', domain: 'Synthesis',
    color: '#8b5cf6', color2: '#ec4899', icon: 'FileText',
    agents: [
      { id: 67, name: 'Insight Distiller', role: 'Summary', crew: 12 },
      { id: 68, name: 'Executive Briefing Writer', role: 'TL;DR', crew: 12 },
      { id: 69, name: 'Data Visualizer', role: 'Charts', crew: 12 },
      { id: 70, name: 'Risk Register Compiler', role: 'Risks', crew: 12 },
      { id: 71, name: 'Action Plan Sequencer', role: 'Next Steps', crew: 12 },
      { id: 72, name: 'Investor Pack Assembler', role: 'Deliverable', crew: 12 },
    ],
  },
];

export interface PipelineStage {
  id: number;
  name: string;
  short: string;
  crew: number;
  icon: string;
  description: string;
  metrics: { label: string; value: string }[];
}

export const PIPELINE: PipelineStage[] = [
  { id: 1, name: 'Idea Validation', short: 'IDEA', crew: 1, icon: 'Lightbulb', description: 'Testing core assumptions against market reality.', metrics: [{ label: 'Hypotheses', value: '14' }, { label: 'Validated', value: '11' }] },
  { id: 2, name: 'Market Research', short: 'MKT', crew: 2, icon: 'Globe', description: 'Mapping demand, segments, and competitive landscape.', metrics: [{ label: 'Segments', value: '6' }, { label: 'TAM', value: '$4.2B' }] },
  { id: 3, name: 'Research & Patent', short: 'R&D', crew: 3, icon: 'FlaskConical', description: 'Mining prior art and securing intellectual property.', metrics: [{ label: 'Patents', value: '3' }, { label: 'White Space', value: '7' }] },
  { id: 4, name: 'Technical Feasibility', short: 'TECH', crew: 4, icon: 'Cpu', description: 'Proving the architecture can scale to demand.', metrics: [{ label: 'Stack', value: '8 layers' }, { label: 'Latency', value: '42ms' }] },
  { id: 5, name: 'Business Planning', short: 'BIZ', crew: 5, icon: 'Briefcase', description: 'Designing the revenue model and unit economics.', metrics: [{ label: 'Revenue', value: 'SaaS' }, { label: 'Margin', value: '78%' }] },
  { id: 6, name: 'Product Development', short: 'PROD', crew: 6, icon: 'Boxes', description: 'Forging the MVP and release roadmap.', metrics: [{ label: 'Features', value: '22' }, { label: 'MVP', value: '6 wks' }] },
  { id: 7, name: 'Legal', short: 'LGL', crew: 7, icon: 'Scale', description: 'Structuring the entity and protecting assets.', metrics: [{ label: 'Entity', value: 'Delaware C' }, { label: 'Trademarks', value: '4' }] },
  { id: 8, name: 'Branding', short: 'BRND', crew: 8, icon: 'Sparkles', description: 'Sculpting the narrative and visual identity.', metrics: [{ label: 'Assets', value: '48' }, { label: 'Guidelines', value: '1' }] },
  { id: 9, name: 'Funding', short: 'FUND', crew: 9, icon: 'Banknote', description: 'Matching with investors and modeling the round.', metrics: [{ label: 'Round', value: 'Seed' }, { label: 'Target', value: '$3M' }] },
  { id: 10, name: 'Growth', short: 'GROW', crew: 10, icon: 'TrendingUp', description: 'Engineering growth loops and retention.', metrics: [{ label: 'CAC', value: '$34' }, { label: 'LTV', value: '$1.2k' }] },
  { id: 11, name: 'Community', short: 'COMM', crew: 11, icon: 'Users', description: 'Cultivating the early audience and advocates.', metrics: [{ label: 'Waitlist', value: '2.4k' }, { label: 'Ambassadors', value: '18' }] },
  { id: 12, name: 'Final Report', short: 'RPT', crew: 12, icon: 'FileText', description: 'Synthesizing everything into an investor-ready pack.', metrics: [{ label: 'Pages', value: '64' }, { label: 'Deliverable', value: 'Ready' }] },
];

export const ALL_AGENTS: Agent[] = CREWS.flatMap((c) => c.agents);
