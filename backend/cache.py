"""
cache.py — Redis Cache Layer

Provides caching for:
1. Gemini API responses (avoid duplicate LLM calls for same conversation)
2. Scoring results (avoid recomputing 8-layer scores for identical inputs)
3. LangGraph state checkpointing (persistent Working Memory)

Redis is optional — all functions gracefully degrade to no-op if Redis
is unavailable, so the system works without it.
"""

import os
import json
import hashlib
from typing import Optional, Any

import redis


class RedisCache:
    """Redis-backed cache with graceful degradation."""

    def __init__(self, url: str = None):
        self._client = None
        self._url = url or os.getenv("REDIS_URL", "redis://localhost:6380/0")
        self._connect()

    def _connect(self):
        try:
            self._client = redis.from_url(self._url, decode_responses=True)
            self._client.ping()
            print(f"✅ Redis connected: {self._url}")
        except Exception as e:
            print(f"⚠️ Redis unavailable ({e}), running without cache")
            self._client = None

    @property
    def connected(self) -> bool:
        return self._client is not None

    def get(self, key: str) -> Optional[Any]:
        """Get a cached value. Returns None if not found or Redis unavailable."""
        if not self._client:
            return None
        try:
            data = self._client.get(key)
            return json.loads(data) if data else None
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """Cache a value with TTL in seconds (default 1 hour)."""
        if not self._client:
            return
        try:
            self._client.setex(key, ttl, json.dumps(value, default=str))
        except Exception as e:
            print(f"Redis set failed: {e}")

    def delete(self, key: str):
        """Delete a cached key."""
        if not self._client:
            return
        try:
            self._client.delete(key)
        except Exception:
            pass

    def hash_messages(self, messages: list) -> str:
        """Create a deterministic hash of messages for cache key generation."""
        content = json.dumps(messages, sort_keys=True, default=str)
        return f"sync:{hashlib.sha256(content.encode()).hexdigest()[:16]}"

    # ─── Specialized Cache Methods ───────────────────────────────────

    def get_scoring_cache(self, messages: list) -> Optional[dict]:
        """Check if scoring results exist for these exact messages."""
        key = f"score:{self.hash_messages(messages)}"
        return self.get(key)

    def set_scoring_cache(self, messages: list, result: dict, ttl: int = 3600):
        """Cache scoring results for 1 hour."""
        key = f"score:{self.hash_messages(messages)}"
        self.set(key, result, ttl)

    def get_llm_cache(self, prompt_hash: str) -> Optional[dict]:
        """Check if LLM response exists for this prompt."""
        key = f"llm:{prompt_hash}"
        return self.get(key)

    def set_llm_cache(self, prompt_hash: str, response: dict, ttl: int = 7200):
        """Cache LLM responses for 2 hours."""
        key = f"llm:{prompt_hash}"
        self.set(key, response, ttl)

    def get_whatsapp_status(self) -> Optional[dict]:
        """Get WhatsApp connection status."""
        return self.get("wa:status")

    def set_whatsapp_status(self, status: dict):
        """Store WhatsApp connection status (no expiry)."""
        if self._client:
            try:
                self._client.set("wa:status", json.dumps(status))
            except Exception:
                pass


# ─── Singleton ───────────────────────────────────────────────────────────

_cache_instance = None

def get_cache() -> RedisCache:
    """Get or create the singleton cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance
