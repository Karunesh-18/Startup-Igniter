"""Unit test suite for shared external research integration module."""

import unittest
from unittest.mock import patch

from ai.schemas.context import MarketResearchContext
from ai.shared.research import web_provider
from ai.shared.research.prompt_formatting import format_research_bundle_for_prompt
from ai.shared.research.research_bundle import ResearchBundle
from ai.shared.research.research_manager import ResearchManager
from ai.shared.research.research_provider import BaseResearchProvider
from ai.shared.research.web_provider import WebResearchProvider


class DummyUnimplementedProvider(BaseResearchProvider):
    """Concrete subclass for testing abstract interface NotImplementedError raising."""

    def search_market(self, query: str, **kwargs: str) -> ResearchBundle:
        return super().search_market(query, **kwargs)

    def search_industry(self, industry_name: str, **kwargs: str) -> ResearchBundle:
        return super().search_industry(industry_name, **kwargs)

    def search_competitors(self, startup_idea: str, category: str, **kwargs: str) -> ResearchBundle:
        return super().search_competitors(startup_idea, category, **kwargs)

    def search_trends(self, category: str, **kwargs: str) -> ResearchBundle:
        return super().search_trends(category, **kwargs)

    def search_patents(self, technology_concept: str, **kwargs: str) -> ResearchBundle:
        return super().search_patents(technology_concept, **kwargs)

    def search_regulations(self, industry: str, region: str = "global", **kwargs: str) -> ResearchBundle:
        return super().search_regulations(industry, region, **kwargs)

    def search_funding(self, market_segment: str, **kwargs: str) -> ResearchBundle:
        return super().search_funding(market_segment, **kwargs)

    def search_news(self, keywords: str, **kwargs: str) -> ResearchBundle:
        return super().search_news(keywords, **kwargs)


class TestResearchModule(unittest.TestCase):
    """Test suite for research architecture extension points."""

    def test_research_bundle_defaults(self) -> None:
        """Test that ResearchBundle initializes with default empty collections."""
        bundle = ResearchBundle()
        self.assertEqual(bundle.market_articles, [])
        self.assertEqual(bundle.industry_reports, [])
        self.assertEqual(bundle.trend_reports, [])
        self.assertEqual(bundle.competitor_data, [])
        self.assertEqual(bundle.research_papers, [])
        self.assertEqual(bundle.government_sources, [])
        self.assertEqual(bundle.startup_sources, [])
        self.assertEqual(bundle.news_articles, [])
        self.assertEqual(bundle.scraped_pages, [])
        self.assertEqual(bundle.citations, [])
        self.assertEqual(bundle.metadata, {})

    def test_base_provider_abstract_raises(self) -> None:
        """Test that base interface abstract methods raise NotImplementedError."""
        dummy = DummyUnimplementedProvider()
        with self.assertRaises(NotImplementedError):
            dummy.search_market("query")
        with self.assertRaises(NotImplementedError):
            dummy.search_industry("EdTech")
        with self.assertRaises(NotImplementedError):
            dummy.search_competitors("Idea", "Category")

    def test_web_search_extracts_pages_and_falls_back_to_snippet(self) -> None:
        """_search fetches each hit; a page that fails extraction keeps its search snippet."""
        hits = [
            {"title": "A", "href": "https://a.example", "body": "snippet a"},
            {"title": "B", "href": "https://b.example", "body": "snippet b"},
            {"title": "no url", "href": "", "body": "dropped"},
        ]
        web_provider._search.cache_clear()
        with patch.object(web_provider, "DDGS") as ddgs, patch.object(
            web_provider, "_fetch_text", side_effect=lambda _c, url: "full text a" if "a." in url else ""
        ):
            ddgs.return_value.text.return_value = hits
            entries = web_provider._search("q-extract-test")
        web_provider._search.cache_clear()

        self.assertEqual([e["content"] for e in entries], ["full text a", "snippet b"])

    def test_research_manager_buckets_and_formats(self) -> None:
        """Each gather_* lands results in its own bucket, citations are filled,
        and the prompt formatter picks them up. Network is stubbed."""
        entry = ({"title": "T", "url": "https://example.com/t", "content": "c", "snippet": "c", "provider": "web"},)
        mgr = ResearchManager()
        with patch.object(web_provider, "_search", return_value=entry):
            market = mgr.gather_market_research("AI EdTech platform", category="EdTech")
            comp = mgr.gather_competitor_research("AI EdTech platform", "EdTech")
            reg = mgr.gather_regulatory_research("Healthcare AI", region="india")
            funding = mgr.gather_funding_research("EdTech")
            trend = mgr.gather_trend_research("EdTech")
            tech = mgr.gather_tech_research("AI tutor")
            news = mgr.gather_news_research("EdTech India")
            patent = mgr.gather_patent_research("adaptive tutoring")

        self.assertEqual(len(market.market_articles), 1)
        self.assertEqual(len(comp.competitor_data), 1)
        self.assertEqual(len(reg.government_sources), 1)
        self.assertIn("site:.gov.in", reg.metadata["web_query"])
        self.assertEqual(len(funding.startup_sources), 1)
        self.assertEqual(len(trend.trend_reports), 1)
        self.assertEqual(len(tech.research_papers), 1)
        self.assertEqual(len(news.news_articles), 1)
        self.assertIn("site:patents.google.com", patent.metadata["web_query"])
        self.assertEqual(market.citations[0]["url"], "https://example.com/t")
        block, has_grounding = format_research_bundle_for_prompt(market.merge(comp))
        self.assertTrue(has_grounding)
        self.assertIn("https://example.com/t", block)

    def test_research_manager_never_raises(self) -> None:
        """A failing search degrades to an empty bundle instead of raising."""
        mgr = ResearchManager()
        with patch.object(web_provider, "_search", side_effect=RuntimeError("blocked")):
            bundle = mgr.gather_news_research("anything")
        self.assertEqual(bundle.news_articles, [])
        self.assertIsInstance(WebResearchProvider().search_market("x", mock_mode=True), ResearchBundle)

    def test_context_research_bundle_placeholder(self) -> None:
        """Test that MarketResearchContext accepts optional research_bundle defaulting to None."""
        from ai.schemas.idea_validation import IdeaValidationResult
        # Dummy validation result
        val = IdeaValidationResult.model_construct(project_id="p1", idea_text="test")
        ctx_default = MarketResearchContext(project_id="p1", idea_validation=val)
        self.assertIsNone(ctx_default.research_bundle)

        bundle = ResearchBundle()
        ctx_populated = MarketResearchContext(project_id="p1", idea_validation=val, research_bundle=bundle)
        self.assertIsNotNone(ctx_populated.research_bundle)


if __name__ == "__main__":
    unittest.main()
