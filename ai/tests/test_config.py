"""Unit tests for Startup Igniter AI Configuration Subsystem.

Uses standard library unittest to ensure tests run reliably anywhere.
"""

import os
import unittest
from ai.config import AISettings, get_ai_settings
from ai.shared.constants import (
    DEFAULT_GROQ_MODELS,
    DEFAULT_SCORE_WEIGHTS,
    ModelTier,
    ScoreDimension,
    StartupCategory,
    StartupPhase,
)
from ai.shared.errors import (
    BudgetExceededError,
    ConfigurationError,
    LLMProviderError,
    MemoryConfigError,
    MissingAPIKeyError,
    StartupOSAIError,
)
from ai.shared.llm_provider import LLMConfig, LLMFactory
from ai.shared.logger import mask_sensitive_data
from ai.shared.memory_config import VectorMemoryConfig


class TestAIConfig(unittest.TestCase):
    """Test suite for AI configuration, settings, logging, and LLM factory."""

    def test_ai_settings_initialization(self):
        """Test loading AI settings and checking environment properties."""
        settings = get_ai_settings(reload=True)
        self.assertIsNotNone(settings)
        self.assertIn(settings.environment, ["development", "staging", "production", "test"])
        self.assertEqual(settings.memory_config.embedding_dimension, 384)

    def test_score_weights_sum_to_one(self):
        """Verify multi-dimensional scoring weights sum exactly to 1.0 (spec §6 requirement)."""
        total_weight = sum(DEFAULT_SCORE_WEIGHTS.values())
        self.assertAlmostEqual(total_weight, 1.0, places=4)
        self.assertNotIn(ScoreDimension.OVERALL, DEFAULT_SCORE_WEIGHTS)

    def test_llm_factory_model_name_resolution(self):
        """Test resolution of Groq model strings for each model tier."""
        heavy_model = LLMFactory.get_model_name(ModelTier.HEAVY)
        self.assertEqual(heavy_model, "groq/llama-3.3-70b-versatile")

        fast_model = LLMFactory.get_model_name(ModelTier.FAST)
        self.assertEqual(fast_model, "groq/llama-3.1-8b-instant")

        custom_model = LLMFactory.get_model_name(ModelTier.HEAVY, custom_model="mixtral-8x7b-32768")
        self.assertEqual(custom_model, "groq/mixtral-8x7b-32768")

    def test_llm_factory_mock_mode(self):
        """Test instantiating LLM in mock mode without requiring live API keys."""
        llm_config = LLMFactory.get_llm(
            model_tier=ModelTier.FAST,
            temperature=0.3,
            mock_mode=True,
        )
        self.assertIsInstance(llm_config, LLMConfig)
        self.assertEqual(llm_config.model_name, "groq/llama-3.1-8b-instant")
        self.assertEqual(llm_config.temperature, 0.3)

    def test_llm_factory_missing_api_key(self):
        """Test raising MissingAPIKeyError when GROQ_API_KEY is missing."""
        original_key = os.environ.pop("GROQ_API_KEY", None)
        settings = get_ai_settings()
        original_settings_key = settings.groq_api_key
        settings.groq_api_key = None
        try:
            with self.assertRaises(MissingAPIKeyError) as ctx:
                LLMFactory.get_llm(
                    model_tier=ModelTier.HEAVY,
                    api_key=None,
                    mock_mode=False,
                )
            self.assertIn("GROQ_API_KEY", str(ctx.exception))
        finally:
            settings.groq_api_key = original_settings_key
            if original_key:
                os.environ["GROQ_API_KEY"] = original_key
                os.environ["GROQ_API_KEY"] = original_key

    def test_sensitive_data_logging_mask(self):
        """Test masking of sensitive API keys in log text."""
        raw_log = "Error using key gsk_abc123456789xyz with tavily tvly-dev-999"
        masked_log = mask_sensitive_data(raw_log)
        self.assertNotIn("gsk_abc123456789xyz", masked_log)
        self.assertNotIn("tvly-dev-999", masked_log)
        self.assertIn("[REDACTED_SECRET]", masked_log)

    def test_vector_memory_config_validation(self):
        """Test vector memory configuration defaults and validation."""
        mem_config = VectorMemoryConfig()
        mem_config.validate_dimension()  # 384 dimension should pass

        invalid_config = VectorMemoryConfig(embedding_dimension=512)
        with self.assertRaises(MemoryConfigError):
            invalid_config.validate_dimension()

    def test_budget_exceeded_error_details(self):
        """Test details payload of BudgetExceededError."""
        err = BudgetExceededError(project_id="proj-123", phase="idea", limit=10, used=11)
        self.assertEqual(err.details["project_id"], "proj-123")
        self.assertEqual(err.details["limit"], 10)
        self.assertEqual(err.details["used"], 11)
        self.assertIn("Action budget exceeded", str(err))


if __name__ == "__main__":
    unittest.main()
