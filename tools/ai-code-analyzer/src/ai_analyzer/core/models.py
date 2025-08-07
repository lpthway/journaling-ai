"""Core data models for the AI Code Analyzer.

This module contains Pydantic models for configuration, analysis results,
project information, and session state management.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class ProjectType(str, Enum):
    """Supported project types for analysis."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    REACT = "react"
    VUE = "vue"
    ANGULAR = "angular"
    FASTAPI = "fastapi"
    DJANGO = "django"
    FLASK = "flask"
    NODEJS = "nodejs"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    CLAUDE = "claude"
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    COPILOT = "copilot"  # GitHub Copilot Chat integration
    LOCAL = "local"
    OLLAMA = "ollama"
    CUSTOM = "custom"


class AnalysisDepth(int, Enum):
    """Analysis depth levels."""

    OVERVIEW = 1  # Quick overview, basic insights
    STANDARD = 2  # Standard analysis with key findings
    DETAILED = 3  # Detailed analysis with recommendations
    COMPREHENSIVE = 4  # Comprehensive deep-dive analysis
    EXHAUSTIVE = 5  # Exhaustive analysis with all features


class OutputFormat(str, Enum):
    """Output format options."""

    CONSOLE = "console"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    PDF = "pdf"


class CompletionStatus(str, Enum):
    """Analysis completion status."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProjectInfo(BaseModel):
    """Information about the analyzed project."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    name: str = Field(..., description="Project name")
    path: Path = Field(..., description="Absolute path to project root")
    project_type: ProjectType = Field(..., description="Detected project type")
    languages: list[str] = Field(default_factory=list, description="Programming languages detected")
    frameworks: list[str] = Field(default_factory=list, description="Frameworks detected")
    file_count: int = Field(ge=0, description="Total number of files")
    line_count: int = Field(ge=0, description="Total lines of code")
    size_bytes: int = Field(ge=0, description="Total size in bytes")
    git_repository: bool = Field(default=False, description="Whether project is a Git repository")
    has_tests: bool = Field(default=False, description="Whether project has test files")
    has_docs: bool = Field(default=False, description="Whether project has documentation")

    @field_validator("path")
    @classmethod
    def validate_path_exists(cls, v: Path) -> Path:
        """Validate that the project path exists."""
        if not v.exists():
            raise ValueError(f"Project path does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Project path is not a directory: {v}")
        return v.resolve()


class Finding(BaseModel):
    """A single analysis finding or insight."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique finding ID")
    title: str = Field(..., min_length=1, description="Finding title")
    description: str = Field(..., min_length=1, description="Detailed description")
    category: str = Field(..., description="Finding category (e.g., 'security', 'performance')")
    severity: str = Field(..., description="Severity level (e.g., 'high', 'medium', 'low')")
    file_path: Path | None = Field(None, description="Related file path")
    line_number: int | None = Field(None, ge=1, description="Related line number")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")
    recommendations: list[str] = Field(default_factory=list, description="Recommended actions")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AnalysisMetrics(BaseModel):
    """Analysis metrics and scores."""

    model_config = ConfigDict(extra="forbid")

    overall_score: float = Field(ge=0.0, le=10.0, description="Overall project score (0-10)")
    code_quality: float = Field(ge=0.0, le=10.0, description="Code quality score")
    documentation: float = Field(ge=0.0, le=10.0, description="Documentation score")
    test_coverage: float = Field(ge=0.0, le=100.0, description="Test coverage percentage")
    security_score: float = Field(ge=0.0, le=10.0, description="Security score")
    performance_score: float = Field(ge=0.0, le=10.0, description="Performance score")
    maintainability: float = Field(ge=0.0, le=10.0, description="Maintainability score")
    complexity: float = Field(ge=0.0, description="Complexity metric")
    technical_debt: float = Field(ge=0.0, description="Technical debt score")


class Recommendation(BaseModel):
    """A recommendation for improving the project."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique recommendation ID"
    )
    title: str = Field(..., min_length=1, description="Recommendation title")
    description: str = Field(..., min_length=1, description="Detailed description")
    priority: str = Field(..., description="Priority level (e.g., 'high', 'medium', 'low')")
    category: str = Field(
        ..., description="Category (e.g., 'refactoring', 'testing', 'documentation')"
    )
    effort_estimate: str = Field(
        ..., description="Effort estimate (e.g., 'small', 'medium', 'large')"
    )
    impact: str = Field(..., description="Expected impact (e.g., 'high', 'medium', 'low')")
    steps: list[str] = Field(default_factory=list, description="Implementation steps")
    related_findings: list[str] = Field(default_factory=list, description="Related finding IDs")


class SessionState(BaseModel):
    """Analysis session state for resume capability."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique session ID"
    )
    project_path: Path = Field(..., description="Project being analyzed")
    started_at: datetime = Field(default_factory=datetime.now, description="Session start time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")
    status: CompletionStatus = Field(
        default=CompletionStatus.NOT_STARTED, description="Current status"
    )
    progress_percentage: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Progress percentage"
    )
    current_step: str = Field(default="", description="Current analysis step")
    completed_steps: list[str] = Field(default_factory=list, description="Completed steps")
    resume_data: dict[str, Any] = Field(
        default_factory=dict, description="Data needed for resuming"
    )
    llm_usage: dict[str, Any] = Field(default_factory=dict, description="LLM usage statistics")

    def mark_completed(self, step: str) -> None:
        """Mark a step as completed."""
        if step not in self.completed_steps:
            self.completed_steps.append(step)
        self.updated_at = datetime.now()

    def update_progress(self, percentage: float, current_step: str = "") -> None:
        """Update session progress."""
        self.progress_percentage = max(0.0, min(100.0, percentage))
        if current_step:
            self.current_step = current_step
        self.updated_at = datetime.now()


class AnalysisResult(BaseModel):
    """Complete analysis result."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(..., description="Analysis session ID")
    project_info: ProjectInfo = Field(..., description="Project information")
    findings: list[Finding] = Field(default_factory=list, description="Analysis findings")
    recommendations: list[Recommendation] = Field(
        default_factory=list, description="Recommendations"
    )
    metrics: AnalysisMetrics = Field(..., description="Analysis metrics")
    completion_status: CompletionStatus = Field(..., description="Analysis completion status")
    started_at: datetime = Field(..., description="Analysis start time")
    completed_at: datetime | None = Field(None, description="Analysis completion time")
    llm_provider: LLMProvider = Field(..., description="LLM provider used")
    analysis_config: dict[str, Any] = Field(
        default_factory=dict, description="Analysis configuration"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @property
    def duration(self) -> float | None:
        """Calculate analysis duration in seconds."""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_complete(self) -> bool:
        """Check if analysis is complete."""
        return self.completion_status == CompletionStatus.COMPLETED


class AnalysisConfig(BaseSettings):
    """Configuration for analysis execution."""

    model_config = ConfigDict(
        env_prefix="AI_ANALYZER_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
    )

    # Project settings
    project_path: Path | None = Field(None, description="Path to project to analyze")
    project_types: list[ProjectType] = Field(
        default_factory=list, description="Forced project types"
    )
    exclude_patterns: list[str] = Field(
        default_factory=lambda: [
            "*.pyc",
            "__pycache__",
            ".git",
            ".svn",
            ".hg",
            "node_modules",
            ".venv",
            "venv",
            "env",
            "*.log",
            "*.tmp",
            ".DS_Store",
        ],
        description="File patterns to exclude from analysis",
    )

    # LLM settings
    llm_provider: LLMProvider = Field(
        default=LLMProvider.CLAUDE, description="Primary LLM provider"
    )
    llm_providers: list[LLMProvider] = Field(
        default_factory=lambda: [LLMProvider.CLAUDE], description="LLM provider preference order"
    )
    max_tokens: int = Field(
        default=4000, ge=100, le=100000, description="Maximum tokens per request"
    )
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="LLM temperature")
    timeout_seconds: int = Field(default=300, ge=10, le=3600, description="Request timeout")
    retry_attempts: int = Field(default=3, ge=1, le=10, description="Maximum retry attempts")

    # Copilot-specific settings
    copilot_workspace_context: bool = Field(
        default=True, description="Use VS Code workspace context for Copilot analysis"
    )
    copilot_chat_mode: str = Field(
        default="focused",
        description="Copilot chat mode: 'focused', 'comprehensive', or 'interactive'",
    )
    copilot_include_git_history: bool = Field(
        default=True, description="Include git history in Copilot context"
    )
    copilot_max_context_files: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of files to include in Copilot context",
    )

    # Analysis settings
    analysis_depth: AnalysisDepth = Field(
        default=AnalysisDepth.STANDARD, description="Analysis depth"
    )
    focus_areas: list[str] = Field(
        default_factory=lambda: ["documentation", "code_quality", "security"],
        description="Analysis focus areas",
    )
    exclude_analyzers: list[str] = Field(default_factory=list, description="Analyzers to exclude")
    include_tests: bool = Field(default=True, description="Include test files in analysis")
    max_file_size_mb: int = Field(
        default=10, ge=1, le=100, description="Maximum file size to analyze"
    )
    max_files: int = Field(default=1000, ge=1, le=10000, description="Maximum number of files")

    # Output settings
    output_format: OutputFormat = Field(default=OutputFormat.CONSOLE, description="Output format")
    output_path: Path | None = Field(None, description="Output file path")
    verbose: bool = Field(default=False, description="Verbose output")
    debug: bool = Field(default=False, description="Debug mode")

    # Session settings
    save_sessions: bool = Field(default=True, description="Save analysis sessions")
    session_dir: Path = Field(default=Path(".ai-analyzer"), description="Session storage directory")
    auto_resume: bool = Field(default=True, description="Auto-resume interrupted sessions")

    @field_validator("project_path")
    @classmethod
    def validate_project_path(cls, v: Path | None) -> Path | None:
        """Validate project path if provided."""
        if v is not None:
            if not v.exists():
                raise ValueError(f"Project path does not exist: {v}")
            if not v.is_dir():
                raise ValueError(f"Project path is not a directory: {v}")
            return v.resolve()
        return v

    @field_validator("session_dir")
    @classmethod
    def validate_session_dir(cls, v: Path) -> Path:
        """Ensure session directory exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v.resolve()
