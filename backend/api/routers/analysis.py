"""
Analysis router — runs the full AI analysis pipeline (Crews 1, 2, 3) directly.

Endpoints:
  POST /api/v1/analysis/run           Submit idea and run all 3 AI crews (single response)
  POST /api/v1/analysis/run/stream    Same pipeline, streamed as NDJSON progress events
  GET  /api/v1/analysis/{project_id}  Retrieve a previously run result (from memory)

/run is synchronous — the AI crews run end-to-end and return the combined
result in one response. /run/stream runs the identical 3 services (no
duplicated business logic) but yields one JSON line per completed crew, so
the frontend can show real progress instead of a cosmetic timer (see
frontend/src/components/AnalysisPage.tsx). Granularity is per-CREW, not
per-agent: the 3 crew services are the natural checkpoints already present
in this code without invasively threading a progress callback through
every one of the ~20 individual agent calls inside them.

Note: No database or auth required for this MVP endpoint.
CORS is handled by the main app middleware.
"""

import json
import sys
import uuid
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
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


# Crew labels for progress events -- matches the 3 real, implemented crews
# (see docs/README.md's implementation status; crews 4-12 don't run here).
_CREW_LABELS = {
    "idea_validation": "Idea Validation",
    "market_research": "Market Research",
    "research_patent": "Research & Patent",
}


async def _stream_analysis(
    request: AnalysisRequest, project_id: str, http_request: Request
) -> AsyncIterator[bytes]:
    """Yield one NDJSON line per completed crew, then a final result/error line.

    Each blocking service call runs in a worker thread (asyncio.to_thread) so
    the event loop stays free to flush already-yielded lines to the client
    immediately, rather than buffering the whole generator's output until
    the synchronous work finishes. Checks for client disconnection (the
    frontend's AbortController firing on a user-initiated cancel) between
    crews -- a cancelled request stops before starting the NEXT crew rather
    than continuing to burn LLM calls nobody will see the result of. It
    can't interrupt a crew already in flight (the underlying service calls
    aren't themselves cancellable), so cancellation is checkpoint-granular,
    matching the per-crew progress granularity everywhere else in this
    endpoint.
    """
    import asyncio

    def emit(event: dict) -> bytes:
        return (json.dumps(event, ensure_ascii=False) + "\n").encode("utf-8")

    try:
        from ai.services.idea_validation_service import IdeaValidationService
        from ai.services.market_research_service import MarketResearchService
        from ai.services.research_patent_service import ResearchPatentService
        from ai.memory.project_memory import ProjectMemoryManager

        memory = ProjectMemoryManager(use_mock_store=True)
        mock = request.mock_mode

        yield emit({"type": "started", "project_id": project_id, "crews": list(_CREW_LABELS.values())})

        val_service = IdeaValidationService(memory_manager=memory)
        val_result = await asyncio.to_thread(
            val_service.validate_idea, idea_text=request.idea_text, project_id=project_id, mock_mode=mock
        )
        yield emit({"type": "crew_complete", "crew": "idea_validation", "label": _CREW_LABELS["idea_validation"]})
        if await http_request.is_disconnected():
            return

        mr_service = MarketResearchService(memory_manager=memory)
        mr_result = await asyncio.to_thread(
            mr_service.run_market_research, idea_validation=val_result, project_id=project_id, mock_mode=mock
        )
        yield emit({"type": "crew_complete", "crew": "market_research", "label": _CREW_LABELS["market_research"]})
        if await http_request.is_disconnected():
            return

        rp_service = ResearchPatentService(memory_manager=memory)
        rp_result = await asyncio.to_thread(
            rp_service.run_research_patent,
            idea_validation=val_result,
            market_research=mr_result,
            project_id=project_id,
            mock_mode=mock,
        )
        yield emit({"type": "crew_complete", "crew": "research_patent", "label": _CREW_LABELS["research_patent"]})

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
        yield emit({"type": "result", "result": combined})

    except Exception as exc:
        yield emit({"type": "error", "project_id": project_id, "error": str(exc)})


@router.post("/run/stream", summary="Run full 3-crew AI analysis, streamed as NDJSON progress")
async def run_analysis_stream(request: AnalysisRequest, http_request: Request) -> StreamingResponse:
    """Same pipeline as /run, but yields one JSON object per line as each of
    the 3 crews completes, ending with a `{"type": "result", ...}` line (or
    `{"type": "error", ...}` on failure). Not Server-Sent-Events framing --
    plain newline-delimited JSON over a POST request body, since EventSource
    only supports GET and this endpoint's idea_text can be up to 5000 chars
    (too long to reliably pass as a query string). Consume with `fetch()` +
    `response.body.getReader()`, splitting decoded chunks on '\\n'.
    """
    project_id = request.project_id or f"proj-{uuid.uuid4().hex[:8]}"
    return StreamingResponse(
        _stream_analysis(request, project_id, http_request),
        media_type="application/x-ndjson",
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
