"""Legacy wrapper delegating to ai.shared.output_validator for backward compatibility."""

from typing import Type, TypeVar
from pydantic import BaseModel

from ai.shared.output_validator import clean_json_text, parse_json_safely, validate_output

T = TypeVar("T", bound=BaseModel)

extract_json_payload = clean_json_text
parse_and_validate_json = validate_output

__all__ = [
    "extract_json_payload",
    "parse_and_validate_json",
    "clean_json_text",
    "parse_json_safely",
    "validate_output",
]
