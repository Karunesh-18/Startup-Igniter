"""Configuration settings for Idea Validation Crew."""

from pydantic import BaseModel, Field
from ai.shared.constants import ModelTier


class IdeaValidationCrewConfig(BaseModel):
    """Configuration options for Idea Validation Crew."""

    classifier_model_tier: ModelTier = Field(
        default=ModelTier.FAST,
        description="Model tier for startup category classification.",
    )
    analysis_model_tier: ModelTier = Field(
        default=ModelTier.HEAVY,
        description="Model tier for deep idea, problem, customer, and value analysis.",
    )
    max_rpm: int = Field(default=30, description="Max requests per minute limit.")
    verbose: bool = Field(default=True, description="Enable verbose logs during crew execution.")
