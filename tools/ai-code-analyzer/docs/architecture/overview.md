# 🏗️ Architecture Overview

Comprehensive overview of the AI Code Analyzer system architecture, design principles, and component interactions.

## 📋 System Architecture

The AI Code Analyzer follows a modular, layered architecture designed for extensibility, maintainability, and scalability.

```
┌─────────────────────────────────────────────────────────┐
│                   Interface Layer                        │
├─────────────────────────────────────────────────────────┤
│  CLI Commands    │  Configuration  │  Output Formats    │
│  Rich UI         │  Validation     │  Error Messages    │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                 Application Layer                        │
├─────────────────────────────────────────────────────────┤
│  Analysis        │  Session        │  Plugin Discovery  │
│  Orchestration   │  Management     │  Result Processing │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                   Domain Layer                          │
├─────────────────────────────────────────────────────────┤
│  Project Type    │  Analysis       │  Configuration     │
│  Detection       │  Data Models    │  Schemas           │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                Infrastructure Layer                      │
├─────────────────────────────────────────────────────────┤
│  LLM Providers   │  File System    │  Network          │
│  Integrations    │  Operations     │  Communications    │
└─────────────────────────────────────────────────────────┘
```

## 🏗️ Layer Responsibilities

### 1. Interface Layer
**Purpose**: User interaction and external interfaces

**Components**:
- **CLI Framework** (`src/ai_analyzer/cli/`): Click-based command interface with Rich formatting
- **Configuration Interface** (`src/ai_analyzer/core/config.py`): YAML/TOML configuration loading
- **Output Formatters**: Console, JSON, YAML, Markdown output formats
- **Error Handling**: User-friendly error messages and help systems

**Key Features**:
- Beautiful terminal UI with Rich formatting
- Comprehensive help system with examples
- Multiple output formats for different use cases
- Graceful error handling with actionable messages

### 2. Application Layer
**Purpose**: Business logic orchestration and workflow management

**Components**:
- **Analysis Orchestrator**: Coordinates analysis across multiple providers
- **Session Manager**: Handles analysis state, resume capabilities, and progress tracking
- **Plugin Registry**: Discovers and manages analyzer plugins
- **Result Aggregator**: Combines and processes analysis results from multiple sources

**Key Features**:
- Intelligent provider selection and failover
- Resume capability for long-running analyses
- Plugin-based architecture for extensibility
- Comprehensive result aggregation and deduplication

### 3. Domain Layer
**Purpose**: Core business concepts and data models

**Components**:
- **Data Models** (`src/ai_analyzer/core/models.py`): Pydantic models for all system entities
- **Project Detection**: Algorithms for detecting project types and characteristics
- **Analysis Configuration**: Schema and validation for analysis parameters
- **Session State**: Models for tracking analysis progress and state

**Key Data Models**:
```python
# Core domain models
class ProjectInfo(BaseModel):
    path: Path
    project_type: ProjectType
    languages: list[str]
    frameworks: list[str]

class AnalysisResult(BaseModel):
    session_id: str
    project_info: ProjectInfo
    findings: list[Finding]
    recommendations: list[Recommendation]
    completion_status: CompletionStatus

class Finding(BaseModel):
    id: str
    title: str
    description: str
    category: str
    severity: str
    confidence: float
```

### 4. Infrastructure Layer
**Purpose**: External integrations and low-level operations

**Components**:
- **LLM Providers** (`src/ai_analyzer/providers/`): Integrations with Claude, OpenAI, Copilot
- **File System Operations**: Async file reading, project scanning, output generation
- **Network Communications**: HTTP clients for API calls, error handling, retry logic
- **Logging and Monitoring**: Structured logging, performance metrics, diagnostics

**Provider Architecture**:
```python
class BaseLLMProvider(ABC):
    @abstractmethod
    async def analyze_code(self, code: str, context: dict[str, Any]) -> AnalysisResult:
        """Analyze code and return structured results."""

    @abstractmethod
    async def analyze_project(self, project_files: list[str], context: dict[str, Any]) -> AnalysisResult:
        """Analyze entire project."""
```

## 🔄 Data Flow

### Analysis Request Flow

```
1. CLI Input
   ↓ (Command parsing and validation)
2. Configuration Loading
   ↓ (Hierarchy: CLI → Env → Project → Global → Defaults)
3. Project Detection
   ↓ (Auto-detect type, scan files, analyze structure)
4. Provider Selection
   ↓ (Choose primary provider, setup fallbacks)
5. Analysis Execution
   ↓ (Orchestrate analysis, handle errors, track progress)
6. Result Processing
   ↓ (Aggregate findings, deduplicate, validate)
7. Output Generation
   ↓ (Format results, apply filters, export)
8. Session Management
   ↓ (Save state, cleanup, handle resume)
```

### Configuration Hierarchy

```
Priority: High → Low

1. CLI Arguments        (--llm copilot --depth deep)
2. Environment Variables (AI_ANALYZER_LLM_PROVIDER=copilot)
3. Project Config       (.ai-analyzer.yaml in project)
4. Global Config        (~/.ai-analyzer/config.yaml)
5. System Defaults      (Hardcoded in models.py)
```

## 🔌 Plugin Architecture

### Analyzer Plugins

```python
# Plugin registration pattern
@register_analyzer("documentation")
class DocumentationAnalyzer(BaseAnalyzer):
    project_types = [ProjectType.ANY]
    priority = 1
    
    async def analyze(self, config: AnalysisConfig) -> AnalysisResult:
        """Implement analysis logic."""
        pass
    
    def can_analyze(self, project_info: ProjectInfo) -> bool:
        """Check if analyzer applies to project."""
        return True
```

### LLM Provider Plugins

```python
# Provider registration pattern
@register_provider(LLMProvider.COPILOT)
class CopilotProvider(BaseLLMProvider):
    supports_streaming = True
    supports_function_calling = False
    cost_per_token = 0.0  # Free with VS Code
    
    async def analyze_code(self, code: str, context: dict[str, Any]) -> AnalysisResult:
        """Implement provider-specific analysis."""
        pass
```

## 🔧 Extension Points

### 1. Custom Analyzers
- Implement `BaseAnalyzer` interface
- Register with `@register_analyzer` decorator
- Define supported project types and priority

### 2. Custom LLM Providers
- Implement `BaseLLMProvider` interface
- Register with `@register_provider` decorator
- Handle provider-specific authentication and API calls

### 3. Custom Output Formats
- Implement output formatter interface
- Register with output format registry
- Support for custom templates and styling

### 4. Custom Project Types
- Extend `ProjectType` enum
- Implement detection logic
- Map to appropriate analyzers

## 📊 Performance Considerations

### Async-First Design
- All I/O operations are async by default
- Concurrent analysis with multiple providers
- Non-blocking file system operations
- Efficient resource utilization

### Caching Strategy
```python
# Configuration caching
@lru_cache(maxsize=128)
def load_config(config_path: Path, **overrides) -> AnalysisConfig:
    """Cache configuration to avoid repeated parsing."""

# Provider result caching
class ProviderCache:
    """Cache provider results for identical inputs."""
    def get_cached_result(self, provider: str, code_hash: str) -> Optional[AnalysisResult]:
        pass
```

### Memory Management
- Stream large files instead of loading entirely
- Lazy loading of analyzer plugins
- Efficient data structures for findings and recommendations
- Cleanup of temporary files and sessions

## 🔒 Security Considerations

### Data Privacy
- No code is sent to external providers without explicit consent
- Local processing option for sensitive codebases
- Configurable data retention policies
- Audit logging for compliance

### API Key Management
```python
# Secure API key handling
class SecureConfig:
    """Handles sensitive configuration data."""
    
    def load_api_keys(self) -> dict[str, str]:
        """Load API keys from secure sources."""
        # Priority: Environment → Keyring → Config file
        pass
```

### Input Validation
- All user input is validated with Pydantic models
- Path traversal protection for file operations
- Sanitization of code inputs before sending to LLMs
- Rate limiting for API calls

## 🧪 Testing Architecture

### Test Structure
```
tests/
├── unit/              # Unit tests for individual components
├── integration/       # Integration tests for component interactions
├── e2e/              # End-to-end CLI tests
├── fixtures/         # Test data and mock projects
└── performance/      # Performance and load tests
```

### Test Strategy
- **Unit Tests**: Mock external dependencies, test individual components
- **Integration Tests**: Test component interactions with real dependencies
- **E2E Tests**: Full CLI workflows with real or simulated providers
- **Performance Tests**: Measure analysis speed and resource usage

## 📈 Monitoring and Observability

### Structured Logging
```python
import structlog

logger = structlog.get_logger()

# Contextual logging
logger.info("Analysis started", 
           session_id=session.id,
           project_type=project.type,
           provider=config.llm_provider)
```

### Metrics Collection
- Analysis duration and success rates
- Provider performance and error rates
- Resource usage (CPU, memory, network)
- User interaction patterns

### Error Tracking
- Comprehensive error context collection
- Provider-specific error categorization
- Automatic retry and fallback mechanisms
- User-friendly error reporting

---

**Architecture Principles**: Modularity, Extensibility, Performance, Security, Maintainability
