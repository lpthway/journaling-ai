"""LLM provider implementations for the AI Code Analyzer.

This module contains providers for different LLM services including:
- Claude (Anthropic)
- OpenAI/Azure OpenAI
- GitHub Copilot Chat
- Local/Ollama models
"""

from __future__ import annotations

# Import all providers to trigger registration
from ai_analyzer.core.models import LLMProvider
from ai_analyzer.providers.base import BaseLLMProvider, ProviderRegistry, get_provider
from ai_analyzer.providers.copilot import CopilotProvider

__all__ = ["LLMProvider", "BaseLLMProvider", "CopilotProvider", "ProviderRegistry", "get_provider"]
