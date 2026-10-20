"""ResearchManager: the one entry point agents/services use for web grounding.

Backed solely by WebResearchProvider (keyless DuckDuckGo + trafilatura).
Every gather_* method returns a ResearchBundle and never raises -- grounding
is best-effort and must not block an analysis run.
"""

from typing import Any, Optional

from ai.shared.logger import ai_logger
from ai.shared.research.research_bundle import ResearchBundle
from ai.shared.research.web_provider import WebResearchProvider


class ResearchManager:
    """Thin, never-raising facade over WebResearchProvider."""

    def __init__(self, provider: Optional[WebResearchProvider] = None) -> None:
        self.provider = provider or WebResearchProvider()

    def _safe(self, method_name: str, *args: Any, **kwargs: Any) -> ResearchBundle:
        try:
            return getattr(self.provider, method_name)(*args, **kwargs)
        except Exception as err:  # noqa: BLE001
            ai_logger.warning(f"ResearchManager.{method_name} failed: {err}")
            return ResearchBundle()

    def gather_market_research(self, startup_idea: str, category: Optional[str] = None, **kwargs: Any) -> ResearchBundle:
        query = f"{startup_idea} ({category})" if category else startup_idea
        return self._safe("search_market", query, **kwargs)

    def gather_competitor_research(self, startup_idea: str, category: str, **kwargs: Any) -> ResearchBundle:
        return self._safe("search_competitors", startup_idea, category, **kwargs)

    def gather_patent_research(self, technology_concept: str, **kwargs: Any) -> ResearchBundle:
        return self._safe("search_patents", technology_concept, **kwargs)

    def gather_regulatory_research(self, industry: str, region: str = "global", **kwargs: Any) -> ResearchBundle:
        return self._safe("search_regulations", industry, region, **kwargs)

    def gather_funding_research(self, market_segment: str, **kwargs: Any) -> ResearchBundle:
        return self._safe("search_funding", market_segment, **kwargs)

    def gather_trend_research(self, category: str, **kwargs: Any) -> ResearchBundle:
        return self._safe("search_trends", category, **kwargs)

    def gather_tech_research(self, idea_text: str, **kwargs: Any) -> ResearchBundle:
        return self._safe("search_tech", idea_text, **kwargs)

    def gather_news_research(self, keywords: str, **kwargs: Any) -> ResearchBundle:
        return self._safe("search_news", keywords, **kwargs)
