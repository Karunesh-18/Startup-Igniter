"""Turn an analysis report into portable artifacts: markdown / PDF, GitHub issues, chat messages."""

import html
from typing import Any

from ai.pipeline import CREW_LABELS
from ai.shared.digest import digest_crew

DISCLAIMER = "AI-generated analysis. Verify findings independently. Legal content is a draft: have a qualified lawyer review it."
MAX_TASKS = 40


def build_tasks(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Actionable items from the report: [{title, body, labels}]."""
    tasks: list[dict[str, Any]] = []
    for f in (result.get("product_development") or {}).get("mvp_features", []):
        pri = f.get("priority", "Must Have")
        tasks.append({"title": f"[MVP] {f['feature_name']}", "labels": ["mvp", pri.lower().replace(" ", "-")],
                      "body": f"{f.get('description', '')}\n\nPriority: {pri} · Complexity: {f.get('complexity', '?')}"})
    for c in (result.get("legal_compliance") or {}).get("compliance_checklist", []):
        if c.get("is_mandatory", True):
            tasks.append({"title": f"[Compliance] {c['title']}", "labels": ["compliance"],
                          "body": f"{c.get('description', '')}\n\nBody: {c.get('regulatory_body') or 'n/a'}"})
    for r in (result.get("skeptic") or {}).get("top_risks", []):
        tasks.append({"title": f"[Risk] {r['risk'][:90]}", "labels": ["risk"],
                      "body": f"Likelihood {r['likelihood']}/100 · Impact {r['impact']}/100\n\nMitigation: {r['mitigation']}"})
    for h in result.get("hypotheses", []):
        tasks.append({"title": f"[Experiment] {h['hypothesis'][:90]}", "labels": ["experiment"],
                      "body": f"Hypothesis: {h['hypothesis']}\n\nMeasure: {h['metric']}"})
    for s in result.get("strategic_recommendations", []) or []:
        tasks.append({"title": f"[Strategy] {str(s)[:90]}", "labels": ["strategy"], "body": str(s)})
    return tasks[:MAX_TASKS]


def to_markdown(title: str, result: dict[str, Any]) -> str:
    v = result.get("verdict") or {}
    g = result.get("grounding") or {}
    lines = [
        f"# {title}", f"*{DISCLAIMER}*", "",
        f"**Readiness {result.get('overall_readiness_score')}/100** "
        f"(range {result.get('score_range', {}).get('low')}-{result.get('score_range', {}).get('high')}) · "
        f"**Verdict: {str(v.get('label', 'n/a')).upper()}** · confidence {result.get('confidence')}% · "
        f"{g.get('score')}% of {g.get('claims')} checked claims supported by sources",
        "", v.get("rationale") or "", "",
    ]
    if v.get("would_change_my_mind"):
        lines += ["**What would change this verdict**", *[f"- {x}" for x in v["would_change_my_mind"]], ""]
    if result.get("executive_summary"):
        lines += ["## Executive summary", result["executive_summary"], ""]
    sk = result.get("skeptic") or {}
    if sk:
        lines += ["## Skeptic review", "**Bull case**", *[f"- {x}" for x in sk.get("bull_case", [])],
                  "", "**Bear case**", *[f"- {x}" for x in sk.get("bear_case", [])], "",
                  "**Pre-mortem**", sk.get("pre_mortem", ""), ""]
    for key, label in CREW_LABELS.items():
        if key in ("skeptic",) or not result.get(key):
            continue
        lines += [f"## {label}", "```", digest_crew(key, result[key], 2600), "```", ""]
    cited = [e for e in result.get("ledger", []) if e.get("status") == "supported" and e.get("source")]
    if cited:
        lines += ["## Evidence", *[f"- {e['claim']} — [{e['source']['title'] or e['source']['url']}]({e['source']['url']})" for e in cited[:40]], ""]
    return "\n".join(lines)


def to_pdf(title: str, result: dict[str, Any]) -> bytes:
    from markdown_it import MarkdownIt
    from weasyprint import HTML

    body = MarkdownIt("commonmark").enable("table").render(to_markdown(title, result))
    css = ("body{font-family:Helvetica,Arial,sans-serif;font-size:11px;line-height:1.5;color:#1a1a1a;margin:0}"
           "h1{font-size:22px}h2{font-size:15px;margin-top:20px;border-bottom:1px solid #ddd;padding-bottom:3px}"
           "pre{white-space:pre-wrap;background:#f6f6f6;padding:8px;border-radius:4px;font-size:10px}"
           "@page{margin:18mm}")
    return HTML(string=f"<html><head><meta charset='utf-8'><style>{css}</style></head><body>{body}</body></html>").write_pdf()


def slack_text(title: str, result: dict[str, Any], url: str | None = None) -> str:
    v = result.get("verdict") or {}
    head = f"*{html.escape(title)}* — readiness {result.get('overall_readiness_score')}/100, verdict {str(v.get('label', 'n/a')).upper()}"
    return head + (f"\n{v.get('rationale', '')}" if v.get("rationale") else "") + (f"\n<{url}|Open report>" if url else "")
