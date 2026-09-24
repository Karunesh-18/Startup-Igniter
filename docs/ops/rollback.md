# Rollback

## Bad model promotion

Since the gateway resolves models by name/adapter-path from config
(`LLM_MODEL_HEAVY`, `LLM_MODEL_FAST`, `training/serve/adapters.yaml`), a bad
promotion is reverted by **config change, not code change**:

1. Revert `LLM_MODEL_HEAVY`/`LLM_MODEL_FAST` (or the adapter path) to the
   previous known-good value.
2. Restart the affected vLLM server(s) (see [serving.md](serving.md)) — LoRA
   adapters can be hot-swapped without a full restart if vLLM's
   `--lora-modules` list already includes the previous adapter; a base-model
   change requires a restart.
3. Re-run `python -m training.eval.harness --backend selfhosted` against the
   reverted endpoint to confirm it matches the previously-recorded results
   for that version before considering the rollback complete.

Keep at least the last 2–3 checkpoints per `save_total_limit` in every
training config (`training/configs/*.yaml`) specifically so "previous
known-good" is always an actual file on disk, not something that needs
re-training.

## Bad deploy (gateway/backend code)

Standard git revert of the offending commit, redeploy. Two things this
migration specifically changed that are worth checking first if a deploy
regresses:

- **`backend/core/config.py` now imports `ai.llm.settings`** via a
  `sys.path` bootstrap (see [ADR 0001](../architecture/0001-llm-gateway.md)
  and the commit that fixed the Docker build context). If a deploy fails at
  import time with `ModuleNotFoundError: No module named 'ai'`, the build
  context is wrong — confirm the image was built from the **repo root**, not
  from `backend/` (`docker build -f backend/Dockerfile .` from the repo
  root, or `docker compose up` from `backend/` since `docker-compose.yml`'s
  `context: ..` already points at the repo root).
- **The gateway falls through to the mock provider** when nothing real is
  configured/reachable — if a deploy silently starts returning mock-shaped
  responses in production, check `LLM_BASE_URL`/`GROQ_API_KEY`/
  `OPENROUTER_API_KEY` are actually set in that environment's config, not
  just locally. `AISettings.validate_api_keys(raise_on_missing=True)` will
  raise `MissingAPIKeyError` if truly nothing is configured — wire a startup
  check to call this rather than discovering the gap from silent mock
  output in production.

## Bad grounding data

If Zyte/Tavily/Exa start returning garbage (a site layout change breaks a
scraper, a search API starts rate-limiting), the pipeline degrades
gracefully by design: `MarketResearchService`/`ResearchPatentService` catch
`ResearchManager` failures and proceed **ungrounded** rather than failing the
run (see [ADR 0005](../architecture/0005-grounding-layer.md)). There is
usually nothing to roll back here — confirm the failure is logged (search
for `"proceeding ungrounded"` in logs) and fix the underlying scraper/API
issue rather than treating it as a deploy incident.
