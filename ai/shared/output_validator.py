"""Reusable Output Validation Utility for Startup Igniter AI Agents.

Provides robust JSON extraction, sanitization, logging, and Pydantic schema validation.
"""

import json
import re
from typing import Any, Dict, Type, TypeVar
from pydantic import BaseModel, ValidationError

from ai.shared.errors import JSONParsingError, OutputValidationError
from ai.shared.logger import ai_logger

T = TypeVar("T", bound=BaseModel)


def clean_json_text(raw_text: str) -> str:
    """Sanitize raw LLM response text to isolate JSON content.

    Strips markdown code blocks (e.g. ```json ... ```) and leading/trailing whitespace.

    Args:
        raw_text: Raw string output from LLM response.

    Returns:
        Clean JSON payload string.
    """
    if not raw_text:
        return ""

    text = raw_text.strip()

    # Pattern matching ```json ... ``` or ``` ... ```
    code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if code_block_match:
        return code_block_match.group(1).strip()

    # Extract inner JSON object {...} or array [...] if surrounded by text
    json_structure_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if json_structure_match:
        return json_structure_match.group(1).strip()

    return text


def parse_json_safely(raw_output: str) -> Dict[str, Any]:
    """Safely parse raw LLM text into a Python dictionary.

    Args:
        raw_output: Raw text output string from LLM call.

    Returns:
        Parsed dictionary.

    Raises:
        JSONParsingError: If JSON syntax decoding fails.
    """
    raw_str = (raw_output or "").strip()
    sanitized_text = clean_json_text(raw_str)

    try:
        data = json.loads(sanitized_text)
    except json.JSONDecodeError as err:
        # Fallback: use raw_decode starting from first '{' or '['
        first_brace = sanitized_text.find('{')
        first_bracket = sanitized_text.find('[')
        if first_brace != -1 or first_bracket != -1:
            indices = [i for i in (first_brace, first_bracket) if i != -1]
            start_idx = min(indices)
            try:
                data, _ = json.JSONDecoder().raw_decode(sanitized_text, start_idx)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                pass

        ai_logger.error(
            f"JSON Decode Failure: {str(err)} | Snippet: {raw_str[:250]!r}"
        )
        raise JSONParsingError(
            f"Failed to decode valid JSON from LLM output: {str(err)}",
            details={
                "json_error": str(err),
                "raw_snippet": raw_str[:500],
            },
        ) from err

    if not isinstance(data, dict):
        ai_logger.error(f"Expected JSON object dict, received type {type(data).__name__}")
        raise JSONParsingError(
            f"Invalid JSON payload: Expected object dict, got {type(data).__name__}",
            details={"received_type": type(data).__name__},
        )

    return data


def validate_output(raw_output: str, schema_class: Type[T]) -> T:
    """Parse raw LLM response text and validate against target Pydantic schema class.

    Args:
        raw_output: Raw text response from LLM call.
        schema_class: Pydantic model class to validate against.

    Returns:
        Validated Pydantic model object instance.

    Raises:
        JSONParsingError: If JSON parsing fails.
        OutputValidationError: If Pydantic schema validation fails.
    """
    # Step 1: Parse JSON safely
    parsed_dict = parse_json_safely(raw_output)

    # Step 2: Validate against Pydantic model
    try:
        validated_instance = schema_class.model_validate(parsed_dict)
        ai_logger.info(
            f"Pydantic Validation Success: {schema_class.__name__} successfully validated."
        )
        return validated_instance
    except ValidationError as err:
        error_details = err.errors()
        ai_logger.error(
            f"Pydantic Schema Validation Error for {schema_class.__name__}:\n"
            f"Field Errors: {len(error_details)} | Details: {err.json(indent=2)}"
        )
        raise OutputValidationError(
            f"Output validation failed for {schema_class.__name__} ({len(error_details)} field error(s)).",
            details={
                "schema": schema_class.__name__,
                "field_errors": error_details,
                "raw_dict": parsed_dict,
            },
        ) from err
