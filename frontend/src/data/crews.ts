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
      { id: 1,  name: 'Startup Idea Analyzer',      role: 'Core Analysis',      crew: 1 },
      { id: 2,  name: 'Problem Statement Analyzer',  role: 'Problem Validation', crew: 1 },
      { id: 3,  name: 'Customer Identifier',         role: 'Target Users',       crew: 1 },
      { id: 4,  name: 'Value Proposition Analyzer',  role: 'Value Analysis',     crew: 1 },
      { id: 5,  name: 'Category Classifier',         role: 'Categorization',     crew: 1 },
      { id: 6,  name: 'Innovation Scoring Engine',   role: 'Innovation Score',   crew: 1 },
    ],
  },
  {
    id: 2, name: 'Market Research', short: 'MKT', domain: 'Landscape',
    color: '#14b8a6', color2: '#2d7ff9', icon: 'Globe',
    agents: [
      { id: 7,  name: 'Market Research Analyst',    role: 'Market Overview',   crew: 2 },
      { id: 8,  name: 'Industry Analysis Agent',    role: 'Industry Insights', crew: 2 },
      { id: 9,  name: 'Trend Analysis Agent',       role: 'Market Trends',     crew: 2 },
      { id: 10, name: 'Competitor Discovery',       role: 'Discover Competitors', crew: 2 },
      { id: 11, name: 'Competitor Comparison',      role: 'Compare Competitors', crew: 2 },
      { id: 12, name: 'Customer Persona Generator', role: 'Generate Personas',  crew: 2 },
      { id: 13, name: 'TAM/SAM/SOM Estimator',      role: 'Market Sizing',      crew: 2 },
    ],
  },
  {
    id: 3, name: 'Research & Patent', short: 'R&D', domain: 'IP',
    color: '#8b5cf6', color2: '#6366f1', icon: 'FlaskConical',
    agents: [
      { id: 14, name: 'Prior Art Search Agent',         role: 'Patent Landscape',      crew: 3 },
      { id: 15, name: 'Research Paper Analyzer',        role: 'Academic Research',      crew: 3 },
      { id: 16, name: 'Innovation Gap Identifier',      role: 'Innovation Gaps',        crew: 3 },
      { id: 17, name: 'Technology Readiness Assessor',  role: 'TRL Evaluation',         crew: 3 },
      { id: 18, name: 'IP Strategy Architect',          role: 'IP Protection',          crew: 3 },
      { id: 19, name: 'R&D Summary Agent',              role: 'Research Synthesis',     crew: 3 },
    ],
  },
  {
    id: 4, name: 'Technical Feasibility', short: 'TECH', domain: 'Engineering',
    color: '#6366f1', color2: '#8b5cf6', icon: 'Cpu',
    agents: [
      { id: 20, name: 'Feasibility Analyzer',           role: 'Risk Audit',        crew: 4 },
      { id: 21, name: 'Architecture Recommender',       role: 'System Design',     crew: 4 },
      { id: 22, name: 'Infrastructure Planner',         role: 'Cloud Infra',       crew: 4 },
      { id: 23, name: 'Scalability Assessment',         role: 'Scale Analysis',    crew: 4 },
      { id: 24, name: 'Security Assessment',            role: 'Security Audit',    crew: 4 },
      { id: 25, name: 'Feasibility Summary',            role: 'Tech Synthesis',    crew: 4 },
    ],
  },
  {
    id: 5, name: 'Business Planning', short: 'BIZ', domain: 'Strategy',
    color: '#fb923c', color2: '#ec4899', icon: 'Briefcase',
    agents: [
      { id: 26, name: 'Lean Canvas Agent',              role: 'Business Model',    crew: 5 },
      { id: 27, name: 'Financial Model Agent',          role: 'Unit Economics',    crew: 5 },
      { id: 28, name: 'Revenue Model Agent',            role: 'Revenue Streams',   crew: 5 },
      { id: 29, name: 'Cost Structure Agent',           role: 'COGS & Burn',       crew: 5 },
      { id: 30, name: 'Pricing Strategy Agent',         role: 'Pricing Tiers',     crew: 5 },
      { id: 31, name: 'Business Plan Summary',          role: 'Plan Synthesis',    crew: 5 },
    ],
  },
  {
    id: 6, name: 'Product Development', short: 'PROD', domain: 'Build',
    color: '#ec4899', color2: '#fb923c', icon: 'Boxes',
    agents: [
      { id: 32, name: 'MVP Feature Prioritizer',        role: 'Feature Scope',     crew: 6 },
      { id: 33, name: 'Tech Stack Advisor',             role: 'Stack Selection',   crew: 6 },
      { id: 34, name: 'Product Roadmap Agent',          role: 'Sprint Planning',   crew: 6 },
      { id: 35, name: 'Effort Estimator',               role: 'Dev Timeline',      crew: 6 },
      { id: 36, name: 'UX Recommendation Agent',        role: 'User Experience',   crew: 6 },
      { id: 37, name: 'Product Dev Summary',            role: 'Dev Synthesis',     crew: 6 },
    ],
  },
  {
    id: 7, name: 'Legal & Compliance', short: 'LGL', domain: 'Compliance',
    color: '#10b981', color2: '#14b8a6', icon: 'Scale',
    agents: [
      { id: 38, name: 'Compliance Checklist Agent',     role: 'Regulatory Map',    crew: 7 },
      { id: 39, name: 'Legal Document Drafter',         role: 'Contract Drafting', crew: 7 },
      { id: 40, name: 'Data Privacy Agent',             role: 'GDPR/DPDP Audit',   crew: 7 },
      { id: 41, name: 'Licensing Advisor',              role: 'OSS Licensing',     crew: 7 },
      { id: 42, name: 'Registration Advisor',           role: 'Incorporation',     crew: 7 },
      { id: 43, name: 'Legal Summary',                  role: 'Legal Synthesis',   crew: 7 },
    ],
  },
  {
    id: 8, name: 'Branding & Marketing', short: 'BRND', domain: 'Identity',
    color: '#ec4899', color2: '#8b5cf6', icon: 'Sparkles',
    agents: [
      { id: 44, name: 'Brand & Marketing Agent',        role: 'Brand Positioning', crew: 8 },
      { id: 45, name: 'Naming Advisor',                 role: 'Brand Naming',      crew: 8 },
      { id: 46, name: 'Marketing Strategy Agent',       role: 'Content Strategy',  crew: 8 },
      { id: 47, name: 'Go-To-Market Agent',             role: 'GTM Launch',        crew: 8 },
      { id: 48, name: 'Digital Marketing Agent',        role: 'Paid Ads & SEO',    crew: 8 },
    ],
  },
  {
    id: 9, name: 'Funding Readiness', short: 'FUND', domain: 'Capital',
    color: '#fb923c', color2: '#10b981', icon: 'Banknote',
    agents: [
      { id: 49, name: 'Funding Readiness Agent',        role: 'Pitch Deck',        crew: 9 },
      { id: 50, name: 'Investor Matcher',               role: 'Investor Fit',      crew: 9 },
      { id: 51, name: 'Grant Discovery Agent',          role: 'Non-dilutive Funds', crew: 9 },
      { id: 52, name: 'Valuation Advisor',              role: 'Pre-Money Valuation', crew: 9 },
      { id: 53, name: 'Funding Summary',                role: 'Funding Synthesis', crew: 9 },
    ],
  },
  {
    id: 10, name: 'Growth & Scaling', short: 'GROW', domain: 'Scale',
    color: '#14b8a6', color2: '#10b981', icon: 'TrendingUp',
    agents: [
      { id: 54, name: 'Growth Scaling Agent',           role: 'Growth Loops',      crew: 10 },
      { id: 55, name: 'Expansion Planner',              role: 'Market Expansion',  crew: 10 },
      { id: 56, name: 'Partnership Advisor',            role: 'B2B Partnerships',  crew: 10 },
      { id: 57, name: 'International Expansion',        role: 'Global Markets',    crew: 10 },
    ],
  },
  {
    id: 11, name: 'Community & Ecosystem', short: 'COMM', domain: 'Network',
    color: '#2d7ff9', color2: '#14b8a6', icon: 'Users',
    agents: [
      { id: 58, name: 'Community Peer Review Agent',    role: 'Peer Review',       crew: 11 },
      { id: 59, name: 'Mentor Recommendation',          role: 'Mentor Matching',   crew: 11 },
      { id: 60, name: 'Accelerator Recommender',        role: 'YC / Techstars Fit', crew: 11 },
      { id: 61, name: 'Startup Ecosystem Agent',        role: 'Regional Hubs',     crew: 11 },
    ],
  },
  {
    id: 12, name: 'Executive Reporting', short: 'RPT', domain: 'Synthesis',
    color: '#8b5cf6', color2: '#ec4899', icon: 'FileText',
    agents: [
      { id: 62, name: 'Master Reporting Agent',         role: 'Master Report',     crew: 12 },
      { id: 63, name: 'Readiness Scoring Agent',        role: 'Readiness Score',   crew: 12 },
      { id: 64, name: 'Roadmap Generator',              role: '12-Month Roadmap',  crew: 12 },
      { id: 65, name: 'Action Plan Generator',          role: '30-60-90 Day Plan', crew: 12 },
      { id: 66, name: 'Final Report Generator',         role: 'Investor Pack',     crew: 12 },
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
  { id: 1,  name: 'Idea Validation',       short: 'IDEA', crew: 1,  icon: 'Lightbulb',    description: 'Testing core assumptions against market reality.',              metrics: [{ label: 'Hypotheses',  value: '14'    }, { label: 'Validated',  value: '11'   }] },
  { id: 2,  name: 'Market Research',       short: 'MKT',  crew: 2,  icon: 'Globe',         description: 'Mapping demand, segments, and competitive landscape.',          metrics: [{ label: 'Segments',    value: '6'     }, { label: 'TAM',        value: '$4.2B'}] },
  { id: 3,  name: 'Research & Patent',     short: 'R&D',  crew: 3,  icon: 'FlaskConical',  description: 'Mining prior art and securing intellectual property.',          metrics: [{ label: 'Patents',     value: '3'     }, { label: 'White Space', value: '7'   }] },
  { id: 4,  name: 'Technical Feasibility', short: 'TECH', crew: 4,  icon: 'Cpu',           description: 'Proving the architecture can scale to demand.',                 metrics: [{ label: 'Stack',       value: '8 layers' }, { label: 'Latency', value: '42ms'}] },
  { id: 5,  name: 'Business Planning',     short: 'BIZ',  crew: 5,  icon: 'Briefcase',     description: 'Designing the revenue model and unit economics.',               metrics: [{ label: 'Revenue',     value: 'SaaS'  }, { label: 'Margin',     value: '78%' }] },
  { id: 6,  name: 'Product Development',   short: 'PROD', crew: 6,  icon: 'Boxes',         description: 'Forging the MVP and release roadmap.',                          metrics: [{ label: 'Features',    value: '22'    }, { label: 'MVP',        value: '6 wks'}] },
  { id: 7,  name: 'Legal & Compliance',    short: 'LGL',  crew: 7,  icon: 'Scale',         description: 'Structuring the entity and protecting assets.',                 metrics: [{ label: 'Entity',      value: 'Delaware C' }, { label: 'Trademarks', value: '4'}] },
  { id: 8,  name: 'Branding & Marketing',  short: 'BRND', crew: 8,  icon: 'Sparkles',      description: 'Sculpting the brand narrative and go-to-market strategy.',      metrics: [{ label: 'Assets',      value: '48'    }, { label: 'Channels',   value: '6'   }] },
  { id: 9,  name: 'Funding Readiness',     short: 'FUND', crew: 9,  icon: 'Banknote',      description: 'Matching with investors and modelling the funding round.',       metrics: [{ label: 'Round',       value: 'Seed'  }, { label: 'Target',     value: '$3M' }] },
  { id: 10, name: 'Growth & Scaling',      short: 'GROW', crew: 10, icon: 'TrendingUp',    description: 'Engineering growth loops and international expansion.',          metrics: [{ label: 'CAC',         value: '$34'   }, { label: 'LTV',        value: '$1.2k'}] },
  { id: 11, name: 'Community & Ecosystem', short: 'COMM', crew: 11, icon: 'Users',         description: 'Cultivating the early community and accelerator pipeline.',     metrics: [{ label: 'Waitlist',    value: '2.4k'  }, { label: 'Accelerators', value: '18'}] },
  { id: 12, name: 'Executive Reporting',   short: 'RPT',  crew: 12, icon: 'FileText',      description: 'Synthesising all phases into an investor-ready master report.', metrics: [{ label: 'Pages',       value: '64'    }, { label: 'Deliverable', value: 'Ready'}] },
];

export const ALL_AGENTS: Agent[] = CREWS.flatMap((c) => c.agents);
