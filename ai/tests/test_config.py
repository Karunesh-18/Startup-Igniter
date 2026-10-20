"""Unit tests for Startup Igniter AI Configuration Subsystem.

Uses standard library unittest to ensure tests run reliably anywhere.
"""

import os
import unittest
from ai.config import AISettings, get_ai_settings
from ai.shared.constants import (
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
from ai.llm.gateway import LLMGateway
from ai.llm.settings import LLMSettings
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

    def test_gateway_model_resolution_per_tier(self):
        """Each tier resolves to the right self-hosted model name."""
        settings = LLMSettings(LLM_BASE_URL="http://localhost:9999/v1")
        gw = LLMGateway(settings=settings)
        self.assertEqual(gw._model_for(ModelTier.HEAVY), settings.llm_model_heavy)
        self.assertEqual(gw._model_for(ModelTier.FAST), settings.llm_model_fast)

    def test_gateway_mock_fallback_when_nothing_configured(self):
        """With no backend configured, the gateway falls through to the mock
        provider rather than crashing local dev/CI with MissingAPIKeyError."""
        settings = LLMSettings(LLM_BASE_URL=None, LLM_ALLOW_MOCK=True)
        gw = LLMGateway(settings=settings)
        result = gw.invoke(system_prompt="sys", user_prompt="user", tier=ModelTier.FAST)
        self.assertTrue(result)  # mock provider always returns valid (non-empty) JSON text

    def test_gateway_raises_when_mock_disabled_and_nothing_configured(self):
        """With mock explicitly disabled and nothing else configured, the
        gateway still raises MissingAPIKeyError — same contract as before."""
        settings = LLMSettings(LLM_BASE_URL=None, LLM_ALLOW_MOCK=True)
        gw = LLMGateway(settings=settings)
        with self.assertRaises(MissingAPIKeyError):
            gw.invoke(system_prompt="sys", user_prompt="user", allow_mock_fallback=False)

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
