"""Memory and vector store configuration for Startup Igniter AI subsystem."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, SecretStr

from ai.shared.constants import (
    DEFAULT_EMBEDDING_DIMENSION,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_MEMORY_TOP_K,
    DEFAULT_SIMILARITY_THRESHOLD,
)
from ai.shared.errors import MemoryConfigError


class VectorMemoryConfig(BaseModel):
    """Configuration for vector memory and pgvector integration in Supabase."""

    embedding_model_name: str = Field(
        default=DEFAULT_EMBEDDING_MODEL,
        description="Self-hosted sentence-transformers embedding model name.",
    )
    embedding_dimension: int = Field(
        default=DEFAULT_EMBEDDING_DIMENSION,
        description="Vector embedding dimension (384 for all-MiniLM-L6-v2).",
    )
    table_name: str = Field(
        default="project_memory",
        description="Postgres table storing cross-phase shared memory vectors.",
    )
    top_k: int = Field(
        default=DEFAULT_MEMORY_TOP_K,
        ge=1,
        le=50,
        description="Default number of relevant memory chunks to retrieve per search.",
    )
    similarity_threshold: float = Field(
        default=DEFAULT_SIMILARITY_THRESHOLD,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity threshold for memory retrieval.",
    )
    enable_local_cache: bool = Field(
        default=True,
        description="Whether to enable in-memory LRU cache for memory lookups.",
    )
    cache_ttl_seconds: int = Field(
        default=3600,
        description="TTL for memory cache items in seconds.",
    )

    def validate_dimension(self) -> None:
        """Validate embedding dimension matches expected table schema."""
        if self.embedding_dimension != 384:
            raise MemoryConfigError(
                f"Embedding dimension {self.embedding_dimension} does not match required 384 for pgvector schema.",
                details={"configured": self.embedding_dimension, "expected": 384},
            )

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as plain dictionary."""
        return self.model_dump()
