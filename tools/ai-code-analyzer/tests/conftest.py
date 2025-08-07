"""Test configuration and fixtures for AI Code Analyzer."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def sample_project_path() -> Generator[Path, None, None]:
    """Provide a sample project directory for testing."""
    test_project = TEST_DATA_DIR / "sample_python_project"
    if not test_project.exists():
        test_project.mkdir(parents=True, exist_ok=True)
        # Create a basic Python project structure
        (test_project / "src").mkdir(exist_ok=True)
        (test_project / "tests").mkdir(exist_ok=True)
        (test_project / "README.md").write_text("# Sample Project")
        (test_project / "pyproject.toml").write_text(
            """
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[project]
name = "sample-project"
version = "0.1.0"
"""
        )
    yield test_project


@pytest.fixture
def mock_llm_provider() -> Mock:
    """Provide a mock LLM provider for testing."""
    provider = Mock()
    provider.analyze.return_value = {
        "insights": ["Test insight"],
        "recommendations": ["Test recommendation"],
        "metrics": {"complexity": 0.5},
    }
    return provider


@pytest.fixture
async def sample_analysis_config() -> Any:
    """Provide a sample analysis configuration."""
    # Import here to avoid circular imports during test discovery
    from ai_analyzer.core.config import AnalysisConfig

    return AnalysisConfig(
        llm_provider="mock",
        analysis_depth=1,
        max_tokens=1000,
        timeout_seconds=30,
    )


# Async test configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
