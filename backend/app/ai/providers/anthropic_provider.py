"""
CodeGuard AI - Anthropic Claude Provider
Cloud LLM provider using the Anthropic API (Claude models).
"""

import logging
from typing import Optional, Dict, Any, List

from app.core.config import settings
from app.ai.providers.base import AIProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(AIProvider):
    """Anthropic Claude API provider."""

    def __init__(self):
        self._client = None
        self._model = "claude-3-5-haiku-20241022"

    def _get_client(self):
        """Lazy-initialize Anthropic client to avoid import at startup."""
        if self._client is None:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(
                api_key=settings.ANTHROPIC_API_KEY,
                timeout=30.0,
                max_retries=2,
            )
        return self._client

    @property
    def client(self):
        return self._get_client()

    @property
    def name(self) -> str:
        return "anthropic"

    async def generate(
        self, prompt: str, system: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        response = await self.client.messages.create(
            model=kwargs.get("model", self._model),
            max_tokens=kwargs.get("max_tokens", 2048),
            temperature=kwargs.get("temperature", 0.3),
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
        )

        content = ""
        if response.content:
            content = response.content[0].text if hasattr(response.content[0], "text") else str(response.content[0])

        return {
            "response": content,
            "model": response.model,
            "provider": self.name,
            "usage": {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
            },
        }

    async def chat(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> Dict[str, Any]:
        # Convert generic messages to Anthropic format (system is a top-level param)
        system_text = ""
        anthropic_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system_text = msg.get("content", "")
            else:
                anthropic_messages.append(msg)

        response = await self.client.messages.create(
            model=kwargs.get("model", self._model),
            max_tokens=kwargs.get("max_tokens", 2048),
            temperature=kwargs.get("temperature", 0.3),
            system=system_text,
            messages=anthropic_messages,
        )

        content = ""
        if response.content:
            content = response.content[0].text if hasattr(response.content[0], "text") else str(response.content[0])

        return {
            "response": content,
            "model": response.model,
            "provider": self.name,
            "usage": {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
            },
        }

    async def check_health(self) -> Dict[str, Any]:
        try:
            # Anthropic doesn't have a simple models.list(); do a minimal request
            response = await self.client.messages.create(
                model=self._model,
                max_tokens=1,
                messages=[{"role": "user", "content": "hi"}],
            )
            return {"available": True, "error": None}
        except Exception as e:
            logger.warning(f"Anthropic health check failed: {e}")
            return {"available": False, "error": str(e)}
