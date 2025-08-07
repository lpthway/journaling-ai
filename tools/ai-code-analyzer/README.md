# 🤖 AI Code Analyzer

*An intelligent, modular code analysis framework powered by multiple LLMs with advanced quota management and resume capabilities.*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

🧠 **Multi-LLM Intelligence**
- Support for Claude, OpenAI GPT-4, and local LLMs
- Intelligent provider selection and automatic failover
- Advanced quota management with timezone-aware scheduling

🎯 **Smart Project Analysis**
- Automatic project type detection (Python, JavaScript, React, Flutter, etc.)
- Modular analyzer system with plugin architecture
- Configurable analysis depth and focus areas

⚡ **Resume & Recovery**
- Intelligent checkpoint system for long-running analyses
- Automatic resume capability when quota limits are reached
- Session state persistence across interruptions

🎨 **Beautiful Terminal UI**
- Rich progress indicators and status displays
- Interactive configuration setup
- Professional error messaging and help system

🔧 **Production Ready**
- Comprehensive error handling and fallback mechanisms
- Type-safe configuration with Pydantic
- Extensive testing with >90% coverage target
- Modern Python practices and async architecture

## 🚀 Quick Start

### Installation

```bash
# Clone and install
git clone <repo-url>
cd ai-code-analyzer
pip install -e .

# Or install from PyPI (when published)
pip install ai-code-analyzer
```

### Basic Usage

```bash
# Analyze current directory
ai-analyze

# Analyze specific project
ai-analyze /path/to/project --llm claude

# Resume interrupted analysis
ai-analyze --resume

# Check analysis status
ai-analyze --status

# Use custom configuration
ai-analyze --config my-config.yaml
```

### Configuration

Create a `config.yaml` file:

```yaml
# LLM Configuration
llm_providers:
  claude:
    enabled: true
    api_key: "${CLAUDE_API_KEY}"
    max_tokens: 4000
  openai:
    enabled: true
    api_key: "${OPENAI_API_KEY}"
    max_tokens: 3000

# Analysis Settings
analysis:
  depth: 3
  enable_deep_dive: true
  max_parallel_analyzers: 3

# Project Detection
project_types:
  - python_backend
  - javascript_frontend
  - react_frontend
```

## 📊 Analysis Types

### 📚 Documentation Analysis
- Documentation completeness and quality
- Architecture decision records
- API documentation validation
- User guide assessment

### 🏗️ Architecture Analysis
- Code organization and structure
- Design pattern implementation
- Dependency analysis
- Technical debt identification

### 🔍 Code Quality Analysis
- Code complexity and maintainability
- Best practices compliance
- Security vulnerability detection
- Performance bottleneck identification

### 🧪 Testing Analysis
- Test coverage assessment
- Test quality and effectiveness
- Missing test scenarios
- Testing best practices

### 📈 Performance Analysis
- Performance bottleneck detection
- Resource usage optimization
- Scalability assessment
- Optimization recommendations

## 🛠️ Development

### Prerequisites

- Python 3.11+
- Git
- LLM API keys (Claude, OpenAI, etc.)

### Development Setup

```bash
# Clone repository
git clone <repo-url>
cd ai-code-analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run type checking
mypy src/

# Format code
black .
isort .
```

### Project Structure

```
ai-code-analyzer/
├── src/ai_analyzer/          # Main source code
│   ├── cli/                  # Command-line interface
│   ├── engine/               # Analysis engine
│   ├── analyzers/            # Analysis modules
│   ├── llm/                  # LLM integrations
│   ├── config/               # Configuration system
│   └── session/              # Session management
├── tests/                    # Test suite
├── docs/                     # Documentation
├── config/                   # Configuration templates
└── examples/                 # Usage examples
```

### Adding New Analyzers

```python
from ai_analyzer.analyzers.base import BaseAnalyzer

class MyCustomAnalyzer(BaseAnalyzer):
    name = "Custom Analysis"
    supported_project_types = [ProjectType.PYTHON_BACKEND]
    
    async def analyze(self, context: AnalysisContext) -> AnalysisResult:
        # Your analysis logic here
        return AnalysisResult(...)
    
    async def can_resume(self, checkpoint: dict) -> bool:
        return True  # If resumable
```

### Adding New LLM Providers

```python
from ai_analyzer.llm.base import LLMProvider

class MyLLMProvider(LLMProvider):
    async def analyze(self, prompt: str, **kwargs) -> LLMResponse:
        # Your LLM integration logic
        return LLMResponse(...)
    
    async def check_quota(self) -> QuotaStatus:
        # Quota checking logic
        return QuotaStatus(...)
```

## 📖 Documentation

- [Architecture Overview](architecture.md)
- [Configuration Guide](docs/configuration.md)
- [API Reference](docs/api.md)
- [Contributing Guidelines](docs/contributing.md)
- [FAQ](docs/faq.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](docs/contributing.md) for details.

### Development Process

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**: Follow our coding standards
4. **Add tests**: Ensure >90% coverage
5. **Update documentation**: Keep docs current
6. **Submit a pull request**: We'll review and merge

### Coding Standards

- **Type Hints**: Required for all public APIs
- **Documentation**: Docstrings for all public functions
- **Testing**: Unit tests for all new features
- **Formatting**: Black + isort + ruff
- **Async First**: Use async/await for I/O operations

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by the original shell script from the AI Journaling Assistant project
- Built with amazing open-source tools: Click, Rich, Pydantic, and more
- Special thanks to the LLM providers making this analysis possible

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/ai-code-analyzer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/ai-code-analyzer/discussions)
- **Email**: support@ai-code-analyzer.dev

---

**Made with ❤️ by developers, for developers**

*Transform your codebase understanding with AI-powered insights*
