"""
CodeGuard AI - AI Module
Provides LLM parsing, prompt management, and Ollama client.
"""

from app.ai.parser import (
    LLMOutputParser,
    ScanResult,
    VulnerabilityFinding,
    FixSuggestion,
    ExplanationResult,
    LLMOutputParseError,
    LLMOutputValidationError,
)
from app.ai.prompts import PromptManager

__all__ = [
    "LLMOutputParser",
    "ScanResult",
    "VulnerabilityFinding",
    "FixSuggestion",
    "ExplanationResult",
    "LLMOutputParseError",
    "LLMOutputValidationError",
    "PromptManager",
]