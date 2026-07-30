"""Integration test suite for CompetitorComparisonAgent running against live Groq LLM API."""

import unittest

from ai.agents.market_research.competitor_comparison_agent import (
    get_competitor_comparison_agent,
    run_competitor_comparison_agent,
)

from ai.memory.project_memory import ProjectMemoryManager
from ai.schemas.context import MarketResearchContext
from ai.schemas.customer_identifier import CustomerIdentification
from ai.schemas.idea_validation import IdeaValidationResult, StartupIdeaAnalysis
from ai.schemas.innovation_score import InnovationScoreAnalysis
from ai.schemas.market_research import CompetitorComparison, CompetitorDiscovery, CompetitorInfo
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


def create_sample_competitor_discovery(category: str) -> CompetitorDiscovery:
    """Helper to construct a realistic CompetitorDiscovery object for testing."""
    return CompetitorDiscovery(
        direct_competitors=[
            CompetitorInfo(
                name=f"Legacy{category}Leader",
                category="Direct",
                description=f"Dominant legacy suite in {category}.",
                target_market="Global Enterprise",
                primary_offering="Monolithic Software Suite",
            ),
            CompetitorInfo(
                name=f"Smart{category}Cloud",
                category="Direct",
                description=f"Cloud-first platform serving mid-market {category} clients.",
                target_market="Mid-market",
                primary_offering="Cloud Platform",
            ),
        ],
        indirect_competitors=[],
        emerging_competitors=[],
        market_leaders=[f"Legacy{category}Leader"],
        startup_challengers=[f"Smart{category}Cloud"],
        alternative_solutions=["Manual Spreadsheets", "In-house custom code"],
        competition_intensity="Moderate to High",
        major_competitor_count=4,
        confidence_score=0.92,
    )


class TestCompetitorComparisonAgent(unittest.TestCase):
    """Live integration tests for CompetitorComparisonAgent running against real Groq LLM API."""

    def test_agent_factory_instantiation(self):
        """Test instantiation of CompetitorComparisonAgent factory."""
        agent = get_competitor_comparison_agent(mock_mode=False)
        self.assertIsNotNone(agent)

    def test_live_competitor_comparison_edtech(self):
        """Test live CompetitorComparisonAgent execution for EdTech."""
        memory_mgr = ProjectMemoryManager(use_mock_store=True)
        proj_id = "proj-test-compcomp-edtech-101"
        edtech_val = create_sample_validation_result(
            project_id=proj_id,
            idea_text="AI-powered interactive learning platform for engineering students.",
            primary_category="EdTech",
            problem_text="Engineering students suffer from rigid, non-interactive teaching methods.",
            customer_text="Engineering Colleges and Universities",
            value_text="Adaptive AI tutoring tailored to individual student learning speeds.",
        )

        context = MarketResearchContext(
            project_id=proj_id,
            idea_validation=edtech_val,
            competitor_discovery=create_sample_competitor_discovery("EdTech"),
        )

        analysis = run_competitor_comparison_agent(
            context=context,
            memory_manager=memory_mgr,
            mock_mode=False,  # LIVE GROQ LLM EXECUTION
        )

        # Context Object Population Verification
        self.assertIsNotNone(context.competitor_comparison)
        self.assertEqual(context.competitor_comparison, analysis)

        # Schema & Type Assertions
        self.assertIsInstance(analysis, CompetitorComparison)
        self.assertTrue(len(analysis.startup_position.strip()) > 0)
        self.assertTrue(len(analysis.competitive_advantages) >= 1)
        self.assertTrue(len(analysis.competitive_weaknesses) >= 1)
        self.assertTrue(len(analysis.feature_comparison) >= 1)
        self.assertTrue(len(analysis.technology_comparison.strip()) > 0)
        self.assertTrue(len(analysis.customer_focus_comparison.strip()) > 0)
        self.assertTrue(len(analysis.pricing_strategy_comparison.strip()) > 0)
        self.assertTrue(len(analysis.innovation_comparison.strip()) > 0)
        self.assertTrue(len(analysis.market_positioning.strip()) > 0)
        self.assertTrue(len(analysis.competitive_gap) >= 1)
        self.assertTrue(len(analysis.differentiation_opportunities) >= 1)

        # Score Bounds Verification
        self.assertGreaterEqual(analysis.overall_competitive_score, 0.0)
        self.assertLessEqual(analysis.overall_competitive_score, 10.0)
        self.assertGreaterEqual(analysis.confidence_score, 0.0)
        self.assertLessEqual(analysis.confidence_score, 1.0)

        # Memory Persistence Verification
        saved_memory = memory_mgr.get_memory_by_key(proj_id, "competitor_comparison")
        self.assertIsNotNone(saved_memory)
        self.assertEqual(saved_memory.value["overall_competitive_score"], analysis.overall_competitive_score)

    def test_live_competitor_comparison_healthtech(self):
        """Test live CompetitorComparisonAgent execution for HealthTech."""
        memory_mgr = ProjectMemoryManager(use_mock_store=True)
        proj_id = "proj-test-compcomp-healthtech-202"
        health_val = create_sample_validation_result(
            project_id=proj_id,
            idea_text="AI early disease detection software analyzing clinical radiology images.",
            primary_category="HealthTech",
            problem_text="High diagnostic workload causing delays in critical disease detection.",
            customer_text="Hospitals and Diagnostic Labs",
            value_text="Real-time AI diagnostic decision support integrated into EHR systems.",
        )

        context = MarketResearchContext(
            project_id=proj_id,
            idea_validation=health_val,
            competitor_discovery=create_sample_competitor_discovery("HealthTech"),
        )

        analysis = run_competitor_comparison_agent(
            context=context,
            memory_manager=memory_mgr,
            mock_mode=False,
        )

        self.assertIsNotNone(context.competitor_comparison)
        self.assertIsInstance(analysis, CompetitorComparison)
        self.assertGreaterEqual(analysis.overall_competitive_score, 0.0)
        self.assertLessEqual(analysis.overall_competitive_score, 10.0)

    def test_comparison_differentiation_across_domains(self):
        """Verify different domains produce dynamically distinct competitor comparisons (AgriTech vs FinTech vs ClimateTech)."""
        memory_mgr = ProjectMemoryManager(use_mock_store=True)

        agri_val = create_sample_validation_result(
            project_id="proj-compcomp-agri-303",
            idea_text="Autonomous AI drone fleet for crop disease detection.",
            primary_category="AgriTech",
            problem_text="Undetected crop blights destroying farm yields.",
            customer_text="Commercial Farm Operators",
            value_text="Early crop blight identification via aerial AI imaging.",
        )

        fin_val = create_sample_validation_result(
            project_id="proj-compcomp-fin-404",
            idea_text="AI micro-lending credit scoring engine for unbanked small businesses.",
            primary_category="FinTech",
            problem_text="Lack of traditional credit history blocking small business loans.",
            customer_text="Microfinance Institutions and Digital Neobanks",
            value_text="Alternative data AI credit underwriting platform.",
        )

        climate_val = create_sample_validation_result(
            project_id="proj-compcomp-climate-505",
            idea_text="AI-driven carbon footprint accounting and offset credit verification engine for enterprises.",
            primary_category="ClimateTech",
            problem_text="Opaque carbon accounting and greenwashing risks for corporate ESG compliance.",
            customer_text="Enterprise Sustainability Officers",
            value_text="Automated satellite and ERP carbon credit audit platform.",
        )

        agri_context = MarketResearchContext(
            project_id="proj-compcomp-agri-303",
            idea_validation=agri_val,
            competitor_discovery=create_sample_competitor_discovery("AgriTech"),
        )
        fin_context = MarketResearchContext(
            project_id="proj-compcomp-fin-404",
            idea_validation=fin_val,
            competitor_discovery=create_sample_competitor_discovery("FinTech"),
        )
        climate_context = MarketResearchContext(
            project_id="proj-compcomp-climate-505",
            idea_validation=climate_val,
            competitor_discovery=create_sample_competitor_discovery("ClimateTech"),
        )

        agri_analysis = run_competitor_comparison_agent(context=agri_context, memory_manager=memory_mgr, mock_mode=False)
        fin_analysis = run_competitor_comparison_agent(context=fin_context, memory_manager=memory_mgr, mock_mode=False)
        climate_analysis = run_competitor_comparison_agent(context=climate_context, memory_manager=memory_mgr, mock_mode=False)

        self.assertIsNotNone(agri_context.competitor_comparison)
        self.assertIsNotNone(fin_context.competitor_comparison)
        self.assertIsNotNone(climate_context.competitor_comparison)

        agri_text = (agri_analysis.startup_position + " " + agri_analysis.technology_comparison).lower()
        fin_text = (fin_analysis.startup_position + " " + fin_analysis.technology_comparison).lower()
        climate_text = (climate_analysis.startup_position + " " + climate_analysis.technology_comparison).lower()

        # Domain differentiation check
        self.assertNotEqual(agri_text, fin_text)
        self.assertNotEqual(fin_text, climate_text)


if __name__ == "__main__":
    unittest.main()
