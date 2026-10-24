"""Compact, structured digests of crew results for downstream prompts and chat.

Raw JSON truncated at N characters drops whatever fields come last; a digest
keeps every crew's headline score, summary text and the first items of its
lists, within a fixed per-crew budget.
"""

from typing import Any

SKIP_SCORE_KEYS = ("confidence", "similarity")


def pct(value: float, key: str = "") -> float:
    """Normalise to 0-100. Schemas use 0-100 for scores and 0-1 for confidence."""
    scaled = value * 100 if "confidence" in key and value <= 1 else value
    return max(0.0, min(100.0, float(scaled)))


def crew_score(result: Any) -> float | None:
    """One headline 0-100 score: an `overall_*` field, else the mean of `*_score` fields, else confidence."""
    if not isinstance(result, dict):
        return None
    nums = {k: v for k, v in result.items() if k.endswith("_score") and isinstance(v, (int, float)) and not isinstance(v, bool)}
    for k, v in nums.items():
        if k.startswith("overall_"):
            return round(pct(v, k), 1)
    scores = {k: v for k, v in nums.items() if not k.startswith(SKIP_SCORE_KEYS)}
    if scores:
        return round(sum(pct(v, k) for k, v in scores.items()) / len(scores), 1)
    conf = nums.get("confidence_score")
    return round(pct(conf, "confidence_score"), 1) if conf is not None else None


def crew_confidence(result: Any) -> float | None:
    if isinstance(result, dict) and isinstance(result.get("confidence_score"), (int, float)):
        return round(pct(result["confidence_score"], "confidence_score"), 1)
    return None


def _flatten(value: Any, path: str, out: list[str], depth: int, cap: int) -> None:
    if len(out) >= cap:
        return
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, (int, float)):
        out.append(f"{path}={value:g}" if isinstance(value, float) else f"{path}={value}")
    elif isinstance(value, str):
        if value.strip() and path.rsplit(".", 1)[-1] not in ("project_id",):
            out.append(f"{path}: {value.strip()[:180]}")
    elif isinstance(value, list):
        items = [x for x in value[:4]]
        if items and all(isinstance(x, str) for x in items):
            out.append(f"{path}: " + " | ".join(x[:120] for x in items))
        elif depth < 2:
            for i, x in enumerate(items[:3]):
                _flatten(x, f"{path}[{i}]", out, depth + 1, cap)
    elif isinstance(value, dict) and depth < 3:
        for k, v in value.items():
            _flatten(v, f"{path}.{k}" if path else k, out, depth + 1, cap)


def digest_crew(key: str, result: Any, budget: int = 2000) -> str:
    """Headline score + the most informative fields of one crew result, within `budget` chars."""
    if result is None:
        return f"{key}: (not available)"
    score = crew_score(result)
    lines: list[str] = []
    _flatten(result, "", lines, 0, 60)
    # Summaries first, then everything else in schema order.
    lines.sort(key=lambda s: 0 if "summary" in s.split(":", 1)[0] else 1)
    text = f"{key} [score {score if score is not None else 'n/a'}/100]\n"
    for line in lines:
        if len(text) + len(line) + 3 > budget:
            break
        text += f"- {line}\n"
    return text.rstrip()


def digest_all(prior: dict[str, Any] | None, budget_per_crew: int = 2000) -> str:
    return "\n\n".join(digest_crew(k, v, budget_per_crew) for k, v in (prior or {}).items())
