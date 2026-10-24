"""Connected accounts and report exports.

  GET    /integrations                          connected providers (never the secrets)
  PUT    /integrations/{provider}               connect/replace: github | slack | webhook | notion   (Pro)
  DELETE /integrations/{provider}
  GET    /analyses/{id}/export?format=pdf|md    download the full report (paid report or Pro)
  POST   /analyses/{id}/push/github             create issues from the roadmap (dry_run by default)  (Pro)
  POST   /analyses/{id}/push/{slack|webhook|notion}                                              (Pro)
"""

import re
import uuid
from typing import Any, Literal

import httpx
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import select

from api.deps import DB
from core.auth import CurrentPrincipal
from core.config import get_settings
from core.logging import get_logger
from db.product import Analysis, Idea, Integration
from services.entitlements import paywall, require_pro
from services.netsafe import assert_public_https, seal, unseal
from services.report_export import build_tasks, slack_text, to_markdown, to_pdf

logger = get_logger(__name__)
router = APIRouter(tags=["Integrations"])
Provider = Literal["github", "slack", "webhook", "notion"]
GH = "https://api.github.com"
_REPO = re.compile(r"^[\w.-]+/[\w.-]+$")


class ConnectIn(BaseModel):
    token: str = Field(min_length=8, max_length=600)
    label: str | None = Field(default=None, max_length=120)
    config: dict[str, str] | None = None  # notion: {"parent_page_id": "..."}


class PushIn(BaseModel):
    repo: str | None = None
    dry_run: bool = True


def _gh_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "User-Agent": "startup-igniter"}


async def _get(db: DB, who: CurrentPrincipal, provider: str) -> Integration:
    row = (await db.execute(select(Integration).where(Integration.owner_id == who.id, Integration.provider == provider))).scalar_one_or_none()
    if row is None:
        raise HTTPException(409, f"Connect {provider} first.")
    return row


@router.get("/integrations")
async def list_integrations(db: DB, who: CurrentPrincipal) -> list[dict[str, Any]]:
    rows = (await db.execute(select(Integration).where(Integration.owner_id == who.id))).scalars().all()
    return [{"provider": r.provider, "label": r.label, "config": r.config, "created_at": r.created_at} for r in rows]


@router.put("/integrations/{provider}")
async def connect(provider: Provider, body: ConnectIn, db: DB, who: CurrentPrincipal) -> dict[str, Any]:
    await require_pro(db, who.id, "integrations")
    token, label, config = body.token.strip(), body.label, body.config
    async with httpx.AsyncClient(timeout=15) as c:
        if provider == "github":
            r = await c.get(f"{GH}/user", headers=_gh_headers(token))
            if r.status_code != 200:
                raise HTTPException(422, "GitHub rejected that token.")
            label = label or r.json()["login"]
        elif provider == "slack":
            if not token.startswith("https://hooks.slack.com/"):
                raise HTTPException(422, "Use a Slack incoming-webhook URL (https://hooks.slack.com/...).")
        elif provider == "webhook":
            assert_public_https(token)
        elif provider == "notion":
            if not config or not config.get("parent_page_id"):
                raise HTTPException(422, "Notion needs config.parent_page_id (a page shared with your integration).")
            r = await c.get("https://api.notion.com/v1/users/me",
                            headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"})
            if r.status_code != 200:
                raise HTTPException(422, "Notion rejected that token.")
            label = label or r.json().get("name")
    row = (await db.execute(select(Integration).where(Integration.owner_id == who.id, Integration.provider == provider))).scalar_one_or_none()
    if row is None:
        row = Integration(owner_id=who.id, provider=provider, secret="")
        db.add(row)
    row.secret, row.label, row.config = seal(token), label, config
    await db.commit()
    return {"provider": provider, "label": row.label}


@router.delete("/integrations/{provider}", status_code=204)
async def disconnect(provider: Provider, db: DB, who: CurrentPrincipal) -> None:
    row = (await db.execute(select(Integration).where(Integration.owner_id == who.id, Integration.provider == provider))).scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.commit()


async def _report(db: DB, who: CurrentPrincipal, analysis_id: uuid.UUID, need_pro: bool) -> tuple[Analysis, Idea]:
    a = await db.get(Analysis, analysis_id)
    if a is None or a.owner_id != who.id or a.status != "complete" or not a.result:
        raise HTTPException(404, "Analysis not found.")
    if need_pro:
        await require_pro(db, who.id, "integrations")
    elif not a.unlocked:
        from services.entitlements import is_pro

        if not await is_pro(db, who.id):
            s = get_settings()
            raise paywall("report", f"Unlock the full report for Rs {s.PRICE_REPORT_PAISE // 100} to export it.")
    return a, await db.get(Idea, a.idea_id)


@router.get("/analyses/{analysis_id}/export")
async def export(analysis_id: uuid.UUID, db: DB, who: CurrentPrincipal, format: Literal["pdf", "md"] = "pdf") -> Response:
    a, idea = await _report(db, who, analysis_id, need_pro=False)
    title = f"{idea.title} (v{a.version})"
    slug = re.sub(r"[^a-z0-9]+", "-", idea.title.lower()).strip("-")[:40] or "report"
    if format == "md":
        return Response(to_markdown(title, a.result), media_type="text/markdown; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{slug}-v{a.version}.md"'})
    return Response(to_pdf(title, a.result), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{slug}-v{a.version}.pdf"'})


@router.post("/analyses/{analysis_id}/push/github")
async def push_github(analysis_id: uuid.UUID, body: PushIn, db: DB, who: CurrentPrincipal) -> dict[str, Any]:
    a, idea = await _report(db, who, analysis_id, need_pro=True)
    tasks = build_tasks(a.result)
    repo = (body.repo or idea.github_repo or "").strip().removeprefix("https://github.com/").strip("/")
    if not _REPO.match(repo):
        raise HTTPException(422, "Pick a repository as owner/name.")
    if body.dry_run:
        return {"dry_run": True, "repo": repo, "count": len(tasks), "issues": tasks}
    token = unseal((await _get(db, who, "github")).secret)
    created, failed = [], []
    async with httpx.AsyncClient(timeout=20, headers=_gh_headers(token)) as c:
        for t in tasks:
            r = await c.post(f"{GH}/repos/{repo}/issues", json={
                "title": t["title"], "body": f"{t['body']}\n\n_Created by Startup Igniter (report v{a.version})._",
                "labels": t["labels"]})
            if r.status_code == 201:
                created.append({"title": t["title"], "url": r.json()["html_url"]})
            else:
                failed.append({"title": t["title"], "status": r.status_code})
                if r.status_code in (401, 403, 404):
                    break  # bad token/permissions/repo: don't hammer the API
    return {"dry_run": False, "repo": repo, "created": created, "failed": failed}


@router.post("/analyses/{analysis_id}/push/{provider}")
async def push_message(provider: Literal["slack", "webhook", "notion"], analysis_id: uuid.UUID, db: DB, who: CurrentPrincipal) -> dict[str, Any]:
    a, idea = await _report(db, who, analysis_id, need_pro=True)
    integ = await _get(db, who, provider)
    secret = unseal(integ.secret)
    title = f"{idea.title} (v{a.version})"
    link = f"{get_settings().FRONTEND_URL.rstrip('/')}/results/{a.id}"
    async with httpx.AsyncClient(timeout=20) as c:
        if provider == "slack":
            r = await c.post(secret, json={"text": slack_text(title, a.result, link)})
        elif provider == "webhook":
            assert_public_https(secret)
            r = await c.post(secret, json={"event": "analysis.complete", "title": title, "url": link, "report": a.result})
        else:
            md = to_markdown(title, a.result)
            blocks = [{"object": "block", "type": "paragraph",
                       "paragraph": {"rich_text": [{"type": "text", "text": {"content": para[:1900]}}]}}
                      for para in md.split("\n\n") if para.strip()][:95]
            r = await c.post("https://api.notion.com/v1/pages",
                             headers={"Authorization": f"Bearer {secret}", "Notion-Version": "2022-06-28"},
                             json={"parent": {"page_id": (integ.config or {})["parent_page_id"]},
                                   "properties": {"title": {"title": [{"text": {"content": title}}]}}, "children": blocks})
    if r.status_code >= 300:
        logger.warning("push_failed", provider=provider, status=r.status_code)
        raise HTTPException(502, f"{provider} rejected the request ({r.status_code}).")
    return {"ok": True}
