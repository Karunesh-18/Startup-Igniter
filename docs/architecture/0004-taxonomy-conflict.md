# ADR 0004: Five phase/agent taxonomies, one declared canonical

**Status:** Documented, partially reconciled · **Date:** 2026-09-24

## Context

This repository accumulated five different, mutually inconsistent
descriptions of "what the phases/agents are" across its history:

| Source | Shape |
|---|---|
| `frontend/src/data/crews.ts` | **12 crews, 66 agents** (newest; the one users actually see in the UI) |
| `FRONTEND_SPECIFICATION.md` | 3 crews, 20 agents ("View 2 Live Agent Execution Stepper") |
| `ai/shared/constants.py::StartupPhase` | 13 phase values (`idea`, `market_validation`, `patent_research`, ... `revenue_model`) |
| `backend/db` `project_phase` Postgres enum + `backend/workflow/engine.py::ALL_PHASES` | 6 phases (`idea`, `validation`, `patent`, `business`, `legal`, `export`) — a real, DB-backed, tested workflow gate |
| `ai/hooks/useAnalysis.ts` (frontend, now deleted) | 20 agents, with names that didn't even match `crews.ts`'s 20 lowest-numbered agents (`"Problem Statement Decoder"` vs `"Problem Statement Analyzer"`) |

Additionally, the actual Python backend implements **7** agents for crew 3
(Research & Patent) where the frontend lists 6 — `existing_solution_analyzer_agent.py`
has no frontend counterpart (see
[docs/agents/67-existing-solution-analyzer.md](../agents/67-existing-solution-analyzer.md)).

## Decision

**`frontend/src/data/crews.ts`'s 12-crew/66-agent structure is canonical**
for documentation and for describing the AI reasoning pipeline. It's the
newest, it's what the shipped UI actually shows users, and every generated
doc under `docs/agents/` and `docs/phases/` is keyed to it
(`docs/generate_docs.py` transcribes it as the one source of truth for
agent docs and schema files).

**The DB-backed 6-phase `WorkflowEngine` is a genuinely separate system, not
a naming variant of the same thing**, and this ADR does not attempt to
collapse them:

- The 12-crew taxonomy describes the **AI reasoning pipeline** —
  what `POST /api/v1/analysis/run` executes (currently crews 1–3 only; see
  [Phase 01](../phases/01-idea-validation.md) through
  [Phase 03](../phases/03-research-and-patent.md)). This endpoint is
  explicitly "no database or auth required for this MVP endpoint" — it
  doesn't touch the DB workflow engine at all.
- The 6-phase `WorkflowEngine` describes **project milestone gating** — the
  `POST /api/v1/phases/{project_id}/idea` family of endpoints, backed by
  real Postgres tables (`idea_analysis`, `validation_reports`,
  `patent_research_reports`, `business_plans`, `legal_checklists`,
  `documents`) and a tested phase-completion/advancement state machine.

**These two systems are not currently connected to each other.** A run
through `/analysis/run` does not advance a project's `WorkflowEngine` phase,
and the `WorkflowEngine`'s per-phase worker tasks
(`backend/workers/tasks.py::_execute_idea_analysis_crew` etc.) call the same
underlying services but through a separate code path with its own
`mock_mode` handling bugs (`workers/tasks.py:594,630` don't forward
`mock_mode` to `validate_idea`, so that path is always live).

## Why not migrate the DB schema to 12 phases now

Expanding `project_phase` from 6 to 12 values, adding output tables for the
9 additional milestones, and updating every consumer
(`backend/api/routers/phases.py`, `backend/workers/tasks.py`,
`backend/db/seeds/categories.py`) would build DB-backed gating for phases
that have no real agents behind them yet — 9 of the 12 crews are
[SPECIFIED, not built](../README.md#implementation-status). That's schema
work in service of features that don't exist, which is worse than no schema
work: it creates tables that look load-bearing but hold nothing but
placeholder rows, and a migration that would need to be revisited anyway
once the real per-agent design for crews 4–12 is settled (see each
[SPECIFIED phase doc](../README.md#phases) for the open design questions —
several stub schemas don't even have a 1:1 field for every listed agent yet,
e.g. [Phase 10](../phases/10-growth-and-scaling.md)).

## What IS reconciled

- `ai/shared/constants.py::StartupPhase`'s 13-value enum and its
  `DEFAULT_CATEGORY_WORKFLOWS` are left as-is: they describe **category-specific
  phase sequences** (a HealthTech startup's workflow differs from a
  Marketplace's), which is a real, distinct concept from both the 12-crew
  taxonomy and the DB's 6-phase gate. Renaming this to avoid superficial
  vocabulary overlap with the other two systems was considered and rejected —
  it would touch `DEFAULT_CATEGORY_WORKFLOWS` consumers for no behavioral
  change, trading one naming collision for a bigger diff.
- `docs/generate_docs.py` is the one script that regenerates agent/schema
  docs from `crews.ts` — there is now exactly one place a human re-verifies
  the canonical taxonomy matches its source when `crews.ts` changes, instead
  of five independently-drifting copies.

## Follow-up (not done in this change)

If/when crews 4–12 get real agents, revisit whether the `WorkflowEngine`'s
6 phases should grow to cover them, or whether `/analysis/run`'s crews stay
deliberately decoupled from DB-backed milestone gating (arguably correct:
gating implies a founder must complete phase N before N+1, which may not fit
a reasoning pipeline that runs many crews in one request).
