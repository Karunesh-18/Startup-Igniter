"""Project Memory Manager for cross-phase AI state sharing and semantic RAG retrieval."""

import json
import math
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from ai.config import get_ai_settings
from ai.shared.errors import MemoryConfigError, StartupOSAIError
from ai.shared.logger import ai_logger

# Optional sentence-transformers import check for vector embeddings
try:
    from sentence_transformers import SentenceTransformer  # type: ignore
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    SentenceTransformer = None


class MemoryEntry(BaseModel):
    """Schema for individual project memory record."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = Field(description="Associated project ID.")
    key: str = Field(description="Unique memory key identifier (e.g. 'swot_analysis').")
    value: Dict[str, Any] = Field(description="Structured JSON payload.")
    source_phase: str = Field(description="Phase in which this memory item was generated.")
    embedding: List[float] = Field(default_factory=list, description="Vector embedding list (384 dimensions).")
    similarity_score: float = Field(default=0.0, description="Similarity score when retrieved via semantic search.")


def generate_mock_embedding(text: str, dimension: int = 384) -> List[float]:
    """Generate a deterministic normalized pseudo-embedding vector for mock mode testing."""
    hash_val = sum(ord(c) for c in text)
    raw_vec = [math.sin(hash_val + i) for i in range(dimension)]
    norm = math.sqrt(sum(v * v for v in raw_vec)) or 1.0
    return [v / norm for v in raw_vec]


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a)) or 1.0
    norm_b = math.sqrt(sum(b * b for b in vec_b)) or 1.0
    return max(0.0, min(1.0, dot / (norm_a * norm_b)))


class ProjectMemoryManager:
    """Manager for storing and retrieving cross-phase memory for AI Crews."""

    _embedder_instance = None

    def __init__(self, use_mock_store: bool = True) -> None:
        """Initialize Project Memory Manager.

        Args:
            use_mock_store: If True, uses in-memory dictionary store for offline tests.
        """
        self.settings = get_ai_settings()
        self.config = self.settings.memory_config
        self.use_mock_store = use_mock_store
        # In-memory mock store: project_id -> List[MemoryEntry]
        self._mock_db: Dict[str, List[MemoryEntry]] = {}

    @classmethod
    def get_embedder(cls, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> Any:
        """Lazy load sentence-transformer model instance."""
        if cls._embedder_instance is None and HAS_SENTENCE_TRANSFORMERS and SentenceTransformer is not None:
            try:
                ai_logger.info(f"Loading local embedding model: {model_name}")
                cls._embedder_instance = SentenceTransformer(model_name)
            except Exception as err:
                ai_logger.warning(f"Failed to load SentenceTransformer ({str(err)}). Using fallback embedder.")
                cls._embedder_instance = None
        return cls._embedder_instance

    def compute_embedding(self, text: str) -> List[float]:
        """Compute 384-dimension embedding for input text.

        Args:
            text: Text content to embed.

        Returns:
            List of 384 float vector values.
        """
        embedder = self.get_embedder(self.config.embedding_model_name)
        if embedder is not None:
            try:
                vec = embedder.encode(text, convert_to_numpy=True).tolist()
                return vec
            except Exception as err:
                ai_logger.warning(f"Embedding computation error ({str(err)}). Falling back to mock vector.")
        
        return generate_mock_embedding(text, self.config.embedding_dimension)

    def write_memory(
        self,
        project_id: str,
        key: str,
        value: Dict[str, Any],
        source_phase: str,
    ) -> MemoryEntry:
        """Store structured JSON memory item and index embedding.

        Args:
            project_id: Project UUID string.
            key: Memory key identifier.
            value: JSON serializable dict payload.
            source_phase: Phase identifier string.

        Returns:
            Created MemoryEntry object.
        """
        text_representation = f"{key}: {json.dumps(value)}"
        embedding_vec = self.compute_embedding(text_representation)

        entry = MemoryEntry(
            project_id=project_id,
            key=key,
            value=value,
            source_phase=source_phase,
            embedding=embedding_vec,
        )

        if self.use_mock_store:
            if project_id not in self._mock_db:
                self._mock_db[project_id] = []
            # Replace existing entry with same key or append
            self._mock_db[project_id] = [
                e for e in self._mock_db[project_id] if e.key != key
            ]
            self._mock_db[project_id].append(entry)
            ai_logger.info(f"[MOCK MEMORY] Saved '{key}' for project '{project_id}' in phase '{source_phase}'")
            return entry

        # Production path: Supabase DB insertion (handled when DB connection is active)
        return entry

    def query_memory(
        self,
        project_id: str,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
        source_phase: Optional[str] = None,
    ) -> List[MemoryEntry]:
        """Perform semantic similarity search over stored project memory.

        Args:
            project_id: Target project UUID.
            query: Natural language query string.
            top_k: Max result items to retrieve.
            threshold: Cosine similarity threshold filter.
            source_phase: Optional phase filter.

        Returns:
            List of matching MemoryEntry items sorted by similarity score.
        """
        k = top_k or self.config.top_k
        min_threshold = threshold or self.config.similarity_threshold
        query_vec = self.compute_embedding(query)

        entries = self._mock_db.get(project_id, [])
        if source_phase:
            entries = [e for e in entries if e.source_phase == source_phase]

        scored_entries: List[MemoryEntry] = []
        for entry in entries:
            score = cosine_similarity(query_vec, entry.embedding)
            if score >= min_threshold:
                scored = entry.model_copy()
                scored.similarity_score = score
                scored_entries.append(scored)

        # Sort descending by score
        scored_entries.sort(key=lambda x: x.similarity_score, reverse=True)
        return scored_entries[:k]

    def get_memory_by_key(self, project_id: str, key: str) -> Optional[MemoryEntry]:
        """Retrieve specific memory entry by key."""
        entries = self._mock_db.get(project_id, [])
        for entry in entries:
            if entry.key == key:
                return entry
        return None
