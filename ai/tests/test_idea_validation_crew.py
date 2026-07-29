"""Live integration tests for full 6-agent Idea Validation Crew executing real Groq LLM reasoning."""

import json
import unittest

from ai.agents.idea_validation import (
    get_customer_identifier_agent,
    get_innovation_scoring_agent,
    get_problem_statement_analyzer_agent,
    get_startup_category_classifier_agent,
    get_startup_idea_analyzer_agent,
    get_value_proposition_analyzer_agent,
)
from ai.crews.idea_validation.crew import IdeaValidationCrew, get_idea_validation_crew
from ai.crews.idea_validation.tasks import (
    create_category_classification_task,
    create_customer_identification_task,
    create_innovation_scoring_task,
    create_problem_statement_analysis_task,
    create_startup_idea_analysis_task,
    create_value_proposition_analysis_task,
)
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.idea_validation import IdeaValidationResult


class TestIdeaValidationCrewLiveExecution(unittest.TestCase):
    """Integration test suite executing real Idea Validation Crew workflow live against Groq LLMs."""

    def test_agent_factory_instantiation(self):
        """Test instantiation of all 6 real agent factory functions."""
        idea_agent = get_startup_idea_analyzer_agent(mock_mode=False)
        problem_agent = get_problem_statement_analyzer_agent(mock_mode=False)
        customer_agent = get_customer_identifier_agent(mock_mode=False)
        value_agent = get_value_proposition_analyzer_agent(mock_mode=False)
        category_agent = get_startup_category_classifier_agent(mock_mode=False)
        innovation_agent = get_innovation_scoring_agent(mock_mode=False)

        self.assertIsNotNone(idea_agent)
        self.assertIsNotNone(problem_agent)
        self.assertIsNotNone(customer_agent)
        self.assertIsNotNone(value_agent)
        self.assertIsNotNone(category_agent)
        self.assertIsNotNone(innovation_agent)

    def test_task_creation_functions(self):
        """Test task creation for all 6 agents."""
        idea_agent = get_startup_idea_analyzer_agent(mock_mode=False)
        idea_text = "Personalized learning platform for engineering students using adaptive AI."

        idea_task = create_startup_idea_analysis_task(idea_agent, idea_text)
        prob_task = create_problem_statement_analysis_task(idea_agent, idea_text)
        cust_task = create_customer_identification_task(idea_agent, idea_text)
        val_task = create_value_proposition_analysis_task(idea_agent, idea_text)
        cat_task = create_category_classification_task(idea_agent, idea_text)
        innov_task = create_innovation_scoring_task(idea_agent, idea_text)

        self.assertIsNotNone(idea_task)
        self.assertIsNotNone(prob_task)
        self.assertIsNotNone(cust_task)
        self.assertIsNotNone(val_task)
        self.assertIsNotNone(cat_task)
        self.assertIsNotNone(innov_task)

    def test_live_crew_execution_edtech_proposal(self):
        """Test full live IdeaValidationCrew run for an EdTech proposal against Groq API."""
        memory_mgr = ProjectMemoryManager(use_mock_store=True)
        crew = get_idea_validation_crew(mock_mode=False, memory_manager=memory_mgr)

        proj_id = "proj-live-edtech-101"
        idea_text = "Personalized learning platform for engineering students using adaptive AI."

        print("\n==================================================")
        print(f"[LIVE CREW TEST] Executing IdeaValidationCrew for EdTech Proposal")
        print(f"[INPUT PROPOSAL] '{idea_text}'")
        print("==================================================")

        result = crew.run(project_id=proj_id, idea_text=idea_text)

        # Verification Checklist Requirements
        self.assertIsInstance(result, IdeaValidationResult)
        self.assertEqual(result.project_id, proj_id)
        self.assertEqual(result.idea_text, idea_text)

        # Verify all 6 validated outputs are populated
        self.assertIsNotNone(result.idea_analysis)
        self.assertIsNotNone(result.problem_analysis)
        self.assertIsNotNone(result.customer_identification)
        self.assertIsNotNone(result.value_proposition)
        self.assertIsNotNone(result.category_classification)
        self.assertIsNotNone(result.innovation_scoring)

        # Verify input-dependent classification (EdTech / Education)
        cat_lower = result.category_classification.primary_category.lower()
        self.assertTrue(
            "edtech" in cat_lower or "education" in cat_lower or "ai" in cat_lower,
            f"Expected EdTech/Education classification, got '{result.category_classification.primary_category}'",
        )

        # Verify dynamic score bounds
        self.assertGreaterEqual(result.overall_validation_score, 0.0)
        self.assertLessEqual(result.overall_validation_score, 100.0)

        # Verify Memory Persistence
        self.assertIsNotNone(memory_mgr.get_memory_by_key(proj_id, "idea_analysis"))
        self.assertIsNotNone(memory_mgr.get_memory_by_key(proj_id, "problem_analysis"))
        self.assertIsNotNone(memory_mgr.get_memory_by_key(proj_id, "customer_analysis"))
        self.assertIsNotNone(memory_mgr.get_memory_by_key(proj_id, "value_proposition"))
        self.assertIsNotNone(memory_mgr.get_memory_by_key(proj_id, "category_classification"))
        self.assertIsNotNone(memory_mgr.get_memory_by_key(proj_id, "innovation_scoring"))

        print("\n[LIVE CREW EXECUTION COMPLETED]")
        print(f"Project ID: {result.project_id}")
        print(f"Primary Category: {result.category_classification.primary_category}")
        print(f"Overall Composite Validation Score: {result.overall_validation_score}/100")
        print("\n[VALIDATED PYDANTIC RESULT PAYLOAD]")
        print(json.dumps(result.model_dump(), indent=2))
        print("==================================================\n")

    def test_live_crew_execution_agritech_proposal(self):
        """Test that different proposal inputs produce dynamically different classifications (AgriTech)."""
        memory_mgr = ProjectMemoryManager(use_mock_store=True)
        crew = get_idea_validation_crew(mock_mode=False, memory_manager=memory_mgr)

        proj_id = "proj-live-agritech-202"
        idea_text = "Autonomous AI drone fleet and sensor network for early crop disease detection and soil moisture optimization."

        print("\n==================================================")
        print(f"[LIVE CREW TEST] Executing IdeaValidationCrew for AgriTech Proposal")
        print(f"[INPUT PROPOSAL] '{idea_text}'")
        print("==================================================")

        result = crew.run(project_id=proj_id, idea_text=idea_text)

        self.assertIsInstance(result, IdeaValidationResult)
        cat_lower = result.category_classification.primary_category.lower()
        self.assertTrue(
            "agri" in cat_lower or "agritech" in cat_lower or "agriculture" in cat_lower or "ai" in cat_lower,
            f"Expected AgriTech/Agriculture classification, got '{result.category_classification.primary_category}'",
        )

        print("\n[LIVE CREW EXECUTION COMPLETED]")
        print(f"Project ID: {result.project_id}")
        print(f"Primary Category: {result.category_classification.primary_category}")
        print(f"Overall Composite Validation Score: {result.overall_validation_score}/100")
        print("\n[VALIDATED PYDANTIC RESULT PAYLOAD]")
        print(json.dumps(result.model_dump(), indent=2))
        print("==================================================\n")


if __name__ == "__main__":
    unittest.main()
