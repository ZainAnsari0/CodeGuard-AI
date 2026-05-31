"""
CodeGuard AI - Redis Prompt Cache
Caches rendered prompts and AI responses in Redis for performance.
Degrades gracefully when Redis is unavailable, using in-memory LRU fallback.
Uses asyncio.to_thread to avoid blocking the event loop with sync Redis calls.
"""

import json
import hashlib
import logging
import asyncio
import time
from collections import OrderedDict
from typing import Optional, Any

logger = logging.getLogger(__name__)


class LRUCache:
    """Simple in-memory LRU cache for when Redis is unavailable."""

    def __init__(self, max_size: int = 256):
        self._cache: OrderedDict[str, tuple] = OrderedDict()
        self._max_size = max_size

    def get(self, key: str) -> Optional[dict]:
        if key in self._cache:
            value, expires_at = self._cache[key]
            if expires_at and time.time() > expires_at:
                del self._cache[key]
                return None
            self._cache.move_to_end(key)
            return value
        return None

    def set(self, key: str, value: dict, ttl: int = 3600) -> bool:
        # Proactively evict expired items before adding new ones
        now = time.time()
        expired_keys = [k for k, (_, exp) in self._cache.items() if exp and exp <= now]
        for k in expired_keys:
            del self._cache[k]

        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (value, time.time() + ttl)
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)
        return True

    def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self):
        self._cache.clear()


class PromptCache:
    """Cache rendered prompts and AI responses in Redis with in-memory fallback.

    All Redis calls are dispatched to a thread pool via asyncio.to_thread()
    so the async event loop is never blocked by synchronous Redis I/O.
    """

    DEFAULT_TTL = 3600  # 1 hour

    def __init__(self, redis_url: Optional[str] = None, ttl: Optional[int] = None,
                 enabled: bool = True):
        self.redis_url = redis_url
        self.ttl = ttl or self.DEFAULT_TTL
        self.enabled = enabled
        self._client = None
        self._fallback = LRUCache(max_size=256)

    def _get_client(self):
        """Lazy-initialize synchronous Redis client for health_check only.

        For all async operations, use the async methods which use
        asyncio.to_thread to avoid blocking the event loop.
        """
        if self._client is not None:
            return self._client

        try:
            import redis
            from app.core.config import settings
            url = self.redis_url or getattr(settings, "REDIS_URL", "redis://localhost:6379/2")
            self._client = redis.from_url(url, decode_responses=True)
            self._client.ping()
            logger.info("PromptCache connected to Redis")
            return self._client
        except Exception as e:
            logger.warning("PromptCache: Redis unavailable, using LRU fallback: %s", e)
            self._client = None
            return None

    def _make_key(self, template_name: str, prompt_hash: str, model: str) -> str:
        return f"prompt_cache:{template_name}:{model}:{prompt_hash}"

    @staticmethod
    def hash_prompt(rendered_prompt: str) -> str:
        return hashlib.sha256(rendered_prompt.encode()).hexdigest()[:16]

    async def get(self, template_name: str, rendered_prompt: str, model: str) -> Optional[dict]:
        """Retrieve cached AI response (non-blocking)."""
        if not self.enabled:
            return None

        prompt_hash = self.hash_prompt(rendered_prompt)
        key = self._make_key(template_name, prompt_hash, model)

        try:
            client = self._get_client()
            if client is None:
                return self._fallback.get(key)

            cached = await asyncio.to_thread(client.get, key)
            if cached:
                logger.info("Cache hit for %s/%s", template_name, model)
                return json.loads(cached)
            return None
        except Exception as e:
            logger.warning("Cache get failed, falling back to LRU: %s", e)
            return self._fallback.get(key)

    async def set(self, template_name: str, rendered_prompt: str, model: str,
                 response: dict, ttl: Optional[int] = None) -> bool:
        """Cache an AI response (non-blocking)."""
        if not self.enabled:
            return False

        prompt_hash = self.hash_prompt(rendered_prompt)
        key = self._make_key(template_name, prompt_hash, model)
        effective_ttl = ttl or self.ttl

        try:
            client = self._get_client()
            if client is None:
                return self._fallback.set(key, response, effective_ttl)

            await asyncio.to_thread(client.setex, key, effective_ttl, json.dumps(response))
            logger.info("Cached response for %s/%s", template_name, model)
            self._fallback.set(key, response, effective_ttl)
            return True
        except Exception as e:
            logger.warning("Cache set failed, falling back to LRU: %s", e)
            return self._fallback.set(key, response, effective_ttl)

    async def invalidate(self, template_name: str) -> bool:
        """Invalidate all cache entries for a template (non-blocking)."""
        if not self.enabled:
            return False

        try:
            client = self._get_client()
            if client is None:
                return False

            pattern = f"prompt_cache:{template_name}:*"
            deleted = 0

            def _scan_and_delete():
                nonlocal deleted
                cursor = 0
                while True:
                    cursor, keys = client.scan(cursor, match=pattern, count=100)
                    if keys:
                        client.delete(*keys)
                        deleted += len(keys)
                    if cursor == 0:
                        break

            await asyncio.to_thread(_scan_and_delete)
            if deleted:
                logger.info("Invalidated %d cache entries for %s", deleted, template_name)
            return True
        except Exception as e:
            logger.warning("Cache invalidation failed: %s", e)
            return False

    def health_check(self) -> dict:
        """Check Redis connectivity and return cache stats."""
        result = {"enabled": self.enabled, "connected": False}

        if not self.enabled:
            result["reason"] = "Redis caching disabled"
            return result

        try:
            client = self._get_client()
            if client is not None:
                client.ping()
                result["connected"] = True
                info = client.info("keyspace")
                result["keyspace_info"] = info
        except Exception as e:
            result["error"] = str(e)

        return result


# Singleton instance
prompt_cache = PromptCache(
    redis_url=None,
    enabled=True,
)