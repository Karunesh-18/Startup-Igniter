"""Reusable JSON extraction and Pydantic validation utilities for AI outputs."""

import json
import re
from typing import Any, Type, TypeVar
from pydantic import BaseModel, ValidationError

from ai.shared.errors import StartupOSAIError
from ai.shared.logger import ai_logger

T = TypeVar("T", bound=BaseModel)


def extract_json_payload(raw_text: str) -> str:
    """Sanitize LLM raw output text to extract clean JSON payload.

    Strips markdown codeblock wrappers (e.g. ```json ... ```) and leading/trailing whitespace.

    Args:
        raw_text: Unsanitized string output from LLM.

    Returns:
        Clean JSON string.
    """
    text = raw_text.strip()

    # Pattern matching ```json ... ``` or ``` ... ```
    code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if code_block_match:
        return code_block_match.group(1).strip()

    # If starts with '{' and ends with '}', extract inner object
    json_object_match = re.search(r"(\{[\s\S]*\})", text)
    if json_object_match:
        return json_object_match.group(1).strip()

    return text


def parse_and_validate_json(raw_output: str, schema_class: Type[T]) -> T:
    """Safely parse JSON text and validate against a target Pydantic schema class.

    Args:
        raw_output: Raw text output string from LLM call.
        schema_class: Pydantic model class to validate against.

    Returns:
        Validated Pydantic model instance.

    Raises:
        StartupOSAIError: If JSON is invalid or Pydantic schema validation fails.
    """
    sanitized_text = extract_json_payload(raw_output)

    # Step 1: JSON Decode
    try:
        data = json.loads(sanitized_text)
    except json.JSONDecodeError as err:
        ai_logger.error(
            f"Failed to decode LLM response as JSON: {str(err)} | Raw Text snippet: {raw_output[:200]!r}"
        )
        raise StartupOSAIError(
            f"Invalid JSON response from LLM: {str(err)}",
            details={
                "json_error": str(err),
                "raw_text_head": raw_output[:300],
            },
        ) from err

    if not isinstance(data, dict):
        ai_logger.error(f"Expected JSON object dict, received type {type(data).__name__}")
        raise StartupOSAIError(
            f"Invalid response structure: Expected JSON object dict, got {type(data).__name__}",
            details={"received_type": type(data).__name__},
        )

    # Step 2: Pydantic Model Validation
    try:
        validated_instance = schema_class.model_validate(data)
        ai_logger.info(f"Successfully validated LLM output against {schema_class.__name__}")
        return validated_instance
    except ValidationError as err:
        ai_logger.error(
            f"Pydantic schema validation failed for {schema_class.__name__}:\n{err.json(indent=2)}"
        )
        raise StartupOSAIError(
            f"Response validation failed against {schema_class.__name__}: {len(err.errors())} field error(s)",
            details={
                "schema": schema_class.__name__,
                "errors": err.errors(),
                "raw_json": data,
            },
        ) from err
