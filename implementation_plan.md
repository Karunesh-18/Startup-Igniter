# AI Startup Navigator / Startup OS — Implementation Plan

## Overview

**Startup OS** is a full-stack, AI-powered startup operating system built for students, researchers, and professionals. It guides a founder from raw idea → validated startup plan → legal + business documents, using a dynamic phase workflow, CrewAI-powered agents, and a shared project memory. The product runs primarily on free-tier services with **Groq API** as the primary LLM provider — chosen for its extremely fast inference speeds and very competitive pricing.

This plan covers the complete build across **3 contributors**, with clear branch ownership, API key responsibilities, and a milestone-based execution order.

---

## Team Structure & Branch Ownership

> [!IMPORTANT]
> All branches should be created from `main`. Use Pull Requests to merge. Never commit secrets or API keys. Use `.env.local` for Next.js and `.env` for FastAPI — both are `.gitignore`d.

### Branch Strategy

```
main (protected — only merge via PR)
├── dev (integration branch — all teammates merge here first)
│   ├── feat/frontend        → Person A (Frontend)
│   ├── feat/backend-core    → Person B (Backend Core + Workflow Engine)
│   └── feat/ai-agents       → Person C (AI Crews + Integrations)
```

| Branch | Owner | Responsibility |
|---|---|---|
| `feat/frontend` | **Person A** | Next.js app, all UI pages, Supabase Auth client, Tailwind/shadcn design system, radar chart, document export UI |
| `feat/backend-core` | **Person B** | FastAPI app, Supabase DB setup & migrations, Workflow Engine, Celery/arq workers, Upstash Redis, REST API endpoints |
| `feat/ai-agents` | **Person C** | CrewAI crews & agents, Brave Search tool, Zyte scraper integration, patent/research APIs, project_memory R/W, legal document templates, AI chat intent router |

---

## What YOU (the project owner) Must Do First

> [!CAUTION]
> These are blocking tasks — the team cannot start without them. Complete all of these before day 1 of coding.

### 🔑 API Keys & Accounts to Set Up

| Service | Action | Link | Notes |
|---|---|---|---|
| **Supabase** | Create a free project | https://supabase.com | Get `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`. Enable pgvector extension in SQL editor: `CREATE EXTENSION IF NOT EXISTS vector;` |
| **Groq** | Create account + generate API key | https://console.groq.com | Get `GROQ_API_KEY`. Set up billing. **Heavy reasoning tasks** use `llama-3.3-70b-versatile` (or `deepseek-r1-distill-llama-70b`); **fast/cheap tasks** use `llama-3.1-8b-instant`. Budget ~$5–15/month for dev — Groq is cheaper per token than Anthropic and significantly faster |
| **Upstash Redis** | Create free Redis database | https://console.upstash.com | Get `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN` |
| **Tavily Search API** | Sign up for free tier | https://tavily.com | Get `TAVILY_API_KEY`. **Primary web search grounding** — AI-native, returns clean Markdown/text directly to the LLM (no HTML parsing needed). Free tier = **1,000 credits/month**. Has a native CrewAI tool integration (`TavilySearchResults`). |
| **Exa** | Sign up for free tier *(secondary/optional)* | https://exa.ai | Get `EXA_API_KEY`. Semantic/neural search — great for research paper discovery and startup similarity search. Free tier = **1,000 credits/month**. Use alongside Tavily for deeper research phases. |
| **Vercel** | Connect GitHub repo | https://vercel.com | Free hobby tier. Connects to your GitHub for auto-deploy |
| **Fly.io or Render** | Create account | https://fly.io or https://render.com | For FastAPI backend. Free tier has cold starts — acceptable for now |
| **Zyte** | You already have this | — | Get `ZYTE_API_KEY` from your existing account |
| **PatentsView** | No key needed | https://patentsview.org/apis/api-endpoints | Free, public USPTO API |
| **arXiv** | No key needed | https://arxiv.org/help/api | Free public API |
| **Semantic Scholar** | Optional free key | https://www.semanticscholar.org/product/api | Free, higher rate limits with key. Get `SEMANTIC_SCHOLAR_API_KEY` |
| **OpenAlex** | No key needed, but polite_email helps | https://openalex.org | Set `OPENALEX_EMAIL=your@email.com` in env for better rate limits |
| **GitHub** | Create repo + set branch protection on `main` | — | Invite teammates as collaborators |
| **Resend** (optional) | Sign up for email service | https://resend.com | Free tier for transactional emails later |

### 📁 Repo & Env Setup Checklist

- [ ] Create GitHub repo: `Startup-Igniter` (already exists with `.git`)
- [ ] Set `main` as protected branch (require PR + 1 review)
- [ ] Create `dev` integration branch
- [ ] Create the three feature branches: `feat/frontend`, `feat/backend-core`, `feat/ai-agents`
- [ ] Create `.env.example` files (template with all keys, no values) — commit this
- [ ] Add `.env`, `.env.local` to `.gitignore`
- [ ] Share actual env values with teammates via a **password manager** (Bitwarden) or **1Password Teams** — never via Slack/WhatsApp/email

---

## Project Structure

```
Startup-Igniter/
├── frontend/                     # Person A — Next.js 14 + TypeScript
│   ├── app/                      # App Router pages
│   ├── components/               # shadcn/ui + custom components
│   ├── lib/                      # Supabase client, API helpers
│   ├── public/
│   ├── .env.local                # (gitignored)
│   └── .env.local.example        # (committed — template only)
│
├── backend/                      # Person B — FastAPI
│   ├── api/
│   │   ├── routers/              # projects, phases, scores, forum, auth
│   │   └── main.py
│   ├── db/
│   │   ├── models.py             # SQLAlchemy models
│   │   └── migrations/           # Alembic migrations
│   ├── workflow/
│   │   └── engine.py             # Workflow Engine (phase gating logic)
│   ├── workers/
│   │   └── tasks.py              # Celery/arq tasks
│   ├── .env                      # (gitignored)
│   └── .env.example
│
├── agents/                       # Person C — CrewAI
│   ├── crews/
│   │   ├── idea_crew.py
│   │   ├── validation_crew.py
│   │   ├── patent_crew.py
│   │   ├── business_crew.py
│   │   ├── legal_crew.py
│   │   └── chat_router.py
│   ├── tools/
│   │   ├── brave_search.py
│   │   ├── zyte_scraper.py
│   │   ├── research_apis.py      # arXiv, Semantic Scholar, OpenAlex, Crossref
│   │   ├── patents_view.py
│   │   └── embeddings.py         # self-hosted sentence-transformers
│   ├── memory/
│   │   └── project_memory.py     # R/W to project_memory table
│   └── templates/
│       └── legal/                # NDA, founder agreement, etc. base templates
│
├── ai-startup-navigator-spec-v2.md
└── README.md
```

---

## Data Model — Supabase SQL (Person B owns this)

Run these in the Supabase SQL editor (or via Alembic migrations):

```sql
-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Core tables (abbreviated — see spec §3 for full column list)
CREATE TABLE users (...);
CREATE TABLE startup_categories (...);
CREATE TABLE projects (...);
CREATE TABLE project_members (...);
CREATE TABLE project_memory (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id),
  key TEXT,
  value JSONB,
  embedding vector(384),   -- all-MiniLM-L6-v2 output dimension
  source_phase TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE idea_analysis (...);
CREATE TABLE validation_reports (...);
CREATE TABLE scores (...);
CREATE TABLE risk_assessments (...);
CREATE TABLE business_plans (...);
CREATE TABLE legal_checklists (...);
CREATE TABLE legal_documents (...);
CREATE TABLE patent_research_reports (...);
CREATE TABLE documents (...);
CREATE TABLE phase_log (...);
CREATE TABLE forum_posts (...);
CREATE TABLE forum_comments (...);
CREATE TABLE forum_votes (...);
```

---

## Milestone Build Order

> Follows spec §10 exactly. Each milestone maps to a team deliverable.

### M1 — Foundation *(All three, ~Week 1)*
| Who | Task |
|---|---|
| **Owner (you)** | Supabase project live, pgvector enabled, all API keys distributed to team |
| **Person B** | FastAPI skeleton, Alembic DB migrations, all tables created in Supabase |
| **Person A** | Next.js app bootstrapped (`create-next-app`), Supabase Auth client wired, landing page + login |
| **Person C** | `agents/` folder scaffolded, sentence-transformers model tested locally, `project_memory.py` CRUD working |

### M2 — Workflow Engine *(Person B)*
- `workflow/engine.py` reads `startup_categories.workflow` JSON array
- Phase gating logic: checks `phase_log` to determine what's unlocked
- API endpoints: `GET /projects/{id}/current-phase`, `POST /projects/{id}/advance-phase`
- Seed `startup_categories` table with all system categories from spec

### M3 — Idea Analysis + Validation Crew *(Person C + B + A)*
| Who | Task |
|---|---|
| **Person C** | `idea_crew.py` (categorization → `llama-3.1-8b-instant`), `validation_crew.py` (Brave Search market research, competitor detection, SWOT, expanded feasibility → `llama-3.3-70b-versatile`) |
| **Person B** | `/api/phases/idea` and `/api/phases/validation` endpoints that enqueue Celery tasks |
| **Person A** | Idea submission form, category picker/override UI, SWOT display, radar chart (recharts or chart.js) |

### M4 — `project_memory` End-to-End *(Person C + B)*
- Every CrewAI agent reads relevant memory rows before calling the Groq LLM
- Every agent writes structured JSON + embeddings back after completing
- Prove cross-phase reuse: validation crew reads idea_crew output from memory

### M5 — Risk Prediction + KPI Dashboard *(Person C + A)*
| Who | Task |
|---|---|
| **Person C** | Add risk prediction to validation crew: structured output (type, severity, mitigation) |
| **Person A** | KPI dashboard page — multi-dimensional score radar chart + risk table |

### M6 — Patent & Research Crew *(Person C)*
- Free APIs: arXiv, Semantic Scholar, OpenAlex, Crossref, PatentsView
- Zyte: scrapes Google Patents, Espacenet, WIPO, India IP for global patent search
- User PDF upload → stored in Supabase Storage → Groq (`llama-3.3-70b-versatile`) compares against search results
- Output: `patent_research_reports` rows + similarity scores

### M7 — Business Planning + Document Export *(Person C + A + B)*
| Who | Task |
|---|---|
| **Person C** | `business_crew.py`: Lean Canvas / BMC generation from `project_memory` |
| **Person B** | `/api/export` endpoints: trigger docxtpl/python-pptx/weasyprint generation, store in Supabase Storage |
| **Person A** | Lean Canvas editor UI, "Export as DOCX/PPTX/PDF" buttons |

### M8 — Legal Checklist + AI Draft Documents *(Person C + A)*
- Static legal checklists per category (hand-maintained JSON, Person C)
- AI draft generation from permissively-licensed templates (Person C)
- Person A: renders checklist UI + document viewer with persistent disclaimer banner

### M9 — Centralized AI Chat *(Person C + A)*
- `chat_router.py`: `llama-3.1-8b-instant` classifies intent → routes to correct crew's context + memory
- Single consistent response voice regardless of domain
- Person A: floating chat widget, present across all project pages

### M10 — Community Forum *(Person A + B)*
- Person B: `/api/forum` CRUD (posts, comments, upvotes)
- Person A: forum UI (Reddit-style thread view, voting, markdown support)

### M11 — Collaboration Roles *(Person B + A)*
- Person B: `project_members` table logic, role-based access middleware
- Person A: invite teammate UI, role badges, permission-aware components

### M12 — Ecosystem Recommendations *(Person C)*
- Personalized incubator/grant/E-Cell suggestions using `users.role` + `projects.category`
- Grounded with Brave Search for current programs
- `llama-3.1-8b-instant` generates structured recommendation list

### M13 — v2+ (Future) *(Post-launch)*
- Investor recommendation database (Zyte-populated `investors` table)
- Product/Marketing/Sales/Funding crews

---

## Environment Variables Reference

### `frontend/.env.local.example`
```env
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### `backend/.env.example`
```env
# Supabase
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
DATABASE_URL=postgresql://...   # from Supabase project settings

# Redis
UPSTASH_REDIS_REST_URL=
UPSTASH_REDIS_REST_TOKEN=

# Groq
GROQ_API_KEY=
GROQ_MODEL_HEAVY=llama-3.3-70b-versatile    # idea analysis, SWOT, risk, legal drafts
GROQ_MODEL_FAST=llama-3.1-8b-instant        # routing, classification, summarization

# Search & Scraping
TAVILY_API_KEY=           # primary web search (market research, competitor detection)
EXA_API_KEY=              # secondary semantic search (startup similarity, research grounding)
ZYTE_API_KEY=

# Research APIs (no key needed for most, but good to document)
SEMANTIC_SCHOLAR_API_KEY=
OPENALEX_EMAIL=

# App
SECRET_KEY=your-jwt-secret-here
ENVIRONMENT=development
```

---

## Guardrails (Non-Negotiable — Person A enforces in UI)

| Guardrail | Where Enforced |
|---|---|
| "AI-generated, verify independently" label on legal, patent, market-size content | Component-level disclaimer banner in UI |
| Legal documents always show "AI-generated draft — have a lawyer review" directly on document (not in ToS) | PDF/DOCX header + UI persistent notice |
| Legal checklist shows "last verified: [date]" | Static JSON includes date field |
| Per-project AI call budget with visible progress indicator (not silent spinner) | Frontend progress bar + backend token counter |
| User can edit any AI output before it's written to `project_memory` | Inline edit UI before confirm → saves to DB |

---

## Multi-Dimensional Scoring (Important Implementation Note)

> [!IMPORTANT]
> The LLM (`llama-3.3-70b-versatile` via Groq) provides **sub-ratings + rationale text per dimension** as structured JSON output.
> The **weighted sum is always computed in Python** — never by the LLM.
> This is deterministic, auditable, and prevents score hallucination.

Dimensions: `validation`, `business`, `market`, `technology`, `patent`, `financial`, `legal`, `overall`

Stored in `scores` table: one row per dimension per run → feeds radar chart.

---

## Cost Discipline

| Strategy | Implementation |
|---|---|
| Cache market/competitor research per category | Redis key: `cache:market:{category_id}`, TTL = 3 days |
| Tavily as primary search grounding | AI-native API — returns LLM-ready text, no HTML parsing overhead; native CrewAI `TavilySearchResults` tool |
| Exa for semantic similarity | Use only in patent + research phases where neural search adds value; skip for simple market queries |
| Deep reasoning → `llama-3.3-70b-versatile` | Idea analysis, SWOT, risk assessment, legal draft generation |
| Optional: `deepseek-r1-distill-llama-70b` | For patent similarity reasoning where chain-of-thought depth matters |
| Self-hosted embeddings | `sentence-transformers/all-MiniLM-L6-v2` in worker process — zero per-call cost |
| Token budget visible to user | Show `X/Y calls used this run` in UI |

---

## Open Questions for Team Alignment

> [!NOTE]
> Resolve these before starting M3+ so no rework is needed.

1. **Hosting choice**: Fly.io or Render for FastAPI backend? (affects deployment config)
2. **Worker library**: Celery (with Redis broker) or `arq` (async, simpler)? Celery is more battle-tested; `arq` is lighter.
3. **Legal templates source**: Which public template sources will Person C use? (suggest: NVCA model docs, public NDA templates from law school clinics)
4. **Category seed list**: Finalize the system startup categories to seed (spec mentions ~10, confirm the full list)
5. **User roles at launch**: Launch with `student/working_professional/graduate/researcher/faculty` as spec says, or simplify for v1?

---

## Verification Plan

### Per Milestone
- Each PR must pass a manual smoke test before merging to `dev`
- Backend: run `pytest` on API routes (Person B sets up test suite)
- Frontend: Vercel preview deploy auto-generated per PR

### Integration Test (after M4)
- Create a project, run idea → validation phase, confirm `project_memory` has rows with embeddings, confirm validation crew reads idea crew output

### Pre-launch Checklist
- [ ] All guardrail disclaimers visible in UI
- [ ] `.env` files not in git history (`git log --all -- .env`)
- [ ] Supabase Row Level Security (RLS) enabled on all tables
- [ ] Rate limit middleware on `/api/phases/*` endpoints (prevent abuse)
- [ ] Legal document disclaimer approved (have college legal cell review)