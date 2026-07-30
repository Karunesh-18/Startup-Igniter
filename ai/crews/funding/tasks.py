"""Tasks definition for Funding & Investor Readiness Crew."""

from ai.schemas.funding import FundingResult
from ai.shared.logger import ai_logger


def execute_funding_readiness_task(project_id: str, idea_text: str) -> FundingResult:
    """Execute pitch deck outline and valuation estimator task."""
    ai_logger.info(f"Executing funding readiness task for project '{project_id}'")

    return FundingResult(
        project_id=project_id,
        pitch_deck_slides=[
            "Slide 1: Title & Tagline",
            "Slide 2: Problem Statement",
            "Slide 3: Solution & Product Demo",
            "Slide 4: Market Size (TAM/SAM/SOM)",
            "Slide 5: Competitive Advantage & Moat",
            "Slide 6: Business & Revenue Model",
            "Slide 7: Traction & Early Validation",
            "Slide 8: Product Roadmap",
            "Slide 9: Team & Advisors",
            "Slide 10: Financial Ask & Use of Funds",
        ],
        estimated_valuation_range="$1.5M - $3.5M Pre-Money Valuation",
        fundraising_target="$500,000 Seed Round",
        investor_checklist=[
            "Incorporation Certificate (MCA)",
            "Cap Table & Founder Equity Split",
            "IP Assignment Agreements",
            "Lean Canvas & 3-Year Financial Model",
            "Interactive Product Demo MVP",
        ],
        investor_types=["Angel Investors", "Micro VCs", "Accelerators (Y Combinator, Techstars)"],
        confidence_score=0.88,
    )
