"""Zyte Research Provider — global patent search and known-URL scraping.

Built on the existing `ai.tools.zyte_scraper.ZyteScraperTool`, which already
implements real Zyte `/v1/extract` calls (basic auth, base64 response
decode), a `MAX_CALLS_PER_RUN=3` cost guard, and a plain-httpx fallback when
Zyte is disabled/unconfigured. This module was previously 8 methods that all
returned an empty `ResearchBundle()` unconditionally — the scraper worked,
nothing ever called it.
"""

from typing import Any, List, Optional

from ai.shared.logger import ai_logger
from ai.shared.research.research_bundle import ResearchBundle
from ai.shared.research.research_provider import BaseResearchProvider
from ai.shared.research.zyte_urls import (
    SearchTarget,
    build_patent_search_urls,
    build_regulatory_search_url,
)
from ai.tools.zyte_scraper import ScrapeResult, ZyteScraperTool


def _truncate(text: str, limit: int = 2000) -> str:
    """Keep prompts bounded — a raw scraped page can be tens of KB."""
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


def _scrape_targets(
    tool: ZyteScraperTool, targets: List[SearchTarget], mock_mode: bool = False
) -> ResearchBundle:
    """Scrape each target URL and fold the results into one ResearchBundle."""
    bundle = ResearchBundle()
    for target in targets:
        try:
            result: ScrapeResult = tool.scrape_url(target.url, mock_mode=mock_mode)
        except Exception as err:  # noqa: BLE001 — one bad source shouldn't sink the whole bundle
            ai_logger.warning(f"Zyte scrape failed for source '{target.source}' ({target.url}): {err}")
            continue

        if not result.clean_text or not result.clean_text.strip():
            continue

        snippet = _truncate(result.clean_text)
        bundle.scraped_pages.append({"source": target.source, "url": target.url, "content": snippet})
        bundle.research_papers.append(
            {"source": target.source, "url": target.url, "summary": snippet, "provider": "zyte"}
        )
        bundle.citations.append({"source": target.source, "url": target.url, "provider": "zyte"})
    bundle.metadata["zyte_calls_made"] = tool._call_count
    return bundle


class ZyteResearchProvider(BaseResearchProvider):
    """Zyte-backed provider for global patent search and known-URL scraping.

    Deliberately does NOT attempt general web/news/funding search — that's
    Tavily/Exa's job (real search APIs); Zyte's value here is sites with no
    API at all (patent offices) and scraping a URL once it's known. See the
    module docstring in ai.shared.research.zyte_urls for the full rationale.
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        super().__init__(api_key=api_key)
        self._tool = ZyteScraperTool(api_key=api_key)

    def search_market(self, query: str, **kwargs: Any) -> ResearchBundle:
        """Not Zyte's job — general market search belongs to Tavily/Exa (real
        search APIs). Returns empty so ResearchManager's merge is a no-op."""
        ai_logger.debug("ZyteResearchProvider.search_market: out of scope by design, see class docstring.")
        return ResearchBundle()

    def search_industry(self, industry_name: str, **kwargs: Any) -> ResearchBundle:
        """Out of scope by design — see search_market."""
        return ResearchBundle()

    def search_competitors(self, startup_idea: str, category: str, **kwargs: Any) -> ResearchBundle:
        """Scrape specific competitor URLs, when the caller already has them.

        Zyte's spec'd value here is "competitor websites & pricing pages" —
        that requires a URL, not a category. Pass `urls=[...]` once discovery
        (Tavily/Exa) has found candidate competitor domains; without one,
        this correctly returns empty rather than guessing at URLs.
        """
        urls: Optional[List[str]] = kwargs.get("urls")
        if not urls:
            ai_logger.debug("ZyteResearchProvider.search_competitors: no explicit competitor URLs supplied.")
            return ResearchBundle()
        targets = [SearchTarget(f"competitor:{i}", url) for i, url in enumerate(urls)]
        bundle = _scrape_targets(self._tool, targets, mock_mode=kwargs.get("mock_mode", False))
        bundle.competitor_data = bundle.research_papers  # relabel into the right bucket
        bundle.research_papers = []
        return bundle

    def search_trends(self, category: str, **kwargs: Any) -> ResearchBundle:
        """Out of scope by design — see search_market."""
        return ResearchBundle()

    def search_patents(self, technology_concept: str, **kwargs: Any) -> ResearchBundle:
        """Scrape Google Patents / Espacenet / WIPO Patentscope / India IP —
        the case with genuinely no unified free API, and Zyte's core reason
        for existing in this project (per ai-startup-navigator-spec-v2.md §6)."""
        targets = build_patent_search_urls(technology_concept)
        bundle = _scrape_targets(self._tool, targets, mock_mode=kwargs.get("mock_mode", False))
        ai_logger.info(
            f"ZyteResearchProvider.search_patents: scraped {len(bundle.scraped_pages)}/{len(targets)} "
            f"patent office sources for '{technology_concept}'."
        )
        return bundle

    def search_regulations(self, industry: str, region: str = "global", **kwargs: Any) -> ResearchBundle:
        """Scrape a .gov-scoped search for the industry/region — a defensible
        best-effort default when no specific regulatory portal URL is known."""
        url = build_regulatory_search_url(industry, region)
        bundle = _scrape_targets(
            self._tool, [SearchTarget(f"regulatory:{region}", url)], mock_mode=kwargs.get("mock_mode", False)
        )
        bundle.government_sources = bundle.research_papers
        bundle.research_papers = []
        return bundle

    def search_funding(self, market_segment: str, **kwargs: Any) -> ResearchBundle:
        """Out of scope by design — see search_market."""
        return ResearchBundle()

    def search_news(self, keywords: str, **kwargs: Any) -> ResearchBundle:
        """Out of scope by design — see search_market."""
        return ResearchBundle()
