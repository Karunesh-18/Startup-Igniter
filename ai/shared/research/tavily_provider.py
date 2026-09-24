"""Tavily Research Provider -- real web-search grounding.

Built on the existing `ai.tools.tavily_search.TavilySearchTool`, a working
Tavily API client that was never called by anything before this. Tavily is
the general-purpose search provider: market/industry/trend/competitor/
funding/news queries where a real search API exists, as opposed to
ZyteResearchProvider's narrower "no API exists at all" scope (patent
offices, known competitor URLs).
"""

from typing import Any, Optional

from ai.shared.logger import ai_logger
from ai.shared.research.research_bundle import ResearchBundle
from ai.shared.research.research_provider import BaseResearchProvider
from ai.tools.tavily_search import TavilySearchOutput, TavilySearchTool


def _bundle_from_results(output: TavilySearchOutput) -> ResearchBundle:
    bundle = ResearchBundle()
    for item in output.results:
        entry = {"title": item.title, "url": item.url, "content": item.content, "score": item.score, "provider": "tavily"}
        bundle.market_articles.append(entry)
        bundle.citations.append({"title": item.title, "url": item.url, "provider": "tavily"})
    bundle.metadata["tavily_query"] = output.query
    return bundle


class TavilyResearchProvider(BaseResearchProvider):
    """Tavily search provider for general market/competitor/trend/news grounding."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        super().__init__(api_key=api_key)
        self._tool = TavilySearchTool(api_key=api_key)

    def _search(self, query: str, **kwargs: Any) -> ResearchBundle:
        try:
            output = self._tool.search(query, mock_mode=kwargs.get("mock_mode", False))
        except Exception as err:  # noqa: BLE001
            ai_logger.warning(f"Tavily search failed for query '{query}': {err}")
            return ResearchBundle()
        return _bundle_from_results(output)

    def search_market(self, query: str, **kwargs: Any) -> ResearchBundle:
        # market_articles is already the right bucket -- _bundle_from_results
        # populates it directly, no relabeling needed (unlike the other methods
        # below, which redirect out of that default bucket into their own).
        return self._search(f"{query} market overview size growth", **kwargs)

    def search_industry(self, industry_name: str, **kwargs: Any) -> ResearchBundle:
        bundle = self._search(f"{industry_name} industry benchmarks CAGR lifecycle", **kwargs)
        bundle.industry_reports = bundle.market_articles
        bundle.market_articles = []
        return bundle

    def search_competitors(self, startup_idea: str, category: str, **kwargs: Any) -> ResearchBundle:
        bundle = self._search(f"top competitors and similar startups in {category}: {startup_idea}", **kwargs)
        bundle.competitor_data = bundle.market_articles
        bundle.market_articles = []
        return bundle

    def search_trends(self, category: str, **kwargs: Any) -> ResearchBundle:
        bundle = self._search(f"{category} emerging technology and consumer trends", **kwargs)
        bundle.trend_reports = bundle.market_articles
        bundle.market_articles = []
        return bundle

    def search_patents(self, technology_concept: str, **kwargs: Any) -> ResearchBundle:
        bundle = self._search(f"{technology_concept} patents prior art", **kwargs)
        bundle.research_papers = bundle.market_articles
        bundle.market_articles = []
        return bundle

    def search_regulations(self, industry: str, region: str = "global", **kwargs: Any) -> ResearchBundle:
        bundle = self._search(f"{industry} regulations compliance requirements {region}", **kwargs)
        bundle.government_sources = bundle.market_articles
        bundle.market_articles = []
        return bundle

    def search_funding(self, market_segment: str, **kwargs: Any) -> ResearchBundle:
        bundle = self._search(f"{market_segment} startup funding rounds valuations", **kwargs)
        bundle.startup_sources = bundle.market_articles
        bundle.market_articles = []
        return bundle

    def search_news(self, keywords: str, **kwargs: Any) -> ResearchBundle:
        bundle = self._search(f"{keywords} recent news", **kwargs)
        bundle.news_articles = bundle.market_articles
        bundle.market_articles = []
        return bundle
