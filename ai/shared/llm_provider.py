"""Back-compat shim over ai.llm.gateway.

Historically this module hardcoded two provider URLs (Groq, OpenRouter) and
picked between them by which API key happened to be set — see git history
for the pre-migration version. It's now a thin wrapper so the ~20 existing
call sites across ai/agents/** and ai/crews/idea_validation/crew.py keep
working with minimal churn while they migrate to passing `schema_class` and
`tier` directly (see ai/llm/gateway.py for the real implementation).

`LLMFactory` (the CrewAI-oriented factory) has been removed: CrewAI was never
actually installed (`HAS_CREWAI` was always False), so it only ever returned
an inert `LLMConfig` object nothing used, while also demanding
`GROQ_API_KEY` even on the OpenRouter path and shipping a `get_llm(tier=...)`
signature that 7 call sites got wrong (they passed `tier=`, not
`model_tier=`, and were silently never exercised because those callers use
`run_*_agent()`, not `get_*_agent()`).
"""

from typing import Optional, Type

from pydantic import BaseModel

from ai.llm.gateway import get_gateway
from ai.shared.constants import ModelTier

__all__ = ["call_live_llm"]


def _infer_tier(model_name: Optional[str]) -> ModelTier:
    """Best-effort tier inference for callers that still pass a raw model
    name instead of a ModelTier. New call sites should pass `tier=` directly.
    """
    if not model_name:
        return ModelTier.HEAVY
    lowered = model_name.lower()
    if any(marker in lowered for marker in ("8b", "instant", "fast", "-8b-")):
        return ModelTier.FAST
    return ModelTier.HEAVY


def call_live_llm(
    system_prompt: str,
    user_prompt: str,
    model_name: Optional[str] = None,
    temperature: float = 0.2,
    timeout: float = 45.0,
    max_retries: int = 8,
    schema_class: Optional[Type[BaseModel]] = None,
    tier: Optional[ModelTier] = None,
) -> str:
    """Execute a live LLM completion via the gateway (selfhosted -> mock).

    Args:
        model_name: Legacy parameter. When `tier` is not given, the tier is
            inferred from this string (e.g. containing "8b"/"instant" -> FAST).
            Prefer passing `tier=` directly in new code.
        schema_class: When given, the self-hosted provider grammar-constrains
            generation to this Pydantic schema (guided decoding); the mock
            provider uses it to produce schema-shaped placeholder output.
        tier: Preferred over `model_name` for selecting FAST vs HEAVY/REASONING.

    Returns:
        Raw response text (not yet parsed/validated — callers still run this
        through ai.shared.output_validator.validate_output as before).
    """
    resolved_tier = tier if tier is not None else _infer_tier(model_name)
    return get_gateway().invoke(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        tier=resolved_tier,
        temperature=temperature,
        timeout=timeout,
        max_retries=max_retries,
        schema_class=schema_class,
    )
