"""Unified Research Service orchestrating Tavily, Exa, Semantic Scholar, OpenAlex, PatentsView, HF embeddings, and Upstash caching."""

from typing import Any, Dict, List, Optional

from ai.tools import (
    ExaSearchTool,
    HFEmbeddingsTool,
    OpenAlexTool,
    PatentsViewTool,
    SemanticScholarTool,
    TavilySearchTool,
    UpstashRedisCache,
    ZyteScraperTool,
)
from ai.shared.logger import ai_logger


class ResearchService:
    """Consolidated orchestrator service for all external research & search APIs."""

    def __init__(self, mock_mode: bool = False) -> None:
        """Initialize all research tool instances."""
        self.mock_mode = mock_mode
        self.tavily = TavilySearchTool()
        self.exa = ExaSearchTool()
        self.semantic_scholar = SemanticScholarTool()
        self.openalex = OpenAlexTool()
        self.patents = PatentsViewTool()
        self.embeddings = HFEmbeddingsTool()
        self.cache = UpstashRedisCache()
        self.zyte = ZyteScraperTool()

    def search_web(self, query: str, use_exa_fallback: bool = True) -> Dict[str, Any]:
        """Perform grounded web search using Tavily with Exa fallback & Redis caching."""
        cache_key = f"cache:web:{hash(query)}"
        cached = self.cache.get(cache_key)
        if cached:
            ai_logger.info(f"[CACHE HIT] Returning cached web search results for '{query}'")
            return cached

        try:
            tav_res = self.tavily.search(query, mock_mode=self.mock_mode)
            results = [r.model_dump() for r in tav_res.results]
            payload = {"source": "tavily", "query": query, "results": results}
        except Exception as e:
            ai_logger.warning(f"Tavily search failed ({e}). Trying Exa fallback...")
            if use_exa_fallback:
                exa_res = self.exa.search(query, mock_mode=self.mock_mode)
                results = [r.model_dump() for r in exa_res.results]
                payload = {"source": "exa", "query": query, "results": results}
            else:
                payload = {"source": "none", "query": query, "results": []}

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
