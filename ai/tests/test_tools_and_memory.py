"""Unit tests for AI tools (Tavily, Zyte) and Project Memory Manager."""

import unittest
from ai.shared.errors import MissingAPIKeyError
from ai.tools.tavily_search import TavilySearchTool, TavilySearchOutput
from ai.tools.zyte_scraper import ZyteScraperTool, strip_html_tags
from ai.memory.project_memory import (
    MemoryEntry,
    ProjectMemoryManager,
    cosine_similarity,
    generate_mock_embedding,
)


class TestToolsAndMemory(unittest.TestCase):
    """Test suite for Tavily, Zyte, and ProjectMemoryManager."""

    def test_strip_html_tags(self):
        """Test HTML tag cleaner utility."""
        raw_html = "<html><body><h1>Title</h1><p>Paragraph text.</p><script>var x = 1;</script></body></html>"
        clean = strip_html_tags(raw_html)
        self.assertNotIn("<html>", clean)
        self.assertNotIn("<script>", clean)
        self.assertIn("Title Paragraph text.", clean)

    def test_tavily_search_mock_mode(self):
        """Test Tavily search tool in mock mode."""
        tool = TavilySearchTool()
        result = tool.search(query="AI SaaS market size", mock_mode=True)
        self.assertIsInstance(result, TavilySearchOutput)
        self.assertEqual(result.query, "AI SaaS market size")
        self.assertTrue(len(result.results) > 0)
        self.assertIn("Mock Result", result.results[0].title)

    def test_tavily_missing_key_error(self):
        """Test raising MissingAPIKeyError when Tavily API key is missing."""
        tool = TavilySearchTool(api_key="")
        with self.assertRaises(MissingAPIKeyError):
            tool.search(query="healthtech market", mock_mode=False)

    def test_zyte_scraper_mock_mode(self):
        """Test Zyte web scraper tool in mock mode."""
        scraper = ZyteScraperTool()
        result = scraper.scrape_url("https://patents.google.com/patent/US12345", mock_mode=True)
        self.assertEqual(result.status_code, 200)
        self.assertIn("Mock patent document", result.clean_text)

    def test_cosine_similarity(self):
        """Test cosine similarity math utility."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        vec3 = [0.0, 1.0, 0.0]
        self.assertAlmostEqual(cosine_similarity(vec1, vec2), 1.0)
        self.assertAlmostEqual(cosine_similarity(vec1, vec3), 0.0)

    def test_generate_mock_embedding(self):
        """Test mock vector embedding generator."""
        vec = generate_mock_embedding("sample text", dimension=384)
        self.assertEqual(len(vec), 384)

    def test_project_memory_write_and_read(self):
        """Test writing memory entry and reading by key."""
        memory_mgr = ProjectMemoryManager(use_mock_store=True)
        proj_id = "proj-test-101"
        payload = {"problem": "High customer churn", "solution": "AI retention engine"}

        entry = memory_mgr.write_memory(
            project_id=proj_id,
            key="idea_summary",
            value=payload,
            source_phase="idea",
        )
        self.assertEqual(entry.key, "idea_summary")
        self.assertEqual(entry.source_phase, "idea")
        self.assertEqual(len(entry.embedding), 384)

        retrieved = memory_mgr.get_memory_by_key(proj_id, "idea_summary")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.value["problem"], "High customer churn")

    def test_project_memory_semantic_search(self):
        """Test semantic similarity retrieval over memory entries."""
        memory_mgr = ProjectMemoryManager(use_mock_store=True)
        proj_id = "proj-test-202"

        memory_mgr.write_memory(
            project_id=proj_id,
            key="swot_analysis",
            value={"strengths": ["Fast inference", "Low cost"]},
            source_phase="market_validation",
        )
        memory_mgr.write_memory(
            project_id=proj_id,
            key="legal_checklist",
            value={"items": ["Founder agreement", "NDA"]},
            source_phase="legal",
        )

        results = memory_mgr.query_memory(
            project_id=proj_id,
            query="swot_analysis strengths fast inference",
            top_k=2,
            threshold=0.0,
        )
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0].key, "swot_analysis")


if __name__ == "__main__":
    unittest.main()
