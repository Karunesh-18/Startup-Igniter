"""Unified Research Service: keyless web search, Semantic Scholar, OpenAlex, PatentsView, HF embeddings, Upstash caching."""

from typing import Any, Dict, List, Optional

from ai.tools import (
    HFEmbeddingsTool,
    OpenAlexTool,
    PatentsViewTool,
    SemanticScholarTool,
    UpstashRedisCache,
)
from ai.shared.logger import ai_logger
from ai.shared.research.web_provider import WebResearchProvider


class ResearchService:
    """Consolidated orchestrator service for all external research & search APIs."""

    def __init__(self, mock_mode: bool = False) -> None:
        """Initialize all research tool instances."""
        self.mock_mode = mock_mode
        self.web = WebResearchProvider()
        self.semantic_scholar = SemanticScholarTool()
        self.openalex = OpenAlexTool()
        self.patents = PatentsViewTool()
        self.embeddings = HFEmbeddingsTool()
        self.cache = UpstashRedisCache()

    def search_web(self, query: str) -> Dict[str, Any]:
        """Grounded web search (DuckDuckGo + page extraction) with Redis caching."""
        cache_key = f"cache:web:{hash(query)}"
        cached = self.cache.get(cache_key)
        if cached:
            ai_logger.info(f"[CACHE HIT] Returning cached web search results for '{query}'")
            return cached

        bundle = self.web.search_market(query, mock_mode=self.mock_mode)
        payload = {"source": "web", "query": query, "results": bundle.market_articles}
        self.cache.set(cache_key, payload, ttl_seconds=86400)
        return payload

    def search_literature(self, query: str) -> Dict[str, Any]:
        """Perform academic paper search using Semantic Scholar and OpenAlex."""
        cache_key = f"cache:lit:{hash(query)}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        sem_res = self.semantic_scholar.search_papers(query, limit=3, mock_mode=self.mock_mode)
        alex_res = self.openalex.search_works(query, per_page=3, mock_mode=self.mock_mode)

        payload = {
            "query": query,
            "semantic_scholar": [p.model_dump() for p in sem_res.papers],
            "openalex": [w.model_dump() for w in alex_res.works],
        }
        self.cache.set(cache_key, payload, ttl_seconds=86400 * 3)
        return payload

    def search_prior_art(self, query: str) -> Dict[str, Any]:
        """Perform patent & prior-art research using PatentsView."""
        cache_key = f"cache:pat:{hash(query)}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        pat_res = self.patents.search_patents(query, limit=5, mock_mode=self.mock_mode)
        payload = {
            "query": query,
            "patents": [p.model_dump() for p in pat_res.patents],
        }
        self.cache.set(cache_key, payload, ttl_seconds=86400 * 7)
        return payload

    def get_embedding(self, text: str) -> List[float]:
        """Generate 384-dimensional vector embedding for project memory."""
        return self.embeddings.embed_text(text, mock_mode=self.mock_mode)


def get_research_service(mock_mode: bool = False) -> ResearchService:
    """Factory function returning configured ResearchService instance."""
    return ResearchService(mock_mode=mock_mode)
