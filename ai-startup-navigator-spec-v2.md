# AI Startup Navigator / Startup OS — Technical Specification (v2)

This supersedes the earlier slimmed v1 spec. Based on your decisions, the project has grown into a fuller "Startup Operating System": CrewAI stays, the workflow is dynamic per startup category, there's a public community forum, multi-dimensional scoring, and a cost model built almost entirely on free-tier services plus your existing Zyte subscription for scraping.

---

## 1. High-Level Architecture

```
                    Frontend (Next.js)
                           │
                           ▼
                    FastAPI Backend
                           │
                           ▼
                  Workflow Engine  ◄── owns: current phase, unlocked phases,
                           │            category-specific phase sequence, gating logic
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
  Project Memory      Crew Manager       Report Generator
  (Postgres+JSONB      (dispatches to          │
   + pgvector)        the right CrewAI crew)   ▼
        │                  │            PDF / DOCX / PPTX
        │                  ▼
        │            CrewAI Crews → Agents → Tools
        │                  │
        └──────────────────┘
           shared context, read/write every call

        Centralized AI Chat (Intent Router)
                           │
              routes to the right crew's
              knowledge + shared memory,
              always replies in one consistent
              voice — user never sees "15 agents"
```

**Key rule carried over from your feedback:** the Workflow Engine is a plain application component (Python/FastAPI logic backed by Postgres state) — it decides phases, gating, and progression. CrewAI is only ever invoked *inside* a phase to do the actual AI reasoning. Don't let CrewAI's own task-chaining logic become your source of truth for where a user is in their journey.

---

## 2. Tech Stack (optimized for $0 infra cost)

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js 14 + TypeScript + Tailwind + shadcn/ui | Free, deploys free on Vercel's hobby tier |
| Backend | FastAPI (Python) | Free, lightweight |
| Database + Auth + Storage | **Supabase (free tier)** | One free-tier account gives you: hosted Postgres **with pgvector already available**, built-in Auth (email/OAuth), and file Storage (for generated PDFs/DOCX/PPTX) — replaces three separate paid services (managed Postgres, Clerk, S3/R2) with one free one |
| Job queue / background workers | **Upstash Redis (free tier)** + Celery or `arq` | Upstash's free tier is serverless Redis, no server to babysit; needed so long AI/agent runs don't block the API |
| Embeddings (for `project_memory` semantic search) | **Self-hosted open-source model** (e.g. `sentence-transformers/all-MiniLM-L6-v2` or `bge-small-en`) run inside your own backend/worker | Zero per-call cost — you control the volume, and `project_memory` gets written to constantly, so a paid embeddings API adds up fast. Quality is more than sufficient for this use case. |
| Frontend hosting | Vercel (hobby/free tier) | Free for this scale |
| Backend/worker hosting | Fly.io or Render free tier | Free tier is limited (cold starts, sleep on idle) — acceptable for a student project/demo, worth knowing before you rely on it for a live pitch |
| Scraping (patents, research aggregators, gov portals without APIs) | **Zyte** (your existing subscription) | Handles proxies/rendering/anti-bot for you — this is what makes multi-jurisdiction patent search realistic at all |
| General web search grounding (market/competitor research) | **Brave Search API free tier** (~2,000 queries/month free) | Genuinely free tier, good enough for grounding market-research claims in real results |
| Document generation | `docxtpl`, `python-pptx`, `weasyprint` | All open-source libraries, no API cost |
| CrewAI | Open-source framework | Free itself — your only real recurring cost is the LLM calls it makes |

**The one cost that can't be made free:** Claude API calls themselves. CrewAI, Supabase, Zyte, Brave Search, embeddings — all free or already paid for. The model calls are inherent to the product; the way to control that cost is call discipline (below), not avoiding the API.

---

## 3. Data Model (Postgres + JSONB, no MongoDB)

```
users
  id, email, name, role (student/working_professional/graduate/researcher/faculty), created_at

startup_categories
  id, name, description, workflow (jsonb — ordered phase list for this category),
  validation_rules (jsonb), created_by (user_id, nullable), is_system (bool),
  is_verified (bool), created_at
  -- system-seeded categories (SaaS, HealthTech, FinTech, D2C, Marketplace, EdTech,
  -- AgriTech, DeepTech, ClimateTech, etc.) plus user-submitted ones awaiting verification

projects
  id, user_id, name, category_id (fk → startup_categories), current_phase,
  category_confidence, category_overridden_by_user (bool), created_at

project_memory
  id, project_id, key, value (jsonb), embedding (vector), source_phase, created_at
  -- the cross-phase shared memory table — every AI call reads relevant rows here first

idea_analysis
  id, project_id, problem_statement, target_audience, value_prop

validation_reports
  id, project_id, market_summary, competitor_summary, similar_startups (jsonb),
  swot (jsonb), created_at

scores
  id, project_id, dimension (validation/business/market/technology/patent/
  financial/legal/overall), value, rationale, created_at
  -- one row per dimension per scoring run → powers the radar chart / KPI dashboard

risk_assessments
  id, project_id, risk_type (market/technical/financial/legal/team/execution),
  severity (low/medium/high), rationale, mitigation, created_at

business_plans
  id, project_id, lean_canvas (jsonb), revenue_model, pricing_notes

legal_checklists
  id, project_id, category_id, checklist_items (jsonb), completed_items (jsonb)

legal_documents
  id, project_id, doc_type, status ('ai_draft' — always this, never 'final'),
  template_source, storage_url, generated_at

patent_research_reports
  id, project_id, query, source ('patentsview'/'zyte_scrape'/'user_upload'/
  'arxiv'/'semantic_scholar'/'openalex'/'crossref'), title, similarity_score,
  novelty_notes, source_url

documents
  id, project_id, type, phase, storage_url, created_at

project_members
  id, project_id, user_id, role (founder/co_founder/mentor/advisor/investor/admin)

forum_posts
  id, user_id, title, body, category, created_at

forum_comments
  id, post_id, user_id, body, created_at

forum_votes
  id, post_id, user_id, value (+1/-1)

phase_log
  id, project_id, phase, status, started_at, completed_at
```

---

## 4. Dynamic Workflow Engine

Each `startup_categories` row carries its own `workflow` JSON — an ordered phase list plus per-phase gating rules. Examples:

```json
// AI Startup
["idea", "market_validation", "patent_research", "business_planning", "mvp", "legal", "launch"]

// Healthcare Startup
["idea", "market_validation", "medical_compliance", "clinical_validation", "business_planning", "legal", "launch"]

// Marketplace
["idea", "demand_validation", "buyer_validation", "seller_validation", "revenue_model", "mvp", "launch"]
```

The Workflow Engine reads this array off the project's category at each step to decide what's unlocked next — no hardcoded phase chain in application code. New categories (system or user-submitted) just need a workflow array to plug in immediately.

**Category flow:**
1. AI predicts category + confidence during idea analysis.
2. User can accept or override with any existing category.
3. If nothing fits, user types a new category name → creates a new `startup_categories` row (`is_system=false`, `is_verified=false`) with a sensible default workflow, editable later by an admin/moderator who can mark it verified.

---

## 5. Crew Manager + CrewAI

- **Crew Manager** is a thin dispatch layer: given `(project, current_phase)`, it knows which CrewAI crew to invoke and what memory context to hand it.
- Each crew is scoped to a phase (Idea Analysis, Validation, Patent & Research, Business, Legal, Marketing, Funding, etc.) with 3-6 agents — resist the urge to make every agent from the original brainstorm its own persona; several of those (e.g. "Financial Agent" and "Pricing Agent") can be one agent with a broader prompt.
- Every agent call: (1) reads relevant `project_memory` rows, (2) does its task, (3) writes structured JSON output back to `project_memory` and the relevant table.

---

## 6. AI Use-Case Table (updated)

| Use Case | Method | Model | Notes |
|---|---|---|---|
| Idea categorization | Structured JSON output, checked against `startup_categories` | Haiku | User can override regardless of confidence |
| Idea analysis | Structured output prompt | Sonnet | — |
| Market research | Brave Search API (free tier) → synthesis | Sonnet + search tool | Ground every claim in a real result |
| Competitor + similar-startup detection | Brave Search + structured comparison output | Sonnet + search tool | Lives inside Validation crew, not a separate module |
| SWOT / expanded feasibility (technical, business, financial, operational, manufacturing, supply chain, scalability, legal, market, risk, tech readiness) | Structured multi-field output, reasoning over `project_memory` | Sonnet | Each dimension gets its own sub-rating + rationale |
| Multi-dimensional scores | Sub-ratings from the LLM (0–100 per dimension with rationale) → **weighted sum computed in Python**, never by the LLM | Deterministic code + Sonnet inputs | Feeds `scores` table → radar chart |
| Risk prediction | Structured output: risk type, severity, mitigation | Sonnet | Own `risk_assessments` rows |
| Research paper search | **Free official APIs**: arXiv, Semantic Scholar, OpenAlex, Crossref | None needed beyond the APIs; Haiku to summarize results | No scraping required here at all |
| Patent search (US) | **PatentsView API** (USPTO, free) | Haiku to structure results | |
| Patent search (global: Google Patents, Espacenet, WIPO, India IP) | **Zyte** scrapes the public search-result pages for these sites given a query | Haiku/Sonnet to extract + rank similarity from scraped content | No unified API exists — Zyte is exactly the right tool for this gap |
| User-uploaded patent/research/proposal validation | User uploads PDF → Claude compares against retrieved search + scrape results | Sonnet | Genuinely differentiating feature; combine with the search-based discovery above, not instead of it |
| Lean Canvas / BMC generation | Template-fill from `project_memory` | Sonnet | |
| Legal checklist | Static, hand-maintained per category | None | |
| Legal document drafts (agreements, NDAs, founder agreements) | Template-fill from permissively-licensed public templates + LLM fill-in | Sonnet | Always stored with `status='ai_draft'`; UI must show a persistent "AI-generated draft — have a qualified lawyer review before use" notice on the document itself |
| Centralized AI chat | Intent router → correct crew's context + shared `project_memory`, single consistent response voice/format regardless of which domain answered | Sonnet (router + response), Haiku for simple intent classification | User never sees "which agent" answered |
| Personalized ecosystem recommendations | Structured output using `users.role` + `projects.category` to recommend incubators/schemes/grants/E-Cells | Haiku, grounded with Brave Search for current programs | |
| Investor recommendation (v2+, not v1) | Curated, manually/Zyte-populated `investors` table tagged by stage/sector/geography/check size, ranked by fit | None (retrieval + ranking, not generation) | This is recommendation, not real matching/introduction — be explicit about that in the UI copy |
| Document export | `docxtpl` / `python-pptx` / `weasyprint`, filled from structured data already generated | None | |
| Community forum summarization (optional) | Summarize long threads on demand | Haiku | |

---

## 7. External Services — All Free or Already-Owned

| Need | Service | Cost |
|---|---|---|
| DB + Auth + Storage | Supabase | Free tier |
| Redis/queue | Upstash | Free tier |
| Web search grounding | Brave Search API | Free tier (~2,000 queries/month) |
| Research papers | arXiv, Semantic Scholar, OpenAlex, Crossref | Free, no key or free key |
| US patents | PatentsView | Free |
| Global patents / scraping anything without an API | **Zyte** | Already have it |
| Embeddings | Self-hosted sentence-transformers model | Free (compute only) |
| Frontend hosting | Vercel | Free tier |
| Backend hosting | Fly.io / Render | Free tier (has cold-start limits) |
| Email (if needed later) | Resend free tier | Free tier |
| LLM | Claude API | **Not free** — the one real cost, controlled via Haiku/Sonnet split and caching |

---

## 8. Legal Document Liability — Concrete Handling

- Every generated legal document is labeled **"AI-generated draft — for informational purposes, review with a qualified lawyer before use"** directly on the document, not only in a ToS footnote.
- Base every template on well-known, permissively-licensed public templates rather than having the model draft clauses fully from scratch.
- Version and date every template so users know what's current.
- Your platform's own Terms of Service need a liability disclaimer for AI-generated legal/financial content and a statement that no attorney-client relationship is formed — that's a real exposure question for *you* as the operator, worth having an actual lawyer (or your college's legal cell) review before this feature goes live publicly. I can tell you the industry-standard pattern, but I can't assess your specific liability.

---

## 9. Guardrails (unchanged, still critical)

- "AI-generated, verify independently" labeling on legal, patent, and market-size content.
- Legal checklist content dated ("last verified: [date]").
- Per-project-action call budget with a visible progress indicator, not a silent spinner.
- Users can edit any AI output before it's written into `project_memory` — bad data shouldn't silently propagate downstream.

---

## 10. Build Order (Milestones)

1. **Foundation**: Supabase project (DB+Auth+Storage), Next.js shell, `startup_categories` seeded with system categories, empty dashboard
2. **Workflow Engine** reading category-specific phase arrays + phase gating
3. **Idea Analysis + Validation crew** (categorization, market research via Brave Search, competitor/similar-startup detection, SWOT, expanded feasibility, multi-dimensional scores computed in Python, radar chart)
4. **`project_memory` wired end-to-end** — prove cross-phase reuse works
5. **Risk prediction** + **KPI dashboard**
6. **Patent & Research crew**: free APIs (arXiv/Semantic Scholar/OpenAlex/Crossref/PatentsView) + Zyte scraping for global patent offices + user-upload validator
7. **Business Planning crew** (Lean Canvas/BMC) + document export
8. **Legal checklist + AI-draft legal documents** (with disclaimers)
9. **Centralized AI chat** (intent router across crews, shared memory, one voice)
10. **Community forum** (posts/comments/votes)
11. **Collaboration roles** (founder/co-founder/mentor/advisor/investor/admin)
12. **Personalized ecosystem recommendations** by user role
13. v2+: **Investor recommendation database**, Product/Marketing/Sales/Funding crews

---

## 11. Cost Awareness (updated)

With Supabase/Upstash/Brave/Zyte/self-hosted embeddings all free or already paid for, your marginal cost per validation run is almost entirely Claude API tokens: roughly 6–10 Sonnet calls (idea analysis, market research, competitor/similarity, SWOT + expanded feasibility, score-input generation, risk assessment) plus a handful of free Brave Search calls. Cache market/competitor research per category for a few days so repeat categories don't re-trigger identical searches, and keep every structural/reformatting step on Haiku.
