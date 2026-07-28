"""Tavily search grounding tool for Startup Igniter AI agents."""

import os
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field

from ai.config import get_ai_settings
from ai.shared.errors import MissingAPIKeyError, StartupOSAIError
from ai.shared.logger import ai_logger

# Optional CrewAI tool import check
try:
    from crewai.tools import tool as crewai_tool  # type: ignore
    HAS_CREWAI_TOOL = True
except ImportError:
    HAS_CREWAI_TOOL = False
    crewai_tool = None


class SearchResultItem(BaseModel):
    """Schema for individual web search result items."""

    title: str = Field(description="Title of the search result page.")
    url: str = Field(description="URL link of the search result.")
    content: str = Field(description="Extracted text/snippet content.")
    score: float = Field(default=0.0, description="Relevance score from search engine.")


class TavilySearchOutput(BaseModel):
    """Structured response container for web search queries."""

    query: str = Field(description="Original input search query.")
    results: List[SearchResultItem] = Field(default_factory=list, description="List of search result items.")
    raw_response: Optional[Dict[str, Any]] = Field(default=None, description="Raw API response object.")


class TavilySearchTool:
    """Production-grade client for Tavily AI Search API."""

    API_URL = "https://api.tavily.com/search"

    def __init__(self, api_key: Optional[str] = None, timeout: float = 15.0) -> None:
        """Initialize Tavily search tool instance."""
        settings = get_ai_settings()
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = settings.tavily_api_key or os.getenv("TAVILY_API_KEY", "")
        self.timeout = timeout

    def search(
        self,
        query: str,
        search_depth: str = "basic",
        max_results: int = 5,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        mock_mode: bool = False,
    ) -> TavilySearchOutput:
        """Execute web search query against Tavily API.

        Args:
            query: Search query text string.
            search_depth: 'basic' or 'advanced' (deep research).
            max_results: Max result items to return (1-10).
            include_domains: Optional target domain filters.
            exclude_domains: Optional excluded domain filters.
            mock_mode: If True, returns mock search results for testing without API keys.

        Returns:
            TavilySearchOutput structured search results.
        """
        if mock_mode:
            ai_logger.info(f"[MOCK] Tavily search executed for query: '{query}'")
            return TavilySearchOutput(
                query=query,
                results=[
                    SearchResultItem(
                        title=f"Mock Result for {query}",
                        url="https://example.com/mock-search",
                        content=f"Sample market validation data grounding claim for '{query}'.",
                        score=0.95,
                    )
                ],
            )

        if not self.api_key:
            raise MissingAPIKeyError(key_name="TAVILY_API_KEY", provider_name="Tavily")

        payload: Dict[str, Any] = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results,
            "include_answer": True,
        }
        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains

        ai_logger.info(f"Executing Tavily web search: query='{query}', depth={search_depth}")

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.API_URL, json=payload)
                response.raise_for_status()
                data = response.json()

            results = [
                SearchResultItem(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("content", ""),
                    score=item.get("score", 0.0),
                )
                for item in data.get("results", [])
            ]

            return TavilySearchOutput(query=query, results=results, raw_response=data)

        except httpx.HTTPStatusError as err:
            ai_logger.error(f"Tavily HTTP error ({err.response.status_code}): {err.response.text}")
            raise StartupOSAIError(
                f"Tavily search API failed with status code {err.response.status_code}",
                details={"status_code": err.response.status_code, "query": query},
            ) from err
        except Exception as err:
            ai_logger.error(f"Tavily search execution failed: {str(err)}")
            raise StartupOSAIError(
                f"Tavily search failed: {str(err)}",
                details={"query": query, "error": str(err)},
            ) from err
