"""Shared source pool: one numbered, de-duplicated set of web/GitHub/HN sources
that every crew can cite and the evidence ledger verifies claims against.
"""

import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Dict, List

from ai.shared.logger import ai_logger
from ai.shared.research.research_manager import ResearchManager

_BUCKETS = (
    "market_articles", "industry_reports", "trend_reports", "competitor_data", "research_papers",
    "government_sources", "startup_sources", "news_articles", "scraped_pages",
)
PROMPT_SOURCES = 14
PROMPT_CHARS = 450
_WS = re.compile(r"\s+")


@dataclass
class Source:
    id: int
    url: str
    title: str
    text: str
    kind: str = "web"  # web|github|hackernews


@dataclass
class SourcePool:
    sources: List[Source] = field(default_factory=list)
    signals: Dict[str, Any] = field(default_factory=dict)  # structured extras (github repos, HN stats)

    def add(self, url: str, title: str, text: str, kind: str = "web") -> None:
        url = (url or "").strip()
        if not url or not (text or "").strip() or any(s.url == url for s in self.sources):
            return
        self.sources.append(Source(len(self.sources) + 1, url, (title or "").strip()[:160], text.strip(), kind))

    def prompt_block(self) -> str:
        if not self.sources:
            return ""
        lines = ["Shared research sources (cite as [n]; use ONLY facts they support; never invent figures):"]
        for s in self.sources[:PROMPT_SOURCES]:
            lines.append(f"[{s.id}] {s.title} ({s.url})\n{_WS.sub(' ', s.text)[:PROMPT_CHARS]}")
        return "\n".join(lines)

    def public(self) -> List[Dict[str, Any]]:
        return [{"id": s.id, "url": s.url, "title": s.title, "kind": s.kind} for s in self.sources]


def gather_sources(idea_text: str, category: str | None = None, github_repo: str | None = None) -> SourcePool:
    """Best-effort: never raises. Runs the web queries and signal lookups concurrently."""
    from ai.evidence import signals

    rm = ResearchManager()
    topic = (category or idea_text)[:160]
    jobs = {
        "market": lambda: rm.gather_market_research(idea_text[:200], category),
        "competitors": lambda: rm.gather_competitor_research(idea_text[:200], category or topic),
        "trends": lambda: rm.gather_trend_research(topic),
        "regulation": lambda: rm.gather_regulatory_research(topic),
        "funding": lambda: rm.gather_funding_research(topic),
        "tech": lambda: rm.gather_tech_research(idea_text[:200]),
        "news": lambda: rm.gather_news_research(topic),
    }
    pool = SourcePool()
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {name: ex.submit(fn) for name, fn in jobs.items()}
        extras = {
            "github": ex.submit(signals.github_competitors, topic),
            "hacker_news": ex.submit(signals.hacker_news, topic),
        }
        if github_repo:
            extras["repo"] = ex.submit(signals.repo_profile, github_repo)
        for name, fut in futures.items():
            try:
                bundle = fut.result(timeout=90)
            except Exception as err:  # noqa: BLE001
                ai_logger.warning(f"source query '{name}' failed: {err}")
                continue
            for bucket in _BUCKETS:
                for e in getattr(bundle, bucket, []) or []:
                    pool.add(e.get("url", ""), e.get("title", ""), e.get("content") or e.get("snippet") or "")
        for key, fut in extras.items():
            try:
                signals.add_to_pool(pool, key, fut.result(timeout=30))
            except Exception as err:  # noqa: BLE001
                ai_logger.warning(f"signal '{key}' failed: {err}")
    ai_logger.info(f"SourcePool: {len(pool.sources)} sources")
    return pool
