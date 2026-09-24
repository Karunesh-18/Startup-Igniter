"""Tests for the Zyte scraping/grounding layer: URL builders, the provider
wiring on top of the existing ZyteScraperTool, and ResearchManager merging.

ZYTE_ENABLED defaults to False (cost-safety), so ZyteScraperTool.scrape_url
falls back to a plain httpx GET by default — these tests mock that GET
directly rather than requiring real Zyte credentials, exercising the exact
code path a developer without a Zyte subscription hits.
"""

import httpx

from ai.shared.research.research_bundle import ResearchBundle
from ai.shared.research.research_manager import ResearchManager
from ai.shared.research.zyte_provider import ZyteResearchProvider
from ai.shared.research.zyte_urls import (
    build_duckduckgo_search_url,
    build_patent_search_urls,
    build_regulatory_search_url,
)


def test_build_patent_search_urls_covers_all_four_offices():
    targets = build_patent_search_urls("autonomous crop drone")
    sources = {t.source for t in targets}
    assert sources == {"google_patents", "espacenet", "wipo_patentscope", "india_ip"}
    for target in targets:
        assert target.url.startswith("https://")
        assert "autonomous" in target.url or "crop" in target.url or "%20" in target.url or "+" in target.url


def test_build_duckduckgo_search_url_encodes_query_and_site_filter():
    url = build_duckduckgo_search_url("fintech licensing", site=".gov.in")
    assert url.startswith("https://html.duckduckgo.com/html/?q=")
    assert "fintech" in url
    assert "site%3A.gov.in" in url or ".gov.in" in url


def test_build_regulatory_search_url_maps_region_to_tld():
    assert ".gov.in" in build_regulatory_search_url("fintech", region="india")
    assert ".gov.uk" in build_regulatory_search_url("healthtech", region="uk")
    assert ".gov" in build_regulatory_search_url("healthtech", region="unknown-region")


def test_search_patents_scrapes_all_sources_and_populates_bundle(httpx_mock):
    targets = build_patent_search_urls("autonomous crop drone")
    for target in targets:
        httpx_mock.add_response(url=target.url, html=f"<html><body>Prior art for {target.source}</body></html>")

    provider = ZyteResearchProvider()
    bundle = provider.search_patents("autonomous crop drone")

    assert isinstance(bundle, ResearchBundle)
    assert len(bundle.scraped_pages) == 4
    assert len(bundle.research_papers) == 4
    assert len(bundle.citations) == 4
    assert {p["source"] for p in bundle.research_papers} == {
        "google_patents", "espacenet", "wipo_patentscope", "india_ip"
    }


def test_search_patents_survives_one_source_raising(monkeypatch):
    """ZyteScraperTool's own safe-fallback mode never raises (it swallows
    network errors into a placeholder result) -- but the REAL Zyte-API path
    does raise StartupOSAIError on failure. _scrape_targets must survive that
    for one source without losing the other three."""
    from ai.tools.zyte_scraper import ScrapeResult
    from ai.shared.errors import StartupOSAIError

    targets = build_patent_search_urls("solar water pump")
    call_count = {"n": 0}

    def fake_scrape_url(self, url, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise StartupOSAIError("Zyte scrape failed with status code 503", details={"url": url})
        return ScrapeResult(url=url, status_code=200, clean_text="content", html_content="<html><body>content</body></html>")

    monkeypatch.setattr("ai.tools.zyte_scraper.ZyteScraperTool.scrape_url", fake_scrape_url)

    provider = ZyteResearchProvider()
    bundle = provider.search_patents("solar water pump")

    assert len(bundle.scraped_pages) == len(targets) - 1


def test_search_competitors_without_urls_returns_empty():
    """Zyte needs a URL to scrape a competitor's page — no URL, no guessing."""
    provider = ZyteResearchProvider()
    bundle = provider.search_competitors("AI startup idea", "SaaS")
    assert bundle.competitor_data == []
    assert bundle.scraped_pages == []


def test_search_competitors_with_explicit_urls_scrapes_and_buckets_correctly(httpx_mock):
    httpx_mock.add_response(url="https://competitor-a.example.com/pricing", html="<html><body>Pricing: $99/mo</body></html>")
    httpx_mock.add_response(url="https://competitor-b.example.com/pricing", html="<html><body>Pricing: $49/mo</body></html>")

    provider = ZyteResearchProvider()
    bundle = provider.search_competitors(
        "AI startup idea", "SaaS", urls=["https://competitor-a.example.com/pricing", "https://competitor-b.example.com/pricing"]
    )

    assert len(bundle.competitor_data) == 2
    assert bundle.research_papers == []  # relabeled out of the generic bucket


def test_search_market_and_news_are_out_of_scope_by_design():
    """Zyte doesn't guess at search-engine URLs -- that's Tavily/Exa's job."""
    provider = ZyteResearchProvider()
    assert provider.search_market("query") == ResearchBundle()
    assert provider.search_industry("industry") == ResearchBundle()
    assert provider.search_trends("category") == ResearchBundle()
    assert provider.search_funding("segment") == ResearchBundle()
    assert provider.search_news("keywords") == ResearchBundle()


def test_search_regulations_scrapes_gov_scoped_search(httpx_mock):
    url = build_regulatory_search_url("fintech", region="india")
    httpx_mock.add_response(url=url, html="<html><body>RBI guidelines for fintech</body></html>")

    provider = ZyteResearchProvider()
    bundle = provider.search_regulations("fintech", region="india")

    assert len(bundle.government_sources) == 1
    assert "RBI" in bundle.government_sources[0]["summary"]


def test_research_manager_merges_zyte_patent_results_into_patent_gather(httpx_mock):
    """ResearchManager.gather_patent_research should actually call the Zyte
    provider now, not just return an empty bundle unconditionally."""
    targets = build_patent_search_urls("crop disease detector")
    for target in targets:
        httpx_mock.add_response(url=target.url, html=f"<html><body>{target.source} result</body></html>")
    # ExaSearchTool falls back to ONE hardcoded mock result on any request
    # failure rather than raising or returning empty (its own pre-existing
    # design) -- register a real empty response so this test isolates Zyte's
    # contribution precisely.
    httpx_mock.add_response(url="https://api.exa.ai/search", json={"results": []})

    manager = ResearchManager()
    bundle = manager.gather_patent_research("crop disease detector")

    assert len(bundle.research_papers) == 4
    assert {p["source"] for p in bundle.research_papers} == {
        "google_patents", "espacenet", "wipo_patentscope", "india_ip"
    }
