"""Base LLM provider interface and common functionality.

This module defines the abstract base class that all LLM providers must implement,
along with common utilities for provider registration and management.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from ai_analyzer.core.models import AnalysisConfig, AnalysisResult, LLMProvider


class ProviderCapabilities(BaseModel):
    """Capabilities and limits of an LLM provider."""

    supports_streaming: bool = Field(default=False, description="Supports streaming responses")
    supports_function_calling: bool = Field(
        default=False, description="Supports function/tool calling"
    )
    supports_vision: bool = Field(default=False, description="Supports image analysis")
    max_context_length: int = Field(default=4000, description="Maximum context window in tokens")
    max_output_tokens: int = Field(default=1000, description="Maximum output tokens per request")
    cost_per_input_token: float = Field(default=0.0, description="Cost per input token in USD")
    cost_per_output_token: float = Field(default=0.0, description="Cost per output token in USD")
    rate_limit_requests_per_minute: int = Field(default=60, description="Rate limit per minute")
    requires_api_key: bool = Field(default=True, description="Requires API key authentication")


class ProviderError(Exception):
    """Base exception for LLM provider errors."""

    def __init__(self, message: str, provider: str, error_code: str | None = None):
        super().__init__(message)
        self.provider = provider
        self.error_code = error_code


class QuotaExhaustedError(ProviderError):
    """Raised when the provider's quota or rate limit is exceeded."""

    def __init__(self, provider: str, reset_time: int | None = None):
        super().__init__(f"Quota exhausted for provider {provider}", provider, "QUOTA_EXCEEDED")
        self.reset_time = reset_time


class AuthenticationError(ProviderError):
    """Raised when authentication fails."""

    def __init__(self, provider: str):
        super().__init__(f"Authentication failed for provider {provider}", provider, "AUTH_FAILED")


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers.

    This class defines the interface that all LLM providers must implement,
    including methods for analysis, configuration, and error handling.
    """

    def __init__(self, config: AnalysisConfig):
        """Initialize the provider with configuration.

        Args:
            config: Analysis configuration containing provider settings
        """
        self.config = config
        self._capabilities: ProviderCapabilities | None = None

    @property
    @abstractmethod
    def provider_type(self) -> LLMProvider:
        """The type of this provider."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        """Provider capabilities and limitations."""
        pass

    @abstractmethod
    async def analyze_code(
        self, code: str, context: dict[str, Any], analysis_type: str = "general"
    ) -> AnalysisResult:
        """Analyze code and return structured results.

        Args:
            code: Code content to analyze
            context: Additional context (file path, project info, etc.)
            analysis_type: Type of analysis to perform

        Returns:
            Structured analysis results

        Raises:
            ProviderError: If analysis fails
            QuotaExhaustedError: If quota is exceeded
            AuthenticationError: If authentication fails
        """
        pass

    @abstractmethod
    async def analyze_project(
        self, project_files: list[str], project_context: dict[str, Any]
    ) -> AnalysisResult:
        """Analyze an entire project.

        Args:
            project_files: List of file paths or contents
            project_context: Project metadata and context

        Returns:
            Comprehensive project analysis

        Raises:
            ProviderError: If analysis fails
        """
        pass

    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate that the provider can connect and authenticate.

        Returns:
            True if connection is valid, False otherwise
        """
        pass

    async def estimate_cost(self, input_text: str, estimated_output_tokens: int = 1000) -> float:
        """Estimate the cost of analyzing the given input.

        Args:
            input_text: Input text to analyze
            estimated_output_tokens: Estimated output length

        Returns:
            Estimated cost in USD
        """
        if not self.capabilities.requires_api_key:
            return 0.0

        # Simple token estimation (rough approximation)
        input_tokens = len(input_text.split()) * 1.3  # Account for tokenization

        input_cost = input_tokens * self.capabilities.cost_per_input_token
        output_cost = estimated_output_tokens * self.capabilities.cost_per_output_token

        return input_cost + output_cost

    def supports_analysis_type(self, analysis_type: str) -> bool:
        """Check if the provider supports a specific analysis type.

        Args:
            analysis_type: Type of analysis to check

        Returns:
            True if supported, False otherwise
        """
        # Base implementation - all providers support general analysis
        supported_types = ["general", "code_review", "security", "performance"]
        return analysis_type in supported_types

    async def health_check(self) -> dict[str, Any]:
        """Perform a health check on the provider.

        Returns:
            Health status information
        """
        try:
            is_valid = await self.validate_connection()
            return {
                "provider": self.provider_type.value,
                "status": "healthy" if is_valid else "unhealthy",
                "capabilities": self.capabilities.dict(),
                "timestamp": asyncio.get_event_loop().time(),
            }
        except Exception as e:
            return {
                "provider": self.provider_type.value,
                "status": "error",
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time(),
            }


class ProviderRegistry:
    """Registry for managing LLM providers."""

    _providers: dict[LLMProvider, type[BaseLLMProvider]] = {}

    @classmethod
    def register(cls, provider_type: LLMProvider, provider_class: type[BaseLLMProvider]) -> None:
        """Register a provider class.

        Args:
            provider_type: The provider type enum
            provider_class: The provider implementation class
        """
        cls._providers[provider_type] = provider_class

    @classmethod
    def get_provider(cls, provider_type: LLMProvider, config: AnalysisConfig) -> BaseLLMProvider:
        """Get a provider instance.

        Args:
            provider_type: The provider type to get
            config: Configuration for the provider

        Returns:
            Provider instance

        Raises:
            ValueError: If provider type is not registered
        """
        if provider_type not in cls._providers:
            raise ValueError(f"Provider {provider_type.value} is not registered")

        provider_class = cls._providers[provider_type]
        return provider_class(config)

    @classmethod
    def list_providers(cls) -> list[LLMProvider]:
        """List all registered providers.

        Returns:
            List of registered provider types
        """
        return list(cls._providers.keys())

    @classmethod
    def is_registered(cls, provider_type: LLMProvider) -> bool:
        """Check if a provider is registered.

        Args:
            provider_type: Provider type to check

        Returns:
            True if registered, False otherwise
        """
        return provider_type in cls._providers


def register_provider(provider_type: LLMProvider):
    """Decorator for registering providers.

    Args:
        provider_type: The provider type to register

    Returns:
        Decorator function
    """

    def decorator(provider_class: type[BaseLLMProvider]):
        ProviderRegistry.register(provider_type, provider_class)
        return provider_class

    return decorator


def get_provider(provider_type: LLMProvider, config: AnalysisConfig) -> BaseLLMProvider:
    """Convenience function to get a provider instance.

    Args:
        provider_type: The provider type to get
        config: Configuration for the provider

    Returns:
        Provider instance
    """
    return ProviderRegistry.get_provider(provider_type, config)
