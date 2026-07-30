"""
Analysis router — runs the full AI analysis pipeline (Crews 1, 2, 3) directly.

Endpoints:
  POST /api/v1/analysis/run           Submit idea and run all 3 AI crews
  GET  /api/v1/analysis/{project_id}  Retrieve a previously run result (from memory)

This is a synchronous endpoint — the AI crews run end-to-end and return the
combined result in one response.

Note: No database or auth required for this MVP endpoint.
CORS is handled by the main app middleware.
"""

import sys
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Add the project root to sys.path so the `ai` module is importable
_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

router = APIRouter(prefix="/analysis", tags=["Analysis"])

# In-memory result cache keyed by project_id (MVP — no DB persistence)
_result_cache: dict[str, Any] = {}


class AnalysisRequest(BaseModel):
    """Request body for running the full AI analysis pipeline."""
    idea_text: str = Field(
        min_length=10,
        max_length=5000,
        description="The startup idea proposal text to analyse.",
    )
    project_id: str | None = Field(
        default=None,
        description="Optional project identifier. Auto-generated if not provided.",
    )
    mock_mode: bool = Field(
        default=False,
        description="If true, run in fast offline mock mode (no live LLM calls).",
    )


@router.post("/run", summary="Run full 3-crew AI analysis")
async def run_analysis(request: AnalysisRequest) -> JSONResponse:
    """
    Submit a startup idea and run all 3 AI crews sequentially.

    Returns a combined result including:
    - IdeaValidationResult (Crew 1: 6 agents)
    - MarketResearchResult (Crew 2: 7 agents)
    - ResearchPatentResult (Crew 3: 7 agents)

    Live mode takes 4-8 minutes. Use mock_mode=true for instant test results.
    """
    project_id = request.project_id or f"proj-{uuid.uuid4().hex[:8]}"

    try:
        from ai.services.idea_validation_service import IdeaValidationService
        from ai.services.market_research_service import MarketResearchService
        from ai.services.research_patent_service import ResearchPatentService
        from ai.memory.project_memory import ProjectMemoryManager

        memory = ProjectMemoryManager(use_mock_store=True)
        mock = request.mock_mode

        # ── Crew 1: Idea Validation ────────────────────────────────────────
        val_service = IdeaValidationService(memory_manager=memory)
        val_result = val_service.validate_idea(
            idea_text=request.idea_text,
            project_id=project_id,
            mock_mode=mock,
        )

        # ── Crew 2: Market Research ────────────────────────────────────────
        mr_service = MarketResearchService(memory_manager=memory)
        mr_result = mr_service.run_market_research(
            idea_validation=val_result,
            project_id=project_id,
            mock_mode=mock,
        )

        # ── Crew 3: Research & Patent ──────────────────────────────────────
        rp_service = ResearchPatentService(memory_manager=memory)
        rp_result = rp_service.run_research_patent(
            idea_validation=val_result,
            market_research=mr_result,
            project_id=project_id,
            mock_mode=mock,
        )

        # ── Derive overall readiness score ─────────────────────────────────
        iv_score = getattr(val_result, "overall_validation_score", 0) or 0
        mr_score = getattr(mr_result, "overall_market_score", 0) or 0
        rp_score = getattr(rp_result, "overall_novelty_score", 0) or 0
        overall = round(iv_score * 0.35 + mr_score * 0.35 + rp_score * 0.30, 2)

        combined: dict[str, Any] = {
            "project_id": project_id,
            "idea_text": request.idea_text,
            "status": "success",
            "ai_generated": True,
            "overall_readiness_score": overall,
            "executive_summary": getattr(rp_result, "executive_summary", None),
            "strategic_recommendations": getattr(rp_result, "strategic_recommendations", []),
            "idea_validation": val_result.model_dump() if val_result else None,
            "market_research": mr_result.model_dump() if mr_result else None,
            "research_patent": rp_result.model_dump() if rp_result else None,
        }

        _result_cache[project_id] = combined
        return JSONResponse(content=combined, status_code=200)

    except Exception as exc:
        return JSONResponse(
            content={
                "project_id": project_id,
                "status": "failed",
                "error": str(exc),
                "ai_generated": True,
            },
            status_code=500,
        )


@router.get("/{project_id}", summary="Retrieve a previous analysis result")
async def get_analysis(project_id: str) -> JSONResponse:
    """Return a previously cached analysis result by project_id."""
    result = _result_cache.get(project_id)
    if not result:
        return JSONResponse(
            content={"error": "Result not found.", "project_id": project_id},
            status_code=404,
        )
    return JSONResponse(content=result, status_code=200)
