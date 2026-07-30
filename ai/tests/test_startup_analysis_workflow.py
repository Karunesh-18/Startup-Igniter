"""Integration test suite for StartupAnalysisWorkflow (Crew 1 + Crew 2).

Executes against live LLMs (mock=False) to verify multi-crew orchestration,
context transfer, memory persistence, single input entry point, and readiness score calculation.
"""

import unittest
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.startup_analysis import StartupAnalysisResult
from ai.workflows.startup_analysis_workflow import StartupAnalysisWorkflow


class TestStartupAnalysisWorkflow(unittest.TestCase):
    """Integration test suite for the complete Startup Analysis Workflow."""

    def setUp(self) -> None:
        """Set up fresh memory manager and workflow instance for each test."""
        self.memory_manager = ProjectMemoryManager(use_mock_store=True)
        self.workflow = StartupAnalysisWorkflow(memory_manager=self.memory_manager)

    def test_workflow_live_edtech_execution(self) -> None:
        """Test full end-to-end workflow execution for an EdTech startup proposal (mock=False)."""
        idea_text = (
            "An AI-powered micro-learning platform for software developers that generates "
            "personalized 5-minute interactive coding challenges based on real-time GitHub commits."
        )
        project_id = "proj-test-wf-edtech-1"

        result: StartupAnalysisResult = self.workflow.run_workflow(
            idea_text=idea_text,
            project_id=project_id,
            mock_mode=False,
        )

        # 1. Verify master output structure
        self.assertIsNotNone(result)
        self.assertEqual(result.project_id, project_id)
        self.assertEqual(result.startup_idea_text, idea_text)
        self.assertEqual(result.status, "success")
        self.assertIsNone(result.error_message)

        # 2. Verify Crew 1 (Idea Validation) execution & output
        val = result.idea_validation
        self.assertIsNotNone(val)
        self.assertGreaterEqual(val.overall_validation_score, 0.0)
        self.assertLessEqual(val.overall_validation_score, 100.0)
        self.assertIsNotNone(val.problem_analysis.problem_statement)
        self.assertGreater(len(val.customer_identification.primary_customers), 0)
        self.assertIsNotNone(val.value_proposition.core_value_proposition)
        self.assertIsNotNone(val.category_classification.primary_category)
        self.assertGreaterEqual(val.innovation_scoring.overall_innovation_score, 0)

        # 3. Verify Crew 2 (Market Research) execution & context transfer from Crew 1
        mr = result.market_research
        self.assertIsNotNone(mr)
        self.assertGreaterEqual(mr.overall_market_score, 0.0)
        self.assertLessEqual(mr.overall_market_score, 100.0)
        self.assertIsNotNone(mr.market_research.market_overview)
        self.assertIsNotNone(mr.industry_analysis.industry_name)
        self.assertGreater(len(mr.trend_analysis.technology_trends), 0)
        self.assertGreater(len(mr.competitor_discovery.direct_competitors), 0)
        self.assertGreaterEqual(mr.competitor_comparison.overall_competitive_score, 0.0)
        self.assertIsNotNone(mr.customer_persona.primary_persona.persona_name)
        self.assertIsNotNone(mr.tam_sam_som.tam_value)

        # 4. Verify Master Synthesis & Dynamic Readiness Score
        self.assertGreaterEqual(result.overall_readiness_score, 0.0)
        self.assertLessEqual(result.overall_readiness_score, 100.0)
        self.assertGreaterEqual(result.confidence_score, 0.0)
        self.assertLessEqual(result.confidence_score, 1.0)
        self.assertIn("STRATEGIC ANALYSIS SUMMARY", result.overall_summary)

        # 5. Verify Memory Persistence
        mem_val = self.memory_manager.get_memory_by_key(project_id, "idea_validation_result")
        self.assertIsNotNone(mem_val)

        mem_mr = self.memory_manager.get_memory_by_key(project_id, "market_research_result")
        self.assertIsNotNone(mem_mr)

        mem_wf = self.memory_manager.get_memory_by_key(project_id, "master_startup_analysis")
        self.assertIsNotNone(mem_wf)

    def test_workflow_mock_execution(self) -> None:
        """Test full workflow execution in mock mode (instant validation)."""
        idea_text = "AI-powered dev tool for micro-learning based on GitHub commits."
        result = self.workflow.run_workflow(
            idea_text=idea_text,
            project_id="proj-mock-1",
            mock_mode=True,
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.status, "success")
        self.assertGreaterEqual(result.overall_readiness_score, 0.0)

    def test_workflow_empty_input_validation(self) -> None:
        """Test that workflow rejects empty startup proposals immediately."""
        with self.assertRaises(ValueError):
            self.workflow.run_workflow(idea_text="   ")


if __name__ == "__main__":
    unittest.main()
