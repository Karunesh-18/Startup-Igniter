"""Free web grounding: DuckDuckGo search (ddgs) + page fetch + trafilatura main-text extraction.

No API keys. Replaces the old Tavily/Exa/Zyte providers. Every search_* method
returns a ResearchBundle with entries shaped {title, url, content, snippet,
provider} in the bucket matching its topic, plus one citation per entry, so
prompt_formatting.format_research_bundle_for_prompt keeps working unchanged.
"""

from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import Any, Dict, List, Tuple

import httpx
import trafilatura

from ai.shared.logger import ai_logger
from ai.shared.research.research_bundle import ResearchBundle
from ai.shared.research.research_provider import BaseResearchProvider

try:
    from ddgs import DDGS
except ImportError:  # legacy package name
    from duckduckgo_search import DDGS

_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
MAX_PAGES = 5
MAX_CHARS_PER_PAGE = 2000
FETCH_TIMEOUT_SECONDS = 10.0

_REGION_SITES = {"global": ".gov", "us": ".gov", "india": ".gov.in", "eu": ".europa.eu", "uk": ".gov.uk"}


def _fetch_text(client: httpx.Client, url: str) -> str:
    """Main text of a page, or '' on any failure (per-page failures never sink the query)."""
    try:
        resp = client.get(url)
        resp.raise_for_status()
        return (trafilatura.extract(resp.text) or "")[:MAX_CHARS_PER_PAGE]
    except Exception as err:  # noqa: BLE001
        ai_logger.debug(f"Web fetch failed for {url}: {err}")
        return ""


# ponytail: per-process cache, move to Redis if multiple workers
@lru_cache(maxsize=256)
def _search(query: str, max_pages: int = MAX_PAGES) -> Tuple[Dict[str, str], ...]:
    """query -> fetched+extracted top pages. Raises on search failure (not cached)."""
    hits = [h for h in (DDGS().text(query, max_results=max_pages) or []) if h.get("href")]
    with httpx.Client(timeout=FETCH_TIMEOUT_SECONDS, follow_redirects=True, headers={"User-Agent": _USER_AGENT}) as client:
        with ThreadPoolExecutor(max_workers=max_pages) as pool:
            texts = list(pool.map(lambda h: _fetch_text(client, h["href"]), hits))
    return tuple(
        {
            "title": h.get("title", ""),
            "url": h["href"],
            # Fall back to the search snippet so a blocked/JS-only page still grounds something.
            "content": text or h.get("body", ""),
            "snippet": h.get("body", ""),
            "provider": "web",
        }
        for h, text in zip(hits, texts)
    )


class WebResearchProvider(BaseResearchProvider):
    """DuckDuckGo + trafilatura research provider (keyless)."""

    def _bundle(self, query: str, bucket: str, **kwargs: Any) -> ResearchBundle:
        bundle = ResearchBundle(metadata={"web_query": query})
        if kwargs.get("mock_mode"):
            return bundle
        try:
            entries: List[Dict[str, str]] = [dict(e) for e in _search(query)]
        except Exception as err:  # noqa: BLE001
            ai_logger.warning(f"Web search failed for '{query}': {err}")
            return bundle
        setattr(bundle, bucket, entries)
        bundle.citations = [{"title": e["title"], "url": e["url"], "provider": "web"} for e in entries]
        return bundle

    def search_market(self, query: str, **kwargs: Any) -> ResearchBundle:
        return self._bundle(f"{query} market size growth", "market_articles", **kwargs)

    def search_industry(self, industry_name: str, **kwargs: Any) -> ResearchBundle:
        return self._bundle(f"{industry_name} industry report CAGR", "industry_reports", **kwargs)

    def search_competitors(self, startup_idea: str, category: str, **kwargs: Any) -> ResearchBundle:
        return self._bundle(f"{startup_idea} {category} competitors alternatives startups", "competitor_data", **kwargs)

    def search_trends(self, category: str, **kwargs: Any) -> ResearchBundle:
        return self._bundle(f"{category} trends 2026", "trend_reports", **kwargs)

    def search_patents(self, technology_concept: str, **kwargs: Any) -> ResearchBundle:
        return self._bundle(f"{technology_concept} site:patents.google.com", "research_papers", **kwargs)

    def search_regulations(self, industry: str, region: str = "global", **kwargs: Any) -> ResearchBundle:
        site = _REGION_SITES.get(region.lower(), ".gov")
        return self._bundle(f"{industry} regulations compliance site:{site}", "government_sources", **kwargs)

    def search_funding(self, market_segment: str, **kwargs: Any) -> ResearchBundle:
        return self._bundle(f"{market_segment} startup funding round raised", "startup_sources", **kwargs)

    def search_news(self, keywords: str, **kwargs: Any) -> ResearchBundle:
        return self._bundle(f"{keywords} news", "news_articles", **kwargs)

    def search_tech(self, idea_text: str, **kwargs: Any) -> ResearchBundle:
        return self._bundle(f"{idea_text} technology stack architecture how it works", "research_papers", **kwargs)
