"""Basic test for package installation."""

import pytest


def test_package_imports():
    """Test that the package can be imported."""
    try:
        import ai_analyzer

        assert ai_analyzer.__version__ == "0.1.0"
    except ImportError:
        pytest.fail("Failed to import ai_analyzer package")
