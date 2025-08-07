# 📦 Installation Guide

Get the AI Code Analyzer up and running in minutes.

## 🎯 Quick Install

### Prerequisites

- **Python 3.11+** (required for modern type hints and performance)
- **Git** (for development installation)
- **VS Code** (optional, for GitHub Copilot integration)

### Install from Source (Development)

```bash
# Clone the repository
git clone https://github.com/lpthway/journaling-ai.git
cd journaling-ai/tools/ai-code-analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install in development mode
pip install -e .

# Verify installation
ai-analyze --version
```

## 🔧 Detailed Installation

### 1. System Requirements

#### Python Version
```bash
# Check Python version
python --version  # Should be 3.11 or higher

# If you need to install Python 3.11+
# Ubuntu/Debian:
sudo apt update && sudo apt install python3.11 python3.11-venv

# macOS (with Homebrew):
brew install python@3.11

# Windows: Download from python.org
```

#### Optional Dependencies
```bash
# For GitHub Copilot integration
# Install VS Code and Copilot extension

# For development
git --version  # Required for cloning repository
```

### 2. Virtual Environment Setup

**Recommended**: Always use a virtual environment to avoid dependency conflicts.

```bash
# Create virtual environment
python -m venv ai-analyzer-env

# Activate virtual environment
source ai-analyzer-env/bin/activate  # Linux/Mac
# or: ai-analyzer-env\Scripts\activate  # Windows

# Verify virtual environment
which python  # Should point to venv
pip list       # Should show minimal packages
```

### 3. Installation Options

#### Option A: Development Installation (Recommended)
```bash
# Clone repository
git clone https://github.com/lpthway/journaling-ai.git
cd journaling-ai/tools/ai-code-analyzer

# Install with development dependencies
pip install -e ".[dev,test,docs]"

# Install pre-commit hooks (optional)
pre-commit install
```

#### Option B: PyPI Installation (Future)
```bash
# This will be available when published to PyPI
pip install ai-code-analyzer
```

### 4. Verify Installation

```bash
# Check CLI is available
ai-analyze --version

# Test basic functionality
ai-analyze --help

# Test with dry run
ai-analyze analyze --dry-run
```

Expected output:
```
AI Code Analyzer v1.0.0-alpha
✅ CLI working correctly
✅ Configuration system ready
✅ Providers available: copilot
```

## 🎭 Provider Setup

### GitHub Copilot (Recommended)

1. **Install VS Code**
   ```bash
   # Download from: https://code.visualstudio.com/
   ```

2. **Install Copilot Extension**
   - Open VS Code
   - Go to Extensions (Ctrl+Shift+X)
   - Search for "GitHub Copilot"
   - Install and sign in with GitHub account

3. **Verify Integration**
   ```bash
   # Test Copilot provider
   ai-analyze analyze --llm copilot --dry-run
   ```

### Claude API (Future - Phase 2)
```bash
# Set API key
export ANTHROPIC_API_KEY=your-key-here

# Test Claude provider
ai-analyze analyze --llm claude --dry-run
```

### OpenAI API (Future - Phase 2)
```bash
# Set API key
export OPENAI_API_KEY=your-key-here

# Test OpenAI provider
ai-analyze analyze --llm openai --dry-run
```

## 📁 Directory Structure

After installation, you'll have:

```
ai-analyzer-env/  (your virtual environment)
journaling-ai/
└── tools/
    └── ai-code-analyzer/
        ├── src/ai_analyzer/     # Main package
        ├── tests/               # Test suite
        ├── docs/                # Documentation
        ├── planning/            # Development plans
        ├── pyproject.toml       # Project configuration
        └── README.md            # Project overview
```

## 🔧 Configuration

### Create Initial Configuration

```bash
# Create project configuration
cd your-project-directory
ai-analyze init

# This creates .ai-analyzer.yaml with defaults:
```

```yaml
# .ai-analyzer.yaml
llm_provider: copilot
analysis_depth: standard
focus_areas:
  - documentation
  - code_quality
  - security
output_format: console
```

### Global Configuration (Optional)

```bash
# Create global configuration
ai-analyze init --global

# Located at: ~/.ai-analyzer/config.yaml
```

## 🧪 Test Your Installation

### Basic Test
```bash
# Navigate to any code project
cd /path/to/your/project

# Run quick analysis
ai-analyze analyze --depth quick --dry-run
```

### Full Test Suite (Development)
```bash
# Run project tests
cd journaling-ai/tools/ai-code-analyzer
python -m pytest tests/ -v

# Run with coverage
python -m pytest --cov=src --cov-report=term-missing
```

## 🚨 Troubleshooting

### Common Issues

#### "ai-analyze: command not found"
```bash
# Check if virtual environment is activated
which python  # Should point to venv

# Reinstall package
pip install -e .

# Check PATH
echo $PATH  # Should include venv/bin
```

#### "No module named 'ai_analyzer'"
```bash
# Reinstall in development mode
pip uninstall ai-code-analyzer
pip install -e .
```

#### Copilot Integration Issues
```bash
# Check VS Code is installed
code --version

# Check Copilot extension
# VS Code → Extensions → Search "GitHub Copilot"

# Test connection
ai-analyze analyze --llm copilot --verbose
```

#### Permission Errors
```bash
# Use virtual environment
python -m venv venv
source venv/bin/activate
pip install -e .
```

### Getting Help

1. **Check documentation**: `ai-analyze --help`
2. **Verbose output**: `ai-analyze --verbose`
3. **GitHub Issues**: [Create an issue](https://github.com/lpthway/journaling-ai/issues)
4. **Discussions**: [GitHub Discussions](https://github.com/lpthway/journaling-ai/discussions)

## 🔄 Updating

### Development Version
```bash
cd journaling-ai/tools/ai-code-analyzer
git pull origin main
pip install -e .
```

### PyPI Version (Future)
```bash
pip install --upgrade ai-code-analyzer
```

## 🗑️ Uninstallation

```bash
# Uninstall package
pip uninstall ai-code-analyzer

# Remove configuration (optional)
rm -rf ~/.ai-analyzer/

# Remove virtual environment
deactivate
rm -rf ai-analyzer-env/
```

---

**Installation Support**: If you encounter issues, please [create an issue](https://github.com/lpthway/journaling-ai/issues) with your system details and error messages.
