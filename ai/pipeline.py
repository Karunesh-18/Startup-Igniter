"""The full 13-crew analysis pipeline, independent of any web framework.

run_pipeline() executes the crews in order (each sees a digest of the ones before it),
builds the shared source pool after crew 1, verifies claims into an evidence ledger,
and returns the final report payload. Progress goes to `emit`; `should_stop`
is polled between crews so a cancelled run stops spending LLM calls.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple

from ai.shared.digest import crew_confidence, crew_score, pct
from ai.shared.logger import ai_logger
from ai.shared.progress import start_run

CREW_LABELS: Dict[str, str] = {
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
    "skeptic": "Skeptic Review",
    "reporting": "Executive Reporting",
}

SKEPTIC_WEIGHT = 0.15
# A failure in these aborts the run; later crews degrade gracefully (the report marks them unavailable).
CORE_CREWS = ("idea_validation", "market_research", "research_patent")


def crew_steps(idea_text: str, project_id: str, mock: bool) -> List[Tuple[str, Callable[[dict], Any]]]:
    """[(crew_key, fn(results_so_far) -> result model)] in run order (keys match CREW_LABELS)."""
    from ai.crews.branding_marketing.crew import get_branding_marketing_crew
    from ai.crews.business_planning.crew import get_business_planning_crew
    from ai.crews.community.crew import get_community_crew
    from ai.crews.feasibility.crew import get_feasibility_crew
    from ai.crews.funding.crew import get_funding_crew
    from ai.crews.growth_scaling.crew import get_growth_scaling_crew
    from ai.crews.legal_compliance.crew import get_legal_compliance_crew
    from ai.crews.product_development.crew import get_product_development_crew
    from ai.crews.reporting.crew import get_reporting_crew
    from ai.crews.skeptic.crew import get_skeptic_crew
    from ai.memory.project_memory import ProjectMemoryManager
    from ai.services.idea_validation_service import IdeaValidationService
    from ai.services.market_research_service import MarketResearchService
    from ai.services.research_patent_service import ResearchPatentService

    memory = ProjectMemoryManager(use_mock_store=True)

    def spec(factory: Callable[..., Any]) -> Callable[[dict], Any]:
        return lambda r: factory(mock_mode=mock, memory_manager=memory).run(
            project_id=project_id, idea_text=idea_text, mock_mode=mock, prior={k: v.model_dump() for k, v in r.items() if v is not None}
        )

    return [
        ("idea_validation", lambda r: IdeaValidationService(memory_manager=memory).validate_idea(
            idea_text=idea_text, project_id=project_id, mock_mode=mock)),
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
        ("skeptic", spec(get_skeptic_crew)),
        ("reporting", spec(get_reporting_crew)),
    ]


def _readiness(results: Dict[str, Any]) -> float:
    """Weighted 0-100 readiness: validation 35%, market 35%, novelty 30%; blended with
    feasibility/funding (20%) and the skeptic's survival score (15%) when present."""
    val, mr, rp = results["idea_validation"], results["market_research"], results["research_patent"]
    overall = (
        (getattr(val, "overall_validation_score", 0) or 0) * 0.35
        + (getattr(mr, "overall_market_score", 0) or 0) * 0.35
        + (getattr(rp, "overall_novelty_score", 0) or 0) * 0.30
    )
    extras = []
    if (f := results.get("feasibility")) is not None:
        extras.append((f.technical_feasibility_score + f.operational_feasibility_score + f.financial_feasibility_score) / 3)
    if (fu := results.get("funding")) is not None:
        extras.append(pct(fu.confidence_score, "confidence_score"))
    if extras:
        overall = overall * 0.8 + (sum(extras) / len(extras)) * 0.2
    if (sk := results.get("skeptic")) is not None:
        overall = overall * (1 - SKEPTIC_WEIGHT) + sk.overall_survival_score * SKEPTIC_WEIGHT
    return round(max(0.0, min(100.0, overall)), 1)


def _verdict(overall: float, skeptic: Any) -> Dict[str, Any] | None:
    if skeptic is None:
        return None
    label = skeptic.verdict
    # Keep the label consistent with the number the user sees.
    if label == "no-go" and overall >= 70:
        label = "pivot"
    elif label == "go" and overall < 35:
        label = "pivot"
    return {
        "label": label,
        "rationale": skeptic.verdict_rationale,
        "would_change_my_mind": skeptic.would_change_my_mind,
        "pivot_suggestions": skeptic.pivot_suggestions,
    }


def finalize(
    idea_text: str,
    project_id: str,
    results: Dict[str, Any],
    mock: bool,
    used_mock: bool,
    ledger: Optional[Dict[str, Any]],
    pool: Any,
    failed: Optional[List[str]] = None,
) -> Dict[str, Any]:
    dumps = {k: (v.model_dump() if v is not None else None) for k, v in results.items()}
    overall = _readiness(results)
    confs = [c for c in (crew_confidence(d) for d in dumps.values()) if c is not None]
    avg_conf = sum(confs) / len(confs) if confs else 50.0
    grounding = ledger["grounding_score"] if ledger else None
    confidence = round(0.6 * avg_conf + 0.4 * grounding, 1) if grounding is not None else round(avg_conf * 0.8, 1)
    sk = results.get("skeptic")
    spread = (100 - confidence) * 0.15
    rp = results.get("research_patent")
    return {
        "project_id": project_id,
        "idea_text": idea_text,
        "status": "success",
        "ai_generated": True,
        "mode": "mock" if (mock or used_mock) else "live",
        "failed_crews": failed or [],
        "overall_readiness_score": overall,
        "score_range": {
            "low": round(max(0.0, min(overall, sk.score_low) if sk else overall - spread), 1),
            "high": round(min(100.0, max(overall, sk.score_high) if sk else overall + spread), 1),
        },
        "confidence": confidence,
        "verdict": _verdict(overall, sk),
        "grounding": {
            "score": grounding,
            "claims": len(ledger["entries"]) if ledger else 0,
            "contradicted": ledger["contradicted"] if ledger else 0,
            "sources": len(pool.sources) if pool else 0,
        },
        "ledger": ledger["entries"] if ledger else [],
        "sources": pool.public() if pool else [],
        "signals": pool.signals if pool else {},
        "crew_scores": {k: crew_score(d) for k, d in dumps.items()},
        "hypotheses": [h.model_dump() for h in sk.testable_hypotheses] if sk else [],
        "executive_summary": getattr(rp, "executive_summary", None),
        "strategic_recommendations": getattr(rp, "strategic_recommendations", []),
        **dumps,
    }


def run_pipeline(
    idea_text: str,
    project_id: str,
    mock: bool = False,
    github_repo: Optional[str] = None,
    emit: Callable[[dict], None] = lambda event: None,
    should_stop: Callable[[], bool] = lambda: False,
) -> Optional[Dict[str, Any]]:
    """Run everything; returns the final payload, or None if stopped early. Raises on crew failure."""
    from ai.evidence.ledger import build_ledger
    from ai.evidence.sources import gather_sources
    from ai.llm.gateway import get_gateway

    run = start_run(emit)
    results: Dict[str, Any] = {}
    failed: List[str] = []
    pool = None

    for key, step in crew_steps(idea_text, project_id, mock):
        if should_stop():
            return None
        run.crew = key
        emit({"type": "crew_start", "crew": key, "label": CREW_LABELS[key]})
        try:
            results[key] = step(results)
        except Exception as err:  # noqa: BLE001
            if key in CORE_CREWS:
                raise
            ai_logger.warning(f"crew '{key}' failed, continuing without it: {err}")
            results[key] = None
            failed.append(key)
            emit({"type": "crew_failed", "crew": key, "label": CREW_LABELS[key], "error": str(err)[:300]})
            continue
        emit({"type": "crew_complete", "crew": key, "label": CREW_LABELS[key],
              "result": results[key].model_dump() if results[key] is not None else None})
        if key == "idea_validation" and not mock:
            run.crew = None
            emit({"type": "stage", "stage": "sources", "label": "Gathering research sources"})
            category = getattr(getattr(results[key], "category_classification", None), "primary_category", None)
            pool = gather_sources(idea_text, category, github_repo)
            run.sources = pool
            emit({"type": "sources", "count": len(pool.sources), "signals": list(pool.signals)})

    ledger = None
    if not mock and pool is not None:
        run.crew = None
        emit({"type": "stage", "stage": "verify", "label": "Verifying claims against sources"})
        try:
            ledger = build_ledger({k: v.model_dump() for k, v in results.items() if v is not None}, pool, get_gateway())
        except Exception as err:  # noqa: BLE001 -- the report is still valid without a ledger
            ai_logger.warning(f"evidence ledger failed: {err}")
    return finalize(idea_text, project_id, results, mock, run.used_mock, ledger, pool, failed)
