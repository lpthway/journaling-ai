# 📚 AI Code Analyzer Documentation

Welcome to the comprehensive documentation for the AI Code Analyzer - an intelligent code analysis framework using multiple LLM providers.

## 📖 Quick Navigation

### 👥 For Users
- **[Installation Guide](user-guide/installation.md)** - Get started quickly
- **[Quick Start](user-guide/quick-start.md)** - Your first analysis in 5 minutes
- **[Configuration](user-guide/configuration.md)** - Customize analysis behavior
- **[Usage Examples](user-guide/usage-examples.md)** - Real-world scenarios
- **[Troubleshooting](user-guide/troubleshooting.md)** - Common issues and solutions

### 🛠️ For Developers
- **[Contributing](developer-guide/contributing.md)** - How to contribute
- **[Development Setup](developer-guide/development-setup.md)** - Environment setup
- **[Testing Guidelines](developer-guide/testing.md)** - Testing strategy and tools
- **[Coding Standards](developer-guide/coding-standards.md)** - Code style and practices
- **[Release Process](developer-guide/release-process.md)** - How releases are made

### 🏗️ Architecture & Design
- **[Architecture Overview](architecture/overview.md)** - High-level system design
- **[Data Models](architecture/data-models.md)** - Core data structures
- **[Plugin System](architecture/plugin-system.md)** - Extensible analyzer architecture
- **[LLM Integration](architecture/llm-integration.md)** - Provider system design
- **[Session Management](architecture/session-management.md)** - Resume and state handling

### 🔧 API Reference
- **[CLI Reference](api/cli-reference.md)** - Complete command documentation
- **[Configuration Schema](api/configuration-schema.md)** - Config file reference
- **[Analyzer API](api/analyzer-api.md)** - Plugin development API
- **[LLM Provider API](api/llm-provider-api.md)** - Provider development API

### 📊 Project Management
- **[Roadmap](project-management/roadmap.md)** - Future features and timeline
- **[Changelog](project-management/changelog.md)** - Version history
- **[Known Issues](project-management/known-issues.md)** - Current limitations

## 🚀 Current Status

**Version**: 1.0.0-alpha (Phase 1 - Foundation)  
**Current Capabilities**:
- ✅ Modern Python CLI with Rich formatting
- ✅ GitHub Copilot integration via VS Code
- ✅ Flexible configuration system (YAML/TOML)
- ✅ Extensible provider architecture
- ✅ Type-safe data models with Pydantic v2

**Upcoming Features**:
- 🔄 Basic analyzer framework (Phase 1 completion)
- ⏳ Claude and OpenAI provider integration (Phase 2)
- ⏳ Advanced analysis features and web UI (Phase 3)

## 💡 Quick Examples

### Basic Analysis
```bash
# Analyze current directory
ai-analyze

# Analyze specific project
ai-analyze /path/to/project --llm copilot

# Force project type
ai-analyze --type python --focus security,performance
```

### Configuration
```yaml
# .ai-analyzer.yaml
llm_provider: copilot
analysis_depth: deep
focus_areas:
  - documentation
  - code_quality
  - security
```

## 🤝 Getting Help

- **Issues**: [GitHub Issues](https://github.com/lpthway/journaling-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/lpthway/journaling-ai/discussions)
- **Documentation**: This documentation site
- **CLI Help**: `ai-analyze --help`

---

**Last Updated**: 2025-08-07  
**Documentation Version**: 1.0.0
