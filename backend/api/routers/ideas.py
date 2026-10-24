"""Saved ideas, their analysis runs, and experiments (hypotheses to test).

  GET    /ideas                          list the caller's ideas (with latest result summary)
  POST   /ideas                          create an idea
  GET    /ideas/{id}                     idea + its analysis versions
  PATCH  /ideas/{id}                     rename / edit text / archive / link a GitHub repo
  DELETE /ideas/{id}
  POST   /ideas/{id}/analyses            start an analysis (background); returns its id
  GET    /analyses/{id}                  status + report (free tier gets a redacted preview)
  GET    /analyses/{id}/events           NDJSON progress stream (replays, then follows)
  POST   /analyses/{id}/cancel
  GET    /ideas/{id}/experiments  POST /ideas/{id}/experiments  POST /ideas/{id}/experiments/seed
  PATCH  /experiments/{id}  DELETE /experiments/{id}
"""

import json
import re
import uuid
from typing import Any, AsyncIterator, Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from api.deps import DB
from core.auth import CurrentPrincipal
from db.product import Analysis, Experiment, Idea
from services import runner
from services.entitlements import check_can_start, is_pro, redact, require_pro

router = APIRouter(tags=["Ideas"])
_REPO = re.compile(r"^[\w.-]+/[\w.-]+$")


class IdeaIn(BaseModel):
    idea_text: str = Field(min_length=10, max_length=5000)
    title: str | None = Field(default=None, max_length=200)
    github_repo: str | None = Field(default=None, max_length=200)


class IdeaPatch(BaseModel):
    idea_text: str | None = Field(default=None, min_length=10, max_length=5000)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    archived: bool | None = None
    github_repo: str | None = Field(default=None, max_length=200)


class ExperimentIn(BaseModel):
    hypothesis: str = Field(min_length=3, max_length=1000)
    metric: str | None = Field(default=None, max_length=1000)


class ExperimentPatch(BaseModel):
    hypothesis: str | None = Field(default=None, min_length=3, max_length=1000)
    metric: str | None = None
    status: Literal["open", "running", "validated", "invalidated"] | None = None
    notes: str | None = Field(default=None, max_length=4000)


def _title(text: str) -> str:
    first = re.split(r"[.\n]", text.strip(), maxsplit=1)[0]
    return (first[:60] + "…") if len(first) > 60 else first


def _repo(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip().removeprefix("https://github.com/").strip("/")
    if not _REPO.match(value):
        raise HTTPException(422, "github_repo must look like owner/name.")
    return value


def _idea_out(i: Idea) -> dict[str, Any]:
    return {"id": str(i.id), "title": i.title, "idea_text": i.idea_text, "archived": i.archived,
            "github_repo": i.github_repo, "created_at": i.created_at, "updated_at": i.updated_at}


def _analysis_out(a: Analysis) -> dict[str, Any]:
    return {"id": str(a.id), "idea_id": str(a.idea_id), "version": a.version, "status": a.status, "mode": a.mode,
            "overall_score": a.overall_score, "verdict": a.verdict, "grounding_score": a.grounding_score,
            "unlocked": a.unlocked, "error": a.error, "created_at": a.created_at, "completed_at": a.completed_at}


async def _own_idea(db: DB, who: CurrentPrincipal, idea_id: uuid.UUID) -> Idea:
    idea = await db.get(Idea, idea_id)
    if idea is None or idea.owner_id != who.id:
        raise HTTPException(404, "Idea not found.")
    return idea


async def _own_analysis(db: DB, who: CurrentPrincipal, analysis_id: uuid.UUID) -> Analysis:
    a = await db.get(Analysis, analysis_id)
    if a is None or a.owner_id != who.id:
        raise HTTPException(404, "Analysis not found.")
    return a


# ── Ideas ─────────────────────────────────────────────────────────────────────


@router.get("/ideas")
async def list_ideas(db: DB, who: CurrentPrincipal, archived: bool = False) -> list[dict[str, Any]]:
    ideas = (await db.execute(
        select(Idea).where(Idea.owner_id == who.id, Idea.archived == archived).order_by(Idea.updated_at.desc())
    )).scalars().all()
    out = []
    for i in ideas:
        runs = (await db.execute(
            select(Analysis).where(Analysis.idea_id == i.id).order_by(Analysis.version.desc())
        )).scalars().all()
        latest = next((r for r in runs if r.status == "complete"), None)
        out.append({**_idea_out(i), "versions": len(runs),
                    "latest": _analysis_out(latest) if latest else None,
                    "running": next((str(r.id) for r in runs if r.status == "running"), None)})
    return out


@router.post("/ideas", status_code=201)
async def create_idea(body: IdeaIn, db: DB, who: CurrentPrincipal) -> dict[str, Any]:
    idea = Idea(owner_id=who.id, idea_text=body.idea_text.strip(),
                title=(body.title or _title(body.idea_text)).strip(), github_repo=_repo(body.github_repo))
    db.add(idea)
    await db.commit()
    return _idea_out(idea)


@router.get("/ideas/{idea_id}")
async def get_idea(idea_id: uuid.UUID, db: DB, who: CurrentPrincipal) -> dict[str, Any]:
    idea = await _own_idea(db, who, idea_id)
    runs = (await db.execute(
        select(Analysis).where(Analysis.idea_id == idea.id).order_by(Analysis.version.desc())
    )).scalars().all()
    latest = next((r for r in runs if r.status == "complete"), None)
    return {**_idea_out(idea), "analyses": [_analysis_out(r) for r in runs],
            "stale": bool(latest and latest.idea_text.strip() != idea.idea_text.strip())}


@router.patch("/ideas/{idea_id}")
async def update_idea(idea_id: uuid.UUID, body: IdeaPatch, db: DB, who: CurrentPrincipal) -> dict[str, Any]:
    idea = await _own_idea(db, who, idea_id)
    data = body.model_dump(exclude_unset=True)
    if "github_repo" in data:
        data["github_repo"] = _repo(data["github_repo"])
    for k, v in data.items():
        setattr(idea, k, v.strip() if isinstance(v, str) else v)
    await db.commit()
    return _idea_out(idea)


@router.delete("/ideas/{idea_id}", status_code=204)
async def delete_idea(idea_id: uuid.UUID, db: DB, who: CurrentPrincipal) -> None:
    idea = await _own_idea(db, who, idea_id)
    await db.delete(idea)
    await db.commit()


# ── Analyses ──────────────────────────────────────────────────────────────────


@router.post("/ideas/{idea_id}/analyses", status_code=202)
async def start_analysis(idea_id: uuid.UUID, db: DB, who: CurrentPrincipal) -> dict[str, Any]:
    idea = await _own_idea(db, who, idea_id)
    running = (await db.execute(
        select(Analysis.id).where(Analysis.idea_id == idea.id, Analysis.status == "running")
    )).scalars().first()
    if running:
        return {"analysis_id": str(running), "already_running": True}
    await check_can_start(db, who.id)
    version = ((await db.execute(select(func.max(Analysis.version)).where(Analysis.idea_id == idea.id))).scalar() or 0) + 1
    a = Analysis(idea_id=idea.id, owner_id=who.id, version=version, idea_text=idea.idea_text,
                 status="running", unlocked=False)
    db.add(a)
    await db.commit()
    runner.launch(a.id, who.id, idea.idea_text, idea.github_repo)
    return {"analysis_id": str(a.id), "version": version}


@router.get("/analyses/{analysis_id}")
async def get_analysis(analysis_id: uuid.UUID, db: DB, who: CurrentPrincipal) -> dict[str, Any]:
    a = await _own_analysis(db, who, analysis_id)
    if not a.unlocked and await is_pro(db, who.id):
        a.unlocked = True  # subscribed after the run finished
        await db.commit()
    result = a.result if a.unlocked else redact(a.result)
    return {**_analysis_out(a), "idea_text": a.idea_text, "result": result}


async def _ndjson(analysis_id: uuid.UUID, request: Request) -> AsyncIterator[bytes]:
    state = runner.get_run(analysis_id)
    if state is None:
        yield (json.dumps({"type": "gone"}) + "\n").encode()
        return
    async for event in state.stream():
        # Per-crew results are paid content: strip them from the live stream for locked users.
        yield (json.dumps(event, ensure_ascii=False, default=str) + "\n").encode()
        if await request.is_disconnected():
            return


@router.get("/analyses/{analysis_id}/events")
async def analysis_events(analysis_id: uuid.UUID, request: Request, db: DB, who: CurrentPrincipal) -> StreamingResponse:
    a = await _own_analysis(db, who, analysis_id)
    if not (a.unlocked or await is_pro(db, who.id)):
        return StreamingResponse(_scrubbed(analysis_id, request), media_type="application/x-ndjson")
    return StreamingResponse(_ndjson(analysis_id, request), media_type="application/x-ndjson")


async def _scrubbed(analysis_id: uuid.UUID, request: Request) -> AsyncIterator[bytes]:
    """Free users see progress, not the paid per-crew content, while a run is live."""
    state = runner.get_run(analysis_id)
    if state is None:
        yield (json.dumps({"type": "gone"}) + "\n").encode()
        return
    async for event in state.stream():
        if event.get("type") == "crew_complete":
            event = {k: v for k, v in event.items() if k != "result"}
        yield (json.dumps(event, ensure_ascii=False, default=str) + "\n").encode()
        if await request.is_disconnected():
            return


@router.post("/analyses/{analysis_id}/cancel")
async def cancel_analysis(analysis_id: uuid.UUID, db: DB, who: CurrentPrincipal) -> dict[str, bool]:
    await _own_analysis(db, who, analysis_id)
    return {"cancelling": runner.cancel(analysis_id)}


# ── Re-scan (Pro) ─────────────────────────────────────────────────────────────


@router.post("/ideas/{idea_id}/rescan")
async def rescan(idea_id: uuid.UUID, db: DB, who: CurrentPrincipal) -> dict[str, Any]:
    """Re-check GitHub and Hacker News for the idea's topic and diff against the latest report's snapshot."""
    import asyncio

    from ai.evidence import signals

    await _own_idea(db, who, idea_id)
    await require_pro(db, who.id, "rescan")
    latest = (await db.execute(
        select(Analysis).where(Analysis.idea_id == idea_id, Analysis.status == "complete").order_by(Analysis.version.desc())
    )).scalars().first()
    if latest is None or not latest.result:
        raise HTTPException(409, "Run an analysis first.")
    result = latest.result
    category = ((result.get("idea_validation") or {}).get("category_classification") or {}).get("primary_category")
    topic = category or latest.idea_text[:160]
    try:
        repos, hn = await asyncio.gather(
            asyncio.to_thread(signals.github_competitors, topic), asyncio.to_thread(signals.hacker_news, topic)
        )
    except Exception as exc:  # noqa: BLE001 -- upstream rate limits / outages
        raise HTTPException(502, f"Could not reach GitHub or Hacker News: {type(exc).__name__}") from exc
    before = {r["full_name"]: r for r in (result.get("signals") or {}).get("github", [])}
    return {
        "since_version": latest.version,
        "new_repos": [r for r in repos if r["full_name"] not in before],
        "star_changes": [
            {"full_name": r["full_name"], "url": r["url"], "from": before[r["full_name"]]["stars"], "to": r["stars"]}
            for r in repos if r["full_name"] in before and r["stars"] != before[r["full_name"]]["stars"]
        ],
        "hn_total_before": ((result.get("signals") or {}).get("hacker_news") or {}).get("total"),
        "hn_total_now": hn["total"],
        "hn_recent": hn["stories"][:3],
    }


# ── Experiments (Pro) ─────────────────────────────────────────────────────────


def _exp_out(e: Experiment) -> dict[str, Any]:
    return {"id": str(e.id), "idea_id": str(e.idea_id), "hypothesis": e.hypothesis, "metric": e.metric,
            "status": e.status, "notes": e.notes, "created_at": e.created_at, "updated_at": e.updated_at}


@router.get("/ideas/{idea_id}/experiments")
async def list_experiments(idea_id: uuid.UUID, db: DB, who: CurrentPrincipal) -> list[dict[str, Any]]:
    await _own_idea(db, who, idea_id)
    rows = (await db.execute(select(Experiment).where(Experiment.idea_id == idea_id).order_by(Experiment.created_at))).scalars().all()
    return [_exp_out(e) for e in rows]


@router.post("/ideas/{idea_id}/experiments", status_code=201)
async def add_experiment(idea_id: uuid.UUID, body: ExperimentIn, db: DB, who: CurrentPrincipal) -> dict[str, Any]:
    await _own_idea(db, who, idea_id)
    await require_pro(db, who.id, "experiments")
    e = Experiment(idea_id=idea_id, owner_id=who.id, hypothesis=body.hypothesis.strip(), metric=body.metric)
    db.add(e)
    await db.commit()
    return _exp_out(e)


@router.post("/ideas/{idea_id}/experiments/seed", status_code=201)
async def seed_experiments(idea_id: uuid.UUID, db: DB, who: CurrentPrincipal) -> list[dict[str, Any]]:
    """Create experiments from the latest report's testable hypotheses (skips ones already tracked)."""
    await _own_idea(db, who, idea_id)
    await require_pro(db, who.id, "experiments")
    latest = (await db.execute(
        select(Analysis).where(Analysis.idea_id == idea_id, Analysis.status == "complete").order_by(Analysis.version.desc())
    )).scalars().first()
    if latest is None or not latest.result:
        raise HTTPException(409, "Run an analysis first.")
    have = {e.hypothesis for e in (await db.execute(select(Experiment).where(Experiment.idea_id == idea_id))).scalars()}
    created = [
        Experiment(idea_id=idea_id, owner_id=who.id, hypothesis=h["hypothesis"], metric=h.get("metric"))
        for h in latest.result.get("hypotheses", []) if h["hypothesis"] not in have
    ]
    db.add_all(created)
    await db.commit()
    return [_exp_out(e) for e in created]


async def _own_experiment(db: DB, who: CurrentPrincipal, experiment_id: uuid.UUID) -> Experiment:
    e = await db.get(Experiment, experiment_id)
    if e is None or e.owner_id != who.id:
        raise HTTPException(404, "Experiment not found.")
    return e


@router.patch("/experiments/{experiment_id}")
async def update_experiment(experiment_id: uuid.UUID, body: ExperimentPatch, db: DB, who: CurrentPrincipal) -> dict[str, Any]:
    e = await _own_experiment(db, who, experiment_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(e, k, v)
    await db.commit()
    return _exp_out(e)


@router.delete("/experiments/{experiment_id}", status_code=204)
async def delete_experiment(experiment_id: uuid.UUID, db: DB, who: CurrentPrincipal) -> None:
    await db.delete(await _own_experiment(db, who, experiment_id))
    await db.commit()
