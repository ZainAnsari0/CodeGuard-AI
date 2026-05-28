"""
CodeGuard AI - OpenAI Provider
Cloud LLM provider using the OpenAI API.
"""

import logging
from typing import Optional, Dict, Any, List

from app.core.config import settings
from app.ai.providers.base import AIProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """OpenAI API provider (GPT models)."""

    def __init__(self):
        self._client = None
        self._model = "gpt-4o-mini"

    def _get_client(self):
        """Lazy-initialize OpenAI client to avoid import at startup."""
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=30.0,
                max_retries=2,
            )
        return self._client

    @property
    def client(self):
        return self._get_client()

    @property
    def name(self) -> str:
        return "openai"

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
        )

        return {
            "response": response.choices[0].message.content,
            "model": response.model,
            "provider": self.name,
        }

    async def chat(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> Dict[str, Any]:
        response = await self.client.chat.completions.create(
            model=kwargs.get("model", self._model),
            messages=messages,
            temperature=kwargs.get("temperature", 0.3),
            max_tokens=kwargs.get("max_tokens", 2048),
        )

        return {
            "response": response.choices[0].message.content,
            "model": response.model,
            "provider": self.name,
        }

    async def check_health(self) -> Dict[str, Any]:
        try:
            await self.client.models.list()
            return {"available": True, "error": None}
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}")
            return {"available": False, "error": str(e)}