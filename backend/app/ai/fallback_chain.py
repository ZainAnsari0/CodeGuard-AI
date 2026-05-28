"""
CodeGuard AI - AI Fallback Chain
Orchestrates AI providers with fallback: OpenAI → Groq → Ollama → Rule-based.
Includes retry logic, token tracking, and circuit breaker.
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

from app.ai.providers.base import AIProvider
from app.ai.providers.ollama_provider import OllamaProvider
from app.ai.providers.rule_based_provider import RuleBasedProvider
from app.core.config import settings
from app.core.exceptions import AIException

logger = logging.getLogger(__name__)


class TokenUsageTracker:
    """Tracks token usage per provider and per day. Persists to Redis when available."""

    def __init__(self):
        self._usage: Dict[str, Dict[str, Any]] = {}
        self._daily_totals: Dict[str, Dict[str, int]] = {}
        self._redis = None

    async def _get_redis(self):
        if self._redis is None and settings.REDIS_ENABLED:
            try:
                import redis.asyncio as aioredis
                self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            except Exception as e:
                logger.warning("TokenUsageTracker: Redis unavailable, using in-memory: %s", e)
        return self._redis

    def record(self, provider: str, input_tokens: int = 0, output_tokens: int = 0, cost_usd: float = 0.0):
        """Record token usage for a provider call.

        In-memory counters are always updated immediately.
        Redis persistence is queued as a fire-and-forget async task when
        called from within a running event loop; otherwise it is skipped
        (the data will still be in memory and persisted on the next async call).
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        if provider not in self._usage:
            self._usage[provider] = {"total_calls": 0, "total_input_tokens": 0, "total_output_tokens": 0, "total_cost": 0.0}
        self._usage[provider]["total_calls"] += 1
        self._usage[provider]["total_input_tokens"] += input_tokens
        self._usage[provider]["total_output_tokens"] += output_tokens
        self._usage[provider]["total_cost"] += cost_usd

        if today not in self._daily_totals:
            self._daily_totals[today] = {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost": 0.0}
        self._daily_totals[today]["calls"] += 1
        self._daily_totals[today]["input_tokens"] += input_tokens
        self._daily_totals[today]["output_tokens"] += output_tokens
        self._daily_totals[today]["cost"] += cost_usd

        logger.debug(f"Token usage: {provider} +{input_tokens}in/+{output_tokens}out, daily total: {self._daily_totals[today]}")

        # Fire-and-forget async persist — safe from both sync and async contexts
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._persist_to_redis(provider, today))
        except RuntimeError:
            # No running event loop — data is still tracked in memory;
            # it will be persisted on the next call made from an async context.
            pass

    async def _persist_to_redis(self, provider: str, today: str):
        """Persist usage data to Redis."""
        import json
        r = await self._get_redis()
        if r:
            key = f"token_usage:provider:{provider}"
            await r.hset(key, mapping={
                "total_calls": self._usage[provider]["total_calls"],
                "total_input_tokens": self._usage[provider]["total_input_tokens"],
                "total_output_tokens": self._usage[provider]["total_output_tokens"],
                "total_cost": self._usage[provider]["total_cost"],
            })
            daily_key = f"token_usage:daily:{today}"
            await r.hset(daily_key, mapping={
                "calls": self._daily_totals[today]["calls"],
                "input_tokens": self._daily_totals[today]["input_tokens"],
                "output_tokens": self._daily_totals[today]["output_tokens"],
                "cost": self._daily_totals[today]["cost"],
            })

    def get_summary(self) -> Dict[str, Any]:
        """Get usage summary for admin visibility."""
        return {
            "by_provider": dict(self._usage),
            "daily_totals": dict(self._daily_totals),
        }


class ProviderCircuitBreaker:
    """Circuit breaker with exponential backoff for provider health tracking."""

    BASE_TIMEOUT: float = 30.0
    MAX_TIMEOUT: float = 300.0

    def __init__(self, failure_threshold: int = 3):
        self.failure_threshold = failure_threshold
        self._failure_counts: Dict[str, int] = {}
        self._last_failure_time: Dict[str, float] = {}
        self._open_circuits: Dict[str, bool] = {}

    def _get_reset_timeout(self, provider: str) -> float:
        """Exponential backoff: 30s → 60s → 120s → 240s → 300s cap."""
        count = self._failure_counts.get(provider, 0)
        timeout = self.BASE_TIMEOUT * (2 ** count)
        return min(timeout, self.MAX_TIMEOUT)

    def record_failure(self, provider: str):
        """Record a provider failure."""
        self._failure_counts[provider] = self._failure_counts.get(provider, 0) + 1
        self._last_failure_time[provider] = time.time()
        if self._failure_counts[provider] >= self.failure_threshold:
            self._open_circuits[provider] = True
            logger.warning(f"Circuit breaker OPEN for {provider} after {self._failure_counts[provider]} failures")

    def record_success(self, provider: str):
        """Record a provider success, resetting the failure count."""
        self._failure_counts[provider] = 0
        self._open_circuits[provider] = False

    def is_open(self, provider: str) -> bool:
        """Check if the circuit breaker is open (provider should be skipped)."""
        if not self._open_circuits.get(provider, False):
            return False
        # Auto-reset after exponential backoff timeout
        last_failure = self._last_failure_time.get(provider, 0)
        timeout = self._get_reset_timeout(provider)
        if time.time() - last_failure > timeout:
            self._open_circuits[provider] = False
            self._failure_counts[provider] = 0
            logger.info(f"Circuit breaker RESET for {provider} after timeout")
            return False
        return True


class AIFallbackChain:
    """Orchestrates AI providers with cascading fallback, retry, and tracking."""

    MAX_RETRIES = 2
    RETRY_DELAY = 1.0  # seconds

    def __init__(self):
        self.providers: List[AIProvider] = []
        self.token_tracker = TokenUsageTracker()
        self.circuit_breaker = ProviderCircuitBreaker()
        self._init_providers()

    def _init_providers(self):
        """Initialize providers based on available configuration."""
        if settings.OPENAI_API_KEY:
            try:
                from app.ai.providers.openai_provider import OpenAIProvider
                self.providers.append(OpenAIProvider())
                logger.info("OpenAI provider registered")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI provider: {e}")

        if settings.GROQ_API_KEY:
            try:
                from app.ai.providers.groq_provider import GroqProvider
                self.providers.append(GroqProvider())
                logger.info("Groq provider registered")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq provider: {e}")

        self.providers.append(OllamaProvider())
        self.providers.append(RuleBasedProvider())

        logger.info(
            f"AI fallback chain initialized: "
            f"{' → '.join(p.name for p in self.providers)}"
        )

    async def generate(
        self, prompt: str, system: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """Try each provider in order with retry logic and circuit breaker."""
        last_error = None

        for provider in self.providers:
            if self.circuit_breaker.is_open(provider.name):
                logger.info(f"Circuit breaker open for {provider.name}, skipping")
                continue

            for attempt in range(self.MAX_RETRIES):
                try:
                    start = time.time()

                    # Health check on first attempt only
                    if attempt == 0:
                        health = await provider.check_health()
                        if not health.get("available", False):
                            logger.info(f"Provider {provider.name} unavailable, skipping")
                            break

                    result = await provider.generate(prompt, system=system, **kwargs)
                    result["provider_used"] = provider.name
                    result["latency_ms"] = round((time.time() - start) * 1000, 1)

                    # Track tokens if available
                    input_tokens = result.get("input_tokens", 0) or result.get("usage", {}).get("prompt_tokens", 0)
                    output_tokens = result.get("output_tokens", 0) or result.get("usage", {}).get("completion_tokens", 0)
                    self.token_tracker.record(provider.name, input_tokens, output_tokens)

                    self.circuit_breaker.record_success(provider.name)
                    logger.info(f"AI response from {provider.name} (attempt {attempt + 1})")
                    return result

                except Exception as e:
                    last_error = e
                    logger.warning(f"Provider {provider.name} attempt {attempt + 1} failed: {e}")
                    if attempt < self.MAX_RETRIES - 1:
                        await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
                    continue

            # All retries exhausted for this provider
            self.circuit_breaker.record_failure(provider.name)

        raise AIException(
            message=f"All AI providers failed. Last error: {last_error}"
        )

    async def chat(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> Dict[str, Any]:
        """Try each provider in order for chat-style interaction with retry."""
        last_error = None

        for provider in self.providers:
            if self.circuit_breaker.is_open(provider.name):
                continue

            for attempt in range(self.MAX_RETRIES):
                try:
                    start = time.time()

                    if attempt == 0:
                        health = await provider.check_health()
                        if not health.get("available", False):
                            break

                    result = await provider.chat(messages, **kwargs)
                    result["provider_used"] = provider.name
                    result["latency_ms"] = round((time.time() - start) * 1000, 1)

                    input_tokens = result.get("input_tokens", 0) or result.get("usage", {}).get("prompt_tokens", 0)
                    output_tokens = result.get("output_tokens", 0) or result.get("usage", {}).get("completion_tokens", 0)
                    self.token_tracker.record(provider.name, input_tokens, output_tokens)

                    self.circuit_breaker.record_success(provider.name)
                    return result

                except Exception as e:
                    last_error = e
                    logger.warning(f"Provider {provider.name} chat attempt {attempt + 1} failed: {e}")
                    if attempt < self.MAX_RETRIES - 1:
                        await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
                    continue

            self.circuit_breaker.record_failure(provider.name)

        raise AIException(
            message=f"All AI providers failed. Last error: {last_error}"
        )

    def get_provider_status(self) -> Dict[str, bool]:
        """Get availability status of each provider."""
        return {
            provider.name: not self.circuit_breaker.is_open(provider.name)
            for provider in self.providers
        }

    def get_token_usage(self) -> Dict[str, Any]:
        """Get token usage summary for admin dashboard."""
        return self.token_tracker.get_summary()


# Singleton instance
ai_chain = AIFallbackChain()