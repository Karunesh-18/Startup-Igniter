# ADR 0006: Evidence ledger and skeptic crew

**Status:** Implemented · **Date:** 2026-10-24

## Context

The first pipeline produced confident scores and prose with nothing to check
them against. Crews 4–12 were also still hardcoded literals (see
[ADR 0004](0004-taxonomy-conflict.md)). A report that reads well but cannot be
audited is not useful to someone deciding whether to build a startup.

## Decision

`ai/pipeline.py::run_pipeline` is the single entry point for a **13-crew** run:
the 12 canonical crews plus a **skeptic** crew (key `skeptic`, before
`reporting`).

1. **Crews 4–12 run through `ai/crews/spec_runner.py`**: one structured call
   per crew, system prompt built from `docs/phases/<NN>-*.md` and the crew's
   `docs/agents/*.md`, validated against the crew's schema. This is why the
   phase and agent docs are read by code and must keep their header format.
2. **Shared source pool** (`ai/evidence/sources.py`, `signals.py`): built once
   after crew 1 from web search plus GitHub and Hacker News signals (keyless;
   `GITHUB_TOKEN` is optional and lifts rate limits). Every source is
   numbered and de-duplicated; later crews cite from the same pool.
3. **Evidence ledger** (`ai/evidence/ledger.py`): after the crews finish, up to
   5 checkable claims per crew are extracted (skipping `skeptic`, `reporting`,
   `community`), matched to the best passages by token overlap, and verified
   by the model. A claim is `supported` only when the verifier returns a quote
   that appears **verbatim** in a retrieved passage. Otherwise it is
   `unsupported` or `contradicted`. Unsupported claims get one targeted web
   search retry (`RETRY_SEARCHES`). Grounding score = supported / total.
4. **Skeptic crew** (`ai/crews/skeptic/`): bull case, bear case, top risks,
   pre-mortem, testable hypotheses, a verdict (`go` / `pivot` / `no-go`),
   what would change its mind, and a survival score with a low/high range.
5. **Fail-soft**: only `idea_validation`, `market_research` and
   `research_patent` abort a run. A failure in any other crew is recorded in
   `failed_crews` and the report marks it unavailable. A ledger failure
   leaves the report valid without a ledger.

## Scoring

- All scores are 0–100 and confidence is 0–1, normalised in
  `ai/shared/digest.py`. The UI never guesses a scale.
- Readiness = validation 35% + market 35% + novelty 30%; blended 80/20 with
  the mean of feasibility and funding when present; then blended
  85/15 with the skeptic's survival score (`SKEPTIC_WEIGHT = 0.15`).
- Report confidence = 0.6 × mean crew confidence + 0.4 × grounding score
  (or 0.8 × the mean when no ledger exists).
- The verdict label is kept consistent with the number: a `no-go` at 70 or
  above becomes `pivot`, and a `go` below 35 becomes `pivot`.

## Consequences

- Mock output is never silent: `mode` is `"mock"` when any step fell back to
  mock data, and production refuses mock runs.
- The ledger only proves a claim appears in a source, not that the source is
  right. Claims about the startup's own features and plans are tagged
  (`own_feature`, `plan`, `estimate`, `score`) so only `external_fact`
  claims count as checkable facts.
- Each crew is one call, so a 32B model may give shallow output for crews
  with many roles. The `ponytail:` note in `spec_runner.py` marks the upgrade
  path: split into per-agent calls.
- Running state is in-process (`backend/services/runner.py`), so run exactly
  one API process.
