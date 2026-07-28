# AI Startup Navigator — Technical Specification (v1)

Scope note: this spec builds the slimmed v1 we agreed on — Idea Analysis, Validation + Readiness Score, Business Planning, and a Legal/Registration *checklist* (not automated filing) — with an architecture that can later expand into Product, Marketing, Sales, and Funding phases without a rewrite.

---

## 1. Tech Stack

### Frontend
- **Next.js 14 (App Router)** — server components for dashboard/report pages, client components for interactive forms
- **TypeScript** throughout
- **Tailwind CSS** + **shadcn/ui** — fast, consistent component library, easy to theme
- **Zustand** — lightweight client state (current phase, active project)
- **TanStack Query (React Query)** — server-state caching, polling for long-running AI jobs
- **react-hook-form + zod** — form validation matching backend schemas

### Backend
- **FastAPI** (Python) — main API layer
- **PostgreSQL** — primary data store
- **pgvector extension** — semantic memory search lives in the same Postgres instance (avoids a separate vector DB for v1)
- **Redis** — job queue broker + caching (rate-limited external API results)
- **Celery** (or **arq**, simpler async-native alternative) — background workers for long AI jobs so the API never blocks on a multi-step agent run
- **SQLAlchemy + Alembic** — ORM and migrations

### Auth & Infra
- **Clerk** or **Supabase Auth** — don't hand-roll auth
- **Cloudflare R2** (S3-compatible) — generated PDF/DOCX/PPTX storage
- **Vercel** — frontend hosting
- **Railway** or **Fly.io** — backend + worker hosting (both are simple for a student budget vs. raw AWS)

### AI Orchestration
- **Recommendation: drop CrewAI for v1.** Use a single orchestrator service that calls the Claude API directly with tool use and structured outputs. This is cheaper, easier to debug, and enough for the phases in this scope.
- **LangGraph** (optional) — only if you want explicit graph-based control flow across the idea → validation → business steps; otherwise plain Python functions calling the API in sequence are fine and easier to reason about.
- Keep the door open: CrewAI (or LangGraph multi-agent) becomes worth its overhead later, once Product/Marketing/Funding phases genuinely need parallel specialist agents debating/handing off work — not before.

---

## 2. Data Model (Postgres)

```
users
  id, email, name, created_at

projects
  id, user_id, name, category (SaaS/HealthTech/FinTech/D2C/AI/etc), current_phase, created_at

project_memory
  id, project_id, key, value (jsonb), embedding (vector), source_phase, created_at
  -- this table IS the cross-crew memory: every phase writes facts here,
  -- every later phase queries it before generating anything

idea_analysis
  id, project_id, problem_statement, target_audience, value_prop, category_confidence

validation_reports
  id, project_id, market_summary, competitor_summary, swot (jsonb),
  score_breakdown (jsonb), total_score, created_at

business_plans
  id, project_id, lean_canvas (jsonb), revenue_model, pricing_notes

legal_checklists
  id, project_id, category, checklist_items (jsonb), completed_items (jsonb)
  -- static checklist content, not auto-filed

documents
  id, project_id, type (pdf/docx/pptx), phase, storage_url, created_at

phase_log
  id, project_id, phase, status, started_at, completed_at
```

`project_memory` is the single most important table in the system — every AI call should read relevant rows from it before generating output, and write new rows after.

---

## 3. AI Layer — Models and Method per Use Case

General model policy:
- **Claude Sonnet** for anything requiring multi-step reasoning, synthesis across memory, or nuanced judgment (validation, business planning, scoring rationale).
- **Claude Haiku** for cheap, structural tasks (reformatting, extracting fields into JSON, short summarization) — don't pay Sonnet prices for tasks that don't need Sonnet reasoning.
- **An embeddings model** (Voyage AI's voyage-3 or similar) to embed `project_memory` rows for semantic retrieval — needed once a project has more memory than fits in a single prompt.
- All outputs use **structured output via tool-calling / JSON schema**, never free-text parsing — this is what makes the dashboard and later phases able to consume earlier phases' outputs reliably.

| Use Case | Method | Model | Notes |
|---|---|---|---|
| Idea categorization | Single prompt, structured JSON output (category, confidence, reasoning) | Haiku | Cheap, deterministic-ish task |
| Idea analysis (problem/value prop/audience) | Single prompt with structured output, informed by category | Sonnet | Needs real reasoning about problem-market fit |
| Market research | Tool-calling loop: web search tool → synthesis | Sonnet + web search tool | Ground every market claim in a real search result, don't let the model invent TAM numbers |
| Competitor analysis | Web search tool + structured comparison table output | Sonnet + web search tool | Same grounding requirement |
| SWOT / feasibility | Single prompt drawing on `project_memory` (idea + market + competitor rows already stored) | Sonnet | This is where cross-phase memory pays off — no re-asking the user |
| Readiness score | Rule-based weighted formula (your 20/15/15/… breakdown) computed in **Python**, not by the LLM | None (deterministic code) | Critical: don't let an LLM compute the score — have the LLM produce the *inputs* (e.g. a 0–15 market-strength rating with justification) and compute the final weighted sum yourself. This keeps scores reproducible and auditable. |
| Lean Canvas / BMC generation | Template-fill: structured JSON output mapped directly into a canvas template | Sonnet | Reads from `project_memory`, not from asking the user to re-describe the idea |
| Legal/registration checklist | **No LLM** — static, hand-maintained checklist per category (MCA/GST/DPIIT/MSME steps), rendered from a config file you maintain and update manually | None | This is the safest way to touch legal/compliance: accurate, maintainable, no hallucination risk. An LLM chat layer on top can answer *general* questions, clearly labeled "not legal advice" |
| Prior-art / patent assistant | Web search tool (Google/USPTO search) + summarization, framed explicitly as "search assistant," not "verification" | Sonnet + web search tool | See API note below — real patent-search APIs are limited |
| Document export (PDF/DOCX/PPTX) | Templating library fills a pre-built template with structured data already generated above | None (deterministic) | `docxtpl` for Word, `python-pptx` for slides, `reportlab` or `weasyprint` for PDF |

---

## 4. External APIs

| Need | API | Notes |
|---|---|---|
| Web search / grounding | **Tavily** or **Serper.dev** | Purpose-built for LLM agent search grounding; cheaper and cleaner than scraping Google directly |
| Patent data (US) | **PatentsView API** (USPTO, free, official) | Real, usable, free API — use this instead of trying to scrape Google Patents |
| Patent data (global) | No clean free API exists for WIPO/Indian Patent Office | Best v1 approach: web search + link out to official databases, don't claim automated global coverage |
| Startup India / DPIIT / MCA / GST | No public founder-usable filing API | Treat as static reference content you maintain, not an integration |
| Payments (if you monetize later) | **Razorpay** (India-first) or **Stripe** | Only needed once you charge users |
| Email | **Resend** | Simple transactional email API, good Next.js integration |
| PDF/DOCX/PPTX generation | `docxtpl`, `python-pptx`, `weasyprint` (all libraries, not external APIs) | Run inside your FastAPI backend |

---

## 5. Workflow / Phase Engine

Keep this simple for v1 — you don't need a heavyweight state-machine library yet:

- A `current_phase` column on `projects` plus a `phase_log` table is enough to gate progression.
- Phase transition rule: a phase is "complete" when its required output rows exist (e.g. Validation phase complete when `validation_reports.total_score` is set). The frontend reads this to decide what's unlocked.
- If this grows complex later (branching paths, skip conditions), migrate to **XState** on the frontend or a proper state machine table on the backend — not needed at v1 scale.

---

## 6. Guardrails to Build In From Day One

- Every AI-generated section in the UI carries a small "AI-generated, verify independently" label — especially on legal, patent, and market-size content.
- Legal checklist content is static and dated ("last verified: [date]") so users know it isn't live-fetched.
- Cap AI calls per project action (e.g. validation run = max N tool calls) and show a progress indicator, not a silent spinner.
- Let users edit any AI output before it's written into `project_memory` — bad data shouldn't silently propagate into every later phase.

---

## 7. Build Order (Milestones)

1. **Foundation**: auth, project creation, Postgres schema, empty dashboard shell
2. **Idea Analysis + Validation + Readiness Score** (deterministic scoring, Sonnet reasoning, web search grounding)
3. **`project_memory` read/write wired into every phase** — prove the cross-phase memory concept end to end
4. **Business Planning** (Lean Canvas generation from memory)
5. **Document export** (PDF/DOCX of validation report + Lean Canvas)
6. **Legal/Registration checklist** (static content + FAQ assistant)
7. Only after 2–6 are working and used: expand into Product/MVP, Marketing, Sales, Funding phases, and reconsider CrewAI/multi-agent orchestration for those.

---

## 8. Rough Cost Awareness

- Validation run (idea categorization + analysis + market research w/ search + competitor analysis + SWOT + score inputs) ≈ 5–8 Sonnet calls + 2–3 search calls per project run. Budget accordingly per active user, and cache market/competitor search results per idea category for a few days to avoid re-searching identical queries.
- Haiku for all structural/reformatting steps keeps the bulk of "glue" calls cheap.
