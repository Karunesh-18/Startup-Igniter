"""Background analysis runner.

An analysis runs as an asyncio task independent of the HTTP request that
started it, so a closed tab doesn't waste a half-finished run and the user can
reconnect to the event stream later. Events are buffered in memory per run;
the final report is persisted to the DB.

ponytail: in-process state, so run a single API process (or move events to Redis
and the pipeline to a worker) before scaling out horizontally.
"""

import asyncio
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Callable, Optional

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.config import get_settings
from core.logging import get_logger
from db.product import Analysis
from services.entitlements import is_pro

logger = get_logger(__name__)

MAX_CONCURRENT_RUNS = 2  # the shared DGX serves everyone
_slots = asyncio.Semaphore(MAX_CONCURRENT_RUNS)

# Tests inject their own factory; production uses the app's engine.
session_factory: Optional[Callable[[], async_sessionmaker[AsyncSession]]] = None


def _factory() -> async_sessionmaker[AsyncSession]:
    if session_factory is not None:
        return session_factory()
    from db.database import get_session_factory

    return get_session_factory()


class RunState:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self.done = False
        self.cancel = threading.Event()
        self._cond = asyncio.Condition()

    async def push(self, event: dict[str, Any], finish: bool = False) -> None:
        async with self._cond:
            self.events.append(event)
            self.done = self.done or finish
            self._cond.notify_all()

    async def stream(self) -> AsyncIterator[dict[str, Any]]:
        """Replay buffered events, then follow live until the run ends."""
        i = 0
        while True:
            async with self._cond:
                await self._cond.wait_for(lambda: i < len(self.events) or self.done)
                batch, i = self.events[i:], len(self.events)
                finished = self.done and i >= len(self.events)
            for event in batch:
                yield event
            if finished:
                return


_runs: dict[uuid.UUID, RunState] = {}


def get_run(analysis_id: uuid.UUID) -> Optional[RunState]:
    return _runs.get(analysis_id)


def cancel(analysis_id: uuid.UUID) -> bool:
    state = _runs.get(analysis_id)
    if state is None or state.done:
        return False
    state.cancel.set()
    return True


async def _finish(analysis_id: uuid.UUID, **values: Any) -> None:
    async with _factory()() as db:
        await db.execute(update(Analysis).where(Analysis.id == analysis_id).values(completed_at=datetime.now(timezone.utc), **values))
        await db.commit()


async def execute(
    analysis_id: uuid.UUID, owner_id: uuid.UUID, idea_text: str, mock: bool, github_repo: Optional[str], state: RunState
) -> None:
    from ai.pipeline import CREW_LABELS, run_pipeline

    loop = asyncio.get_running_loop()
    project_id = str(analysis_id)

    def emit(event: dict[str, Any]) -> None:  # called from the pipeline thread
        asyncio.run_coroutine_threadsafe(state.push(event), loop)

    try:
        if _slots.locked():
            await state.push({"type": "queued"})
        async with _slots:
            await state.push({"type": "started", "analysis_id": project_id, "crews": list(CREW_LABELS.values()),
                              "keys": list(CREW_LABELS)})
            payload = await asyncio.to_thread(
                run_pipeline, idea_text, project_id, mock, github_repo, emit, state.cancel.is_set
            )
        if payload is None:
            await _finish(analysis_id, status="cancelled")
            await state.push({"type": "cancelled"}, finish=True)
            return
        async with _factory()() as db:
            unlocked = await is_pro(db, owner_id)
        await _finish(
            analysis_id, status="complete", result=payload, mode=payload["mode"],
            overall_score=payload["overall_readiness_score"],
            verdict=(payload.get("verdict") or {}).get("label"),
            grounding_score=payload["grounding"]["score"], unlocked=unlocked,
        )
        await state.push({"type": "complete", "analysis_id": project_id}, finish=True)
    except Exception as exc:  # noqa: BLE001
        logger.exception("analysis_failed", analysis_id=project_id)
        message = f"{type(exc).__name__}: {exc}"[:500]
        await _finish(analysis_id, status="failed", error=message)
        await state.push({"type": "error", "error": message}, finish=True)
    finally:
        # Keep the buffer briefly so a reconnecting client can still read the tail.
        loop.call_later(300, _runs.pop, analysis_id, None)


def launch(analysis_id: uuid.UUID, owner_id: uuid.UUID, idea_text: str, github_repo: Optional[str]) -> RunState:
    settings = get_settings()
    mock = False
    if not settings.is_production:
        from ai.llm.settings import get_llm_settings

        mock = not get_llm_settings().has_selfhosted  # dev without an LLM: clearly-labelled mock run
    state = RunState()
    _runs[analysis_id] = state
    asyncio.create_task(execute(analysis_id, owner_id, idea_text, mock, github_repo, state))
    return state


async def recover_interrupted() -> None:
    """On startup, runs left 'running' by a previous process can never finish."""
    async with _factory()() as db:
        await db.execute(update(Analysis).where(Analysis.status == "running").values(
            status="failed", error="Interrupted by a server restart. Please run it again.",
            completed_at=datetime.now(timezone.utc)))
        await db.commit()
