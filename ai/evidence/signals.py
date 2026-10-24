"""Real-world signals beyond web search: GitHub (competing/adjacent projects, a linked repo)
and Hacker News. All keyless; GITHUB_TOKEN (optional) lifts GitHub rate limits.
"""

import os
import re
from typing import Any, Dict, List, Optional

import httpx

GITHUB = "https://api.github.com"
HN = "https://hn.algolia.com/api/v1"
_TIMEOUT = 15.0
_STOP = {"the", "a", "an", "and", "or", "for", "to", "of", "in", "on", "with", "that", "is", "are", "app", "platform", "startup", "using", "based"}


def _gh_headers() -> Dict[str, str]:
    h = {"Accept": "application/vnd.github+json", "User-Agent": "startup-igniter"}
    if token := os.environ.get("GITHUB_TOKEN"):
        h["Authorization"] = f"Bearer {token}"
    return h


def keywords(topic: str, n: int = 5) -> str:
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z\-]{2,}", topic.lower()) if w not in _STOP]
    return " ".join(list(dict.fromkeys(words))[:n])


def github_competitors(topic: str, limit: int = 6) -> List[Dict[str, Any]]:
    """Top repositories for the topic: stars, last push, open issues."""
    q = keywords(topic)
    if not q:
        return []
    r = httpx.get(f"{GITHUB}/search/repositories", params={"q": q, "sort": "stars", "per_page": limit},
                  headers=_gh_headers(), timeout=_TIMEOUT)
    r.raise_for_status()
    return [
        {
            "full_name": i["full_name"], "url": i["html_url"], "description": i.get("description") or "",
            "stars": i["stargazers_count"], "open_issues": i["open_issues_count"],
            "language": i.get("language"), "pushed_at": i.get("pushed_at"), "created_at": i.get("created_at"),
            "archived": i.get("archived", False),
        }
        for i in r.json().get("items", [])
    ]


def repo_profile(full_name: str) -> Optional[Dict[str, Any]]:
    """README excerpt, languages and activity of the founder's own repo (owner/name)."""
    full_name = full_name.strip().removeprefix("https://github.com/").strip("/")
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", full_name):
        return None
    with httpx.Client(headers=_gh_headers(), timeout=_TIMEOUT) as c:
        meta = c.get(f"{GITHUB}/repos/{full_name}")
        meta.raise_for_status()
        m = meta.json()
        langs = c.get(f"{GITHUB}/repos/{full_name}/languages").json()
        readme = c.get(f"{GITHUB}/repos/{full_name}/readme", headers={**_gh_headers(), "Accept": "application/vnd.github.raw+json"})
        commits = c.get(f"{GITHUB}/repos/{full_name}/commits", params={"per_page": 30})
    return {
        "full_name": m["full_name"], "url": m["html_url"], "description": m.get("description") or "",
        "stars": m["stargazers_count"], "open_issues": m["open_issues_count"], "pushed_at": m.get("pushed_at"),
        "languages": langs if isinstance(langs, dict) else {},
        "recent_commits": len(commits.json()) if commits.status_code == 200 else None,
        "readme": readme.text[:3000] if readme.status_code == 200 else "",
    }


def hacker_news(topic: str, limit: int = 6) -> Dict[str, Any]:
    q = keywords(topic)
    if not q:
        return {"query": q, "total": 0, "stories": []}
    r = httpx.get(f"{HN}/search", params={"query": q, "tags": "story", "hitsPerPage": limit}, timeout=_TIMEOUT)
    r.raise_for_status()
    d = r.json()
    return {
        "query": q, "total": d.get("nbHits", 0),
        "stories": [
            {"title": h.get("title") or "", "points": h.get("points") or 0, "comments": h.get("num_comments") or 0,
             "url": f"https://news.ycombinator.com/item?id={h['objectID']}", "date": (h.get("created_at") or "")[:10]}
            for h in d.get("hits", [])
        ],
    }


def add_to_pool(pool: Any, key: str, data: Any) -> None:
    """Record structured signals on the pool and register citable sources for them."""
    if not data:
        return
    pool.signals[key] = data
    if key == "github":
        for r in data:
            pool.add(r["url"], f"GitHub: {r['full_name']}", (
                f"{r['description']} Stars: {r['stars']}. Open issues: {r['open_issues']}. "
                f"Language: {r['language']}. Last push: {r['pushed_at']}. Archived: {r['archived']}."), "github")
    elif key == "hacker_news":
        for s in data["stories"]:
            pool.add(s["url"], f"HN: {s['title']}",
                     f"{s['title']} ({s['points']} points, {s['comments']} comments, {s['date']})", "hackernews")
    elif key == "repo":
        pool.add(data["url"], f"Linked repo: {data['full_name']}", (
            f"{data['description']} Languages: {', '.join(data['languages'])}. Stars: {data['stars']}. "
            f"Open issues: {data['open_issues']}. Last push: {data['pushed_at']}. README: {data['readme'][:1200]}"), "github")
