"""Shared runner for the spec-driven crews (4-12).

Each crew's phase doc + agent docs (docs/phases, docs/agents) become the system
prompt; prior crew results + optional research become the user prompt; the
gateway returns a validated instance of the crew's result schema.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Optional, Type, TypeVar

from pydantic import BaseModel

from ai.shared.logger import ai_logger

T = TypeVar("T", bound=BaseModel)

_DOCS = Path(__file__).resolve().parents[2] / "docs"
_PRIOR_MAX_CHARS = 6000

# crew_key -> docs/phases/<NN>-*.md prefix
CREW_PHASE = {
    "feasibility": "04",
    "business_planning": "05",
    "product_development": "06",
    "legal_compliance": "07",
    "branding_marketing": "08",
    "funding": "09",
    "growth_scaling": "10",
    "community": "11",
    "reporting": "12",
}


@lru_cache(maxsize=None)
def build_system_prompt(crew_key: str) -> str:
    phase = CREW_PHASE[crew_key]
    phase_doc = next(_DOCS.glob(f"phases/{phase}-*.md"))
    phase_ref = f"phases/{phase_doc.name}"
    agent_docs = [
        p.read_text(encoding="utf-8")
        for p in sorted(_DOCS.glob("agents/*.md"))
        if phase_ref in p.read_text(encoding="utf-8").split("\n", 3)[2]  # line 3 is the **Crew:** line
    ]
    names = [d.splitlines()[0].lstrip("# ").strip() for d in agent_docs]
    return (
        f"You are the {crew_key.replace('_', ' ').title()} crew of a startup-analysis system, acting as "
        f"these named agents working together: {', '.join(names)}.\n"
        "Reason as each agent in turn, then synthesize. Ground every claim in the idea, the prior crew "
        "results, and any research sources provided; never invent citations or statistics.\n"
        "Return ONLY one JSON object matching the required output schema exactly.\n\n"
        f"=== PHASE SPEC ===\n{phase_doc.read_text(encoding='utf-8')}\n\n"
        "=== AGENT SPECS ===\n" + "\n\n---\n\n".join(agent_docs)
    )


def category_of(prior: Optional[dict], fallback: str) -> str:
    """Primary category from the idea-validation result, else the fallback text."""
    cc = ((prior or {}).get("idea_validation") or {}).get("category_classification") or {}
    return cc.get("primary_category") or fallback[:120]


def fetch_research(method: str, *args: Any) -> Optional[str]:
    """Call ResearchManager.<method>(*args) and format it; None on any failure or empty bundle."""
    try:
        from ai.shared.research.prompt_formatting import format_research_bundle_for_prompt
        from ai.shared.research.research_manager import ResearchManager

        text, has_research = format_research_bundle_for_prompt(getattr(ResearchManager(), method)(*args))
        return text if has_research else None
    except Exception as err:  # noqa: BLE001 -- research is best-effort grounding
        ai_logger.warning(f"Research '{method}' unavailable: {err}")
        return None


def build_user_prompt(project_id: str, idea_text: str, prior: Optional[dict], research_text: Optional[str]) -> str:
    # Even per-crew budget so later crews (e.g. reporting) still see every earlier crew.
    budget = _PRIOR_MAX_CHARS // max(len(prior or {}), 1)
    prior_text = "\n".join(
        f"{key}: {json.dumps(value, default=str, separators=(',', ':'))[:budget]}" for key, value in (prior or {}).items()
    )
    parts = [
        f"project_id: {project_id}  (set the `project_id` field to exactly this value)",
        f"Startup idea:\n{idea_text}",
        f"Prior crew results (JSON per crew, may be truncated):\n{prior_text or 'none'}",
    ]
    if research_text:
        parts.append(research_text)
    return "\n\n".join(parts)


# ponytail: one structured call per crew, split per-agent if 32B output too shallow
def run_spec_crew(
    crew_key: str,
    schema_cls: Type[T],
    project_id: str,
    idea_text: str,
    prior: Optional[dict],
    research_text: Optional[str],
    mock_result: Callable[[], T],
    mock_mode: bool,
) -> T:
    if mock_mode:
        return mock_result()

    from ai.llm.gateway import get_gateway
    from ai.shared.constants import ModelTier

    result = get_gateway().invoke_structured(
        system_prompt=build_system_prompt(crew_key),
        user_prompt=build_user_prompt(project_id, idea_text, prior, research_text),
        schema_class=schema_cls,
        tier=ModelTier.HEAVY,
    )
    result.project_id = project_id
    return result
