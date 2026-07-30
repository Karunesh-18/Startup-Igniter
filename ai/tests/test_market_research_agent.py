"""Integration test suite for MarketResearchAgent running against live Groq LLM API."""

import json
import unittest

from ai.agents.market_research.market_research_agent import (
    get_market_research_agent,
    run_market_research_agent,
    validate_agent_output,
)
from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.context import MarketResearchContext
from ai.schemas.customer_identifier import CustomerIdentification
from ai.schemas.idea_validation import IdeaValidationResult, StartupIdeaAnalysis
from ai.schemas.innovation_score import InnovationScoreAnalysis
from ai.schemas.market_research import MarketResearchAnalysis
from ai.schemas.problem_statement import ProblemStatementAnalysis
from ai.schemas.startup_category import StartupCategoryClassification
from ai.schemas.value_proposition import ValuePropositionAnalysis


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


class TestMarketResearchAgent(unittest.TestCase):
    """Live integration tests for MarketResearchAgent using real Groq LLM API."""

    def test_agent_factory_instantiation(self):
        """Test instantiation of MarketResearchAgent factory."""
        agent = get_market_research_agent(mock_mode=False)
        self.assertIsNotNone(agent)

    def test_live_market_research_edtech(self):
        """Test live MarketResearchAgent execution for an EdTech proposal."""
        memory_mgr = ProjectMemoryManager(use_mock_store=True)
        proj_id = "proj-test-mr-edtech-101"
        edtech_result = create_sample_validation_result(
            project_id=proj_id,
            idea_text="AI-powered interactive learning platform for engineering students.",
            primary_category="EdTech",
            problem_text="Engineering students suffer from rigid, non-interactive teaching methods.",
            customer_text="Engineering Colleges and Universities",
            value_text="Adaptive AI tutoring tailored to individual student learning speeds.",
        )

        context = MarketResearchContext(
            project_id=proj_id,
            idea_validation=edtech_result,
        )

        analysis = run_market_research_agent(
            context=context,
            memory_manager=memory_mgr,
            mock_mode=False,  # LIVE GROQ LLM EXECUTION
        )

        # Context Object Population Verification
        self.assertIsNotNone(context.market_research)
        self.assertEqual(context.market_research, analysis)

        # Schema & Type Assertions
        self.assertIsInstance(analysis, MarketResearchAnalysis)
        self.assertTrue(len(analysis.market_overview.strip()) > 0)
        self.assertTrue(len(analysis.industry_overview.strip()) > 0)
        self.assertIsNotNone(analysis.market_stage)
        self.assertIsNotNone(analysis.market_maturity)
        self.assertTrue(len(analysis.market_opportunities) >= 1)
        self.assertTrue(len(analysis.market_challenges) >= 1)
        self.assertTrue(len(analysis.growth_drivers) >= 1)
        self.assertTrue(len(analysis.market_risks) >= 1)
        self.assertTrue(len(analysis.future_outlook.strip()) > 0)

        # Confidence Score Range Assertion (0.0 to 1.0)
        self.assertGreaterEqual(analysis.confidence_score, 0.0)
        self.assertLessEqual(analysis.confidence_score, 1.0)

        # Memory Persistence Verification
        saved_memory = memory_mgr.get_memory_by_key(proj_id, "market_research")
        self.assertIsNotNone(saved_memory)
        self.assertEqual(saved_memory.value["market_stage"], analysis.market_stage)

    def test_live_market_research_healthtech(self):
        """Test live MarketResearchAgent execution for a HealthTech proposal."""
        memory_mgr = ProjectMemoryManager(use_mock_store=True)
        proj_id = "proj-test-mr-healthtech-202"
        health_result = create_sample_validation_result(
            project_id=proj_id,
            idea_text="AI early disease detection software analyzing clinical radiology images.",
            primary_category="HealthTech",
            problem_text="High diagnostic workload causing delays in critical disease detection.",
            customer_text="Hospitals and Diagnostic Labs",
            value_text="Real-time AI diagnostic decision support integrated into EHR systems.",
        )

        context = MarketResearchContext(
            project_id=proj_id,
            idea_validation=health_result,
        )

        analysis = run_market_research_agent(
            context=context,
            memory_manager=memory_mgr,
            mock_mode=False,  # LIVE GROQ LLM EXECUTION
        )

        self.assertIsNotNone(context.market_research)
        self.assertIsInstance(analysis, MarketResearchAnalysis)
        self.assertGreaterEqual(analysis.confidence_score, 0.0)
        self.assertLessEqual(analysis.confidence_score, 1.0)

        # Category differentiation check
        overview_lower = (analysis.market_overview + " " + analysis.industry_overview).lower()
        self.assertTrue(
            "health" in overview_lower or "med" in overview_lower or "care" in overview_lower or "diagnostic" in overview_lower,
            f"Expected HealthTech context, got overview: '{analysis.market_overview}'",
        )

    def test_category_differentiation_agritech_vs_fintech(self):
        """Verify different startup categories produce dynamically distinct market research analyses."""
        memory_mgr = ProjectMemoryManager(use_mock_store=True)

        agri_result = create_sample_validation_result(
            project_id="proj-mr-agri-303",
            idea_text="Autonomous AI drone fleet for crop disease detection.",
            primary_category="AgriTech",
            problem_text="Undetected crop blights destroying farm yields.",
            customer_text="Commercial Farm Operators",
            value_text="Early crop blight identification via aerial AI imaging.",
        )

        fin_result = create_sample_validation_result(
            project_id="proj-mr-fin-404",
            idea_text="AI micro-lending credit scoring engine for unbanked small businesses.",
            primary_category="FinTech",
            problem_text="Lack of traditional credit history blocking small business loans.",
            customer_text="Microfinance Institutions and Digital Neobanks",
            value_text="Alternative data AI credit underwriting platform.",
        )

        agri_context = MarketResearchContext(
            project_id="proj-mr-agri-303",
            idea_validation=agri_result,
        )
        fin_context = MarketResearchContext(
            project_id="proj-mr-fin-404",
            idea_validation=fin_result,
        )

        agri_analysis = run_market_research_agent(
            context=agri_context,
            memory_manager=memory_mgr,
            mock_mode=False,
        )

        fin_analysis = run_market_research_agent(
            context=fin_context,
            memory_manager=memory_mgr,
            mock_mode=False,
        )

        self.assertIsNotNone(agri_context.market_research)
        self.assertIsNotNone(fin_context.market_research)
        self.assertIsInstance(agri_analysis, MarketResearchAnalysis)
        self.assertIsInstance(fin_analysis, MarketResearchAnalysis)

        agri_text = (agri_analysis.market_overview + " " + agri_analysis.industry_overview).lower()
        fin_text = (fin_analysis.market_overview + " " + fin_analysis.industry_overview).lower()

        # Verify distinct category-specific terminology
        self.assertTrue(
            "agri" in agri_text or "farm" in agri_text or "crop" in agri_text or "food" in agri_text,
            f"Expected AgriTech context in agri_analysis, got: {agri_text}",
        )
        self.assertTrue(
            "fin" in fin_text or "bank" in fin_text or "credit" in fin_text or "loan" in fin_text or "pay" in fin_text,
            f"Expected FinTech context in fin_analysis, got: {fin_text}",
        )


if __name__ == "__main__":
    unittest.main()
