"""Custom exception hierarchy for Startup Igniter AI module."""

from typing import Optional


class StartupOSAIError(Exception):
    """Base exception class for all AI module errors in Startup Igniter."""

    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ConfigurationError(StartupOSAIError):
    """Raised when AI settings or configuration are invalid."""

    pass


class MissingAPIKeyError(ConfigurationError):
    """Raised when a required API key is missing or empty."""

    def __init__(self, key_name: str, provider_name: str) -> None:
        super().__init__(
            message=f"Missing required API key '{key_name}' for provider '{provider_name}'.",
            details={"key_name": key_name, "provider_name": provider_name},
        )
        self.key_name = key_name
        self.provider_name = provider_name


class LLMProviderError(StartupOSAIError):
    """Raised when initializing or executing calls against an LLM provider fails."""

    pass


class MemoryConfigError(StartupOSAIError):
    """Raised when vector store or project memory configuration fails."""

    pass


class BudgetExceededError(StartupOSAIError):
    """Raised when a project or phase token/action budget is exceeded."""

    def __init__(self, project_id: str, phase: str, limit: int, used: int) -> None:
        super().__init__(
            message=f"Action budget exceeded for project '{project_id}' in phase '{phase}'. Limit: {limit}, Used: {used}.",
            details={
                "project_id": project_id,
                "phase": phase,
                "limit": limit,
                "used": used,
            },
        )
        self.project_id = project_id
        self.phase = phase
        self.limit = limit
        self.used = used


class JSONParsingError(StartupOSAIError):
    """Raised when raw LLM response text cannot be parsed as valid JSON."""

    pass


class OutputValidationError(StartupOSAIError):
    """Raised when parsed JSON fails Pydantic schema validation."""

    pass
