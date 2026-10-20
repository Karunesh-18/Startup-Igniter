"""Unit tests for Project Memory Manager."""

import unittest
from ai.memory.project_memory import (
    MemoryEntry,
    ProjectMemoryManager,
    cosine_similarity,
    generate_mock_embedding,
)


class TestToolsAndMemory(unittest.TestCase):
    """Test suite for ProjectMemoryManager."""

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
