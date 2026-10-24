"""Idea-refinement chat (Pro): a candid "co-founder" that knows the idea and its latest report,
and can propose a concrete revision of the idea for the founder to accept.

  GET  /ideas/{id}/chat                       message history
  POST /ideas/{id}/chat                       send a message; NDJSON stream of deltas, then the saved message
  POST /chat/messages/{id}/proposal           accept | dismiss a proposed idea revision
"""

import asyncio
import json
import time
import uuid
from collections import defaultdict, deque
from typing import Any, AsyncIterator, Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select

from api.deps import DB
from core.auth import CurrentPrincipal
from core.logging import get_logger
from db.product import Analysis, ChatMessage, Idea
from services import runner
from services.entitlements import require_pro

logger = get_logger(__name__)
router = APIRouter(tags=["Chat"])

HISTORY_TURNS = 12
_hits: dict[uuid.UUID, deque[float]] = defaultdict(deque)

SYSTEM = """You are the founder's AI co-founder inside Startup Igniter. You know their idea and the latest analysis of it.
Be direct, specific and brief. Challenge weak assumptions; do not flatter. When the analysis shows a problem, say it plainly and suggest the smallest change that fixes it.
Use ONLY facts from the idea, the analysis digest, and what the founder tells you; if you do not know, say so and suggest how to find out.
Suggest concrete edits (target customer, pricing, wedge, scope) when relevant, and ask one focused question when you need information."""


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ProposalAction(BaseModel):
    action: Literal["accept", "dismiss"]


class IdeaRevision(BaseModel):
    should_revise: bool = Field(description="True only if the founder is changing or agreeing to change the idea itself.")
    title: str = Field(default="", description="Short title for the revised idea (max 80 chars).")
    idea_text: str = Field(default="", description="The FULL revised idea text (max 4000 chars), keeping everything unchanged that was not discussed.")
    changes: list[str] = Field(default_factory=list, description="Bullet list of what changed, one short line each.")


def _msg_out(m: ChatMessage) -> dict[str, Any]:
    return {"id": str(m.id), "role": m.role, "content": m.content, "proposal": m.proposal,
            "proposal_status": m.proposal_status, "created_at": m.created_at}


def _throttle(user_id: uuid.UUID) -> None:
    q, now = _hits[user_id], time.monotonic()
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= 15:
        raise HTTPException(429, "Slow down: 15 messages per minute.")
    q.append(now)


async def _own_idea(db: DB, who: CurrentPrincipal, idea_id: uuid.UUID) -> Idea:
    idea = await db.get(Idea, idea_id)
    if idea is None or idea.owner_id != who.id:
        raise HTTPException(404, "Idea not found.")
    return idea


def _context(idea: Idea, analysis: Analysis | None) -> str:
    from ai.shared.digest import digest_all

    parts = [f"IDEA TITLE: {idea.title}", f"IDEA:\n{idea.idea_text}"]
    if analysis and analysis.result:
        r = analysis.result
        v = r.get("verdict") or {}
        parts.append(
            f"LATEST ANALYSIS (v{analysis.version}): readiness {r.get('overall_readiness_score')}/100, "
            f"verdict {v.get('label')}, confidence {r.get('confidence')}, grounding {r.get('grounding', {}).get('score')}%.\n"
            f"Verdict rationale: {v.get('rationale')}"
        )
        crews = {k: r[k] for k in ("market_research", "feasibility", "business_planning", "legal_compliance", "funding", "skeptic") if r.get(k)}
        parts.append("DIGEST:\n" + digest_all(crews, 1200))
    else:
        parts.append("No analysis has been run yet.")
    return "\n\n".join(parts)


@router.get("/ideas/{idea_id}/chat")
async def history(idea_id: uuid.UUID, db: DB, who: CurrentPrincipal) -> list[dict[str, Any]]:
    await _own_idea(db, who, idea_id)
    rows = (await db.execute(select(ChatMessage).where(ChatMessage.idea_id == idea_id).order_by(ChatMessage.created_at))).scalars().all()
    return [_msg_out(m) for m in rows]


def _revise(idea: Idea, user_text: str, reply: str) -> dict[str, Any] | None:
    from ai.llm.gateway import get_gateway
    from ai.shared.constants import ModelTier

    try:
        rev = get_gateway().invoke_structured(
            system_prompt=(
                "Decide whether the founder's latest message changes the startup idea itself (customer, pricing, "
                "wedge, scope, business model). If yes, rewrite the idea text in full with only those changes. "
                "If it is only a question or discussion, set should_revise=false. Return JSON only."
            ),
            user_prompt=f"CURRENT IDEA:\n{idea.idea_text}\n\nFOUNDER:\n{user_text}\n\nCO-FOUNDER REPLY:\n{reply}",
            schema_class=IdeaRevision, tier=ModelTier.HEAVY, max_tokens=1800, allow_mock_fallback=False,
        )
    except Exception as err:  # noqa: BLE001 -- a proposal is a bonus, never fail the chat
        logger.warning("revision_failed", error=str(err))
        return None
    text = rev.idea_text.strip()
    if not rev.should_revise or len(text) < 10 or text == idea.idea_text.strip():
        return None
    return {"title": rev.title.strip()[:80] or idea.title, "idea_text": text[:5000], "changes": rev.changes[:8]}


async def _stream(idea_id: uuid.UUID, owner_id: uuid.UUID, user_text: str) -> AsyncIterator[bytes]:
    from ai.llm.chat import stream_chat

    def line(obj: dict[str, Any]) -> bytes:
        return (json.dumps(obj, ensure_ascii=False, default=str) + "\n").encode()

    async with runner._factory()() as db:
        idea = await db.get(Idea, idea_id)
        analysis = (await db.execute(
            select(Analysis).where(Analysis.idea_id == idea_id, Analysis.status == "complete").order_by(Analysis.version.desc())
        )).scalars().first()
        past = (await db.execute(
            select(ChatMessage).where(ChatMessage.idea_id == idea_id).order_by(ChatMessage.created_at.desc()).limit(HISTORY_TURNS)
        )).scalars().all()[::-1]
        db.add(ChatMessage(idea_id=idea_id, owner_id=owner_id, role="user", content=user_text))
        await db.commit()

        messages = [{"role": "system", "content": f"{SYSTEM}\n\n{_context(idea, analysis)}"}]
        messages += [{"role": m.role, "content": m.content} for m in past]
        messages.append({"role": "user", "content": user_text})

        parts: list[str] = []
        try:
            it = stream_chat(messages)
            while (chunk := await asyncio.to_thread(next, it, None)) is not None:
                parts.append(chunk)
                yield line({"type": "delta", "text": chunk})
        except Exception as err:  # noqa: BLE001
            logger.warning("chat_failed", error=str(err))
            yield line({"type": "error", "error": "The AI is unavailable right now. Try again in a moment."})
            return

        reply = "".join(parts).strip()
        proposal = await asyncio.to_thread(_revise, idea, user_text, reply)
        msg = ChatMessage(idea_id=idea_id, owner_id=owner_id, role="assistant", content=reply,
                          proposal=proposal, proposal_status="pending" if proposal else None)
        db.add(msg)
        await db.commit()
        yield line({"type": "message", "message": _msg_out(msg)})


@router.post("/ideas/{idea_id}/chat")
async def send(idea_id: uuid.UUID, body: ChatIn, db: DB, who: CurrentPrincipal) -> StreamingResponse:
    await _own_idea(db, who, idea_id)
    await require_pro(db, who.id, "chat")
    _throttle(who.id)
    return StreamingResponse(_stream(idea_id, who.id, body.message.strip()), media_type="application/x-ndjson")


@router.post("/chat/messages/{message_id}/proposal")
async def decide(message_id: uuid.UUID, body: ProposalAction, db: DB, who: CurrentPrincipal) -> dict[str, Any]:
    m = await db.get(ChatMessage, message_id)
    if m is None or m.owner_id != who.id or not m.proposal or m.proposal_status != "pending":
        raise HTTPException(404, "No pending proposal.")
    m.proposal_status = "accepted" if body.action == "accept" else "dismissed"
    idea = await db.get(Idea, m.idea_id)
    if body.action == "accept":
        idea.idea_text, idea.title = m.proposal["idea_text"], m.proposal["title"]
    await db.commit()
    return {"message": _msg_out(m),
            "idea": {"id": str(idea.id), "title": idea.title, "idea_text": idea.idea_text}}
