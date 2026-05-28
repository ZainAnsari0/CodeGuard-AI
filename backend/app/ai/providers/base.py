"""
CodeGuard AI - Base AI Provider
Abstract interface for all AI/LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class AIProvider(ABC):
    """Base class for AI providers."""

    @abstractmethod
    async def generate(
        self, prompt: str, system: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """Generate a response from a prompt.

        Returns dict with 'response', 'model', 'provider' keys.
        """
        ...

    @abstractmethod
    async def chat(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> Dict[str, Any]:
        """Chat-style interaction. Returns dict with 'response', 'model', 'provider' keys."""
        ...

    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """Check provider availability. Returns {'available': bool, 'error': str|None}."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging."""
        ...