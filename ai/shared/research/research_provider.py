"""Abstract Base Interface for External Research Providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from ai.shared.research.research_bundle import ResearchBundle


class BaseResearchProvider(ABC):
    """Abstract Base Class defining the contract for all external research integrations.

    Architecture Note:
        Version 1: Methods act as clean extension points raising NotImplementedError
                   or returning an empty ResearchBundle without making API calls.
        Version 2: Subclasses implement real Tavily, Exa, or Zyte network requests.
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize provider with optional API key."""
        self.api_key = api_key

    @abstractmethod
    def search_market(self, query: str, **kwargs: Any) -> ResearchBundle:
        """Search for high-level market landscape and overview data."""
        raise NotImplementedError("search_market is not implemented in Version 1.")

    @abstractmethod
    def search_industry(self, industry_name: str, **kwargs: Any) -> ResearchBundle:
        """Search for industry benchmarks, CAGR, and lifecycle data."""
        raise NotImplementedError("search_industry is not implemented in Version 1.")

    @abstractmethod
    def search_competitors(self, startup_idea: str, category: str, **kwargs: Any) -> ResearchBundle:
        """Discover and profile market competitors."""
        raise NotImplementedError("search_competitors is not implemented in Version 1.")

    @abstractmethod
    def search_trends(self, category: str, **kwargs: Any) -> ResearchBundle:
        """Search for emerging technological and consumer trends."""
        raise NotImplementedError("search_trends is not implemented in Version 1.")

    @abstractmethod
    def search_patents(self, technology_concept: str, **kwargs: Any) -> ResearchBundle:
        """Search for patent filings and prior art."""
        raise NotImplementedError("search_patents is not implemented in Version 1.")

    @abstractmethod
    def search_regulations(self, industry: str, region: str = "global", **kwargs: Any) -> ResearchBundle:
        """Search for legal, compliance, and regulatory frameworks."""
        raise NotImplementedError("search_regulations is not implemented in Version 1.")

    @abstractmethod
    def search_funding(self, market_segment: str, **kwargs: Any) -> ResearchBundle:
        """Search for venture capital funding events and startup valuation data."""
        raise NotImplementedError("search_funding is not implemented in Version 1.")

    @abstractmethod
    def search_news(self, keywords: str, **kwargs: Any) -> ResearchBundle:
        """Search for recent market news articles and industry press releases."""
        raise NotImplementedError("search_news is not implemented in Version 1.")
