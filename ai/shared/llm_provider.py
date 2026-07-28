"""LLM provider factory and model configuration for Groq and CrewAI."""

import os
from typing import Any, Dict, Optional, Union, TYPE_CHECKING
from pydantic import BaseModel, Field

from ai.shared.constants import DEFAULT_GROQ_MODELS, ModelTier
from ai.shared.errors import LLMProviderError, MissingAPIKeyError
from ai.shared.logger import ai_logger

# Optional CrewAI import check with type safety
HAS_CREWAI = False
CrewAILLM = None

try:
    from crewai import LLM as CrewAILLM  # type: ignore
    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False
    CrewAILLM = None


class LLMConfig(BaseModel):
    """Configuration settings for LLM invocation."""

    model_tier: ModelTier = Field(
        default=ModelTier.HEAVY,
        description="Execution tier (FAST for routing, HEAVY for deep analysis).",
    )
    model_name: str = Field(
        default=DEFAULT_GROQ_MODELS[ModelTier.HEAVY],
        description="Full LiteLLM model identifier string (e.g. groq/llama-3.3-70b-versatile).",
    )
    temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for LLM outputs.",
    )
    max_tokens: Optional[int] = Field(
        default=4096,
        ge=1,
        description="Maximum tokens to generate per response.",
    )
    top_p: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling parameter.",
    )
    timeout_seconds: float = Field(
        default=60.0,
        ge=1.0,
        description="Timeout duration in seconds for LLM call.",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Number of retry attempts on transient failure.",
    )


class LLMFactory:
    """Factory for instantiating and configuring LLMs for CrewAI agents."""

    @staticmethod
    def get_model_name(
        model_tier: Union[ModelTier, str],
        custom_model: Optional[str] = None,
    ) -> str:
        """Resolve full model name from tier or custom model string."""
        if custom_model:
            return custom_model if custom_model.startswith("groq/") else f"groq/{custom_model}"
        
        tier = ModelTier(model_tier) if isinstance(model_tier, str) else model_tier
        return DEFAULT_GROQ_MODELS.get(tier, DEFAULT_GROQ_MODELS[ModelTier.HEAVY])

    @classmethod
    def get_llm(
        cls,
        model_tier: Union[ModelTier, str] = ModelTier.HEAVY,
        temperature: float = 0.2,
        max_tokens: Optional[int] = 4096,
        api_key: Optional[str] = None,
        custom_model: Optional[str] = None,
        mock_mode: bool = False,
    ) -> Any:
        """Instantiate a configured CrewAI LLM instance backed by Groq.

        Args:
            model_tier: Model execution tier (FAST, HEAVY, REASONING).
            temperature: Generation temperature.
            max_tokens: Max output token limit.
            api_key: Optional explicit API key (falls back to GROQ_API_KEY env var).
            custom_model: Optional explicit model override.
            mock_mode: If True, returns mock config object for testing without API keys.

        Returns:
            CrewAI LLM instance or LLMConfig object.
        """
        # Resolve API Key from settings or environment
        from ai.config import get_ai_settings
        settings = get_ai_settings()
        groq_api_key = api_key or settings.groq_api_key or os.getenv("GROQ_API_KEY")
        if not groq_api_key and not mock_mode:
            raise MissingAPIKeyError(
                key_name="GROQ_API_KEY",
                provider_name="Groq",
            )

        model_name = cls.get_model_name(model_tier, custom_model)

        ai_logger.info(
            f"Initializing LLM: model={model_name}, temp={temperature}, mock={mock_mode}"
        )

        config = LLMConfig(
            model_tier=ModelTier(model_tier) if isinstance(model_tier, str) else model_tier,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if mock_mode:
            return config

        # If CrewAI is installed, instantiate native CrewAI LLM
        if HAS_CREWAI and CrewAILLM is not None:
            try:
                return CrewAILLM(
                    model=model_name,
                    api_key=groq_api_key,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as err:
                raise LLMProviderError(
                    f"Failed to instantiate CrewAI LLM '{model_name}': {str(err)}",
                    details={"model": model_name, "error": str(err)},
                ) from err

        # Fallback if CrewAI not yet installed
        return config
