#!/usr/bin/env python3
"""Generate docs/agents/*.md and docs/schemas/*.json from source of truth.

Run this after any change to `frontend/src/data/crews.ts` (the canonical
12-crew/66-agent taxonomy — see docs/README.md for why that file, and not
one of the four other conflicting taxonomies in this repo, was picked) or
to any Pydantic schema in `ai/schemas/`.

Usage (from repo root):
    python docs/generate_docs.py

This intentionally does NOT touch docs/phases/*.md or docs/architecture/*.md —
those are hand-written process documentation and ADRs, not generated from
structured data.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

DOCS_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Canonical taxonomy, transcribed from frontend/src/data/crews.ts.
# Keep this in sync by hand when crews.ts changes -- there is no crew count
# or agent count invariant a script can safely infer, so this is the one
# place a human re-verifies the source of truth matches.
# ---------------------------------------------------------------------------

CREWS = [
    {"id": 1, "name": "Idea Validation", "short": "IDEA", "domain": "Concept", "agents": [
        (1, "Startup Idea Analyzer", "Core Analysis"),
        (2, "Problem Statement Analyzer", "Problem Validation"),
        (3, "Customer Identifier", "Target Users"),
        (4, "Value Proposition Analyzer", "Value Analysis"),
        (5, "Category Classifier", "Categorization"),
        (6, "Innovation Scoring Engine", "Innovation Score"),
    ]},
    {"id": 2, "name": "Market Research", "short": "MKT", "domain": "Landscape", "agents": [
        (7, "Market Research Analyst", "Market Overview"),
        (8, "Industry Analysis Agent", "Industry Insights"),
        (9, "Trend Analysis Agent", "Market Trends"),
        (10, "Competitor Discovery", "Discover Competitors"),
        (11, "Competitor Comparison", "Compare Competitors"),
        (12, "Customer Persona Generator", "Generate Personas"),
        (13, "TAM/SAM/SOM Estimator", "Market Sizing"),
    ]},
    {"id": 3, "name": "Research & Patent", "short": "R&D", "domain": "IP", "agents": [
        (14, "Prior Art Search Agent", "Patent Landscape"),
        (15, "Research Paper Analyzer", "Academic Research"),
        (16, "Innovation Gap Identifier", "Innovation Gaps"),
        (17, "Technology Readiness Assessor", "TRL Evaluation"),
        (18, "IP Strategy Architect", "IP Protection"),
        (19, "R&D Summary Agent", "Research Synthesis"),
    ]},
    {"id": 4, "name": "Technical Feasibility", "short": "TECH", "domain": "Engineering", "agents": [
        (20, "Feasibility Analyzer", "Risk Audit"),
        (21, "Architecture Recommender", "System Design"),
        (22, "Infrastructure Planner", "Cloud Infra"),
        (23, "Scalability Assessment", "Scale Analysis"),
        (24, "Security Assessment", "Security Audit"),
        (25, "Feasibility Summary", "Tech Synthesis"),
    ]},
    {"id": 5, "name": "Business Planning", "short": "BIZ", "domain": "Strategy", "agents": [
        (26, "Lean Canvas Agent", "Business Model"),
        (27, "Financial Model Agent", "Unit Economics"),
        (28, "Revenue Model Agent", "Revenue Streams"),
        (29, "Cost Structure Agent", "COGS & Burn"),
        (30, "Pricing Strategy Agent", "Pricing Tiers"),
        (31, "Business Plan Summary", "Plan Synthesis"),
    ]},
    {"id": 6, "name": "Product Development", "short": "PROD", "domain": "Build", "agents": [
        (32, "MVP Feature Prioritizer", "Feature Scope"),
        (33, "Tech Stack Advisor", "Stack Selection"),
        (34, "Product Roadmap Agent", "Sprint Planning"),
        (35, "Effort Estimator", "Dev Timeline"),
        (36, "UX Recommendation Agent", "User Experience"),
        (37, "Product Dev Summary", "Dev Synthesis"),
    ]},
    {"id": 7, "name": "Legal & Compliance", "short": "LGL", "domain": "Compliance", "agents": [
        (38, "Compliance Checklist Agent", "Regulatory Map"),
        (39, "Legal Document Drafter", "Contract Drafting"),
        (40, "Data Privacy Agent", "GDPR/DPDP Audit"),
        (41, "Licensing Advisor", "OSS Licensing"),
        (42, "Registration Advisor", "Incorporation"),
        (43, "Legal Summary", "Legal Synthesis"),
    ]},
    {"id": 8, "name": "Branding & Marketing", "short": "BRND", "domain": "Identity", "agents": [
        (44, "Brand & Marketing Agent", "Brand Positioning"),
        (45, "Naming Advisor", "Brand Naming"),
        (46, "Marketing Strategy Agent", "Content Strategy"),
        (47, "Go-To-Market Agent", "GTM Launch"),
        (48, "Digital Marketing Agent", "Paid Ads & SEO"),
    ]},
    {"id": 9, "name": "Funding Readiness", "short": "FUND", "domain": "Capital", "agents": [
        (49, "Funding Readiness Agent", "Pitch Deck"),
        (50, "Investor Matcher", "Investor Fit"),
        (51, "Grant Discovery Agent", "Non-dilutive Funds"),
        (52, "Valuation Advisor", "Pre-Money Valuation"),
        (53, "Funding Summary", "Funding Synthesis"),
    ]},
    {"id": 10, "name": "Growth & Scaling", "short": "GROW", "domain": "Scale", "agents": [
        (54, "Growth Scaling Agent", "Growth Loops"),
        (55, "Expansion Planner", "Market Expansion"),
        (56, "Partnership Advisor", "B2B Partnerships"),
        (57, "International Expansion", "Global Markets"),
    ]},
    {"id": 11, "name": "Community & Ecosystem", "short": "COMM", "domain": "Network", "agents": [
        (58, "Community Peer Review Agent", "Peer Review"),
        (59, "Mentor Recommendation", "Mentor Matching"),
        (60, "Accelerator Recommender", "YC / Techstars Fit"),
        (61, "Startup Ecosystem Agent", "Regional Hubs"),
    ]},
    {"id": 12, "name": "Executive Reporting", "short": "RPT", "domain": "Synthesis", "agents": [
        (62, "Master Reporting Agent", "Master Report"),
        (63, "Readiness Scoring Agent", "Readiness Score"),
        (64, "Roadmap Generator", "12-Month Roadmap"),
        (65, "Action Plan Generator", "30-60-90 Day Plan"),
        (66, "Final Report Generator", "Investor Pack"),
    ]},
]

# agent_id -> (module_path, backend_role, schema_class_name)
# Only crews 1-3 have real backend modules. existing_solution_analyzer_agent
# is a 7th real agent in crew 3 with NO frontend id -- see the taxonomy ADR.
IMPLEMENTED = {
    1: ("ai/agents/idea_validation/startup_idea_analyzer.py", "Senior Startup Architect & Feasibility Lead", "StartupIdeaAnalysis"),
    2: ("ai/agents/idea_validation/problem_statement_analyzer.py", "Lead Problem Validation Strategist", "ProblemStatementAnalysis"),
    3: ("ai/agents/idea_validation/customer_identifier.py", "Target Audience & User Persona Strategist", "CustomerIdentification"),
    4: ("ai/agents/idea_validation/value_proposition_analyzer.py", "Value Proposition & Competitive Advantage Specialist", "ValuePropositionAnalysis"),
    5: ("ai/agents/idea_validation/startup_category_classifier.py", "Startup Category & Taxonomy Lead", "StartupCategoryClassification"),
    6: ("ai/agents/idea_validation/innovation_scoring_agent.py", "Innovation & Technology Differentiation Specialist", "InnovationScoreAnalysis"),
    7: ("ai/agents/market_research/market_research_agent.py", "Senior Market Research & Industry Analysis Specialist", "MarketResearchAnalysis"),
    8: ("ai/agents/market_research/industry_analysis_agent.py", "Senior Industry Analyst & Sector Dynamics Specialist", "IndustryAnalysis"),
    9: ("ai/agents/market_research/trend_analysis_agent.py", "Senior Trend Analysis & Technology Futures Specialist", "TrendAnalysis"),
    10: ("ai/agents/market_research/competitor_discovery_agent.py", "Senior Competitor Intelligence & Market Landscape Specialist", "CompetitorDiscovery"),
    11: ("ai/agents/market_research/competitor_comparison_agent.py", "Senior Competitive Strategy & Market Differentiation Specialist", "CompetitorComparison"),
    12: ("ai/agents/market_research/customer_persona_generator.py", "Senior Customer Research & Persona Generation Specialist", "CustomerPersona"),
    13: ("ai/agents/market_research/tam_sam_som_estimator.py", "Senior Financial & Market Sizing Specialist", "TAMSAMSOMAnalysis"),
    14: ("ai/agents/research_patent/patent_search_agent.py", "Patent & Intellectual Property Research Specialist", "PatentAnalysis"),
    15: ("ai/agents/research_patent/research_paper_analyzer_agent.py", "Academic & Scientific Research Literature Specialist", "ResearchPaperAnalysis"),
    16: ("ai/agents/research_patent/innovation_gap_identifier_agent.py", "Chief Innovation Officer & Strategic Gap Specialist", "InnovationGapAnalysis"),
    17: ("ai/agents/research_patent/technology_readiness_agent.py", "Chief Technology Officer & System Architecture Specialist", "TechnologyReadiness"),
    18: ("ai/agents/research_patent/intellectual_property_strategy_agent.py", "Chief IP Counsel & Strategic Patent Strategist", "IPStrategy"),
    19: ("ai/agents/research_patent/research_patent_summary_agent.py", "Senior Strategic Research & IP Director", "ResearchPatentResult"),
}

# The 7th real crew-3 agent with no frontend counterpart (see the ADR).
UNLISTED_IMPLEMENTED_AGENT = (
    "existing_solution_analyzer_agent",
    "ai/agents/research_patent/existing_solution_analyzer_agent.py",
    "Commercial Solution & Open-Source Landscape Specialist",
    "ExistingSolutionAnalysis",
    3,
)


# crew id -> actual snake_case directory name under ai/crews/ and ai/prompts/
# (independent of the doc-slug, which is kebab-case for URL/filename friendliness)
CREW_DIR_NAMES = {
    1: "idea_validation",
    2: "market_research",
    3: "research_patent",
    4: "feasibility",
    5: "business_planning",
    6: "product_development",
    7: "legal_compliance",
    8: "branding_marketing",
    9: "funding",
    10: "growth_scaling",
    11: "community",
    12: "reporting",
}


def slugify(name: str) -> str:
    import re

    s = name.lower().replace("&", " and ").replace("/", "-")
    s = re.sub(r"[^a-z0-9\-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def render_agent_doc(crew: dict, agent_id: int, name: str, role: str) -> str:
    impl = IMPLEMENTED.get(agent_id)
    crew_slug = slugify(crew["name"])
    crew_dir = CREW_DIR_NAMES[crew["id"]]
    phase_num = f"{crew['id']:02d}"

    if impl:
        module_path, backend_role, schema_name = impl
        badge = "🟢 IMPLEMENTED"
        status_block = f"""## Implementation

| | |
|---|---|
| Module | `{module_path}` |
| Backend role string | {backend_role} |
| Output schema | [`{schema_name}`](../schemas/{schema_name}.json) |
| Prompt | `ai/prompts/{crew_dir}/*.md` |

This agent makes a real, self-hosted-model-backed LLM call through
[`ai.llm.gateway`](../architecture/0001-llm-gateway.md), validated against its
output schema with a bounded repair loop on schema mismatch.
"""
    else:
        badge = "⚪ SPECIFIED"
        status_block = f"""## Implementation

**Not built.** `ai/crews/{crew_dir}/tasks.py` returns a hardcoded literal
result for the whole {crew['name']} crew — no LLM call, no per-agent
reasoning. This document describes the *intended* behavior so it can be
implemented against a real spec rather than invented at build time.

Building this agent means: a Pydantic output schema in `ai/schemas/`, a
system prompt in `ai/prompts/{crew_dir}/`, and a `get_*_agent()` /
`run_*_agent()` pair following the pattern in
`ai/agents/idea_validation/startup_idea_analyzer.py` (the reference
implementation — see [Phase {phase_num}](../phases/{phase_num}-{crew_slug}.md)).
"""

    return f"""# {name}

**Crew:** [{crew['name']}](../phases/{phase_num}-{crew_slug}.md) ({crew['short']}) · **Role:** {role} · **Status:** {badge}

{status_block}
## Where this fits

Part of the **{crew['name']}** crew ({crew['domain']}), agent {agent_id} of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
"""


def render_unlisted_agent_doc() -> str:
    name, module_path, role, schema_name, crew_id = UNLISTED_IMPLEMENTED_AGENT
    crew = next(c for c in CREWS if c["id"] == crew_id)
    crew_slug = slugify(crew["name"])
    phase_num = f"{crew_id:02d}"
    return f"""# Existing Solution Analyzer

**Crew:** [{crew['name']}](../phases/{phase_num}-{crew_slug}.md) ({crew['short']}) · **Role:** Commercial Landscape Analysis · **Status:** 🟢 IMPLEMENTED (not in the frontend's 66)

## Implementation

| | |
|---|---|
| Module | `{module_path}` |
| Backend role string | {role} |
| Output schema | [`{schema_name}`](../schemas/{schema_name}.json) |

## A real inconsistency, not a doc error

This is a genuine 7th agent in the Research & Patent crew's backend
(`ai/agents/research_patent/`) with no corresponding entry in
`frontend/src/data/crews.ts`'s 66-agent list — the frontend lists 6 agents
for this crew (ids 14-19), the backend implements 7. See
[ADR 0004: taxonomy conflict](../architecture/0004-taxonomy-conflict.md).
"""


def main() -> None:
    agents_dir = DOCS_DIR / "agents"
    agents_dir.mkdir(exist_ok=True)

    count = 0
    for crew in CREWS:
        for agent_id, name, role in crew["agents"]:
            slug = f"{agent_id:02d}-{slugify(name)}"
            (agents_dir / f"{slug}.md").write_text(render_agent_doc(crew, agent_id, name, role), encoding="utf-8")
            count += 1

    (agents_dir / "67-existing-solution-analyzer.md").write_text(render_unlisted_agent_doc(), encoding="utf-8")
    count += 1
    print(f"Wrote {count} agent docs to {agents_dir}")

    # --- Schemas -------------------------------------------------------
    schemas_dir = DOCS_DIR / "schemas"
    schemas_dir.mkdir(exist_ok=True)

    import importlib
    import pkgutil

    import ai.schemas as schemas_pkg
    from pydantic import BaseModel

    schema_count = 0
    for _, module_name, _ in pkgutil.iter_modules(schemas_pkg.__path__):
        module = importlib.import_module(f"ai.schemas.{module_name}")
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BaseModel)
                and attr is not BaseModel
                and attr.__module__ == module.__name__
            ):
                schema_json = attr.model_json_schema()
                (schemas_dir / f"{attr_name}.json").write_text(
                    json.dumps(schema_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
                )
                schema_count += 1
    print(f"Wrote {schema_count} schema JSON files to {schemas_dir}")


if __name__ == "__main__":
    main()
