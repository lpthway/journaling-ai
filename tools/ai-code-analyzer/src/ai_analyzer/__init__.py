"""AI Code Analyzer - Intelligent code analysis with multiple LLM providers.

A modular, extensible framework for analyzing codebases using AI models like Claude,
OpenAI, and local LLMs with advanced quota management and resume capabilities.

Example:
    Basic usage:
    >>> from ai_analyzer import analyze_project
    >>> result = await analyze_project("/path/to/project")
    >>> print(result.summary)

    Advanced usage with configuration:
    >>> from ai_analyzer.core.config import AnalysisConfig
    >>> config = AnalysisConfig(
    ...     llm_provider="claude",
    ...     analysis_depth=3,
    ...     focus_areas=["documentation", "security"]
    ... )
    >>> result = await analyze_project("/path/to/project", config=config)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from ai_analyzer.core.config import AnalysisConfig
    from ai_analyzer.core.models import AnalysisResult

# Version information
__version__ = "0.1.0"
__author__ = "AI Code Analyzer Team"
__email__ = "contact@ai-code-analyzer.dev"
__license__ = "MIT"

# Package metadata
__title__ = "ai-code-analyzer"
__description__ = "AI-powered code analysis framework"
__url__ = "https://github.com/ai-code-analyzer/ai-code-analyzer"

# Configure default logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

# Public API exports
__all__ = [
    "__version__",
    "analyze_project",
    "AnalysisConfig",
    "AnalysisResult",
]


async def analyze_project(
    project_path: Path | str,
    *,
    config: AnalysisConfig | None = None,
) -> AnalysisResult:
    """Analyze a project with AI-powered insights.

    This is the main entry point for the AI Code Analyzer. It provides
    a simple interface for analyzing any codebase with intelligent
    project type detection and configurable analysis depth.

    Args:
        project_path: Path to the project directory to analyze
        config: Optional analysis configuration. If not provided,
               defaults will be used with auto-detection.

    Returns:
        Comprehensive analysis results with insights and recommendations

    Example:
        >>> result = await analyze_project("/my/project")
        >>> print(f"Project type: {result.project_info.project_type}")
        >>> print(f"Overall score: {result.metrics.overall_score}")
        >>> for finding in result.findings:
        ...     print(f"- {finding.title}: {finding.description}")
    """
    # Import here to avoid circular imports
    from ai_analyzer.core.analyzer import ProjectAnalyzer
    from ai_analyzer.core.config import AnalysisConfig as Config

    if config is None:
        config = Config()

    analyzer = ProjectAnalyzer(config)
    return await analyzer.analyze(project_path)


# Lazy imports for better startup performance
def __getattr__(name: str) -> object:
    """Lazy import of heavy modules."""
    if name == "AnalysisConfig":
        from ai_analyzer.core.config import AnalysisConfig

        return AnalysisConfig
    elif name == "AnalysisResult":
        from ai_analyzer.core.models import AnalysisResult

        return AnalysisResult
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
