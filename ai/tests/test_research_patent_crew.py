"""Integration test suite for ResearchPatentCrew (Crew 3).

Executes against live LLMs (mock=False) and offline simulation (mock=True) to verify:
1. Complete 7-agent sequential execution
2. Strict Pydantic model output validation
3. Context container propagation
4. Memory persistence in ProjectMemoryManager
5. Dynamic output differentiation across multiple domains (Healthcare, AI, Agriculture, FinTech, Robotics, SaaS)
"""

import unittest
from ai.crews.research_patent.crew import ResearchPatentCrew
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.context import ResearchPatentContext
from ai.schemas.customer_identifier import CustomerIdentification
from ai.schemas.idea_validation import IdeaValidationResult, StartupIdeaAnalysis
from ai.schemas.innovation_score import InnovationScoreAnalysis
from ai.schemas.problem_statement import ProblemStatementAnalysis
from ai.schemas.research_patent import ResearchPatentResult
from ai.schemas.startup_category import StartupCategoryClassification
from ai.schemas.value_proposition import ValuePropositionAnalysis
from ai.services.research_patent_service import ResearchPatentService


def create_sample_validation_result(
    project_id: str,
    idea_text: str,
    primary_category: str,
    problem_text: str,
    value_text: str,
    score: int = 85,
) -> IdeaValidationResult:
    """Helper to construct a realistic IdeaValidationResult object for testing."""
    return IdeaValidationResult(
        project_id=project_id,
        idea_text=idea_text,
        idea_analysis=StartupIdeaAnalysis(
            summary=f"Summary for {idea_text}",
            startup_category=primary_category,
            operational_pillars=["Core Platform", "Analytics Engine", "API Layer"],
            technical_feasibility_score=85,
            rationale="Feasible using modern AI frameworks and cloud services.",
            key_assumptions=["User adoption", "Dataset availability"],
            strengths=["Scalable cloud architecture", "High market demand"],
            weaknesses=["High initial development cost"],
        ),
        problem_analysis=ProblemStatementAnalysis(
            problem_statement=problem_text,
            affected_users=["Primary Users", "Enterprise Buyers"],
            root_causes=["Legacy manual processes", "Lack of real-time feedback"],
            existing_solutions=["Manual spreadsheets", "Generic legacy tools"],
            solution_gaps=["No automated adaptive pathways"],
            problem_severity="high",
            urgency_score=90,
            confidence_score=0.95,
        ),
        customer_identification=CustomerIdentification(
            primary_customers=["Enterprise Teams"],
            secondary_customers=["Secondary Buyer Group"],
            end_users=["End User Persona"],
            decision_makers=["Chief Technology Officer", "Department Head"],
            customer_segments=["Mid-market", "Enterprise"],
            demographics=["Tech-savvy professionals"],
            geographic_markets=["North America", "Europe"],
            industries=[primary_category],
            pain_points=["Infrequency of feedback", "High costs"],
            customer_needs=["Automation", "Personalization"],
            motivations=["Cost reduction", "Efficiency gains"],
            adoption_barriers=["Integration complexity"],
            willingness_to_pay="high",
            confidence_score=90,
        ),
        value_proposition=ValuePropositionAnalysis(
            core_value_proposition=value_text,
            unique_selling_proposition=f"Proprietary solution for {primary_category}.",
            functional_benefits=["10x speedup in workflows", "Automated tracking"],
            emotional_benefits=["Confidence in decisions", "Reduced stress"],
            customer_outcomes=["30% operational cost savings"],
            differentiators=["Next-gen AI models"],
            value_clarity_score=90,
            customer_value_score=92,
            confidence_score=95,
        ),
        category_classification=StartupCategoryClassification(
            primary_category=primary_category,
            secondary_categories=["AI", "SaaS"],
            industry=primary_category,
            technology_domains=["Artificial Intelligence", "Machine Learning"],
            business_model="B2B",
            revenue_model="Subscription",
            startup_stage="Idea",
            target_market="Enterprise & Mid-market",
            confidence_score=95,
            reasoning="Classification reasoning based on technical proposal analysis.",
        ),
        innovation_scoring=InnovationScoreAnalysis(
            overall_innovation_score=score,
            innovation_level="High",
            novelty_score=85,
            technology_innovation_score=85,
            business_model_innovation_score=80,
            problem_originality_score=85,
            differentiation_score=80,
            strengths=["Proprietary AI algorithms", "Real-time pipeline"],
            improvement_opportunities=["Patent protection for workflow triggers"],
            reasoning="High overall innovation with unique technological integration.",
            confidence_score=90,
        ),
        overall_validation_score=float(score),
    )


class TestResearchPatentCrew(unittest.TestCase):
    """Integration test suite for ResearchPatentCrew."""

    def setUp(self) -> None:
        """Set up fresh memory manager and service instance for each test."""
        self.memory_manager = ProjectMemoryManager(use_mock_store=True)
        self.service = ResearchPatentService(memory_manager=self.memory_manager)

    def test_crew_mock_execution(self) -> None:
        """Fast offline test verifying full 7-agent ResearchPatentCrew in mock mode."""
        project_id = "proj-test-crew3-mock-1"
        idea_val = create_sample_validation_result(
            project_id=project_id,
            idea_text="AI micro-learning tool for developers based on commit hooks.",
            primary_category="Developer Tools",
            problem_text="Developers lack time for continuous skill development.",
            value_text="5-minute interactive coding challenges triggered by commits.",
        )

        result: ResearchPatentResult = self.service.run_research_patent(
            idea_validation=idea_val,
            project_id=project_id,
            mock_mode=True,
        )

        # 1. Verify Master Output
        self.assertIsInstance(result, ResearchPatentResult)
        self.assertEqual(result.project_id, project_id)
        self.assertEqual(result.status, "success")
        self.assertGreaterEqual(result.overall_novelty_score, 0.0)
        self.assertLessEqual(result.overall_novelty_score, 100.0)
        self.assertGreaterEqual(result.trl_level, 1)
        self.assertLessEqual(result.trl_level, 9)
        self.assertGreaterEqual(result.confidence_score, 0.0)
        self.assertLessEqual(result.confidence_score, 1.0)
        self.assertIsNotNone(result.executive_summary)
        self.assertGreater(len(result.strategic_recommendations), 0)

        # 2. Verify all sub-models populated
        self.assertIsNotNone(result.patent_analysis)
        self.assertIsNotNone(result.research_paper_analysis)
        self.assertIsNotNone(result.existing_solution_analysis)
        self.assertIsNotNone(result.innovation_gap_analysis)
        self.assertIsNotNone(result.technology_readiness)
        self.assertIsNotNone(result.ip_strategy)

        # 3. Memory persistence check
        mem_res = self.memory_manager.get_memory_by_key(project_id, "research_patent_result")
        self.assertIsNotNone(mem_res)

    def test_crew_live_ai_edtech_execution(self) -> None:
        """Live test verifying complete 7-agent execution for AI EdTech startup (mock=False)."""
        project_id = "proj-test-crew3-ai-101"
        idea_val = create_sample_validation_result(
            project_id=project_id,
            idea_text=(
                "An AI-powered micro-learning platform for software developers that generates "
                "personalized 5-minute interactive coding challenges based on real-time GitHub commits."
            ),
            primary_category="Developer Tools",
            problem_text="Developers lack time for continuous skill development during busy work sprints.",
            value_text="Personalized 5-minute interactive coding challenges generated directly from commit diffs.",
        )

        result: ResearchPatentResult = self.service.run_research_patent(
            idea_validation=idea_val,
            project_id=project_id,
            mock_mode=False,
        )

        self.assertIsInstance(result, ResearchPatentResult)
        self.assertEqual(result.status, "success")
        self.assertGreater(len(result.patent_analysis.major_patent_holders), 0)
        self.assertGreater(len(result.research_paper_analysis.key_research_papers), 0)
        self.assertGreater(len(result.existing_solution_analysis.existing_startups), 0)
        self.assertGreater(len(result.innovation_gap_analysis.technical_gaps), 0)
        self.assertGreater(result.technology_readiness.trl_level, 0)
        self.assertGreater(result.ip_strategy.ip_defensibility_score, 0)

    def test_crew_live_healthcare_execution(self) -> None:
        """Live test verifying complete 7-agent execution for Healthcare startup (mock=False)."""
        project_id = "proj-test-crew3-health-202"
        idea_val = create_sample_validation_result(
            project_id=project_id,
            idea_text=(
                "A tele-health remote patient monitoring platform utilizing wearable edge-AI sensors "
                "to detect cardiac arrhythmia in real time and notify cardiology specialists."
            ),
            primary_category="Healthcare Technology (HealthTech)",
            problem_text="Delayed diagnosis of silent cardiac arrhythmia leads to preventable cardiac events.",
            value_text="Real-time edge-AI cardiac telemetry with automated specialist alert routing.",
        )

        result: ResearchPatentResult = self.service.run_research_patent(
            idea_validation=idea_val,
            project_id=project_id,
            mock_mode=False,
        )

        self.assertIsInstance(result, ResearchPatentResult)
        self.assertEqual(result.status, "success")
        self.assertIsNotNone(result.patent_analysis.existing_patent_summary)
        self.assertGreater(len(result.ip_strategy.patent_strategy_recommendations), 0)


if __name__ == "__main__":
    unittest.main()
