"""ResearchManager orchestrator for external research providers."""

import os
from typing import Any, Dict, Optional

from ai.config import get_ai_settings
from ai.shared.logger import ai_logger
from ai.shared.research.exa_provider import ExaResearchProvider
from ai.shared.research.research_bundle import ResearchBundle
from ai.shared.research.tavily_provider import TavilyResearchProvider
from ai.shared.research.zyte_provider import ZyteResearchProvider


class ResearchManager:
    """Orchestrator for managing external research services (Tavily, Exa, Zyte).

    Architecture Documentation:
        Version 1:
            - Operates strictly in LLM-only reasoning mode.
            - Returns an empty ResearchBundle without making external API calls.
            - Zero network overhead and zero latency impact.

        Version 2:
            - Will instantiate active providers using configured API keys:
                * TAVILY_API_KEY (Deep web research & real-time search)
                * EXA_API_KEY (Neural semantic search & academic papers)
                * ZYTE_API_KEY (Structured web scraping & competitor profiling)
            - Will merge multi-provider search results into a unified ResearchBundle
              to enrich reasoning across Market Research, Patent, Legal, and Funding crews.
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

        # Extension point provider instances
        self.tavily_provider = TavilyResearchProvider(api_key=self.tavily_key)
        self.exa_provider = ExaResearchProvider(api_key=self.exa_key)
        self.zyte_provider = ZyteResearchProvider(api_key=self.zyte_key)

    def gather_market_research(
        self,
        startup_idea: str,
        category: Optional[str] = None,
        **kwargs: Any,
    ) -> ResearchBundle:
        """Gather market research data across providers.

        Version 1: Returns empty ResearchBundle (LLM-only).
        Version 2: Aggregates Tavily market articles, Exa industry trends, and Zyte competitor pages.
        """
        ai_logger.debug("ResearchManager: Returning empty ResearchBundle for Version 1 LLM-only execution.")
        return ResearchBundle()

    def gather_competitor_research(
        self,
        startup_idea: str,
        category: str,
        **kwargs: Any,
    ) -> ResearchBundle:
        """Gather competitor profiling data across providers.

        Version 1: Returns empty ResearchBundle (LLM-only).
        Version 2: Aggregates Tavily & Exa competitor queries and Zyte competitor pricing scrapes.
        """
        ai_logger.debug("ResearchManager: Returning empty ResearchBundle for Version 1 LLM-only execution.")
        return ResearchBundle()

    def gather_patent_research(
        self,
        technology_concept: str,
        **kwargs: Any,
    ) -> ResearchBundle:
        """Gather patent filings and technical research papers.

        Version 1: Returns empty ResearchBundle (LLM-only).
        Version 2: Aggregates Exa research paper search and USPTO/WIPO data.
        """
        ai_logger.debug("ResearchManager: Returning empty ResearchBundle for Version 1 LLM-only execution.")
        return ResearchBundle()

    def gather_regulatory_research(
        self,
        industry: str,
        region: str = "global",
        **kwargs: Any,
    ) -> ResearchBundle:
        """Gather legal, regulatory, and compliance data.

        Version 1: Returns empty ResearchBundle (LLM-only).
        Version 2: Aggregates official regulatory portal scrapes via Zyte and Tavily.
        """
        ai_logger.debug("ResearchManager: Returning empty ResearchBundle for Version 1 LLM-only execution.")
        return ResearchBundle()
