"""
CodeGuard AI - Ollama Provider
Local LLM provider wrapping the existing OllamaClient.
"""

import logging
from typing import Optional, Dict, Any, List

from app.ai.providers.base import AIProvider
from app.ai.ollama_client import ollama_client

logger = logging.getLogger(__name__)


class OllamaProvider(AIProvider):
    """Local Ollama LLM provider."""

    @property
    def name(self) -> str:
        return "ollama"

    async def generate(
        self, prompt: str, system: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        result = await ollama_client.generate(
            prompt=prompt,
            system=system,
            model=kwargs.get("model"),
        )

        return {
            "response": result.get("response", ""),
            "model": result.get("model", kwargs.get("model", "ollama")),
            "provider": self.name,
        }

    async def chat(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> Dict[str, Any]:
        result = await ollama_client.chat(
            messages=messages,
            model=kwargs.get("model"),
        )

        return {
            "response": result.get("message", {}).get("content", ""),
            "model": result.get("model", kwargs.get("model", "ollama")),
            "provider": self.name,
        }

    async def check_health(self) -> Dict[str, Any]:
        return await ollama_client.check_health()