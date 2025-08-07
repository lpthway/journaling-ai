"""Configuration management for the AI Code Analyzer.

This module provides configuration loading, validation, and management
using Pydantic settings with support for multiple configuration sources.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from ai_analyzer.core.models import AnalysisConfig


class ConfigurationError(Exception):
    """Raised when configuration is invalid or cannot be loaded."""

    pass


class ConfigManager:
    """Manages configuration loading and validation."""

    DEFAULT_CONFIG_NAMES = [
        ".ai-analyzer.yaml",
        ".ai-analyzer.yml",
        "ai-analyzer.yaml",
        "ai-analyzer.yml",
        "pyproject.toml",  # Will look for [tool.ai-analyzer] section
    ]

    GLOBAL_CONFIG_PATHS = [
        Path.home() / ".config" / "ai-analyzer" / "config.yaml",
        Path.home() / ".ai-analyzer" / "config.yaml",
        Path.home() / ".ai-analyzer.yaml",
    ]

    def __init__(self) -> None:
        """Initialize configuration manager."""
        self._cache: dict[str, AnalysisConfig] = {}

    def load_config(
        self,
        config_path: Path | None = None,
        project_path: Path | None = None,
        **overrides: Any,
    ) -> AnalysisConfig:
        """Load configuration from multiple sources.

        Configuration hierarchy (highest to lowest priority):
        1. Explicit overrides passed as parameters
        2. Environment variables (AI_ANALYZER_*)
        3. Explicit config file (if config_path provided)
        4. Project-specific config file
        5. User global config file
        6. Default values

        Args:
            config_path: Explicit path to config file
            project_path: Project directory to search for config
            **overrides: Direct configuration overrides

        Returns:
            Validated configuration object

        Raises:
            ConfigurationError: If configuration is invalid or files are missing
            FileNotFoundError: If explicit config_path doesn't exist
        """
        # Convert lists to tuples for hashing
        hashable_overrides = {
            k: tuple(v) if isinstance(v, list) else v for k, v in overrides.items()
        }
        cache_key = f"{config_path}:{project_path}:{hash(frozenset(hashable_overrides.items()))}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        # Start with empty config data
        config_data: dict[str, Any] = {}

        # 1. Load global config
        global_config = self._load_global_config()
        if global_config:
            config_data.update(global_config)

        # 2. Load project config
        if project_path:
            project_config = self._load_project_config(project_path)
            if project_config:
                config_data.update(project_config)

        # 3. Load explicit config file
        if config_path:
            if not config_path.exists():
                raise FileNotFoundError(f"Config file not found: {config_path}")
            explicit_config = self._load_yaml_config(config_path)
            if explicit_config:
                config_data.update(explicit_config)

        # 4. Apply overrides
        config_data.update(overrides)

        # 5. Set project_path if not already set
        if project_path and "project_path" not in config_data:
            config_data["project_path"] = project_path

        # Create and validate configuration
        try:
            config = AnalysisConfig(**config_data)
            self._cache[cache_key] = config
            return config
        except ValidationError as e:
            raise ConfigurationError(f"Invalid configuration: {e}") from e

    def _load_global_config(self) -> dict[str, Any] | None:
        """Load global user configuration."""
        for config_path in self.GLOBAL_CONFIG_PATHS:
            if config_path.exists():
                return self._load_yaml_config(config_path)
        return None

    def _load_project_config(self, project_path: Path) -> dict[str, Any] | None:
        """Load project-specific configuration."""
        for config_name in self.DEFAULT_CONFIG_NAMES:
            config_path = project_path / config_name
            if config_path.exists():
                if config_name == "pyproject.toml":
                    return self._load_toml_config(config_path)
                else:
                    return self._load_yaml_config(config_path)
        return None

    def _load_yaml_config(self, config_path: Path) -> dict[str, Any] | None:
        """Load YAML configuration file."""
        try:
            with config_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else None
        except (yaml.YAMLError, OSError) as e:
            raise ConfigurationError(f"Failed to load YAML config {config_path}: {e}") from e

    def _load_toml_config(self, config_path: Path) -> dict[str, Any] | None:
        """Load TOML configuration from pyproject.toml."""
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib  # fallback for Python < 3.11
            except ImportError:
                return None

        try:
            with config_path.open("rb") as f:
                data = tomllib.load(f)
                # Look for [tool.ai-analyzer] section
                return data.get("tool", {}).get("ai-analyzer")
        except (OSError, tomllib.TOMLDecodeError) as e:
            raise ConfigurationError(f"Failed to load TOML config {config_path}: {e}") from e

    def save_config(self, config: AnalysisConfig, config_path: Path) -> None:
        """Save configuration to YAML file.

        Args:
            config: Configuration to save
            config_path: Path where to save the config
        """
        # Convert config to dict, excluding computed fields
        config_dict = config.model_dump(
            exclude_unset=True,
            exclude_none=True,
            exclude={"session_dir"},  # Don't save computed paths
        )

        # Convert Path objects to strings for YAML serialization
        config_dict = self._serialize_paths(config_dict)

        # Ensure parent directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with config_path.open("w", encoding="utf-8") as f:
                yaml.dump(
                    config_dict,
                    f,
                    default_flow_style=False,
                    indent=2,
                    sort_keys=True,
                )
        except (yaml.YAMLError, OSError) as e:
            raise ConfigurationError(f"Failed to save config to {config_path}: {e}") from e

    def _serialize_paths(self, data: Any) -> Any:
        """Convert Path objects to strings for serialization."""
        if isinstance(data, Path):
            return str(data)
        elif isinstance(data, dict):
            return {k: self._serialize_paths(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_paths(item) for item in data]
        else:
            return data

    def create_default_config(self, project_path: Path) -> AnalysisConfig:
        """Create default configuration for a project.

        Args:
            project_path: Path to the project

        Returns:
            Default configuration for the project
        """
        return AnalysisConfig(project_path=project_path)

    def get_config_template(self, template_type: str = "standard") -> dict[str, Any]:
        """Get configuration template.

        Args:
            template_type: Type of template ("minimal", "standard", "advanced")

        Returns:
            Configuration template dictionary
        """
        templates = {
            "minimal": {
                "llm_provider": "claude",
                "analysis_depth": 2,
                "output_format": "console",
            },
            "standard": {
                "llm_provider": "claude",
                "llm_providers": ["claude", "openai"],
                "analysis_depth": 3,
                "focus_areas": ["documentation", "code_quality", "security"],
                "output_format": "console",
                "max_tokens": 4000,
                "timeout_seconds": 300,
                "include_tests": True,
                "verbose": False,
            },
            "advanced": {
                "llm_provider": "claude",
                "llm_providers": ["claude", "openai", "local"],
                "analysis_depth": 4,
                "focus_areas": [
                    "documentation",
                    "code_quality",
                    "security",
                    "performance",
                    "architecture",
                ],
                "output_format": "markdown",
                "max_tokens": 8000,
                "temperature": 0.1,
                "timeout_seconds": 600,
                "retry_attempts": 3,
                "include_tests": True,
                "max_file_size_mb": 20,
                "max_files": 2000,
                "verbose": True,
                "save_sessions": True,
                "auto_resume": True,
            },
        }

        return templates.get(template_type, templates["standard"])

    def validate_config(self, config_data: dict[str, Any]) -> list[str]:
        """Validate configuration data and return any errors.

        Args:
            config_data: Configuration data to validate

        Returns:
            List of validation error messages
        """
        try:
            AnalysisConfig(**config_data)
            return []
        except ValidationError as e:
            return [str(error) for error in e.errors()]

    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._cache.clear()


# Global configuration manager instance
config_manager = ConfigManager()


def load_config(
    config_path: Path | None = None,
    project_path: Path | None = None,
    **overrides: Any,
) -> AnalysisConfig:
    """Convenience function to load configuration.

    Args:
        config_path: Optional explicit config file path
        project_path: Optional project directory path
        **overrides: Configuration overrides

    Returns:
        Loaded and validated configuration
    """
    return config_manager.load_config(
        config_path=config_path,
        project_path=project_path,
        **overrides,
    )


def create_config_file(
    output_path: Path,
    template_type: str = "standard",
    **overrides: Any,
) -> None:
    """Create a configuration file from template.

    Args:
        output_path: Where to save the config file
        template_type: Template to use ("minimal", "standard", "advanced")
        **overrides: Additional configuration values
    """
    template = config_manager.get_config_template(template_type)
    template.update(overrides)

    # Create a config object to validate the template
    config = AnalysisConfig(**template)

    # Save the configuration
    config_manager.save_config(config, output_path)
