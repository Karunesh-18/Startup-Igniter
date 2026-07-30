import pytest

from ai.services.research_service import get_research_service
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


@pytest.mark.asyncio
async def test_tavily_search_mock():
    tool = TavilySearchTool()
    res = tool.search("FinTech SaaS startups", mock_mode=True)
    assert res.query == "FinTech SaaS startups"
    assert len(res.results) > 0


@pytest.mark.asyncio
async def test_exa_search_mock():
    tool = ExaSearchTool()
    res = tool.search("AI diagnostic imaging", mock_mode=True)
    assert res.query == "AI diagnostic imaging"
    assert len(res.results) > 0


@pytest.mark.asyncio
async def test_semantic_scholar_mock():
    tool = SemanticScholarTool()
    res = tool.search_papers("Deep Learning NLP", mock_mode=True)
    assert len(res.papers) > 0


@pytest.mark.asyncio
async def test_openalex_mock():
    tool = OpenAlexTool()
    res = tool.search_works("Generative AI market analysis", mock_mode=True)
    assert len(res.works) > 0


@pytest.mark.asyncio
async def test_patents_view_mock():
    tool = PatentsViewTool()
    res = tool.search_patents("Autonomous Vehicle Sensors", mock_mode=True)
    assert len(res.patents) > 0


@pytest.mark.asyncio
async def test_hf_embeddings_mock():
    tool = HFEmbeddingsTool()
    vec = tool.embed_text("Startup OS project memory embedding", mock_mode=True)
    assert isinstance(vec, list)
    assert len(vec) == 384


@pytest.mark.asyncio
async def test_zyte_scraper_safe_fallback():
    tool = ZyteScraperTool()
    # ZYTE_ENABLED is False by default, so it uses httpx safe fallback
    res = tool.scrape_url("https://example.com")
    assert res.status_code == 200
    assert "Example Domain" in res.clean_text or "Content summary" in res.clean_text or "example" in res.clean_text.lower()


@pytest.mark.asyncio
async def test_unified_research_service():
    service = get_research_service(mock_mode=True)

    web_data = service.search_web("Autonomous Drones for Agriculture")
    assert "results" in web_data

    lit_data = service.search_literature("Precision Agriculture AI")
    assert "semantic_scholar" in lit_data
    assert "openalex" in lit_data

    pat_data = service.search_prior_art("Agricultural Sensor Systems")
    assert "patents" in pat_data

    emb = service.get_embedding("Agriculture Tech Vector")
    assert len(emb) == 384
