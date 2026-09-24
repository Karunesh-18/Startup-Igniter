# ADR 0002: Removing CrewAI

**Status:** Implemented · **Date:** 2026-09-24

## Context

`crewai` was imported, conditionally, in 22 files across `ai/agents/`,
`ai/crews/`, and `ai/shared/llm_provider.py`, following this pattern:

```python
try:
    from crewai import Agent as CrewAIAgent
    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False
    CrewAIAgent = None
```

`crewai` was never declared in `backend/pyproject.toml` and never installed
in the venv. `HAS_CREWAI` was therefore `False` in every environment this
code has ever run in, and every `if HAS_CREWAI and ...:` branch — the "real"
CrewAI orchestration path — was unreachable dead code. What actually ran was
always the `else` branch: a plain dict, or in `ai/shared/llm_provider.py`'s
case, a hand-rolled sequential `httpx` orchestrator making the 20 live LLM
calls that constitute the actual pipeline.

Two consequences of this followed the same pattern:
- `ai/crews/idea_validation/tasks.py` and `ai/crews/market_research/tasks.py`
  defined `output_pydantic`-configured `CrewAITask` factories that the
  corresponding `crew.py` files imported and never called.
- `LLMFactory.get_llm()` demanded `GROQ_API_KEY` even when the actual call
  would go to OpenRouter, and 7 call sites passed `get_llm(tier=...)` — a
  parameter name that doesn't exist on the real signature
  (`model_tier=...`) — a `TypeError` that was never triggered only because
  those callers use `run_*_agent()`, which never calls `get_*_agent()`.

## Decision

Remove CrewAI entirely rather than either (a) actually installing and wiring
it, or (b) leaving the dead branches in place.

**Why not install it for real?** The custom sequential orchestrator already
does exactly what this pipeline needs — sequential agent calls with context
propagation and schema validation — and is what's actually been running and
tested this whole time. Adopting CrewAI now would mean redesigning around
its `Crew`/`Task`/`Process` abstractions for a benefit (multi-agent
delegation, parallel task graphs) this pipeline doesn't currently use: every
crew's task DAG is linear, not a graph CrewAI's `Process.hierarchical` would
add value to.

**Why not just leave the dead code?** It actively misleads: docstrings claim
"Production CrewAI Tasks", `if HAS_CREWAI and ... : return CrewAIAgent(...)`
reads as live code to anyone who hasn't verified the import actually
succeeds, and the dead `tasks.py` modules duplicate (inconsistently) prompt
logic that also lives inline in each `crew.py`'s `run()` method.

## Consequences

- 20 agent factory files: removed the `HAS_CREWAI` try/except block, the
  `LLMFactory.get_llm(...)` call, the `if HAS_CREWAI...: return CrewAIAgent(...)`
  branch, and the `"llm": llm` dict key. Each now returns a plain
  configuration dict directly — the only code path that ever ran.
- 2 crew-level files (`idea_validation/crew.py`, `market_research/crew.py`):
  removed the equivalent `Crew`/`Process` dead import.
- Deleted `ai/crews/idea_validation/tasks.py` and
  `ai/crews/market_research/tasks.py` outright (46 KB of dead code) and the
  one test (`test_idea_validation_crew.py::test_task_creation_functions`)
  that exercised them for their own sake.
- Deleted `LLMFactory` from `ai/shared/llm_provider.py` — see
  [ADR 0001](0001-llm-gateway.md) for what replaced it.
- The 7 `get_llm(tier=...)` `TypeError`s are gone by construction: there's no
  `LLMFactory.get_llm` left to call incorrectly.

## What this does NOT mean

This is not a statement that CrewAI is a bad framework, or that the training
pipeline (see [ADR 0003](0003-qwen3-base-models.md)) can't use crew-like
abstractions later. It's specifically that *this codebase's* orchestration
need is linear sequencing with schema validation, which the existing custom
code already does, tested and working — reintroducing CrewAI would be
solving a problem this pipeline doesn't have.
