"""Tests for AI fallback chain: circuit breaker, token tracker, provider fallback."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone


class TestCircuitBreaker:
    """Tests for the circuit breaker pattern in the fallback chain."""

    def test_circuit_breaker_starts_closed(self):
        """Circuit breaker should start in closed (healthy) state."""
        from app.ai.fallback_chain import ProviderCircuitBreaker

        cb = ProviderCircuitBreaker(failure_threshold=3)
        # No circuits should be open initially
        assert cb.is_open("test-provider") is False

    def test_circuit_breaker_opens_after_threshold(self):
        """Circuit breaker should open after reaching failure threshold."""
        from app.ai.fallback_chain import ProviderCircuitBreaker

        cb = ProviderCircuitBreaker(failure_threshold=3)
        cb.record_failure("provider-a")
        cb.record_failure("provider-a")
        assert cb.is_open("provider-a") is False  # Not yet at threshold

        cb.record_failure("provider-a")  # Third failure
        assert cb.is_open("provider-a") is True

    def test_circuit_breaker_success_resets_count(self):
        """A successful call should reset the failure count."""
        from app.ai.fallback_chain import ProviderCircuitBreaker

        cb = ProviderCircuitBreaker(failure_threshold=3)
        cb.record_failure("provider-a")
        cb.record_failure("provider-a")

        cb.record_success("provider-a")
        # After success, failure count is reset, so not open
        assert cb.is_open("provider-a") is False

    def test_circuit_breaker_per_provider_isolation(self):
        """Failures for one provider should not affect another."""
        from app.ai.fallback_chain import ProviderCircuitBreaker

        cb = ProviderCircuitBreaker(failure_threshold=2)
        cb.record_failure("provider-a")
        cb.record_failure("provider-a")
        assert cb.is_open("provider-a") is True

        # provider-b should be unaffected
        assert cb.is_open("provider-b") is False


class TestTokenUsageTracker:
    """Tests for token usage tracking."""

    def test_token_tracker_records_usage(self):
        """Token tracker should record input/output tokens and cost."""
        from app.ai.fallback_chain import TokenUsageTracker

        tracker = TokenUsageTracker()
        tracker.record(provider="openai", input_tokens=100, output_tokens=50, cost_usd=0.015)

        summary = tracker.get_summary()
        assert "by_provider" in summary
        assert "openai" in summary["by_provider"]
        assert summary["by_provider"]["openai"]["total_calls"] == 1
        assert summary["by_provider"]["openai"]["total_input_tokens"] == 100
        assert summary["by_provider"]["openai"]["total_output_tokens"] == 50

    def test_token_tracker_accumulates(self):
        """Multiple calls should accumulate in the tracker."""
        from app.ai.fallback_chain import TokenUsageTracker

        tracker = TokenUsageTracker()
        tracker.record("openai", input_tokens=100, output_tokens=50, cost_usd=0.015)
        tracker.record("openai", input_tokens=200, output_tokens=100, cost_usd=0.030)
        tracker.record("groq", input_tokens=50, output_tokens=25, cost_usd=0.001)

        summary = tracker.get_summary()
        assert summary["by_provider"]["openai"]["total_calls"] == 2
        assert summary["by_provider"]["openai"]["total_input_tokens"] == 300
        assert summary["by_provider"]["groq"]["total_calls"] == 1

    def test_token_tracker_daily_tracking(self):
        """Token tracker should track usage by day."""
        from app.ai.fallback_chain import TokenUsageTracker

        tracker = TokenUsageTracker()
        tracker.record("openai", input_tokens=100, output_tokens=50, cost_usd=0.015)

        summary = tracker.get_summary()
        assert "daily_totals" in summary

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        assert today in summary["daily_totals"]
        assert summary["daily_totals"][today]["calls"] == 1


class TestProviderFallback:
    """Tests for provider fallback behavior."""

    @pytest.mark.asyncio
    async def test_fallback_to_next_provider_on_failure(self):
        """When the first provider fails, should try the next."""
        from app.ai.fallback_chain import AIFallbackChain, ProviderCircuitBreaker

        chain = AIFallbackChain()

        # Mock providers: first fails, second succeeds
        provider1 = MagicMock()
        provider1.name = "provider-1"
        provider1.check_health = AsyncMock(return_value={"available": True})
        provider1.generate = AsyncMock(side_effect=Exception("Provider 1 failed"))

        provider2 = MagicMock()
        provider2.name = "provider-2"
        provider2.check_health = AsyncMock(return_value={"available": True})
        provider2.generate = AsyncMock(return_value={
            "response": "Success from provider 2",
            "provider": "mock-2",
            "model": "test",
        })

        chain.providers = [provider1, provider2]

        result = await chain.generate(prompt="test prompt")
        assert result["response"] == "Success from provider 2"

    @pytest.mark.asyncio
    async def test_all_providers_fail_raises_exception(self):
        """When all providers fail, should raise an exception."""
        from app.ai.fallback_chain import AIFallbackChain
        from app.core.exceptions import AIException

        chain = AIFallbackChain()

        failing_provider = MagicMock()
        failing_provider.name = "failing-provider"
        failing_provider.check_health = AsyncMock(return_value={"available": True})
        failing_provider.generate = AsyncMock(side_effect=Exception("All providers down"))

        chain.providers = [failing_provider]

        with pytest.raises(AIException):
            await chain.generate(prompt="test prompt")

    @pytest.mark.asyncio
    async def test_unavailable_provider_skipped(self):
        """Provider with failed health check should be skipped."""
        from app.ai.fallback_chain import AIFallbackChain

        chain = AIFallbackChain()

        provider1 = MagicMock()
        provider1.name = "provider-1"
        provider1.check_health = AsyncMock(return_value={"available": False})
        # Should never be called
        provider1.generate = AsyncMock()

        provider2 = MagicMock()
        provider2.name = "provider-2"
        provider2.check_health = AsyncMock(return_value={"available": True})
        provider2.generate = AsyncMock(return_value={
            "response": "Success",
            "provider": "provider-2",
            "model": "test",
        })

        chain.providers = [provider1, provider2]

        result = await chain.generate(prompt="test prompt")
        assert result["response"] == "Success"
        provider1.generate.assert_not_called()