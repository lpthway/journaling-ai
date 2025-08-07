"""Main CLI interface for the AI Code Analyzer.

This module provides the command-line interface using Click with Rich formatting
for beautiful terminal output.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ai_analyzer import __version__
from ai_analyzer.core.config import create_config_file, load_config
from ai_analyzer.core.models import AnalysisDepth, LLMProvider, OutputFormat

# Initialize Rich console
console = Console()


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version information")
@click.option(
    "--config", "-c", type=click.Path(exists=True, path_type=Path), help="Configuration file path"
)
@click.option("--verbose", "-v", count=True, help="Increase verbosity (use -vv for debug)")
@click.pass_context
def cli(ctx: click.Context, version: bool, config: Path | None, verbose: int) -> None:
    """AI Code Analyzer - Intelligent code analysis with multiple LLM providers.

    Analyze any codebase with AI-powered insights, supporting multiple LLM providers
    with advanced quota management and resume capabilities.

    Examples:
        ai-analyze                          # Analyze current directory
        ai-analyze /path/to/project         # Analyze specific project
        ai-analyze --type python            # Force project type detection
        ai-analyze --llm claude             # Use specific LLM provider
        ai-analyze --config my-config.yaml  # Use custom configuration
    """
    # Ensure the context object exists
    ctx.ensure_object(dict)

    # Store common options in context
    ctx.obj["config_path"] = config
    ctx.obj["verbose"] = verbose

    if version:
        show_version()
        return

    # If no command specified, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path.cwd(),
)
@click.option("--type", "project_type", help="Force specific project type detection")
@click.option(
    "--llm",
    type=click.Choice([provider.value for provider in LLMProvider]),
    default="claude",
    help="LLM provider to use (claude, openai, copilot, azure_openai, local, ollama, custom)",
)
@click.option(
    "--depth",
    type=click.Choice([str(depth.value) for depth in AnalysisDepth]),
    default="2",
    help="Analysis depth (1=overview, 5=exhaustive)",
)
@click.option(
    "--focus", multiple=True, help="Focus areas for analysis (can be used multiple times)"
)
@click.option("--exclude", multiple=True, help="Analyzers to exclude (can be used multiple times)")
@click.option(
    "--output",
    type=click.Choice([fmt.value for fmt in OutputFormat]),
    default="console",
    help="Output format",
)
@click.option("--export", type=click.Path(path_type=Path), help="Export results to file")
@click.option("--resume", is_flag=True, help="Resume interrupted analysis")
@click.option("--dry-run", is_flag=True, help="Show what would be analyzed without running")
@click.pass_context
def analyze(
    ctx: click.Context,
    project_path: Path,
    project_type: str | None,
    llm: str,
    depth: str,
    focus: list[str],
    exclude: list[str],
    output: str,
    export: Path | None,
    resume: bool,
    dry_run: bool,
) -> None:
    """Analyze a codebase for insights and recommendations.

    This command analyzes the specified project directory using AI-powered
    analysis to provide insights, identify issues, and suggest improvements.

    PROJECT_PATH: Path to the project directory to analyze (default: current directory)

    Examples:
        ai-analyze                              # Analyze current directory
        ai-analyze /my/project                  # Analyze specific project
        ai-analyze --llm openai --depth 4      # Use OpenAI with detailed analysis
        ai-analyze --focus security testing    # Focus on security and testing
        ai-analyze --output markdown --export report.md  # Export markdown report
    """
    verbose = ctx.obj.get("verbose", 0)
    config_path = ctx.obj.get("config_path")

    try:
        # Load configuration
        config = load_config(
            config_path=config_path,
            project_path=project_path,
            llm_provider=llm,
            analysis_depth=int(depth),
            focus_areas=list(focus) if focus else [],
            exclude_analyzers=list(exclude) if exclude else [],
            output_format=output,
            output_path=export,
            verbose=verbose > 0,
            debug=verbose > 1,
        )

        if dry_run:
            show_analysis_plan(config)
            return

        if resume:
            console.print("[yellow]Resume functionality not yet implemented[/yellow]")
            return

        # Show analysis start
        show_analysis_start(config)

        # TODO: Implement actual analysis
        console.print("[red]Analysis engine not yet implemented[/red]")
        console.print("[yellow]This is Phase 1 - implementing CLI framework first[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose > 1:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option(
    "--template",
    type=click.Choice(["minimal", "standard", "advanced"]),
    default="standard",
    help="Configuration template to use",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=Path(".ai-analyzer.yaml"),
    help="Output file path",
)
@click.option("--force", is_flag=True, help="Overwrite existing config file")
def init(template: str, output: Path, force: bool) -> None:
    """Initialize configuration file for the current project.

    Creates a configuration file with sensible defaults that can be
    customized for your specific project needs.

    Examples:
        ai-analyze init                          # Create standard config
        ai-analyze init --template minimal      # Create minimal config
        ai-analyze init --template advanced     # Create advanced config
        ai-analyze init -o custom-config.yaml   # Custom output file
    """
    if output.exists() and not force:
        console.print(f"[red]Config file already exists: {output}[/red]")
        console.print("Use --force to overwrite")
        sys.exit(1)

    try:
        create_config_file(output, template)
        console.print(f"[green]Created configuration file: {output}[/green]")
        console.print(f"Template: {template}")
        console.print("\nEdit the file to customize your analysis settings.")
    except Exception as e:
        console.print(f"[red]Error creating config: {e}[/red]")
        sys.exit(1)


@cli.command()
def status() -> None:
    """Show status of current analysis sessions.

    Displays information about any running or paused analysis sessions,
    including progress and resume options.
    """
    # TODO: Implement session status checking
    console.print("[yellow]Session status not yet implemented[/yellow]")
    console.print("This will show running/paused analysis sessions")


@cli.command()
@click.argument("session_id", required=False)
def resume(session_id: str | None) -> None:
    """Resume a paused analysis session.

    SESSION_ID: Specific session to resume (optional, will prompt if not provided)

    Examples:
        ai-analyze resume                    # Show available sessions to resume
        ai-analyze resume abc123             # Resume specific session
    """
    # TODO: Implement session resume
    console.print("[yellow]Session resume not yet implemented[/yellow]")
    if session_id:
        console.print(f"Would resume session: {session_id}")
    else:
        console.print("Would show available sessions to resume")


def show_version() -> None:
    """Display version information with Rich formatting."""
    title = Text("AI Code Analyzer", style="bold blue")
    version_text = Text(f"Version: {__version__}", style="green")

    table = Table.grid(padding=1)
    table.add_column(style="bold")
    table.add_column()

    table.add_row("🤖", title)
    table.add_row("📊", version_text)
    table.add_row("🔗", Text("https://github.com/ai-code-analyzer/ai-code-analyzer"))
    table.add_row("📚", Text("Intelligent code analysis with multiple LLM providers"))

    panel = Panel(table, title="[bold]About[/bold]", border_style="blue")
    console.print(panel)


def show_analysis_plan(config) -> None:
    """Show what would be analyzed in dry-run mode."""
    console.print("\n[bold blue]📋 Analysis Plan[/bold blue]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Project Path", str(config.project_path))
    table.add_row("LLM Provider", config.llm_provider.value)
    table.add_row("Analysis Depth", str(config.analysis_depth.value))
    table.add_row("Focus Areas", ", ".join(config.focus_areas))
    table.add_row("Output Format", config.output_format.value)

    if config.exclude_analyzers:
        table.add_row("Excluded Analyzers", ", ".join(config.exclude_analyzers))

    console.print(table)
    console.print("\n[yellow]This is a dry run - no actual analysis would be performed[/yellow]")


def show_analysis_start(config) -> None:
    """Show analysis start information."""
    console.print("\n[bold green]🚀 Starting Analysis[/bold green]")

    # Project info panel
    project_info = f"""
[bold]Project:[/bold] {config.project_path.name}
[bold]Path:[/bold] {config.project_path}
[bold]LLM Provider:[/bold] {config.llm_provider.value}
[bold]Analysis Depth:[/bold] {config.analysis_depth.value}/5
"""

    panel = Panel(
        project_info.strip(), title="[bold]Analysis Configuration[/bold]", border_style="green"
    )
    console.print(panel)


if __name__ == "__main__":
    cli()
