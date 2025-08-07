# 🚀 CLI Reference - AI Code Analyzer

Complete reference for all CLI commands, options, and usage patterns.

## 📋 Global Options

Available for all commands:

```bash
ai-analyze [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

### Global Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--version` | | Show version information | |
| `--config PATH` | `-c` | Configuration file path | Auto-detect |
| `--verbose` | `-v` | Increase verbosity (use -vv for debug) | 0 |
| `--help` | | Show help message | |

## 🔍 Commands Overview

| Command | Purpose | Status |
|---------|---------|--------|
| [`analyze`](#analyze) | Analyze a codebase | ✅ Available |
| [`init`](#init) | Initialize configuration | ✅ Available |
| [`resume`](#resume) | Resume paused analysis | ✅ Available |
| [`status`](#status) | Show analysis status | ✅ Available |

## 📊 `analyze` Command

Analyze a codebase for insights and recommendations.

### Usage

```bash
ai-analyze analyze [PROJECT_PATH] [OPTIONS]
```

### Arguments

| Argument | Description | Required | Default |
|----------|-------------|----------|---------|
| `PROJECT_PATH` | Path to project directory | No | Current directory |

### Options

#### LLM Provider Selection
```bash
--llm {claude,openai,copilot,local}     # Primary LLM provider
--providers LIST                        # Provider preference order
```

#### Analysis Control
```bash
--type {python,javascript,typescript,mixed}  # Force project type
--depth {quick,standard,deep,comprehensive}  # Analysis depth
--focus LIST                            # Focus areas (comma-separated)
--exclude LIST                          # Exclude analyzers (comma-separated)
```

#### Output Control
```bash
--output {console,json,yaml,markdown}   # Output format
--export PATH                           # Export results to file
--dry-run                              # Show analysis plan without execution
```

#### Session Management
```bash
--resume                               # Resume interrupted analysis
--session-id ID                        # Specific session to resume
```

### Examples

#### Basic Analysis
```bash
# Analyze current directory with GitHub Copilot
ai-analyze analyze --llm copilot

# Analyze specific project
ai-analyze analyze /path/to/project

# Quick analysis with focus areas
ai-analyze analyze --depth quick --focus "security,performance"
```

#### Advanced Analysis
```bash
# Deep analysis with multiple providers
ai-analyze analyze --depth deep --providers "claude,openai,copilot"

# Export results to file
ai-analyze analyze --export results.json --output json

# Exclude specific analyzers
ai-analyze analyze --exclude "style,documentation"
```

#### Development & Debugging
```bash
# Dry run to see analysis plan
ai-analyze analyze --dry-run --verbose

# Debug mode with comprehensive logging
ai-analyze analyze --debug --verbose --verbose
```

### Focus Areas

Available focus areas for `--focus` option:

| Focus Area | Description |
|------------|-------------|
| `architecture` | System design and structure |
| `code_quality` | Code maintainability and style |
| `security` | Security vulnerabilities and best practices |
| `performance` | Performance optimization opportunities |
| `documentation` | Documentation completeness and quality |
| `testing` | Test coverage and quality |
| `dependencies` | Dependency management and security |
| `complexity` | Code complexity analysis |

### Project Types

Available for `--type` option:

| Type | Description |
|------|-------------|
| `python` | Python projects |
| `javascript` | JavaScript/Node.js projects |
| `typescript` | TypeScript projects |
| `mixed` | Multi-language projects |
| `unknown` | Auto-detect project type |

## ⚙️ `init` Command

Initialize configuration file for the current project.

### Usage

```bash
ai-analyze init [OPTIONS]
```

### Options

```bash
--template {standard,minimal,comprehensive}  # Configuration template
--global                                    # Create global config
--force                                     # Overwrite existing config
```

### Examples

```bash
# Create standard project configuration
ai-analyze init

# Create minimal configuration
ai-analyze init --template minimal

# Create global user configuration
ai-analyze init --global
```

## 🔄 `resume` Command

Resume a paused analysis session.

### Usage

```bash
ai-analyze resume [SESSION_ID]
```

### Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `SESSION_ID` | Specific session to resume | No |

### Examples

```bash
# Resume last paused session
ai-analyze resume

# Resume specific session
ai-analyze resume abc123-def456-789
```

## 📈 `status` Command

Show status of current analysis sessions.

### Usage

```bash
ai-analyze status [OPTIONS]
```

### Options

```bash
--all                    # Show all sessions (including completed)
--session-id ID          # Show specific session details
--cleanup                # Clean up old sessions
```

### Examples

```bash
# Show active sessions
ai-analyze status

# Show all sessions
ai-analyze status --all

# Clean up old sessions
ai-analyze status --cleanup
```

## 🔧 Configuration Integration

All CLI options can be set in configuration files:

### YAML Configuration
```yaml
# .ai-analyzer.yaml
llm_provider: copilot
analysis_depth: standard
focus_areas:
  - code_quality
  - security
exclude_analyzers:
  - style
output_format: console
```

### Environment Variables
```bash
export AI_ANALYZER_LLM_PROVIDER=copilot
export AI_ANALYZER_ANALYSIS_DEPTH=deep
export AI_ANALYZER_FOCUS_AREAS=security,performance
```

### Priority Order
1. Command-line arguments (highest)
2. Environment variables
3. Project configuration (`.ai-analyzer.yaml`)
4. Global configuration (`~/.ai-analyzer/config.yaml`)
5. System defaults (lowest)

## 📝 Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | Analysis error |
| 4 | Provider error |
| 5 | Network error |

## 💡 Tips & Best Practices

### Performance Tips
- Use `--depth quick` for fast overviews
- Focus on specific areas with `--focus` for targeted analysis
- Use `--dry-run` to preview analysis scope

### Configuration Tips
- Create project-specific `.ai-analyzer.yaml` for consistent results
- Use global config for personal preferences
- Combine multiple providers for comprehensive analysis

### Debugging Tips
- Use `-v` or `-vv` for verbose output
- Use `--dry-run` to understand analysis plan
- Check `ai-analyze status` for session information

---

**Last Updated**: 2025-08-07  
**CLI Version**: 1.0.0-alpha
