"""Upstash Redis response caching tool for search and research queries."""

import json
import os
from typing import Any, Dict, Optional
import httpx

from ai.config import get_ai_settings
from ai.shared.logger import ai_logger


class UpstashRedisCache:
    """Production Redis caching client via Upstash REST API."""

    def __init__(
        self,
        url: Optional[str] = None,
        token: Optional[str] = None,
        timeout: float = 5.0,
    ) -> None:
        """Initialize Upstash Redis cache client."""
        settings = get_ai_settings()
        self.url = url or settings.upstash_redis_rest_url or os.getenv("UPSTASH_REDIS_REST_URL", "")
        self.token = token or settings.upstash_redis_rest_token or os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
        self.timeout = timeout

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached JSON object by key."""
        if not self.url or not self.token:
            return None

        clean_url = f"{self.url.rstrip('/')}/get/{key}"
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(clean_url, headers=headers)
                if resp.status_code == 200:
                    val = resp.json().get("result")
                    if val:
                        return json.loads(val)
        except Exception as e:
            ai_logger.debug(f"Upstash cache miss/error for key '{key}': {e}")
        return None

    def set(self, key: str, value: Dict[str, Any], ttl_seconds: int = 86400) -> bool:
        """Set cached JSON object with TTL in seconds."""
        if not self.url or not self.token:
            return False

        clean_url = f"{self.url.rstrip('/')}/set/{key}"
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            payload_str = json.dumps(value)
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(clean_url, headers=headers, json=[payload_str, "EX", ttl_seconds])
                return resp.status_code == 200
        except Exception as e:
            ai_logger.debug(f"Upstash cache write error for key '{key}': {e}")
            return False
