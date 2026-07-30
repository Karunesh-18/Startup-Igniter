"""Unit test suite for shared external research integration module."""

import unittest
from ai.schemas.context import MarketResearchContext
from ai.shared.research.exa_provider import ExaResearchProvider
from ai.shared.research.research_bundle import ResearchBundle
from ai.shared.research.research_manager import ResearchManager
from ai.shared.research.research_provider import BaseResearchProvider
from ai.shared.research.tavily_provider import TavilyResearchProvider
from ai.shared.research.zyte_provider import ZyteResearchProvider


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

    def test_provider_subclasses_return_empty_bundle(self) -> None:
        """Test that provider subclasses (Tavily, Exa, Zyte) return empty bundles."""
        tavily = TavilyResearchProvider()
        exa = ExaResearchProvider()
        zyte = ZyteResearchProvider()

        self.assertIsInstance(tavily.search_market("test"), ResearchBundle)
        self.assertIsInstance(exa.search_industry("test"), ResearchBundle)
        self.assertIsInstance(zyte.search_competitors("test", "cat"), ResearchBundle)

    def test_research_manager_version_1_behavior(self) -> None:
        """Test that ResearchManager returns empty bundles without API calls."""
        mgr = ResearchManager()
        market_bundle = mgr.gather_market_research("AI EdTech platform")
        comp_bundle = mgr.gather_competitor_research("AI EdTech platform", "EdTech")
        patent_bundle = mgr.gather_patent_research("AI code generation")
        reg_bundle = mgr.gather_regulatory_research("Healthcare AI")

        self.assertIsInstance(market_bundle, ResearchBundle)
        self.assertIsInstance(comp_bundle, ResearchBundle)
        self.assertIsInstance(patent_bundle, ResearchBundle)
        self.assertIsInstance(reg_bundle, ResearchBundle)

        self.assertEqual(len(market_bundle.market_articles), 0)

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
