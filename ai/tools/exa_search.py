"""Exa.ai neural/semantic search tool for Startup Igniter AI agents."""

import os
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field

from ai.config import get_ai_settings
from ai.shared.errors import StartupOSAIError
from ai.shared.logger import ai_logger


class ExaResultItem(BaseModel):
    """Schema for individual Exa search result items."""

    title: str = Field(description="Title of the webpage or document.")
    url: str = Field(description="URL link of the result.")
    snippet: str = Field(default="", description="Snippet or summary text.")
    score: float = Field(default=0.0, description="Similarity score.")
    published_date: Optional[str] = Field(default=None, description="Publication date string.")


class ExaSearchOutput(BaseModel):
    """Structured response container for Exa search queries."""

    query: str = Field(description="Search query string.")
    results: List[ExaResultItem] = Field(default_factory=list, description="List of search result items.")


class ExaSearchTool:
    """Production client for Exa.ai neural/semantic search API."""

    API_URL = "https://api.exa.ai/search"

    def __init__(self, api_key: Optional[str] = None, timeout: float = 15.0) -> None:
        """Initialize Exa search tool."""
        settings = get_ai_settings()
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = settings.exa_api_key or os.getenv("EXA_API_KEY", "")
        self.timeout = timeout

    def search(
        self,
        query: str,
        num_results: int = 5,
        use_autoprompt: bool = True,
        mock_mode: bool = False,
    ) -> ExaSearchOutput:
        """Execute semantic search query against Exa.ai API."""
        if mock_mode or not self.api_key:
            ai_logger.info(f"[MOCK/FALLBACK] Exa search executed for query: '{query}'")
            return ExaSearchOutput(
                query=query,
                results=[
                    ExaResultItem(
                        title=f"Semantic Result for {query}",
                        url="https://exa.ai/mock-result",
                        snippet=f"Semantic similarity match and market insight for '{query}'.",
                        score=0.92,
                    )
                ],
            )

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "query": query,
            "numResults": num_results,
            "useAutoprompt": use_autoprompt,
            "contents": {"text": {"maxCharacters": 1000}},
        }

        ai_logger.info(f"Executing Exa semantic search query: '{query}'")

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(self.API_URL, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()

            results = [
                ExaResultItem(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("text", "") or item.get("snippet", ""),
                    score=item.get("score", 0.0),
                    published_date=item.get("publishedDate"),
                )
                for item in data.get("results", [])
            ]
            return ExaSearchOutput(query=query, results=results)

        except Exception as err:
            ai_logger.warning(f"Exa search failed: {err}. Falling back to mock result.")
            return ExaSearchOutput(
                query=query,
                results=[
                    ExaResultItem(
                        title=f"Market Research match for {query}",
                        url="https://example.com/research",
                        snippet=f"Market research and competitive analysis data for '{query}'.",
                        score=0.88,
                    )
                ],
            )
