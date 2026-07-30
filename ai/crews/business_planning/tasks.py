"""Tasks definition for Business Planning Crew."""

from typing import Any, Dict, Optional
from ai.schemas.business_plan import BusinessPlanResult, FinancialModel, LeanCanvas
from ai.shared.logger import ai_logger


def create_lean_canvas_task(
    project_id: str,
    idea_text: str,
    mock_mode: bool = True,
) -> LeanCanvas:
    """Generate Lean Canvas 9-box business model components."""
    ai_logger.info(f"Executing Lean Canvas generation task for project '{project_id}'")

    return LeanCanvas(
        problem="High cost of manual startup validation; fragmented market research tools; legal template ambiguity.",
        solution="AI-powered co-founder platform; automated 6-agent validation pipeline; interactive Lean Canvas generation.",
        unique_value_proposition="Autonomous multi-agent OS that turns raw startup ideas into investor-ready validation reports.",
        unfair_advantage="Proprietary CrewAI orchestration with persistent project memory and real-time research API integration.",
        customer_segments="Early-stage tech founders, student entrepreneurs, incubator managers, and venture builders.",
        key_metrics=["Monthly Active Projects", "Validation Report Downloads", "Founder Retention Rate", "Customer Lifetime Value"],
        channels=["Direct Founder Communities", "Incubator Partnerships", "ProductHunt Launches", "SEO Content Marketing"],
        cost_structure=["LLM API Token Expenses (Groq/OpenRouter)", "Hosting & Server Infrastructure (GCP/Vercel)", "Data Provider Fees"],
        revenue_streams=["Subscription Tiers ($29-$99/mo)", "Per-Report Validation Credits", "Enterprise Incubator Licenses"],
    )


def create_financial_model_task(
    project_id: str,
    mock_mode: bool = True,
) -> FinancialModel:
    """Formulate pricing strategy and financial projections."""
    return FinancialModel(
        pricing_model="Freemium Subscription (Free Starter / $49 Pro / $199 Scale)",
        price_points={
            "Free Tier": "$0/mo - 1 Idea Validation Report",
            "Pro Founder": "$49/mo - Unlimited Validations & Lean Canvas",
            "Agency/Incubator": "$199/mo - Multi-team collaboration & API access",
        },
        estimated_cac="$85 per acquiring paid subscriber",
        estimated_ltv="$588 average lifetime revenue",
        year_1_revenue_projection="$150,000 ARR target with 250 paying subscribers",
    )
