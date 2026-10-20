# ADR 0005: Grounding via Zyte/Tavily/Exa before the model swap

**Status:** Implemented (Phases 01–03) · **Date:** 2026-09-24

## Context

Before this change, `ai/shared/research/{zyte,tavily,exa}_provider.py` were
three clean extension points — 8 methods each, every one returning an empty
`ResearchBundle()` — sitting on top of three *already-working* low-level API
clients (`ZyteScraperTool`, `TavilySearchTool`, `ExaSearchTool`) that nothing
ever called. `ResearchManager`, the orchestrator meant to merge their
results, unconditionally returned an empty bundle from every `gather_*`
method regardless of what its own provider instances could do.
`market_research_agent.py`'s prompt-building code read:

```python
if market_context.research_bundle:
    # Future enhancement: Use verified external research from ResearchManager
    pass
```

So every market/patent claim the pipeline made came from the model's
parametric memory alone, with zero source attribution.

## Why this had to happen before, not after, the model swap

A rate-limited Llama-3.3-70B (the pre-migration model) has more world
knowledge baked into its weights than a fine-tuned Qwen3-32B will, simply by
parameter count and training-data recency. Moving to a smaller, fine-tuned,
self-hosted model **without** fixing grounding first would make
hallucinated market sizes and invented competitor names *more* confident,
not less — the fine-tune (see [ADR 0003](0003-qwen3-base-models.md)) teaches
the model its schema and reasoning shape, explicitly **not** facts, which
only makes sense if real facts arrive at inference time via retrieval.

## Decision

Wire all three providers for real, then close the loop into the two crews
that currently run:

- **Zyte** ([`zyte_urls.py`](../../ai/shared/research/zyte_urls.py) +
  `zyte_provider.py`): scoped narrowly to what it's uniquely good for — the
  4 global patent offices with no unified free API (Google Patents,
  Espacenet, WIPO Patentscope, India IP), and scraping a specific known URL
  (e.g. a competitor's pricing page once discovery has found it via
  `urls=[...]`). Deliberately does **not** guess at search-engine URLs for
  general market/news queries — that's real search APIs' job, and building
  scrapers against Google/Bing SERP HTML is fragile and ToS-grey for no
  benefit over an actual search API.
- **Tavily / Exa** (`tavily_provider.py` / `exa_provider.py`): implemented
  for real on the same existing tool clients, covering
  market/industry/trend/competitor/funding/news — the general search-API
  surface Zyte was never meant to cover.
- **`ResearchManager`**: now actually calls and merges provider results
  (`ResearchBundle.merge()`) per `gather_*` method, catching any one
  provider's failure so it never sinks the others.
- **The actual grounding gap**: `market_research_agent.py`'s `pass` and
  `patent_search_agent.py`'s equivalent no-op are now real prompt injection
  via `ai.shared.research.prompt_formatting.format_research_bundle_for_prompt`,
  which renders up to 8 sources as a numbered list and instructs the model
  either to cite them (`citations` field, added to both
  `MarketResearchAnalysis` and `PatentAnalysis`) or to leave `citations`
  empty rather than inventing sources when none were supplied.

## Consequences

- [Phase 02](../phases/02-market-research.md) and
  [Phase 03](../phases/03-research-and-patent.md) are grounded; Phase 01
  (Idea Validation) has no external-research need by design — it's pure
  analysis of the user's own submitted text.
- `MarketResearchService` and `ResearchPatentService` now call
  `ResearchManager` before running their crews; a grounding failure is
  logged and the crew proceeds ungrounded rather than failing the run —
  research is an enhancement, not a hard dependency, for these two crews.
- `backend/db/models.py`'s `VECTOR_TYPE` now resolves to a real
  `pgvector.sqlalchemy.Vector(384)` (the dependency is installed; the
  `ImportError` fallback to `Text` was already there, just unreachable
  without the package).
- Real embeddings (`sentence-transformers`) are gated behind
  `AI_USE_REAL_EMBEDDINGS` (default off) — installing the package makes
  `ProjectMemoryManager` *capable* of loading a real model, but doing so
  unconditionally would make every memory write attempt a live Hugging Face
  download on first use, discovered when it hung a test run during this
  migration.
- `ProjectMemoryManager.write_memory()`'s "production path" — previously a
  comment claiming Supabase persistence that called nothing — now accepts an
  optional `persist_callback`. `ai/` still doesn't import `backend/db`
  directly; the caller with a DB session (`backend/workers/tasks.py`) is
  responsible for wiring one in.

## Known gaps

- Only `market_research_agent.py` (of Phase 02's 7 agents) and
  `patent_search_agent.py` (of Phase 03's 7) currently consume the research
  bundle. The other agents in those crews still reason without grounding —
  a natural next extension, following the same
  `format_research_bundle_for_prompt` pattern.
- `research_patent_summary_agent.py`'s output isn't validated against one
  clean Pydantic schema the way the others are (its raw output is manually
  merged field-by-field with `context`), so it doesn't yet get
  `schema_class`-driven guided decoding — see the note in
  [`ai/shared/llm_provider.py`](../../ai/shared/llm_provider.py)'s migration
  commit for why this one call site was left as-is rather than forced.
- Upstash caching for research results (TTLs already exist in
  `backend/core/config.py` as `CACHE_MARKET_TTL`/`CACHE_COMPETITOR_TTL`) is
  not yet wired to the new provider calls — every grounded run re-queries
  Tavily/Exa/Zyte fresh.
