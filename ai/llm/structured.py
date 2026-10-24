"""Structured-output helpers: <think> stripping, repair-loop prompting, and a
schema-conformant dummy generator used by the mock provider and by tests.
"""

import re
from typing import Any, List, Type, get_args, get_origin

from pydantic import BaseModel, ValidationError

_THINK_BLOCK_RE = re.compile(r"<think>[\s\S]*?</think>", re.IGNORECASE)


def strip_think_blocks(text: str) -> str:
    """Remove Qwen3/DeepSeek-style <think>...</think> reasoning blocks.

    Reasoning models emit these before the final answer. Left in place, the
    greedy `(\\{[\\s\\S]*\\})` salvage regex in ai.shared.output_validator can
    swallow braces from *inside* the reasoning text and hand back a malformed
    or wrong JSON object. Guided decoding (Workstream A's other half) makes
    this moot for the self-hosted path since the schema is enforced at the
    token level, but stripping stays cheap insurance for the fallback
    providers and for any reasoning-tier call.
    """
    if not text:
        return text
    text = _THINK_BLOCK_RE.sub("", text)
    # An unclosed block means generation stopped mid-thought; nothing after it is an answer.
    return text.split("<think>", 1)[0].strip()


def build_repair_prompt(original_user_prompt: str, raw_output: str, errors: List[dict]) -> str:
    """Build a follow-up user prompt asking the model to fix schema violations.

    Used by the gateway's bounded repair loop: on OutputValidationError, we
    resend the same conversation with the model's own bad output and the
    exact field errors, rather than starting over from scratch or (as today)
    losing the entire multi-agent run to one bad field.
    """
    error_lines = "\n".join(
        f"- {'.'.join(str(p) for p in err.get('loc', []))}: {err.get('msg', 'invalid value')}"
        for err in errors
    )
    return (
        f"{original_user_prompt}\n\n"
        "---\n"
        "Your previous response failed schema validation. Fix ONLY the listed "
        "problems and return the complete corrected JSON object (not a diff, "
        "not an explanation — the full object).\n\n"
        f"Your previous response:\n{raw_output}\n\n"
        f"Validation errors:\n{error_lines}"
    )


def _dummy_value_for_annotation(annotation: Any, field_name: str) -> Any:
    """Produce a plausible placeholder value for a Pydantic field's type annotation.

    Used only by the mock provider and by tests that need a schema-valid
    instance without a real model call — never for anything user-facing.
    """
    origin = get_origin(annotation)

    if origin is list or origin is List:
        (inner,) = get_args(annotation) or (str,)
        return [_dummy_value_for_annotation(inner, field_name)]

    if origin is not None:  # Optional[...] / Union[...] — use the first non-None arg
        args = [a for a in get_args(annotation) if a is not type(None)]
        return _dummy_value_for_annotation(args[0], field_name) if args else None

    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return generate_mock_json(annotation)

    if annotation is bool:
        return True
    if annotation is int:
        return 50
    if annotation is float:
        return 0.5
    return f"Mock {field_name.replace('_', ' ')}"


_ENUM_CHOICES_RE = re.compile(r"must be one of \{([^}]+)\}")


def _extract_enum_choice(error_msg: str) -> Any:
    """Pull a usable literal out of a custom validator's error message.

    Several schemas in ai/schemas/ use a plain `str` field plus a
    `@field_validator` that raises "X must be one of {'a', 'b', ...}"
    (e.g. ProblemStatementAnalysis.problem_severity) rather than a
    `Literal[...]` type annotation the generator could introspect
    statically. Parsing the validator's own error message is the only
    generic way to recover a valid value without special-casing every
    field name.
    """
    match = _ENUM_CHOICES_RE.search(error_msg)
    if not match:
        return None
    choices = re.findall(r"'([^']*)'", match.group(1))
    return choices[0] if choices else None


def generate_mock_json(schema_class: Type[BaseModel]) -> dict:
    """Generate a minimal dict that validates against `schema_class`.

    Only fills fields that don't already have a default, so real defaults
    from the schema are preserved. Respects `ge`/`le` numeric bounds where
    declared, since several schemas in ai/schemas/ use a 0-100 or 0.0-1.0
    scale and a lazy constant like `50` for a `ge=0, le=1` field would fail
    validation.

    After the first pass, self-corrects against the schema's own custom
    `@field_validator`s (not just its type annotations) by re-validating
    and substituting a value parsed out of each failure's error message,
    bounded to a few passes so a validator this can't satisfy fails fast
    rather than looping.
    """
    values: dict = {}
    for name, field in schema_class.model_fields.items():
        if field.is_required():
            value = _dummy_value_for_annotation(field.annotation, name)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                lo, hi = None, None
                for meta in field.metadata:
                    lo = getattr(meta, "ge", lo) or getattr(meta, "gt", lo)
                    hi = getattr(meta, "le", hi) or getattr(meta, "lt", hi)
                if hi is not None and hi <= 1.0:
                    value = 0.5 if isinstance(value, float) else 1
                elif lo is not None or hi is not None:
                    value = min(max(value, lo or 0), hi if hi is not None else value)
            values[name] = value

    for _ in range(5):
        try:
            schema_class.model_validate(values)
            break
        except ValidationError as exc:
            made_progress = False
            for err in exc.errors():
                loc = err.get("loc", ())
                if len(loc) != 1 or loc[0] not in values:
                    continue
                choice = _extract_enum_choice(err.get("msg", ""))
                if choice is not None and values[loc[0]] != choice:
                    values[loc[0]] = choice
                    made_progress = True
            if not made_progress:
                break  # best-effort: return what we have rather than loop forever

    return values
