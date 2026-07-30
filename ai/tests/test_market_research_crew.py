"""Integration test suite for the complete MarketResearchCrew running against live Groq LLM API."""

import time
import unittest

from ai.crews.market_research.crew import MarketResearchCrew
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.context import MarketResearchContext
from ai.schemas.customer_identifier import CustomerIdentification
from ai.schemas.idea_validation import IdeaValidationResult, StartupIdeaAnalysis
from ai.schemas.innovation_score import InnovationScoreAnalysis
from ai.schemas.market_research import MarketResearchResult
from ai.schemas.problem_statement import ProblemStatementAnalysis
from ai.schemas.startup_category import StartupCategoryClassification
from ai.schemas.value_proposition import ValuePropositionAnalysis
from ai.services.market_research_service import MarketResearchService


def create_sample_validation_result(
    project_id: str,
    idea_text: str,
    primary_category: str,
    problem_text: str,
    customer_text: str,
    value_text: str,
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
            primary_customers=[customer_text],
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
            unique_selling_proposition=f"Proprietary AI solution for {primary_category}.",
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
            reasoning=f"Classified as {primary_category} based on core domain.",
        ),
        innovation_scoring=InnovationScoreAnalysis(
            overall_innovation_score=85,
            innovation_level="High",
            novelty_score=88,
            technology_innovation_score=90,
            business_model_innovation_score=75,
            problem_originality_score=82,
            differentiation_score=85,
            strengths=["Unique AI application"],
            improvement_opportunities=["Expand market channels"],
            reasoning="Strong technological novelty and market fit.",
            confidence_score=90,
        ),
        overall_validation_score=88.5,
    )


class TestMarketResearchCrew(unittest.TestCase):
    """Live integration tests for the full MarketResearchCrew running against real Groq LLM API."""

    def tearDown(self):
        """Brief pause between live LLM tests to respect API rate limits."""
        time.sleep(4)

    def test_live_market_research_crew_execution(self):
        """Test end-to-end execution of MarketResearchCrew for EdTech proposal."""
        memory_mgr = ProjectMemoryManager(use_mock_store=True)
        proj_id = "proj-test-mr-crew-edtech-101"
        edtech_val = create_sample_validation_result(
            project_id=proj_id,
            idea_text="AI-powered interactive learning platform for engineering students.",
            primary_category="EdTech",
            problem_text="Engineering students suffer from rigid, non-interactive teaching methods.",
            customer_text="Engineering Colleges and Universities",
            value_text="Adaptive AI tutoring tailored to individual student learning speeds.",
        )

        service = MarketResearchService(memory_manager=memory_mgr)
        result = service.run_market_research(
            idea_validation=edtech_val,
            project_id=proj_id,
            mock_mode=False,  # LIVE GROQ LLM EXECUTION
        )

        # Schema & Instance Assertions
        self.assertIsInstance(result, MarketResearchResult)
        self.assertEqual(result.project_id, proj_id)

        # Verify All 7 Task Outputs in Result
        self.assertIsNotNone(result.market_research)
        self.assertIsNotNone(result.industry_analysis)
        self.assertIsNotNone(result.trend_analysis)
        self.assertIsNotNone(result.competitor_discovery)
        self.assertIsNotNone(result.competitor_comparison)
        self.assertIsNotNone(result.customer_persona)
        self.assertIsNotNone(result.tam_sam_som)

        # Verify Overall Summary & Calculated Scores
        self.assertTrue(len(result.overall_summary.strip()) > 0)
        self.assertGreaterEqual(result.overall_market_score, 0.0)
        self.assertLessEqual(result.overall_market_score, 100.0)
        self.assertGreaterEqual(result.confidence_score, 0.0)
        self.assertLessEqual(result.confidence_score, 1.0)

        # Memory Persistence Verification for Master Result & Sub-tasks
        saved_mem = memory_mgr.get_memory_by_key(proj_id, "market_research_result")
        self.assertIsNotNone(saved_mem)
        self.assertEqual(saved_mem.value["overall_market_score"], result.overall_market_score)

    def test_market_research_differentiation_across_domains(self):
        """Verify different domains produce dynamically distinct full reports (AgriTech vs FinTech)."""
        memory_mgr = ProjectMemoryManager(use_mock_store=True)

        agri_val = create_sample_validation_result(
            project_id="proj-mr-agri-303",
            idea_text="Autonomous AI drone fleet for crop disease detection.",
            primary_category="AgriTech",
            problem_text="Undetected crop blights destroying farm yields.",
            customer_text="Commercial Farm Operators",
            value_text="Early crop blight identification via aerial AI imaging.",
        )

        fin_val = create_sample_validation_result(
            project_id="proj-mr-fin-404",
            idea_text="AI micro-lending credit scoring engine for unbanked small businesses.",
            primary_category="FinTech",
            problem_text="Lack of traditional credit history blocking small business loans.",
            customer_text="Microfinance Institutions and Digital Neobanks",
            value_text="Alternative data AI credit underwriting platform.",
        )

        service = MarketResearchService(memory_manager=memory_mgr)

        agri_res = service.run_market_research(idea_validation=agri_val, mock_mode=False)
        fin_res = service.run_market_research(idea_validation=fin_val, mock_mode=False)

        # Domain differentiation check
        agri_text = (agri_res.overall_summary + " " + agri_res.tam_sam_som.tam_value).lower()
        fin_text = (fin_res.overall_summary + " " + fin_res.tam_sam_som.tam_value).lower()

        self.assertNotEqual(agri_text, fin_text)


if __name__ == "__main__":
    unittest.main()
