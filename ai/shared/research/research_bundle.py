"""Pydantic model for structured external research data bundle."""

from typing import Any, Dict, List
from pydantic import BaseModel, Field


class ResearchBundle(BaseModel):
    """Reusable data container holding external research data retrieved across providers.

    Architecture Note:
        Version 1: Default instance with empty collections (LLM-only reasoning).
        Version 2: Populated by ResearchManager using Tavily, Exa, and Zyte APIs.
    """

    market_articles: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Market research articles, reports, and industry overview snippets.",
    )
    industry_reports: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Detailed industry sector reports, growth benchmarks, and lifecycle data.",
    )
    trend_reports: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Technology and consumer macro trend analysis documents.",
    )
    competitor_data: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Competitor profiling data, product offerings, and market positioning.",
    )
    research_papers: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Academic research papers, patent references, and technical publications.",
    )
    government_sources: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Regulatory filings, legal compliance docs, and official statistics.",
    )
    startup_sources: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Startup database profiles, funding history, and ecosystem data.",
    )
    news_articles: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Recent press releases, news articles, and market announcements.",
    )
    scraped_pages: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Raw structured content scraped from web pages via Zyte.",
    )
    citations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="External source URLs, titles, and reference metadata.",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution metadata including provider response times and query params.",
    )
