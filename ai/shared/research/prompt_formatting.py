"""Format a ResearchBundle into prompt text agents can ground their answers in.

Shared by every agent that accepts a `research_bundle` on its context (today:
market_research_agent.py; research_patent's patent_search_agent.py is the
next natural consumer). Centralizing this in one place means the citation
instruction and source formatting stay consistent across agents instead of
each one inventing its own shape.
"""

from typing import List, Optional, Tuple

from ai.shared.research.research_bundle import ResearchBundle

# Keep the prompt bounded -- a bundle can carry dozens of scraped pages across
# providers, and every extra token here is inference cost on every one of the
# ~20 (eventually 66) agent calls per run.
_MAX_SOURCES_IN_PROMPT = 8


def _collect_snippets(bundle: ResearchBundle) -> List[dict]:
    """Flatten every content-bearing bucket into one (source, url, content) list."""
    snippets: List[dict] = []
    for bucket_name in (
        "market_articles",
        "industry_reports",
        "trend_reports",
        "competitor_data",
        "research_papers",
        "government_sources",
        "startup_sources",
        "news_articles",
    ):
        for item in getattr(bundle, bucket_name):
            url = item.get("url", "")
            content = item.get("content") or item.get("summary") or item.get("snippet") or ""
            title = item.get("title") or item.get("source") or url
            if content and url:
                snippets.append({"title": title, "url": url, "content": content})
    return snippets


def format_research_bundle_for_prompt(bundle: Optional[ResearchBundle]) -> Tuple[str, bool]:
    """Render a bundle as a numbered source list for the prompt.

    Returns (block_text, has_grounding). `has_grounding` is False when the
    bundle is None/empty, so the caller can adjust its citation instruction
    ("cite these" vs. "don't invent citations") instead of always claiming
    sources exist.
    """
    if bundle is None:
        return "", False

    snippets = _collect_snippets(bundle)[:_MAX_SOURCES_IN_PROMPT]
    if not snippets:
        return "", False

    lines = ["\nExternal research sources (cite these, do not invent others):"]
    for i, snippet in enumerate(snippets, start=1):
        lines.append(f"[{i}] {snippet['title']} — {snippet['url']}\n    {snippet['content']}")
    return "\n".join(lines), True
