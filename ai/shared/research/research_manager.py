"""ResearchManager orchestrator for external research providers."""

import os
from typing import Any, List, Optional

from ai.config import get_ai_settings
from ai.shared.logger import ai_logger
from ai.shared.research.exa_provider import ExaResearchProvider
from ai.shared.research.research_bundle import ResearchBundle
from ai.shared.research.research_provider import BaseResearchProvider
from ai.shared.research.tavily_provider import TavilyResearchProvider
from ai.shared.research.zyte_provider import ZyteResearchProvider


def _merge_provider_results(
    providers: List[BaseResearchProvider], method_name: str, *args: Any, **kwargs: Any
) -> ResearchBundle:
    """Call the same method across every provider and merge the bundles.

    A single provider failing (network error, missing key -> its own
    MissingAPIKeyError, etc.) does not sink the others -- the point of having
    three providers is that they degrade independently.
    """
    merged = ResearchBundle()
    for provider in providers:
        try:
            bundle = getattr(provider, method_name)(*args, **kwargs)
        except Exception as err:  # noqa: BLE001
            ai_logger.warning(f"{provider.__class__.__name__}.{method_name} failed: {err}")
            continue
        merged = merged.merge(bundle)
    return merged


class ResearchManager:
    """Orchestrator merging Tavily, Exa, and Zyte results into one ResearchBundle.

    Tavily and Exa are general search APIs and cover market/industry/trend/
    competitor-discovery/funding/news queries. Zyte covers what neither can:
    global patent offices (no unified free API) and scraping a specific known
    URL (e.g. a competitor's pricing page once discovery has found it).
    """

    def __init__(
        self,
        tavily_api_key: Optional[str] = None,
        exa_api_key: Optional[str] = None,
        zyte_api_key: Optional[str] = None,
    ) -> None:
        """Initialize ResearchManager with optional API keys or environment variables."""
        settings = get_ai_settings()
        self.tavily_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
        self.exa_key = exa_api_key or os.getenv("EXA_API_KEY")
        self.zyte_key = zyte_api_key or os.getenv("ZYTE_API_KEY")

        self.tavily_provider = TavilyResearchProvider(api_key=self.tavily_key)
        self.exa_provider = ExaResearchProvider(api_key=self.exa_key)
        self.zyte_provider = ZyteResearchProvider(api_key=self.zyte_key)

    def gather_market_research(
        self,
        startup_idea: str,
        category: Optional[str] = None,
        **kwargs: Any,
    ) -> ResearchBundle:
        """Aggregate Tavily + Exa market articles (Zyte has no role here -- see
        ZyteResearchProvider's class docstring)."""
        query = f"{startup_idea} ({category})" if category else startup_idea
        return _merge_provider_results([self.tavily_provider, self.exa_provider], "search_market", query, **kwargs)

    def gather_competitor_research(
        self,
        startup_idea: str,
        category: str,
        **kwargs: Any,
    ) -> ResearchBundle:
        """Aggregate Tavily + Exa competitor discovery, plus Zyte page scrapes
        of any explicit competitor URLs passed via kwargs["urls"]."""
        return _merge_provider_results(
            [self.tavily_provider, self.exa_provider, self.zyte_provider],
            "search_competitors",
            startup_idea,
            category,
            **kwargs,
        )

    def gather_patent_research(
        self,
        technology_concept: str,
        **kwargs: Any,
    ) -> ResearchBundle:
        """Aggregate Exa's academic/semantic patent search with Zyte's direct
        scrape of the four global patent office search-result pages -- the
        genuinely no-free-API case Zyte exists in this project for."""
        return _merge_provider_results(
            [self.exa_provider, self.zyte_provider], "search_patents", technology_concept, **kwargs
        )

    def gather_regulatory_research(
        self,
        industry: str,
        region: str = "global",
        **kwargs: Any,
    ) -> ResearchBundle:
        """Aggregate Tavily + Zyte's .gov-scoped scrape for the industry/region."""
        return _merge_provider_results(
            [self.tavily_provider, self.zyte_provider], "search_regulations", industry, region, **kwargs
        )
