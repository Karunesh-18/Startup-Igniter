# Startup OS — Backend (`feat/backend-core`)

FastAPI backend for the AI Startup Navigator / Startup OS platform.

> **Branch:** `feat/backend-core` · **Owner:** Person B
>
> See [implementation_plan.md](../implementation_plan.md) for the full team plan and milestone breakdown.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Quick Start (Local Dev)](#quick-start-local-dev)
4. [Environment Variables](#environment-variables)
5. [API Reference](#api-reference)
6. [Database & Migrations](#database--migrations)
7. [Workflow Engine](#workflow-engine)
8. [Scoring System](#scoring-system)
9. [Background Workers (arq)](#background-workers-arq)
10. [Integration Points for Person C](#integration-points-for-person-c)
11. [Tests](#tests)
12. [Deployment](#deployment)
13. [Guardrails](#guardrails)

---

## Architecture Overview

```
                    ┌─────────────────────────────────────────────┐
                    │           Next.js Frontend (Person A)        │
                    └──────────────────┬──────────────────────────┘
                                       │ HTTPS + JWT
                    ┌──────────────────▼──────────────────────────┐
                    │         FastAPI   /api/v1/*                  │
                    │  ┌───────┐ ┌──────────┐ ┌───────┐ ┌──────┐ │
                    │  │ auth  │ │ projects │ │phases │ │forum │ │
                    │  └───────┘ └──────────┘ └───┬───┘ └──────┘ │
                    │                             │               │
                    │              ┌──────────────▼──────┐        │
                    │              │   Workflow Engine    │        │
                    │              │   (workflow/engine)  │        │
                    │              └──────────────┬──────┘        │
                    │                             │               │
                    │              ┌──────────────▼──────┐        │
                    │              │   arq Task Queue     │        │
                    │              │  (workers/tasks.py)  │        │
                    └──────────────┴──────────────┬──────┘        │
                                                  │
                    ┌─────────────────────────────▼───────────────┐
                    │         AI Crews (Person C — agents/)        │
                    │  idea_crew · validation_crew · business_crew │
                    └──────────────────────────────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────────────┐
                    │          Supabase (PostgreSQL + pgvector)    │
                    │  users · projects · project_memory · ...     │
                    └──────────────────────────────────────────────┘
```

---

## Project Structure

```
backend/
├── api/
│   ├── main.py                  # FastAPI app — entrypoint
│   ├── deps.py                  # FastAPI dependency providers (auth, DB, access)
│   └── routers/
│       ├── auth.py              # POST /auth/register, /auth/login, GET /auth/me
│       ├── projects.py          # CRUD + member management + phase-status
│       ├── phases.py            # Trigger AI jobs, get phase outputs
│       ├── scores.py            # Radar chart data + score history
│       ├── forum.py             # Community discussion posts + voting
│       └── export.py            # PDF/DOCX/PPTX generation
├── core/
│   ├── config.py                # Pydantic Settings — reads from .env
│   ├── security.py              # JWT + bcrypt
│   └── logging.py               # structlog — JSON in prod, pretty in dev
├── db/
│   ├── database.py              # Async engine, session factory, get_db dep
│   ├── models.py                # All ORM models (16 tables)
│   ├── migrations/
│   │   ├── env.py               # Alembic config
│   │   ├── script.py.mako       # Migration template
│   │   └── versions/
│   │       └── 0001_initial_schema.py
│   └── seeds/
│       └── categories.py        # 11 startup categories with workflows + checklists
├── workflow/
│   ├── engine.py                # Phase gating — the core orchestration logic
│   └── scoring.py               # Deterministic weighted score calculator
├── workers/
│   └── tasks.py                 # arq job functions + WorkerSettings
├── tests/
│   ├── conftest.py              # pytest fixtures, test DB, auth helpers
│   ├── test_auth.py             # Auth endpoint tests
│   ├── test_projects.py         # Project CRUD + phase tests
│   └── test_scoring.py          # Scoring unit tests
├── templates/                   # (Place startup_report.docx here for docxtpl)
├── .env.example                 # Template — copy to .env and fill values
├── alembic.ini                  # Alembic configuration
├── pyproject.toml               # Dependencies + tool config
├── Dockerfile                   # Multi-stage: api + worker targets
├── docker-compose.yml           # Local dev stack (API + Worker + Postgres + Redis)
└── fly.toml                     # Fly.io deployment config
```

---

## Quick Start (Local Dev)

### Option 1 — Docker Compose (recommended)

```bash
# 1. Clone and enter the backend directory
cd backend

# 2. Copy env template
cp .env.example .env
# Fill in GROQ_API_KEY, TAVILY_API_KEY, etc.

# 3. Start the full stack
docker compose up

# 4. Run migrations (first time)
docker compose exec api alembic upgrade head

# 5. Seed categories
docker compose exec api python -m db.seeds.categories
```

API will be live at http://localhost:8000
Interactive docs at http://localhost:8000/docs

---

### Option 2 — Virtual environment (no Docker)

Requirements: Python 3.11+, PostgreSQL 15+ with pgvector, Redis

```bash
cd backend

# 1. Create and activate venv
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Copy and fill .env
cp .env.example .env

# 4. Run DB migrations
alembic upgrade head

# 5. Seed categories
python -m db.seeds.categories

# 6. Start the API server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 7. In a separate terminal — start the worker
arq workers.tasks.WorkerSettings
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | asyncpg DSN (e.g. `postgresql+asyncpg://user:pass@host/db`) |
| `DATABASE_URL_SYNC` | ✅ | psycopg2 DSN for Alembic migrations |
| `SUPABASE_URL` | ✅ | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | ✅ | Supabase service role key (never expose to frontend) |
| `UPSTASH_REDIS_REST_URL` | ✅ | Upstash Redis REST URL |
| `UPSTASH_REDIS_REST_TOKEN` | ✅ | Upstash Redis auth token |
| `SECRET_KEY` | ✅ | JWT signing key — min 32 chars — use `openssl rand -hex 32` |
| `GROQ_API_KEY` | ✅ | Groq API key (for AI crews — Person C uses this) |
| `TAVILY_API_KEY` | ✅ | Tavily search API (primary web grounding) |
| `EXA_API_KEY` | Optional | Exa.ai semantic search (research/patent phases) |
| `ZYTE_API_KEY` | Optional | Zyte scraper |
| `SEMANTIC_SCHOLAR_API_KEY` | Optional | Higher rate limits |
| `OPENALEX_EMAIL` | Optional | Better rate limits on OpenAlex |
| `ENVIRONMENT` | Optional | `development` \| `staging` \| `production` |

Copy `.env.example` to `.env` and fill in your values. **Never commit `.env`.**

---

## API Reference

Full interactive documentation: `http://localhost:8000/docs`

### Base URL
```
/api/v1
```

### Authentication
All endpoints (except `/health`) require:
```
Authorization: Bearer <JWT>
```

Obtain a token via `POST /api/v1/auth/register` or `POST /api/v1/auth/login`.

### Key Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/register` | Register + receive JWT |
| `POST` | `/auth/login` | Login + receive JWT |
| `GET` | `/auth/me` | Current user profile |
| `POST` | `/projects` | Create startup project |
| `GET` | `/projects` | List user's projects |
| `GET` | `/projects/{id}` | Project details |
| `PATCH` | `/projects/{id}` | Update project |
| `DELETE` | `/projects/{id}` | Delete project |
| `GET` | `/projects/{id}/phase-status` | Full workflow phase map |
| `POST` | `/projects/{id}/advance-phase` | Advance to next phase |
| `POST` | `/projects/{id}/members` | Invite collaborator |
| `POST` | `/phases/{id}/idea` | **Trigger** idea analysis (async) |
| `GET` | `/phases/{id}/idea` | Get idea analysis result |
| `PATCH` | `/phases/{id}/idea` | User-edit idea analysis |
| `POST` | `/phases/{id}/validation` | **Trigger** validation + scoring |
| `GET` | `/phases/{id}/validation` | Get validation report |
| `GET` | `/phases/{id}/risks` | Get risk items |
| `POST` | `/phases/{id}/business` | **Trigger** Lean Canvas generation |
| `GET` | `/phases/{id}/business` | Get business plan |
| `GET` | `/phases/{id}/job/{job_id}` | Poll async job status |
| `GET` | `/scores/{id}` | Radar chart data |
| `GET` | `/scores/{id}/history` | Score history |
| `POST` | `/export/{id}/pdf` | Generate PDF |
| `POST` | `/export/{id}/docx` | Generate DOCX |
| `POST` | `/export/{id}/pptx` | Generate PPTX |
| `GET` | `/export/{id}` | List all documents |
| `GET` | `/forum/posts` | List forum posts |
| `POST` | `/forum/posts` | Create post |
| `GET` | `/forum/posts/{id}` | Post detail + comments |
| `POST` | `/forum/posts/{id}/vote` | Vote (toggle) |
| `POST` | `/forum/posts/{id}/comments` | Add comment |

---

## Database & Migrations

### Running Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration after changing models.py
alembic revision --autogenerate -m "describe_your_change"

# Rollback one migration
alembic downgrade -1

# See current migration state
alembic current
```

### Tables

| Table | Purpose |
|---|---|
| `users` | Shadow records mirroring Supabase Auth |
| `startup_categories` | System categories with workflow JSON |
| `projects` | Core entity — one per startup idea |
| `project_members` | Collaboration roles (owner/editor/viewer) |
| `project_memory` | **Cross-phase AI memory** (pgvector embeddings) |
| `idea_analysis` | Idea phase output |
| `validation_reports` | Market research + SWOT |
| `scores` | Per-dimension readiness scores |
| `risk_assessments` | Risk items from validation crew |
| `business_plans` | Lean Canvas JSON |
| `legal_checklists` | Static compliance checklist per project |
| `legal_documents` | AI-drafted legal documents |
| `patent_research_reports` | Patent/prior-art search results |
| `documents` | Generated PDF/DOCX/PPTX exports |
| `phase_log` | Audit log of all phase transitions |
| `forum_posts` | Community discussion posts |
| `forum_comments` | Threaded replies |
| `forum_votes` | One vote per user per post |

### Seeding Categories

```bash
python -m db.seeds.categories
```

Seeds 11 categories: SaaS, HealthTech, FinTech, AI/ML, D2C, DeepTech, EdTech, CleanTech, AgriTech, Social Impact, Other.

---

## Workflow Engine

The `WorkflowEngine` (`workflow/engine.py`) manages phase progression:

```python
engine = WorkflowEngine(db)

# Check what phase a project is in and what's unlocked
status = await engine.get_phase_status(project)
# → {"current_phase": "idea", "workflow": [...], "phases": {...}}

# Check if a specific phase is done (DB-row-based, not client state)
done = await engine.is_phase_complete(project, "idea")

# Advance to the next phase (validates completion first)
next_phase = await engine.advance_phase(project)

# Gate check (raises PhaseNotUnlockedError if not yet reachable)
await engine.assert_phase_unlocked(project, "validation")
```

**Phase completion criteria** (deterministic, DB-row-based):

| Phase | Complete when... |
|---|---|
| `idea` | `idea_analysis` row exists with non-null `problem_statement` |
| `validation` | `validation_reports` row exists with non-null `total_score` |
| `patent` | `patent_research_reports` row exists |
| `business` | `business_plans` row exists with non-null `lean_canvas` |
| `legal` | `legal_checklists` row exists |
| `export` | `documents` row exists |

---

## Scoring System

**Spec requirement:** *"Never let the LLM compute the score."*

The LLM (in Person C's agents) produces sub-ratings (0-100) per dimension. The weighted sum is always computed in Python:

```python
from workflow.scoring import compute_weighted_score, score_label

raw_scores = {
    "validation": 75, "market": 60, "technology": 80,
    "business": 65, "financial": 55, "patent": 50,
    "legal": 70, "overall": 68
}

result = compute_weighted_score(raw_scores)
print(result.total)         # 67.65
print(score_label(67.65))   # "Promising"
```

**Weights** (sum to 1.0):

| Dimension | Weight |
|---|---|
| validation | 20% |
| market | 20% |
| technology | 15% |
| business | 15% |
| financial | 10% |
| patent | 10% |
| legal | 5% |
| overall | 5% |

---

## Background Workers (arq)

Long-running AI jobs run in the background via arq (async Redis queue):

```bash
# Start the worker
arq workers.tasks.WorkerSettings
```

**Job functions:**

| Function | Trigger |
|---|---|
| `run_idea_phase` | `POST /phases/{id}/idea` |
| `run_validation_phase` | `POST /phases/{id}/validation` |
| `run_business_phase` | `POST /phases/{id}/business` |
| `generate_export_documents` | `POST /export/{id}/*` |

**Polling pattern** (frontend):
1. Call `POST /phases/{id}/idea` → get `job_id`
2. Poll `GET /phases/{id}/job/{job_id}` every 3-5 seconds
3. When status = `complete`, call `GET /phases/{id}/idea` for the result

---

## Integration Points for Person C

Person C's AI crews (`agents/`) integrate with the backend at clearly marked stubs in `workers/tasks.py`:

```python
# In workers/tasks.py → run_idea_phase():
# REPLACE this placeholder:
analysis_output = await _placeholder_idea_analysis(project)

# WITH:
from agents.crews.idea_crew import IdeaCrew
analysis_output = await IdeaCrew(project, db).run()
```

Similarly for `run_validation_phase` and `run_business_phase`.

**Memory interface** — Person C's agents read/write `project_memory` via:
```python
from workers.tasks import _upsert_memory
await _upsert_memory(db, project_id, key, value_dict, source_phase)
```

The `value_dict` is stored as JSONB. Embeddings (vector(384)) are set by Person C using sentence-transformers.

---

## Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_scoring.py -v
```

Tests use SQLite in-memory — no Postgres needed for the test suite.

---

## Deployment

### Fly.io (recommended for India/Asia)

```bash
cd backend

# Install Fly CLI
# https://fly.io/docs/hands-on/install-flyctl/

# Deploy
fly launch --config fly.toml

# Set secrets (one-time)
fly secrets set \
  DATABASE_URL="postgresql+asyncpg://..." \
  SECRET_KEY="$(openssl rand -hex 32)" \
  GROQ_API_KEY="gsk_..." \
  TAVILY_API_KEY="tvly-..." \
  SUPABASE_URL="https://..." \
  SUPABASE_SERVICE_ROLE_KEY="..." \
  UPSTASH_REDIS_REST_URL="https://..." \
  UPSTASH_REDIS_REST_TOKEN="..."

# Run migrations on deployed instance
fly ssh console -C "alembic upgrade head"
fly ssh console -C "python -m db.seeds.categories"
```

### Render

```yaml
# render.yaml
services:
  - type: web
    name: startup-os-api
    env: docker
    dockerfilePath: ./backend/Dockerfile
    dockerTarget: app
    envVars:
      - key: DATABASE_URL
        sync: false  # set in Render dashboard
```

---

## Guardrails

These are non-negotiable requirements from the spec:

| Guardrail | Where enforced |
|---|---|
| `ai_generated: true` in every phase response | `api/routers/phases.py`, `api/routers/scores.py` |
| AI call budget checked before every AI trigger | `_check_and_increment_budget()` in phases.py |
| Legal documents always tagged with disclaimer text | DB column + export templates |
| User can edit AI output before saving to memory | `PATCH /phases/{id}/idea`, `PATCH /phases/{id}/business` |
| Phase advancement blocked until completion | `WorkflowEngine.advance_phase()` checks DB rows |
| Scores computed in Python, not by LLM | `workflow/scoring.py` |

---

## Contributing

1. Create your branch from `main` (or merge to `dev` via PR).
2. Run `ruff format .` and `ruff check .` before pushing.
3. All PRs must pass `pytest` (CI check).
4. Never commit `.env` files or API keys.
