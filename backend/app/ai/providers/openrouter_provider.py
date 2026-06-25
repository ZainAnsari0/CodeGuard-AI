"""
CodeGuard AI - OpenRouter Provider
Cloud LLM provider using the OpenRouter API (OpenAI-compatible).
"""

import logging
from typing import Optional, Dict, Any, List

from app.core.config import settings
from app.ai.providers.base import AIProvider

logger = logging.getLogger(__name__)


class OpenRouterProvider(AIProvider):
    """OpenRouter API provider — universal gateway to hundreds of models."""

    def __init__(self):
        self._client = None
        # Budget-friendly fast model; users can override via kwargs
        self._model = "google/gemma-3-4b-it:free"

    def _get_client(self):
        """Lazy-initialize OpenAI-compatible client for OpenRouter."""
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.OPENROUTER_API_KEY,
                timeout=30.0,
                max_retries=2,
            )
        return self._client

    @property
    def client(self):
        return self._get_client()

    @property
    def name(self) -> str:
        return "openrouter"

    async def generate(
        self, prompt: str, system: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=kwargs.get("model", self._model),
            messages=messages,
            temperature=kwargs.get("temperature", 0.3),
            max_tokens=kwargs.get("max_tokens", 2048),
            extra_headers={
                "HTTP-Referer": "https://codeguard.ai",
                "X-Title": "CodeGuard AI",
            },
        )

        return {
            "response": response.choices[0].message.content,
            "model": response.model,
            "provider": self.name,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            },
        }

    async def chat(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> Dict[str, Any]:
        response = await self.client.chat.completions.create(
            model=kwargs.get("model", self._model),
            messages=messages,
            temperature=kwargs.get("temperature", 0.3),
            max_tokens=kwargs.get("max_tokens", 2048),
            extra_headers={
                "HTTP-Referer": "https://codeguard.ai",
                "X-Title": "CodeGuard AI",
            },
        )

        return {
            "response": response.choices[0].message.content,
            "model": response.model,
            "provider": self.name,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            },
        }

    async def check_health(self) -> Dict[str, Any]:
        try:
            # Use the free model for a minimal health check
            await self.client.chat.completions.create(
                model="google/gemma-3-4b-it:free",
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1,
            )
            return {"available": True, "error": None}
        except Exception as e:
            logger.warning(f"OpenRouter health check failed: {e}")
            return {"available": False, "error": str(e)}
