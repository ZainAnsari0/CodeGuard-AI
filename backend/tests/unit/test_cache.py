"""Tests for the caching service: Redis cache with in-memory fallback."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.cache import PromptCache


class TestCacheService:
    """Tests for cache service operations."""

    def test_hash_prompt_is_deterministic(self):
        """Same input should produce the same hash."""
        cache = PromptCache(enabled=False)
        h1 = cache.hash_prompt("test prompt")
        h2 = cache.hash_prompt("test prompt")
        assert h1 == h2

    def test_hash_prompt_differs_for_different_prompts(self):
        """Different prompts should produce different hashes."""
        cache = PromptCache(enabled=False)
        h1 = cache.hash_prompt("prompt A")
        h2 = cache.hash_prompt("prompt B")
        assert h1 != h2

    def test_cache_key_format(self):
        """Cache key should follow the expected format."""
        cache = PromptCache(enabled=False)
        key = cache._make_key("vulnerability_analysis", "abc123", "gpt-4")
        assert key == "prompt_cache:vulnerability_analysis:gpt-4:abc123"

    def test_cache_get_returns_none_when_disabled(self):
        """When cache is disabled, get should return None."""
        cache = PromptCache(enabled=False)
        result = cache.get("vulnerability_analysis", "test prompt", "gpt-4")
        assert result is None

    def test_cache_set_returns_false_when_disabled(self):
        """When cache is disabled, set should return False."""
        cache = PromptCache(enabled=False)
        result = cache.set("vulnerability_analysis", "test prompt", "gpt-4", {"data": "test"})
        assert result is False

    def test_cache_invalidate_returns_false_when_disabled(self):
        """When cache is disabled, invalidate should return False."""
        cache = PromptCache(enabled=False)
        result = cache.invalidate("vulnerability_analysis")
        assert result is False

    def test_cache_get_with_mock_redis(self):
        """Test cache get with mocked Redis client."""
        import json

        cache = PromptCache(enabled=True)
        mock_redis = MagicMock()
        mock_redis.get.return_value = json.dumps({"findings": [], "summary": "test"})
        cache._client = mock_redis

        result = cache.get("vulnerability_analysis", "test prompt", "gpt-4")
        assert result is not None
        assert result["summary"] == "test"

    def test_cache_set_with_mock_redis(self):
        """Test cache set with mocked Redis client."""
        cache = PromptCache(enabled=True)
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        cache._client = mock_redis

        result = cache.set("vulnerability_analysis", "test prompt", "gpt-4", {"data": "test"})
        assert result is True
        mock_redis.setex.assert_called_once()

    def test_cache_get_handles_redis_error(self):
        """Cache should gracefully handle Redis errors."""
        cache = PromptCache(enabled=True)
        mock_redis = MagicMock()
        mock_redis.get.side_effect = Exception("Redis connection error")
        cache._client = mock_redis

        # Override _get_client to return our mock
        with patch.object(cache, '_get_client', return_value=mock_redis):
            result = cache.get("vulnerability_analysis", "test prompt", "gpt-4")
            assert result is None  # Should return None on error