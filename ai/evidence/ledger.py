"""Evidence ledger: extract checkable claims from each crew's output, then verify
each against the shared source pool.

A claim is `supported` only if the verifier returns a quote that appears
VERBATIM in a retrieved passage; otherwise it is `unsupported` (no relevant
source) or `contradicted`. The grounding score is supported / total.
"""

import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Literal, Tuple

from pydantic import BaseModel, Field

from ai.evidence.sources import SourcePool
from ai.shared.constants import ModelTier
from ai.shared.digest import digest_crew
from ai.shared.logger import ai_logger

CLAIMS_PER_CREW = 5
PASSAGE_CHARS = 420
MIN_OVERLAP = 0.2
_TOKEN = re.compile(r"[a-z0-9][a-z0-9.%$,]*")
_STOP = frozenset("the a an and or of to in on for with is are was were be by as at from that this it its their our your has have had".split())
# Crews whose output is opinion/synthesis rather than checkable fact.
SKIP_CREWS = {"skeptic", "reporting", "community"}
_SELF_REFERENTIAL = re.compile(r"\b(score|confidence|valuation|fundraising target|checklist has been|pitch deck)\b", re.I)
RETRY_SEARCHES = 12  # targeted web searches for claims the shared pool could not support


class ClaimItem(BaseModel):
    claim: str = Field(description="One self-contained sentence, copied or lightly condensed from the section.")
    kind: Literal["external_fact", "estimate", "plan", "own_feature", "score"] = Field(
        description=(
            "external_fact: something about the world a web page could confirm (a market size reported by someone, a named "
            "competitor and what it offers, a price, a regulation, a statistic). estimate: a figure this analysis computed. "
            "plan: a recommendation, target, KPI or strategy. own_feature: what the startup itself would do or build. "
            "score: a score, rating or confidence."
        )
    )


class ClaimList(BaseModel):
    claims: List[ClaimItem] = Field(default_factory=list, description="Up to 8 claims from the section; may be empty.")


class ClaimCheck(BaseModel):
    label: Literal["supported", "contradicted", "unrelated"] = Field(
        description="supported: the passage states the claim. contradicted: the passage states the opposite. unrelated: otherwise."
    )
    quote: str = Field(default="", description="Exact sentence copied from the passage that supports/contradicts the claim; empty if unrelated.")


def _tokens(text: str) -> set[str]:
    return {t.strip(".,") for t in _TOKEN.findall(text.lower()) if t not in _STOP and len(t) > 1}


def _passages(pool: SourcePool) -> List[Tuple[int, str, set[str]]]:
    """(source_id, passage, tokens): overlapping sentence windows of each source."""
    out = []
    for s in pool.sources:
        sentences = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", s.text))
        window = ""
        for sent in sentences:
            window = f"{window} {sent}".strip()
            if len(window) >= PASSAGE_CHARS:
                out.append((s.id, window, _tokens(window)))
                window = sent
        if window:
            out.append((s.id, window, _tokens(window)))
    return out


def best_passages(claim: str, passages: List[Tuple[int, str, set[str]]], k: int = 2) -> List[Tuple[float, int, str]]:
    """Top-k passages by token overlap with the claim. Numbers count double: they carry the claim."""
    ct = _tokens(claim)
    if not ct:
        return []
    weight = {t: (2.0 if any(c.isdigit() for c in t) else 1.0) for t in ct}
    total = sum(weight.values())
    scored = [(sum(weight[t] for t in ct & pt) / total, sid, text) for sid, text, pt in passages]
    return sorted((x for x in scored if x[0] >= MIN_OVERLAP), key=lambda x: -x[0])[:k]


def _norm(s: str) -> str:
    return re.sub(r"\W+", " ", s.lower()).strip()


def _extract(gw: Any, crew: str, result: Any) -> List[str]:
    try:
        out = gw.invoke_structured(
            system_prompt="You extract checkable factual claims from a startup analysis section. Return JSON only.",
            user_prompt=f"Section: {crew}\n\n{digest_crew(crew, result, 3500)}",
            schema_class=ClaimList, tier=ModelTier.FAST, max_tokens=2000, allow_mock_fallback=False,
        )
        facts = [c.claim.strip() for c in out.claims if c.kind == "external_fact"]
        return [c for c in facts if len(c) > 15 and not _SELF_REFERENTIAL.search(c)][:CLAIMS_PER_CREW]
    except Exception as err:  # noqa: BLE001
        ai_logger.warning(f"claim extraction failed for {crew}: {err}")
        return []


def _check(gw: Any, claim: str, hits: List[Tuple[float, int, str]]) -> Dict[str, Any] | None:
    for score, sid, text in hits:
        try:
            verdict = gw.invoke_structured(
                system_prompt="You verify a claim against ONE passage. Quote exactly; never paraphrase. Return JSON only.",
                user_prompt=f"Claim: {claim}\n\nPassage: {text}",
                schema_class=ClaimCheck, tier=ModelTier.FAST, max_tokens=300, allow_mock_fallback=False,
            )
        except Exception as err:  # noqa: BLE001
            ai_logger.warning(f"claim check failed: {err}")
            continue
        if verdict.label == "unrelated":
            continue
        quote_ok = bool(verdict.quote) and _norm(verdict.quote) in _norm(text)
        if verdict.label == "supported" and not quote_ok:
            continue  # unverifiable quote: never count as supported
        return {"status": verdict.label, "source_id": sid, "quote": verdict.quote if quote_ok else "", "match": round(score, 2)}
    return None


def _search_claim(claim: str) -> List[Dict[str, str]]:
    """Top web pages for the claim text. [] on any failure (search is best-effort)."""
    try:
        from ai.shared.research.web_provider import _search

        return [dict(h) for h in _search(claim[:200], 4)]
    except Exception as err:  # noqa: BLE001
        ai_logger.debug(f"targeted claim search failed: {err}")
        return []


def build_ledger(results: Dict[str, Any], pool: SourcePool, gw: Any) -> Dict[str, Any]:
    """results: crew_key -> result dict. Returns {entries, grounding_score, per_crew, source_count}."""
    passages = _passages(pool)
    crews = {k: v for k, v in results.items() if v and k not in SKIP_CREWS}
    with ThreadPoolExecutor(max_workers=4) as ex:
        extracted = dict(zip(crews, ex.map(lambda k: _extract(gw, k, crews[k]), crews)))
        jobs = [(k, c) for k, claims in extracted.items() for c in claims]

        def run(job: Tuple[str, str]) -> Dict[str, Any]:
            crew, claim = job
            found = _check(gw, claim, best_passages(claim, passages)) if passages else None
            entry: Dict[str, Any] = {"crew": crew, "claim": claim, **(found or {"status": "unsupported", "source_id": None, "quote": ""})}
            return entry

        entries = list(ex.map(run, jobs))

        # Second pass: search the web for each unsupported claim itself, then re-check against what comes back.
        todo = [e for e in entries if e["status"] == "unsupported"][:RETRY_SEARCHES]
        if todo:
            fetched = list(ex.map(lambda e: _search_claim(e["claim"]), todo))
            for e, hits in zip(todo, fetched):
                new = []
                for h in hits:
                    before = len(pool.sources)
                    pool.add(h["url"], h["title"], h["content"])
                    if len(pool.sources) > before:
                        new.append(pool.sources[-1])
                if not new:
                    continue
                local = _passages(SourcePool(sources=new))
                found = _check(gw, e["claim"], best_passages(e["claim"], local))
                if found:
                    e.update(found)
    by_id = {s.id: s for s in pool.sources}
    for e in entries:
        s = by_id.get(e["source_id"])
        e["source"] = {"url": s.url, "title": s.title} if s else None
    total = len(entries)
    supported = sum(e["status"] == "supported" for e in entries)
    per_crew: Dict[str, Any] = {}
    for e in entries:
        c = per_crew.setdefault(e["crew"], {"total": 0, "supported": 0})
        c["total"] += 1
        c["supported"] += e["status"] == "supported"
    return {
        "entries": entries,
        "grounding_score": round(100 * supported / total, 1) if total else None,
        "per_crew": per_crew,
        "source_count": len(pool.sources),
        "contradicted": sum(e["status"] == "contradicted" for e in entries),
    }
