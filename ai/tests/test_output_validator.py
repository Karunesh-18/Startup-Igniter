"""Unit tests for reusable output_validator utility module."""

import unittest
from pydantic import BaseModel, Field, ValidationError

from ai.schemas.idea_validation import StartupIdeaAnalysis
from ai.shared.errors import JSONParsingError, OutputValidationError
from ai.shared.output_validator import clean_json_text, parse_json_safely, validate_output


class SampleSchema(BaseModel):
    name: str
    score: int = Field(ge=0, le=100)


class TestOutputValidator(unittest.TestCase):
    """Test suite for output_validator utilities."""

    def test_clean_json_text_markdown_stripping(self):
        """Test stripping markdown code block wrappers."""
        raw_markdown = "```json\n{\n  \"key\": \"value\"\n}\n```"
        cleaned = clean_json_text(raw_markdown)
        self.assertEqual(cleaned, '{\n  "key": "value"\n}')

    def test_parse_json_safely_valid(self):
        """Test parsing valid JSON string into dictionary."""
        valid_json = '{"name": "Startup Igniter", "score": 95}'
        parsed = parse_json_safely(valid_json)
        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed["name"], "Startup Igniter")

    def test_parse_json_safely_invalid_syntax(self):
        """Test raising JSONParsingError on malformed JSON string."""
        invalid_json = '{"name": "Missing quote, score: 95}'
        with self.assertRaises(JSONParsingError):
            parse_json_safely(invalid_json)

    def test_validate_output_success(self):
        """Test successful validation against Pydantic model."""
        json_data = '{"name": "HealthTech Platform", "score": 85}'
        instance = validate_output(json_data, SampleSchema)
        self.assertIsInstance(instance, SampleSchema)
        self.assertEqual(instance.name, "HealthTech Platform")
        self.assertEqual(instance.score, 85)

    def test_validate_output_missing_field(self):
        """Test raising OutputValidationError when a required field is missing."""
        incomplete_json = '{"name": "Incomplete proposal"}'
        with self.assertRaises(OutputValidationError):
            validate_output(incomplete_json, SampleSchema)

    def test_validate_output_out_of_range(self):
        """Test raising OutputValidationError when score is out of 0-100 bounds."""
        out_of_bounds_json = '{"name": "Over 100 Score", "score": 150}'
        with self.assertRaises(OutputValidationError):
            validate_output(out_of_bounds_json, SampleSchema)

    def test_validate_startup_idea_analysis_schema(self):
        """Test validate_output against real StartupIdeaAnalysis schema."""
        raw_payload = """
        {
          "summary": "AI mobile app for early crop disease detection.",
          "startup_category": "AgriTech",
          "operational_pillars": ["AI Model", "Mobile App", "Agronomy DB"],
          "technical_feasibility_score": 88,
          "rationale": "High feasibility using modern CNN architectures.",
          "key_assumptions": ["Dataset availability", "Camera access"],
          "strengths": ["Fast detection", "Low cost"],
          "weaknesses": ["Lighting variation dependency"]
        }
        """
        validated = validate_output(raw_payload, StartupIdeaAnalysis)
        self.assertIsInstance(validated, StartupIdeaAnalysis)
        self.assertEqual(validated.startup_category, "AgriTech")
        self.assertEqual(len(validated.operational_pillars), 3)
        self.assertEqual(validated.technical_feasibility_score, 88)


if __name__ == "__main__":
    unittest.main()
