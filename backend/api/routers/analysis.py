"""
Analysis router: runs the full 12-crew AI analysis pipeline directly.

Endpoints:
  POST /api/v1/analysis/run           Submit idea and run all 12 AI crews (single response)
  POST /api/v1/analysis/run/stream    Same pipeline, streamed as NDJSON progress events
  GET  /api/v1/analysis/{project_id}  Retrieve a previously run result (from memory)

Both endpoints share _crew_steps (crews run in order; each receives the
accumulated results of the crews before it). /run/stream yields one JSON
line per completed crew (including that crew's result) so the frontend can
show real progress. Granularity is per-CREW, not per-agent.

Note: No database or auth required for this MVP endpoint.
CORS is handled by the main app middleware.
"""

import json
import sys
import uuid
from pathlib import Path
from typing import Any, AsyncIterator, Callable

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


# Crew keys (result-payload keys) -> labels, in run order. All 12 crews run.
_CREW_LABELS = {
    "idea_validation": "Idea Validation",
    "market_research": "Market Research",
    "research_patent": "Research & Patent",
    "feasibility": "Technical Feasibility",
    "business_planning": "Business Planning",
    "product_development": "Product Development",
    "legal_compliance": "Legal & Compliance",
    "branding_marketing": "Branding & Marketing",
    "funding": "Funding Readiness",
    "growth_scaling": "Growth & Scaling",
    "community": "Community & Ecosystem",
    "reporting": "Executive Reporting",
}


def _crew_steps(request: AnalysisRequest, project_id: str) -> list[tuple[str, Callable[[dict], Any]]]:
    """[(crew_key, fn(results_so_far) -> result model)] in run order (same keys as _CREW_LABELS)."""
    from ai.crews.branding_marketing.crew import get_branding_marketing_crew
    from ai.crews.business_planning.crew import get_business_planning_crew
    from ai.crews.community.crew import get_community_crew
    from ai.crews.feasibility.crew import get_feasibility_crew
    from ai.crews.funding.crew import get_funding_crew
    from ai.crews.growth_scaling.crew import get_growth_scaling_crew
    from ai.crews.legal_compliance.crew import get_legal_compliance_crew
    from ai.crews.product_development.crew import get_product_development_crew
    from ai.crews.reporting.crew import get_reporting_crew
    from ai.memory.project_memory import ProjectMemoryManager
    from ai.services.idea_validation_service import IdeaValidationService
    from ai.services.market_research_service import MarketResearchService
    from ai.services.research_patent_service import ResearchPatentService

    memory = ProjectMemoryManager(use_mock_store=True)
    mock, idea = request.mock_mode, request.idea_text

    def spec(factory: Callable[..., Any]) -> Callable[[dict], Any]:
        return lambda r: factory(mock_mode=mock, memory_manager=memory).run(
            project_id=project_id, idea_text=idea, mock_mode=mock, prior={k: v.model_dump() for k, v in r.items()}
        )

    return [
        ("idea_validation", lambda r: IdeaValidationService(memory_manager=memory).validate_idea(
            idea_text=idea, project_id=project_id, mock_mode=mock)),
        ("market_research", lambda r: MarketResearchService(memory_manager=memory).run_market_research(
            idea_validation=r["idea_validation"], project_id=project_id, mock_mode=mock)),
        ("research_patent", lambda r: ResearchPatentService(memory_manager=memory).run_research_patent(
            idea_validation=r["idea_validation"], market_research=r["market_research"],
            project_id=project_id, mock_mode=mock)),
        ("feasibility", spec(get_feasibility_crew)),
        ("business_planning", spec(get_business_planning_crew)),
        ("product_development", spec(get_product_development_crew)),
        ("legal_compliance", spec(get_legal_compliance_crew)),
        ("branding_marketing", spec(get_branding_marketing_crew)),
        ("funding", spec(get_funding_crew)),
        ("growth_scaling", spec(get_growth_scaling_crew)),
        ("community", spec(get_community_crew)),
        ("reporting", spec(get_reporting_crew)),
    ]


def _combine(request: AnalysisRequest, project_id: str, results: dict[str, Any]) -> dict[str, Any]:
    """Final payload: readiness score + one model_dump per crew key."""
    val, mr, rp = results["idea_validation"], results["market_research"], results["research_patent"]
    iv_score = getattr(val, "overall_validation_score", 0) or 0
    mr_score = getattr(mr, "overall_market_score", 0) or 0
    rp_score = getattr(rp, "overall_novelty_score", 0) or 0
    overall = iv_score * 0.35 + mr_score * 0.35 + rp_score * 0.30

    # Blend in feasibility (mean of its 0-100 scores) and funding confidence (0-1 -> 0-100) at 20% weight.
    extras = []
    if (f := results.get("feasibility")) is not None:
        extras.append((f.technical_feasibility_score + f.operational_feasibility_score + f.financial_feasibility_score) / 3)
    if (fu := results.get("funding")) is not None:
        extras.append(fu.confidence_score * 100)
    if extras:
        overall = overall * 0.8 + (sum(extras) / len(extras)) * 0.2

    return {
        "project_id": project_id,
        "idea_text": request.idea_text,
        "status": "success",
        "ai_generated": True,
        "overall_readiness_score": round(overall, 2),
        "executive_summary": getattr(rp, "executive_summary", None),
        "strategic_recommendations": getattr(rp, "strategic_recommendations", []),
        **{key: (res.model_dump() if res is not None else None) for key, res in results.items()},
    }


@router.post("/run", summary="Run full 12-crew AI analysis")
async def run_analysis(request: AnalysisRequest) -> JSONResponse:
    """
    Submit a startup idea and run all 12 AI crews sequentially, each crew
    receiving the accumulated results of the crews before it.

    Returns the readiness score plus one result object per crew key
    (see _CREW_LABELS). Use mock_mode=true for instant test results.
    """
    project_id = request.project_id or f"proj-{uuid.uuid4().hex[:8]}"

    try:
        results: dict[str, Any] = {}
        for key, step in _crew_steps(request, project_id):
            results[key] = step(results)

        combined = _combine(request, project_id, results)
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


async def _stream_analysis(
    request: AnalysisRequest, project_id: str, http_request: Request
) -> AsyncIterator[bytes]:
    """Yield one NDJSON line per completed crew, then a final result/error line.

    Each blocking crew call runs in a worker thread (asyncio.to_thread) so
    the event loop stays free to flush already-yielded lines to the client
    immediately. Checks for client disconnection (the frontend's
    AbortController firing on a user-initiated cancel) between crews: a
    cancelled request stops before starting the NEXT crew rather than
    continuing to burn LLM calls nobody will see. A crew already in flight
    cannot be interrupted, so cancellation is checkpoint-granular.
    """
    import asyncio

    def emit(event: dict) -> bytes:
        return (json.dumps(event, ensure_ascii=False) + "\n").encode("utf-8")

    try:
        yield emit({"type": "started", "project_id": project_id, "crews": list(_CREW_LABELS.values())})

        results: dict[str, Any] = {}
        for key, step in _crew_steps(request, project_id):
            results[key] = await asyncio.to_thread(step, results)
            yield emit({
                "type": "crew_complete",
                "crew": key,
                "label": _CREW_LABELS[key],
                "result": results[key].model_dump() if results[key] is not None else None,
            })
            if await http_request.is_disconnected():
                return

        combined = _combine(request, project_id, results)
        _result_cache[project_id] = combined
        yield emit({"type": "result", "result": combined})

    except Exception as exc:
        yield emit({"type": "error", "project_id": project_id, "error": str(exc)})


@router.post("/run/stream", summary="Run full 12-crew AI analysis, streamed as NDJSON progress")
async def run_analysis_stream(request: AnalysisRequest, http_request: Request) -> StreamingResponse:
    """Same pipeline as /run, but yields one JSON object per line as each of
    the 12 crews completes, ending with a `{"type": "result", ...}` line (or
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
