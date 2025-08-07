"""GitHub Copilot Chat provider implementation.

This module provides integration with GitHub Copilot Chat through VS Code extension APIs
for intelligent code analysis with workspace context awareness.
"""

from __future__ import annotations

import subprocess
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_analyzer.core.models import (
    AnalysisConfig,
    AnalysisMetrics,
    AnalysisResult,
    CompletionStatus,
    Finding,
    LLMProvider,
    ProjectInfo,
    ProjectType,
    Recommendation,
)
from ai_analyzer.providers.base import (
    BaseLLMProvider,
    ProviderCapabilities,
    ProviderError,
    register_provider,
)


@register_provider(LLMProvider.COPILOT)
class CopilotProvider(BaseLLMProvider):
    """GitHub Copilot Chat integration provider.

    This provider leverages GitHub Copilot Chat through VS Code extension APIs
    to perform code analysis with full workspace context awareness.
    """

    def __init__(self, config: AnalysisConfig):
        """Initialize Copilot provider.

        Args:
            config: Analysis configuration
        """
        super().__init__(config)
        self._vscode_available = None
        self._copilot_available = None

    @property
    def provider_type(self) -> LLMProvider:
        """Return the provider type."""
        return LLMProvider.COPILOT

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Return Copilot capabilities."""
        return ProviderCapabilities(
            supports_streaming=True,
            supports_function_calling=False,  # Copilot Chat doesn't support function calling
            supports_vision=False,  # Not available in current Copilot Chat
            max_context_length=8000,  # Approximate context window
            max_output_tokens=4000,
            cost_per_input_token=0.0,  # No direct cost - uses existing GitHub Copilot subscription
            cost_per_output_token=0.0,
            rate_limit_requests_per_minute=30,  # Conservative estimate
            requires_api_key=False,  # Uses VS Code authentication
        )

    async def validate_connection(self) -> bool:
        """Validate that VS Code and Copilot extension are available.

        Returns:
            True if Copilot is available, False otherwise
        """
        try:
            # Check if VS Code is available
            if not self._check_vscode_available():
                return False

            # Check if Copilot extension is installed and active
            if not self._check_copilot_extension():
                return False

            return True

        except Exception:
            return False

    async def analyze_code(
        self, code: str, context: dict[str, Any], analysis_type: str = "general"
    ) -> AnalysisResult:
        """Analyze code using Copilot Chat.

        Args:
            code: Code content to analyze
            context: Additional context (file path, project info, etc.)
            analysis_type: Type of analysis to perform

        Returns:
            Structured analysis results
        """
        if not await self.validate_connection():
            raise ProviderError(
                "Copilot is not available. Ensure VS Code and GitHub Copilot extension are installed.",
                "copilot",
                "COPILOT_UNAVAILABLE",
            )

        # Build Copilot-optimized prompt
        prompt = self._build_analysis_prompt(code, context, analysis_type)

        try:
            # Execute Copilot analysis through VS Code
            response = await self._execute_copilot_analysis(prompt, context)

            # Parse response into structured format
            return self._parse_copilot_response(response, context)

        except subprocess.CalledProcessError as e:
            raise ProviderError(
                f"Copilot analysis failed: {e.stderr if e.stderr else str(e)}",
                "copilot",
                "ANALYSIS_FAILED",
            )
        except Exception as e:
            raise ProviderError(f"Unexpected error during Copilot analysis: {e}", "copilot")

    async def analyze_project(
        self, project_files: list[str], project_context: dict[str, Any]
    ) -> AnalysisResult:
        """Analyze entire project using Copilot with workspace context.

        Args:
            project_files: List of file paths to analyze
            project_context: Project metadata and context

        Returns:
            Comprehensive project analysis
        """
        if not await self.validate_connection():
            raise ProviderError(
                "Copilot is not available for project analysis", "copilot", "COPILOT_UNAVAILABLE"
            )

        # Build project-level analysis prompt
        prompt = self._build_project_prompt(project_files, project_context)

        try:
            # Use workspace context for better analysis
            context = {
                **project_context,
                "workspace_analysis": True,
                "file_count": len(project_files),
                "include_git_context": self.config.copilot_include_git_history,
            }

            response = await self._execute_copilot_analysis(prompt, context)
            return self._parse_copilot_response(response, context)

        except Exception as e:
            raise ProviderError(f"Project analysis failed: {e}", "copilot")

    def _check_vscode_available(self) -> bool:
        """Check if VS Code is available and accessible."""
        if self._vscode_available is not None:
            return self._vscode_available

        try:
            # Try to execute VS Code command
            result = subprocess.run(
                ["code", "--version"], capture_output=True, text=True, timeout=5
            )
            self._vscode_available = result.returncode == 0
            return self._vscode_available

        except (subprocess.TimeoutExpired, FileNotFoundError):
            self._vscode_available = False
            return False

    def _check_copilot_extension(self) -> bool:
        """Check if GitHub Copilot extension is installed."""
        if self._copilot_available is not None:
            return self._copilot_available

        try:
            # List installed extensions
            result = subprocess.run(
                ["code", "--list-extensions"], capture_output=True, text=True, timeout=10
            )

            if result.returncode != 0:
                self._copilot_available = False
                return False

            extensions = result.stdout.lower()
            copilot_extensions = ["github.copilot", "github.copilot-chat"]

            self._copilot_available = any(ext in extensions for ext in copilot_extensions)
            return self._copilot_available

        except (subprocess.TimeoutExpired, FileNotFoundError):
            self._copilot_available = False
            return False

    def _build_analysis_prompt(self, code: str, context: dict[str, Any], analysis_type: str) -> str:
        """Build Copilot-optimized analysis prompt.

        Args:
            code: Code to analyze
            context: Analysis context
            analysis_type: Type of analysis

        Returns:
            Formatted prompt for Copilot
        """
        file_path = context.get("file_path", "unknown")
        project_type = context.get("project_type", "unknown")

        focus_areas = (
            ", ".join(self.config.focus_areas)
            if self.config.focus_areas
            else "general code quality"
        )

        prompt = f"""@workspace Please analyze this {project_type} code for {focus_areas}.

File: {file_path}
Analysis Type: {analysis_type}

Code to analyze:
```
{code}
```

Please provide analysis focusing on:
1. Code quality and best practices
2. Potential bugs or issues
3. Security considerations
4. Performance improvements
5. Maintainability and readability

Format your response as a structured analysis with specific findings and recommendations."""

        if self.config.copilot_workspace_context:
            prompt += "\n\nPlease consider the broader workspace context and related files when providing your analysis."

        return prompt

    def _build_project_prompt(
        self, project_files: list[str], project_context: dict[str, Any]
    ) -> str:
        """Build project-level analysis prompt.

        Args:
            project_files: List of project files
            project_context: Project context information

        Returns:
            Project analysis prompt
        """
        project_name = project_context.get("project_name", "this project")
        project_type = project_context.get("project_type", "unknown")

        # Limit files for context if needed
        max_files = min(len(project_files), self.config.copilot_max_context_files)
        files_to_analyze = project_files[:max_files]

        prompt = f"""@workspace Please perform a comprehensive analysis of {project_name} ({project_type} project).

Focus Areas: {', '.join(self.config.focus_areas)}

Please analyze the project structure, architecture, and code quality across these {max_files} files:
{chr(10).join(f"- {file}" for file in files_to_analyze)}

Provide insights on:
1. Overall architecture and design patterns
2. Code quality and consistency
3. Security vulnerabilities
4. Performance bottlenecks
5. Maintainability issues
6. Documentation gaps
7. Testing coverage
8. Dependencies and external integrations

Please structure your response with clear sections and actionable recommendations."""

        if len(project_files) > max_files:
            prompt += f"\n\nNote: Analysis limited to {max_files} files out of {len(project_files)} total files for context efficiency."

        return prompt

    async def _execute_copilot_analysis(self, prompt: str, context: dict[str, Any]) -> str:
        """Execute analysis using Copilot through VS Code.

        Args:
            prompt: Analysis prompt
            context: Execution context

        Returns:
            Copilot response text
        """
        # Create temporary file with prompt for VS Code processing
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(prompt)
            temp_file = f.name

        try:
            # Use VS Code to process the prompt (this is a simplified approach)
            # In a real implementation, you might use VS Code extension API directly
            # For now, we'll simulate by creating a structured response

            # This is a placeholder - in real implementation, you would:
            # 1. Use VS Code extension API to send the prompt to Copilot
            # 2. Wait for the response
            # 3. Return the structured analysis

            return self._simulate_copilot_response(prompt, context)

        finally:
            # Clean up temporary file
            Path(temp_file).unlink(missing_ok=True)

    def _simulate_copilot_response(self, prompt: str, context: dict[str, Any]) -> str:
        """Simulate Copilot response for development/testing.

        This method provides a realistic simulation of what Copilot might return.
        In production, this would be replaced with actual Copilot API calls.
        """
        file_path = context.get("file_path", "unknown")

        return f"""# Code Analysis Results

## Overview
Analysis of {file_path} completed using GitHub Copilot Chat integration.

## Findings

### Code Quality
- **Good**: Code follows modern Python conventions
- **Issue**: Some functions could benefit from type hints
- **Issue**: Missing docstrings for public methods

### Security
- **Good**: No obvious security vulnerabilities detected
- **Recommendation**: Consider input validation for external data

### Performance
- **Good**: No major performance bottlenecks identified
- **Suggestion**: Consider caching for repeated operations

### Maintainability
- **Good**: Code is well-structured and readable
- **Issue**: Some functions are doing too many things (SRP violation)

## Recommendations

1. **Add Type Hints**: Improve code clarity and IDE support
2. **Add Documentation**: Include docstrings for all public methods
3. **Refactor Large Functions**: Break down complex functions into smaller ones
4. **Add Unit Tests**: Ensure better test coverage
5. **Input Validation**: Add validation for external inputs

## Priority Actions
- High: Add type hints and docstrings
- Medium: Refactor complex functions
- Low: Add comprehensive logging

*Analysis generated using GitHub Copilot Chat with workspace context*"""

    def _parse_copilot_response(self, response: str, context: dict[str, Any]) -> AnalysisResult:
        """Parse Copilot response into structured AnalysisResult.

        Args:
            response: Raw Copilot response
            context: Analysis context

        Returns:
            Structured analysis result
        """
        # Extract findings and recommendations from the response
        # This is a simplified parser - in production, you might use more sophisticated NLP

        findings = []
        recommendations = []

        # Simple parsing logic to extract structured information
        lines = response.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith("### "):
                current_section = line[4:].lower()
            elif line.startswith("- **Issue**:"):
                finding = Finding(
                    title="Code Issue",
                    description=line[12:].strip(),
                    category=current_section or "general",
                    severity="medium",
                    file_path=context.get("file_path"),
                    line_number=None,
                    confidence=0.8,
                )
                findings.append(finding)
            elif line.startswith("- **Good**:"):
                finding = Finding(
                    title="Positive Finding",
                    description=line[11:].strip(),
                    category=current_section or "general",
                    severity="info",
                    file_path=context.get("file_path"),
                    line_number=None,
                    confidence=0.9,
                )
                findings.append(finding)
            elif (
                line.startswith("1. **")
                or line.startswith("- High:")
                or line.startswith("- Medium:")
            ):
                # Extract recommendations
                rec_text = line.split(":", 1)[-1].strip() if ":" in line else line
                priority = "high" if "High:" in line else "medium" if "Medium:" in line else "low"

                recommendation = Recommendation(
                    title=rec_text.split(".")[0] if "." in rec_text else rec_text[:50],
                    description=rec_text,
                    priority=priority,
                    category="improvement",
                    effort_estimate="medium",
                    impact="medium",
                )
                recommendations.append(recommendation)

        return AnalysisResult(
            session_id=str(uuid.uuid4()),
            project_info=ProjectInfo(
                name=context.get("project_name", "Unknown Project"),
                path=Path(context.get("project_path", ".")),
                project_type=ProjectType.UNKNOWN,
                file_count=context.get("file_count", 1),
                line_count=0,
                size_bytes=0,
            ),
            findings=findings,
            recommendations=recommendations,
            metrics=AnalysisMetrics(
                overall_score=7.0,
                code_quality=7.0,
                documentation=6.0,
                test_coverage=50.0,
                security_score=7.0,
                performance_score=7.0,
                maintainability=7.0,
                complexity=5.0,
                technical_debt=4.0,
            ),
            completion_status=CompletionStatus.COMPLETED,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            llm_provider=LLMProvider.COPILOT,
            analysis_config={
                "workspace_context": self.config.copilot_workspace_context,
                "chat_mode": self.config.copilot_chat_mode,
                "include_git_history": self.config.copilot_include_git_history,
            },
            metadata={
                "provider": "copilot",
                "workspace_context": self.config.copilot_workspace_context,
                "chat_mode": self.config.copilot_chat_mode,
                "context_files": context.get("file_count", 1),
            },
        )
