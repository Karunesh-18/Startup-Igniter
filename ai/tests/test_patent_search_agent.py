"""Integration test suite for PatentSearchAgent (Crew 3 Agent 1).

Executes against live LLMs (mock=False) to verify execution, Pydantic validation,
memory persistence, context container update, and distinct domain analysis outputs.
"""

import unittest
from ai.agents.research_patent.patent_search_agent import run_patent_search_agent
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.context import ResearchPatentContext
from ai.schemas.customer_identifier import CustomerIdentification
from ai.schemas.idea_validation import IdeaValidationResult, StartupIdeaAnalysis
from ai.schemas.innovation_score import InnovationScoreAnalysis
from ai.schemas.problem_statement import ProblemStatementAnalysis
from ai.schemas.research_patent import PatentAnalysis
from ai.schemas.startup_category import StartupCategoryClassification
from ai.schemas.value_proposition import ValuePropositionAnalysis


def create_mock_idea_validation(
    project_id: str,
    idea_text: str,
    category: str,
    problem: str,
    value_prop: str,
    score: int = 85,
) -> IdeaValidationResult:
    """Helper to construct a realistic IdeaValidationResult object for testing."""
    return IdeaValidationResult(
        project_id=project_id,
        idea_text=idea_text,
        idea_analysis=StartupIdeaAnalysis(
            summary=f"Summary for {idea_text}",
            startup_category=category,
            operational_pillars=["Core Platform", "Analytics Engine", "API Layer"],
            technical_feasibility_score=85,
            rationale="Feasible using modern AI frameworks and cloud services.",
            key_assumptions=["User adoption", "Dataset availability"],
            strengths=["Scalable cloud architecture", "High market demand"],
            weaknesses=["High initial development cost"],
        ),
        problem_analysis=ProblemStatementAnalysis(
            problem_statement=problem,
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
            industries=[category],
            pain_points=["Infrequency of feedback", "High costs"],
            customer_needs=["Automation", "Personalization"],
            motivations=["Cost reduction", "Efficiency gains"],
            adoption_barriers=["Integration complexity"],
            willingness_to_pay="high",
            confidence_score=90,
        ),
        value_proposition=ValuePropositionAnalysis(
            core_value_proposition=value_prop,
            unique_selling_proposition=f"Proprietary solution for {category}.",
            functional_benefits=["10x speedup in workflows", "Automated tracking"],
            emotional_benefits=["Confidence in decisions", "Reduced stress"],
            customer_outcomes=["30% operational cost savings"],
            differentiators=["Next-gen AI models"],
            value_clarity_score=90,
            customer_value_score=92,
            confidence_score=95,
        ),
        category_classification=StartupCategoryClassification(
            primary_category=category,
            secondary_categories=["AI", "SaaS"],
            industry=category,
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


class TestPatentSearchAgent(unittest.TestCase):
    """Integration test suite for PatentSearchAgent."""

    def setUp(self) -> None:
        """Set up fresh memory manager for each test."""
        self.memory_manager = ProjectMemoryManager(use_mock_store=True)

    def test_patent_search_ai_domain(self) -> None:
        """Test PatentSearchAgent for an AI Developer Tool startup proposal (mock=False)."""
        idea_text = (
            "An AI-powered micro-learning platform for software developers that generates "
            "personalized 5-minute interactive coding challenges based on real-time GitHub commits."
        )
        project_id = "proj-patent-ai-101"
        idea_val = create_mock_idea_validation(
            project_id=project_id,
            idea_text=idea_text,
            category="Artificial Intelligence",
            problem="Software developers struggle to find time for continuous skill development.",
            value_prop="Personalized 5-minute coding challenges delivered right in the developer's workflow.",
        )
        context = ResearchPatentContext(project_id=project_id, idea_validation=idea_val)

        result: PatentAnalysis = run_patent_search_agent(
            context=context,
            memory_manager=self.memory_manager,
            mock_mode=False,
        )

        # 1. Assertions on output structure & types
        self.assertIsInstance(result, PatentAnalysis)
        self.assertIsNotNone(result.existing_patent_summary)
        self.assertIsNotNone(result.patent_landscape)
        self.assertGreater(len(result.major_patent_holders), 0)
        self.assertGreater(len(result.related_technology_domains), 0)
        self.assertIn(result.patent_activity_level, ["Low", "Moderate", "High", "Very High"])
        self.assertGreater(len(result.white_space_opportunities), 0)
        self.assertIsNotNone(result.patentability_assessment)
        self.assertGreater(len(result.freedom_to_operate_observations), 0)
        self.assertGreater(len(result.innovation_opportunities), 0)
        self.assertGreater(len(result.patent_risks), 0)
        self.assertIsNotNone(result.novelty_assessment)
        self.assertGreaterEqual(result.confidence_score, 0.0)
        self.assertLessEqual(result.confidence_score, 1.0)

        # 2. Memory persistence check
        mem_data = self.memory_manager.get_memory_by_key(project_id, "patent_analysis")
        self.assertIsNotNone(mem_data)

        # 3. Context update check
        self.assertIsNotNone(context.patent_analysis)
        self.assertEqual(context.patent_analysis.patent_activity_level, result.patent_activity_level)

    def test_patent_search_healthcare_domain(self) -> None:
        """Test PatentSearchAgent for a Healthcare Remote Patient Monitoring startup (mock=False)."""
        idea_text = (
            "A tele-health remote patient monitoring platform utilizing wearable edge-AI sensors "
            "to detect cardiac arrhythmia in real time and notify cardiology specialists."
        )
        project_id = "proj-patent-health-202"
        idea_val = create_mock_idea_validation(
            project_id=project_id,
            idea_text=idea_text,
            category="Healthcare Technology (HealthTech)",
            problem="Delayed diagnosis of silent cardiac arrhythmia leads to severe patient complications.",
            value_prop="Real-time edge-AI cardiac telemetry with direct automated specialist notification.",
        )
        context = ResearchPatentContext(project_id=project_id, idea_validation=idea_val)

        result: PatentAnalysis = run_patent_search_agent(
            context=context,
            memory_manager=self.memory_manager,
            mock_mode=False,
        )

        self.assertIsInstance(result, PatentAnalysis)
        self.assertGreater(len(result.major_patent_holders), 0)
        self.assertGreater(len(result.white_space_opportunities), 0)
        self.assertGreaterEqual(result.confidence_score, 0.0)

    def test_patent_search_robotics_domain(self) -> None:
        """Test PatentSearchAgent for a Warehouse Robotics startup proposal (mock=False)."""
        idea_text = (
            "An autonomous warehouse sorting robot using spatial vision-language models "
            "to identify and sort non-standard parcels without pre-programmed templates."
        )
        project_id = "proj-patent-robot-303"
        idea_val = create_mock_idea_validation(
            project_id=project_id,
            idea_text=idea_text,
            category="Robotics & Industrial Automation",
            problem="Warehouse fulfillment centers struggle to automate sorting of irregularly shaped parcels.",
            value_prop="Zero-template spatial vision-language model parcel sorting for warehouse logistics.",
        )
        context = ResearchPatentContext(project_id=project_id, idea_validation=idea_val)

        result: PatentAnalysis = run_patent_search_agent(
            context=context,
            memory_manager=self.memory_manager,
            mock_mode=False,
        )

        self.assertIsInstance(result, PatentAnalysis)
        self.assertGreater(len(result.major_patent_holders), 0)
        self.assertGreater(len(result.freedom_to_operate_observations), 0)

    def test_patent_search_mock_mode(self) -> None:
        """Fast offline verification test for PatentSearchAgent in mock mode."""
        idea_text = "AI code generation micro-service."
        project_id = "proj-patent-mock-999"
        idea_val = create_mock_idea_validation(
            project_id=project_id,
            idea_text=idea_text,
            category="Developer Tools",
            problem="Slow coding speed.",
            value_prop="Instant AI code snippets.",
        )
        context = ResearchPatentContext(project_id=project_id, idea_validation=idea_val)

        result: PatentAnalysis = run_patent_search_agent(
            context=context,
            memory_manager=self.memory_manager,
            mock_mode=True,
        )

        self.assertIsInstance(result, PatentAnalysis)
        self.assertEqual(result.patent_activity_level, "High")
        self.assertEqual(result.confidence_score, 0.85)


if __name__ == "__main__":
    unittest.main()
