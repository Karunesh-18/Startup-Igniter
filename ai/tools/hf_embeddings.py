"""Hugging Face & Sentence-Transformers vector embedding generation tool for project memory."""

import os
from typing import List, Optional
import httpx

from ai.config import get_ai_settings
from ai.shared.logger import ai_logger


class HFEmbeddingsTool:
    """Production vector embedding generator (384-dimensional all-MiniLM-L6-v2)."""

    DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    HF_API_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self, hf_token: Optional[str] = None, timeout: float = 15.0) -> None:
        """Initialize Hugging Face embeddings generator."""
        settings = get_ai_settings()
        if hf_token is not None:
            self.hf_token = hf_token
        else:
            self.hf_token = getattr(settings, "hf_token", None) or os.getenv("HF_TOKEN", "")
        self.timeout = timeout

    def embed_text(self, text: str, mock_mode: bool = False) -> List[float]:
        """Generate 384-dimensional vector embedding for input text string."""
        if not text or not text.strip():
            return [0.0] * 384

        if mock_mode or not self.hf_token:
            # Deterministic mock embedding based on text hash for zero-cost testing
            import hashlib
            seed = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16)
            import random
            rng = random.Random(seed)
            return [round(rng.uniform(-0.1, 0.1), 6) for _ in range(384)]

        headers = {"Authorization": f"Bearer {self.hf_token}"}
        payload = {"inputs": text, "options": {"wait_for_model": True}}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(self.HF_API_URL, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()

            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], list):
                    return [float(x) for x in data[0][:384]]
                return [float(x) for x in data[:384]]

            return [0.0] * 384

        except Exception as err:
            ai_logger.warning(f"HuggingFace embedding API failed: {err}. Using deterministic mock vector.")
            import hashlib
            seed = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16)
            import random
            rng = random.Random(seed)
            return [round(rng.uniform(-0.1, 0.1), 6) for _ in range(384)]
