"""Tasks definition for Product Development Crew."""

from typing import List, Optional
from ai.schemas.product_development import MVPFeature, ProductDevelopmentResult, TechStackRecommendation
from ai.shared.logger import ai_logger


def execute_mvp_roadmap_task(project_id: str, idea_text: str) -> List[MVPFeature]:
    """Generate prioritized MVP feature roadmap."""
    return [
        MVPFeature(
            feature_name="User Authentication & Supabase Auth",
            description="Role-based login, JWT validation, and secure session management.",
            priority="Must Have",
            complexity="Low",
        ),
        MVPFeature(
            feature_name="AI Multi-Agent Validation Engine",
            description="Execution pipeline for CrewAI agents generating validation reports.",
            priority="Must Have",
            complexity="Medium",
        ),
        MVPFeature(
            feature_name="Interactive Lean Canvas Dashboard",
            description="Visual 9-box editing interface for business model canvas.",
            priority="Must Have",
            complexity="Low",
        ),
        MVPFeature(
            feature_name="Automated PDF Export & Share Links",
            description="Export completed startup reports as PDF documents.",
            priority="Should Have",
            complexity="Medium",
        ),
    ]


def recommend_tech_stack_task(project_id: str, category: str = "SaaS") -> TechStackRecommendation:
    """Recommend optimal technology stack."""
    return TechStackRecommendation(
        frontend="Next.js 15 App Router / TailwindCSS / TypeScript",
        backend="FastAPI Python 3.11 / Supabase / Celery / Redis",
        database="Supabase PostgreSQL + pgvector",
        hosting="Vercel (Frontend) + Google Cloud Run (Backend API & Workers)",
        ai_ml_tools=["CrewAI", "Groq Llama-3.3-70b", "OpenRouter", "Sentence-Transformers"],
    )
