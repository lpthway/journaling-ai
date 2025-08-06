# AI Services Module Documentation

## Project Overview

**Module Name**: AI Services Infrastructure  
**Purpose**: Comprehensive AI-powered service layer replacing hardcoded AI systems with intelligent, adaptive services for journaling application  
**Current Status**: ✅ **COMPLETE and READY** - All 4 services initialized and registered successfully  
**Technology Stack**: Python 3.13, PyTorch, Transformers, Sentence Transformers, NumPy, PSUtil  
**Dependencies**: Unified Cache Service (Phase 2), Service Registry (Phase 2), Hugging Face models  
**Entry Points**: `app.services.ai_service_init.initialize_ai_services()`

## Architecture Documentation

### Project Structure
```
backend/app/services/
├── ai_service_init.py          # Central initialization and health monitoring
├── ai_model_manager.py         # AI model loading and memory management
├── ai_prompt_service.py        # Dynamic prompt generation
├── ai_emotion_service.py       # Advanced emotion analysis
└── ai_intervention_service.py  # Crisis intervention and safety
```

### Data Flow
1. **Initialization**: `ai_service_init.py` imports and registers all AI services
2. **Model Management**: `ai_model_manager.py` loads and caches AI models on-demand
3. **Service Integration**: All services register with Phase 2 service registry
4. **Cache Integration**: Services use unified cache for performance optimization
5. **Health Monitoring**: Continuous status tracking and error reporting

### Key Components

#### 1. AI Service Initialization (`ai_service_init.py`)
- **Purpose**: Central coordinator for AI service lifecycle
- **Functions**: 
  - `initialize_ai_services()` - Loads and registers all AI services
  - `get_ai_services_status()` - Real-time health monitoring
  - `run_ai_services_health_check()` - Comprehensive health validation
- **Integration**: Phase 2 service registry, logging system

#### 2. AI Model Manager (`ai_model_manager.py`)
- **Purpose**: Centralized AI model loading, caching, and memory management
- **Key Features**:
  - Hardware-aware model selection (GPU/CPU detection)
  - Memory optimization with 9.3GB GPU limit awareness
  - 9 pre-configured AI model types
  - Lazy loading and intelligent caching
- **Models Supported**:
  - Text Generation: facebook/bart-base, facebook/bart-large
  - Emotion Analysis: j-hartmann/emotion-english-distilroberta-base
  - Sentiment Analysis: cardiffnlp/twitter-roberta-base-sentiment-latest
  - Embeddings: sentence-transformers/all-MiniLM-L6-v2

#### 3. AI Prompt Service (`ai_prompt_service.py`)
- **Purpose**: Dynamic AI-powered prompt generation replacing static templates
- **Features**:
  - 10 generation strategies (creative, analytical, supportive, etc.)
  - Cultural adaptation for international users
  - Template enhancement with AI-generated variations
  - Caching for performance optimization
- **Integration**: Uses AI Model Manager for text generation models

#### 4. AI Emotion Service (`ai_emotion_service.py`)
- **Purpose**: Advanced emotion detection replacing keyword-based analysis
- **Capabilities**:
  - Multi-model emotion analysis
  - 6 pattern detection rules
  - 4 cultural emotion mappings
  - Confidence scoring and validation
- **Models**: Integrates with DistilRoBERTa emotion models

#### 5. AI Intervention Service (`ai_intervention_service.py`)
- **Purpose**: Intelligent crisis intervention and safety assessment
- **Safety Features**:
  - 8 crisis indicator patterns
  - 7 intervention template types
  - 7 therapeutic technique applications
  - Professional referral logic
- **Compliance**: Mental health safety standards integration

### Design Patterns
- **Service Registry Pattern**: All services register with Phase 2 global registry
- **Singleton Pattern**: Single instances per service type
- **Factory Pattern**: Model creation and configuration
- **Cache-Aside Pattern**: Integration with unified cache service
- **Health Check Pattern**: Continuous monitoring and status reporting

### Configuration
- **Environment Variables**: GPU detection, memory limits
- **Model Configurations**: Pre-defined in each service class
- **Cache Settings**: Inherited from Phase 2 unified cache
- **Service Registry**: Global registration with Phase 2 architecture

## Change Log (CRITICAL)

### 2025-08-06 12:00:00 UTC - AI Service Infrastructure Implementation

**Type**: Major Feature Addition - AI Service Refactoring Phase A  
**Files Created**:
- `/backend/app/services/ai_service_init.py` (300+ lines)
- `/backend/app/services/ai_model_manager.py` (530+ lines)
- `/backend/app/services/ai_prompt_service.py` (650+ lines)
- `/backend/app/services/ai_emotion_service.py` (800+ lines)
- `/backend/app/services/ai_intervention_service.py` (1000+ lines)

**Reason**: Replace monolithic hardcoded AI systems with intelligent, adaptive services following Phase 2 enterprise architecture patterns

**Impact**: 
- Complete transformation from static to AI-powered journaling features
- Integration with Phase 2 service registry and caching infrastructure
- Foundation for advanced AI capabilities in journaling application

**Before/After**:
```python
# BEFORE: Hardcoded static systems
class StaticEmotionDetector:
    def detect_emotion(self, text):
        # Simple keyword matching
        if "sad" in text.lower():
            return "sadness"

# AFTER: AI-powered intelligent analysis
class AIEmotionService:
    def analyze_emotion(self, text, context=None):
        # Multi-model AI analysis with confidence scoring
        emotion_result = self.emotion_model.predict(text)
        pattern_analysis = self.detect_patterns(text)
        cultural_adaptation = self.apply_cultural_mapping(emotion_result)
        return EnhancedEmotionResult(...)
```

**Testing**: All services initialize successfully (4/4), register in service registry (4/4), and pass health checks

### Service Registry Integration Fix - 2025-08-06 11:45:00 UTC

**Type**: Bug Fix  
**Files Modified**:
- `ai_model_manager.py` - Line 520-525
- `ai_prompt_service.py` - Line 640-645  
- `ai_emotion_service.py` - Line 790-795
- `ai_intervention_service.py` - Line 990-995
- `ai_service_init.py` - Line 210-228

**Reason**: Services were creating new ServiceRegistry instances instead of using global service_registry

**Before**:
```python
from app.core.service_interfaces import ServiceRegistry
service_registry = ServiceRegistry()  # ❌ Creates new instance
```

**After**:
```python
from app.core.service_interfaces import service_registry  # ✅ Uses global instance
```

**Testing**: Service registration test now shows 4/4 services registered successfully

## Current Implementation Details

### Functions/Methods

#### AI Service Initialization (`ai_service_init.py`)

**`initialize_ai_services() -> Dict[str, Any]`**
- **Purpose**: Initialize and register all AI services
- **Parameters**: None
- **Returns**: Initialization status with service counts, errors, and registry status
- **Side Effects**: Registers services in global service registry, logs initialization status
- **Error Handling**: Captures individual service failures, continues with partial initialization

**`get_ai_services_status() -> Dict[str, Any]`**
- **Purpose**: Real-time health monitoring of all AI services
- **Parameters**: None
- **Returns**: Comprehensive status report including service health, performance metrics
- **Side Effects**: None (read-only status check)

**`run_ai_services_health_check() -> Dict[str, Any]`**
- **Purpose**: Comprehensive health validation with recommendations
- **Parameters**: None
- **Returns**: Health check results with pass/fail status and recommendations
- **Side Effects**: May trigger service recovery procedures

#### AI Model Manager (`ai_model_manager.py`)

**`load_model(model_type: ModelType) -> transformers.PreTrainedModel`**
- **Purpose**: Load and cache AI models with hardware optimization
- **Parameters**: `model_type` - Enum specifying which model to load
- **Returns**: Loaded transformer model ready for inference
- **Side Effects**: Updates model cache, allocates GPU/CPU memory
- **Memory Management**: Respects 9.3GB GPU limit, falls back to CPU if needed

**`get_model_status() -> Dict[str, Any]`**
- **Purpose**: Report current model loading status and memory usage
- **Parameters**: None
- **Returns**: Status dict with loaded models, memory usage, GPU availability
- **Side Effects**: None (read-only status)

#### AI Prompt Service (`ai_prompt_service.py`)

**`generate_prompt(prompt_type: PromptType, context: Dict) -> GeneratedPrompt`**
- **Purpose**: Generate AI-powered prompts based on context and type
- **Parameters**: 
  - `prompt_type` - Type of prompt needed (reflection, gratitude, etc.)
  - `context` - User context for personalization
- **Returns**: Enhanced prompt with AI-generated content
- **Side Effects**: Updates generation statistics, cache writes
- **AI Integration**: Uses text generation models from AI Model Manager

#### AI Emotion Service (`ai_emotion_service.py`)

**`analyze_emotion(text: str, context: Optional[Dict]) -> EmotionAnalysisResult`**
- **Purpose**: Comprehensive emotion analysis using multiple AI models
- **Parameters**:
  - `text` - Text to analyze
  - `context` - Optional context for better analysis
- **Returns**: Emotion analysis with confidence scores and patterns
- **Side Effects**: Updates analysis statistics, cache operations
- **AI Models**: Uses DistilRoBERTa emotion detection models

#### AI Intervention Service (`ai_intervention_service.py`)

**`assess_crisis_indicators(text: str, user_context: Dict) -> CrisisAssessmentResult`**
- **Purpose**: Intelligent crisis detection and intervention recommendations
- **Parameters**:
  - `text` - User input to assess
  - `user_context` - User history and context
- **Returns**: Crisis assessment with intervention recommendations
- **Side Effects**: May trigger safety protocols, logs safety events
- **Safety Features**: Professional referral logic, emergency contact protocols

### Data Structures

#### ModelConfiguration
```python
@dataclass
class ModelConfiguration:
    model_name: str
    model_type: ModelType
    memory_requirement_gb: float
    gpu_preferred: bool
    fallback_cpu: bool
    cache_strategy: CacheStrategy
```

#### EmotionAnalysisResult
```python
@dataclass
class EmotionAnalysisResult:
    primary_emotion: str
    confidence_score: float
    secondary_emotions: List[Tuple[str, float]]
    patterns_detected: List[str]
    cultural_adaptation: Dict[str, Any]
    recommendations: List[str]
```

#### CrisisAssessmentResult
```python
@dataclass
class CrisisAssessmentResult:
    crisis_level: CrisisLevel  # LOW, MEDIUM, HIGH, CRITICAL
    indicators_detected: List[str]
    recommended_interventions: List[str]
    safety_resources: List[str]
    requires_professional_referral: bool
    immediate_actions: List[str]
```

### Algorithms

#### Model Selection Algorithm (AI Model Manager)
1. **Hardware Detection**: Check GPU availability and memory
2. **Memory Calculation**: Estimate model memory requirements
3. **Optimization Decision**: Choose GPU vs CPU based on capacity
4. **Fallback Strategy**: CPU fallback if GPU memory insufficient
5. **Cache Management**: LRU eviction if memory limits exceeded

#### Emotion Pattern Detection (AI Emotion Service)
1. **Multi-Model Analysis**: Run text through 3 emotion detection models
2. **Confidence Aggregation**: Combine results with weighted averaging
3. **Pattern Recognition**: Apply 6 behavioral pattern rules
4. **Cultural Mapping**: Adapt results for cultural context
5. **Validation**: Cross-validate with user history patterns

#### Crisis Indicator Assessment (AI Intervention Service)
1. **Text Analysis**: Scan for 8 crisis indicator patterns
2. **Context Integration**: Consider user history and recent patterns
3. **Risk Scoring**: Calculate composite risk score
4. **Intervention Mapping**: Match risk level to intervention templates
5. **Safety Protocol**: Trigger professional referral if needed

## Known Issues and Limitations

### Current Limitations
- **Model Download**: First-time model loading requires internet connection
- **Memory Usage**: Large models may exceed memory limits on low-end hardware
- **Cultural Adaptation**: Limited to English language emotion models currently
- **Real-time Processing**: Some AI operations may have latency for complex analysis

### Performance Considerations
- **Cold Start**: Initial model loading adds startup time
- **Memory Management**: GPU memory must be carefully managed
- **Cache Optimization**: Cache hit rates improve with usage patterns
- **Concurrent Users**: Multiple simultaneous AI requests may queue

### Missing Features (Planned)
- **Multi-language Support**: Extend emotion analysis to other languages
- **Custom Model Training**: User-specific model fine-tuning
- **Advanced Intervention**: Integration with external mental health services
- **Real-time Adaptation**: Dynamic model selection based on usage patterns

## Setup and Usage Instructions

### Prerequisites
- Python 3.13+
- PyTorch with CUDA support (optional, for GPU acceleration)
- Phase 2 service registry and cache infrastructure
- Internet connection for initial model downloads

### Installation
```bash
# Install AI dependencies (if not already installed)
pip install torch transformers sentence-transformers psutil

# Verify GPU support (optional)
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### Configuration
```python
# Environment variables (optional)
export CUDA_VISIBLE_DEVICES=0  # Specify GPU
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512  # Memory management
```

### Running AI Services
```python
# Initialize all AI services
from app.services.ai_service_init import initialize_ai_services

result = initialize_ai_services()
print(f"Services initialized: {len(result['services_initialized'])}/4")

# Check service status
from app.services.ai_service_init import get_ai_services_status
status = get_ai_services_status()
print(f"Overall status: {status['overall_status']}")

# Access individual services
from app.core.service_interfaces import service_registry

ai_model_manager = service_registry.get_service('ai_model_manager')
ai_emotion_service = service_registry.get_service('ai_emotion_service')
```

### Common Tasks

#### Load Specific AI Model
```python
from app.services.ai_model_manager import ModelType
model = ai_model_manager.load_model(ModelType.EMOTION_ANALYSIS)
```

#### Generate AI Prompt
```python
from app.services.ai_prompt_service import PromptType
prompt = ai_prompt_service.generate_prompt(
    PromptType.REFLECTION,
    context={"user_mood": "contemplative", "time_of_day": "evening"}
)
```

#### Analyze Emotion
```python
result = ai_emotion_service.analyze_emotion(
    "I'm feeling overwhelmed with work lately",
    context={"user_id": "123", "recent_patterns": ["stress"]}
)
print(f"Primary emotion: {result.primary_emotion}")
```

#### Crisis Assessment
```python
assessment = ai_intervention_service.assess_crisis_indicators(
    "I don't see the point in anything anymore",
    user_context={"history": "recent_stress", "support_network": "limited"}
)
if assessment.requires_professional_referral:
    print("Professional intervention recommended")
```

### Troubleshooting

#### Service Registration Issues
```python
# Check if services are registered
from app.core.service_interfaces import service_registry
services = ['ai_model_manager', 'ai_prompt_service', 'ai_emotion_service', 'ai_intervention_service']
for service_name in services:
    try:
        service = service_registry.get_service(service_name)
        print(f"✓ {service_name}: Available")
    except ValueError:
        print(f"✗ {service_name}: Not registered")
```

#### Memory Issues
```python
# Check GPU memory usage
import torch
if torch.cuda.is_available():
    print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
    print(f"GPU memory used: {torch.cuda.memory_allocated() / 1e9:.1f}GB")
```

#### Model Loading Problems
```python
# Verify model availability
model_status = ai_model_manager.get_model_status()
print(f"Loaded models: {model_status['loaded_models']}")
print(f"GPU available: {model_status['gpu_available']}")
```

## Development Guidelines

### Code Style
- **Naming**: Use descriptive names for AI-related functions (`analyze_emotion` vs `analyze`)
- **Type Hints**: All functions include comprehensive type hints
- **Documentation**: Docstrings include AI model information and expected behavior
- **Error Handling**: Graceful degradation when AI models fail

### Testing Strategy
- **Unit Tests**: Test individual AI service methods
- **Integration Tests**: Test service registry integration
- **Performance Tests**: Validate memory usage and response times
- **AI Model Tests**: Validate model outputs meet quality thresholds

### AI Model Management
- **Version Control**: Track model versions and configurations
- **Performance Monitoring**: Monitor inference times and accuracy
- **Memory Optimization**: Regular profiling of memory usage patterns
- **Fallback Strategies**: Ensure graceful degradation when models unavailable

### Safety Considerations
- **Crisis Detection**: Regular validation of crisis intervention triggers
- **Privacy**: Ensure AI analysis respects user privacy requirements
- **Bias Monitoring**: Regular evaluation of AI model bias and fairness
- **Professional Standards**: Maintain compliance with mental health guidelines

This documentation provides comprehensive coverage of the AI services infrastructure, enabling future development and maintenance by any AI agent or developer working on the project.
