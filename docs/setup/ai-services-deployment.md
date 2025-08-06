# AI Services Setup and Deployment Guide

## Prerequisites

### System Requirements
- **Python**: 3.13+ (recommended 3.13.5)
- **RAM**: Minimum 4GB, recommended 8GB+
- **Storage**: 5GB+ free space for AI models
- **Network**: Internet connection for initial model downloads
- **GPU**: Optional but recommended (NVIDIA with CUDA support)

### Phase 2 Dependencies
- Phase 2 service registry infrastructure
- Unified cache service implementation
- Logging and monitoring systems

## Installation

### 1. Python Environment Setup
```bash
# Ensure Python 3.13+ is installed
python --version  # Should show 3.13.x

# Create virtual environment (if not already created)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

### 2. AI Dependencies Installation
```bash
# Install PyTorch (CPU version)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install PyTorch with CUDA support (if GPU available)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install Transformers and related libraries
pip install transformers sentence-transformers

# Install system utilities
pip install psutil

# Verify installation
python -c "import torch; print(f'PyTorch version: {torch.__version__}')"
python -c "import transformers; print(f'Transformers version: {transformers.__version__}')"
```

### 3. GPU Support Verification (Optional)
```bash
# Check CUDA availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Check GPU details
python -c "
import torch
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB')
else:
    print('No GPU detected, will use CPU')
"
```

## Configuration

### 1. Environment Variables (Optional)
```bash
# GPU configuration
export CUDA_VISIBLE_DEVICES=0                    # Specify GPU device
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512  # Memory management

# Model cache directory
export TRANSFORMERS_CACHE=/path/to/model/cache   # Custom model storage location

# Logging level
export LOG_LEVEL=INFO                             # Adjust logging verbosity
```

### 2. Model Cache Configuration
```python
# In your application configuration
AI_CONFIG = {
    "model_cache_dir": "/path/to/models",         # Custom model storage
    "memory_limit_gb": 8.0,                       # Memory usage limit
    "gpu_memory_limit_gb": 9.3,                   # GPU memory limit
    "cache_strategy": "lru",                      # Cache eviction strategy
    "preload_models": False,                      # Lazy loading (recommended)
}
```

## Deployment

### 1. Development Deployment
```bash
# Navigate to backend directory
cd /path/to/journaling-ai/backend

# Initialize AI services
python -c "
from app.services.ai_service_init import initialize_ai_services
result = initialize_ai_services()
print(f'Services initialized: {len(result[\"services_initialized\"])}/4')
"

# Verify deployment
python -c "
from app.services.ai_service_init import get_ai_services_status
status = get_ai_services_status()
print(f'Overall status: {status[\"overall_status\"]}')
print(f'Service registry: {status[\"integrations\"][\"service_registry\"][\"status\"]}')
"
```

### 2. Production Deployment
```bash
# Pre-download models (optional, for faster startup)
python -c "
from app.services.ai_model_manager import ai_model_manager, ModelType
models_to_preload = [
    ModelType.EMOTION_ANALYSIS,
    ModelType.TEXT_GENERATION,
    ModelType.SENTIMENT_ANALYSIS
]
for model_type in models_to_preload:
    print(f'Loading {model_type.value}...')
    ai_model_manager.load_model(model_type)
print('Pre-loading complete')
"

# Production startup
python -m app.main  # Your application entry point
```

### 3. Docker Deployment
```dockerfile
# Dockerfile example
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install AI dependencies
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install transformers sentence-transformers psutil

# Copy application code
COPY . .

# Environment variables
ENV PYTHONPATH=/app
ENV TRANSFORMERS_CACHE=/app/models

# Create model cache directory
RUN mkdir -p /app/models

# Expose port
EXPOSE 8000

# Startup command
CMD ["python", "-m", "app.main"]
```

### 4. Docker Compose with GPU Support
```yaml
version: '3.8'
services:
  journaling-ai:
    build: .
    ports:
      - "8000:8000"
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
    volumes:
      - ./models:/app/models  # Persistent model storage
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## First-Time Setup

### 1. Initial Model Download
```python
# Run this once to download all required models
from app.services.ai_model_manager import ai_model_manager, ModelType

print("Downloading AI models (this may take several minutes)...")

models = [
    ModelType.EMOTION_ANALYSIS,
    ModelType.TEXT_GENERATION, 
    ModelType.SENTIMENT_ANALYSIS,
    ModelType.EMBEDDINGS
]

for i, model_type in enumerate(models, 1):
    print(f"[{i}/{len(models)}] Downloading {model_type.value}...")
    try:
        model = ai_model_manager.load_model(model_type)
        print(f"✓ {model_type.value} loaded successfully")
    except Exception as e:
        print(f"✗ {model_type.value} failed: {e}")

print("Model download complete!")
```

### 2. Verify Installation
```python
# Complete verification script
from app.services.ai_service_init import initialize_ai_services, get_ai_services_status
from app.core.service_interfaces import service_registry

print("=== AI Services Installation Verification ===")

# 1. Initialize services
print("\n1. Initializing AI services...")
init_result = initialize_ai_services()
print(f"   Services initialized: {len(init_result['services_initialized'])}/4")
print(f"   Services failed: {len(init_result['services_failed'])}")

if init_result['errors']:
    print("   Errors:")
    for error in init_result['errors']:
        print(f"     - {error}")

# 2. Check service registry
print("\n2. Checking service registry...")
status = get_ai_services_status()
registry_status = status['integrations']['service_registry']['status']
print(f"   Registry status: {registry_status}")
print(f"   Registered services: {status['integrations']['service_registry']['registered_services']}/4")

# 3. Test individual services
print("\n3. Testing individual services...")
services = ['ai_model_manager', 'ai_prompt_service', 'ai_emotion_service', 'ai_intervention_service']
for service_name in services:
    try:
        service = service_registry.get_service(service_name)
        print(f"   ✓ {service_name}: Available ({type(service).__name__})")
    except Exception as e:
        print(f"   ✗ {service_name}: Error - {e}")

# 4. Hardware check
print("\n4. Hardware capabilities...")
import torch
print(f"   PyTorch version: {torch.__version__}")
print(f"   CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"   GPU: {torch.cuda.get_device_name(0)}")
    print(f"   GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")

# 5. Overall status
print(f"\n=== Installation Status: {'✅ SUCCESS' if len(init_result['services_initialized']) == 4 else '⚠️ PARTIAL'} ===")
```

## Monitoring and Maintenance

### 1. Health Monitoring
```python
# Regular health check script
import asyncio
from app.services.ai_service_init import run_ai_services_health_check, get_ai_services_status

async def daily_health_check():
    print("Running daily AI services health check...")
    
    # Comprehensive health check
    health_result = await run_ai_services_health_check()
    print(f"Overall health: {health_result['overall_health']}")
    print(f"Checks passed: {len(health_result['checks_passed'])}/{len(health_result['checks_performed'])}")
    
    if health_result['checks_failed']:
        print("Failed checks:")
        for check in health_result['checks_failed']:
            print(f"  - {check}")
    
    if health_result['recommendations']:
        print("Recommendations:")
        for rec in health_result['recommendations']:
            print(f"  - {rec}")
    
    # Service status
    status = get_ai_services_status()
    print(f"Service registry status: {status['integrations']['service_registry']['status']}")
    
    return health_result['overall_health'] == 'healthy'

# Run health check
asyncio.run(daily_health_check())
```

### 2. Memory Monitoring
```python
# Memory usage monitoring
import psutil
import torch
from app.services.ai_model_manager import ai_model_manager

def monitor_memory_usage():
    # System memory
    memory = psutil.virtual_memory()
    print(f"System RAM: {memory.used / 1e9:.1f}GB / {memory.total / 1e9:.1f}GB ({memory.percent:.1f}%)")
    
    # GPU memory (if available)
    if torch.cuda.is_available():
        gpu_memory_used = torch.cuda.memory_allocated() / 1e9
        gpu_memory_total = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"GPU Memory: {gpu_memory_used:.1f}GB / {gpu_memory_total:.1f}GB")
    
    # AI model status
    model_status = ai_model_manager.get_model_status()
    print(f"Loaded models: {model_status['loaded_models']}")
    print(f"Model memory usage: {model_status['total_memory_usage']:.1f}GB")

monitor_memory_usage()
```

### 3. Performance Monitoring
```python
# Performance metrics collection
from app.services.ai_prompt_service import ai_prompt_service
from app.services.ai_emotion_service import ai_emotion_service
from app.services.ai_intervention_service import ai_intervention_service

def collect_performance_metrics():
    metrics = {}
    
    # Prompt service metrics
    prompt_stats = ai_prompt_service.get_generation_stats()
    metrics['prompt_service'] = {
        'total_generated': prompt_stats['total_generated'],
        'cache_hit_rate': prompt_stats['cache_hit_rate'],
        'avg_response_time': prompt_stats.get('avg_response_time', 'N/A')
    }
    
    # Emotion service metrics
    emotion_stats = ai_emotion_service.get_analysis_stats()
    metrics['emotion_service'] = {
        'total_analyses': emotion_stats['total_analyses'],
        'cache_hit_rate': emotion_stats['cache_hit_rate'],
        'pattern_detection_rate': emotion_stats['pattern_detection_rate']
    }
    
    # Intervention service metrics
    intervention_stats = ai_intervention_service.get_intervention_stats()
    metrics['intervention_service'] = {
        'total_assessments': intervention_stats['total_assessments'],
        'crisis_detection_rate': intervention_stats['crisis_detection_rate'],
        'safety_referral_rate': intervention_stats['safety_referral_rate']
    }
    
    return metrics

metrics = collect_performance_metrics()
print("Performance Metrics:", metrics)
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Service Registration Failures
```python
# Diagnostic script
from app.core.service_interfaces import service_registry

def diagnose_service_registry():
    print("Diagnosing service registry issues...")
    
    # Check registry instance
    print(f"Registry type: {type(service_registry)}")
    print(f"Registry ID: {id(service_registry)}")
    
    # List all registered services
    if hasattr(service_registry, '_services'):
        print(f"All registered services: {list(service_registry._services.keys())}")
    
    # Test service registration
    ai_services = ['ai_model_manager', 'ai_prompt_service', 'ai_emotion_service', 'ai_intervention_service']
    for service_name in ai_services:
        try:
            service = service_registry.get_service(service_name)
            print(f"✓ {service_name}: {type(service).__name__}")
        except Exception as e:
            print(f"✗ {service_name}: {e}")

diagnose_service_registry()
```

#### 2. Memory Issues
```python
# Memory cleanup script
import gc
import torch

def cleanup_memory():
    print("Cleaning up memory...")
    
    # Python garbage collection
    collected = gc.collect()
    print(f"Garbage collected: {collected} objects")
    
    # GPU memory cleanup
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        print("GPU cache cleared")
    
    # Force model unloading (if needed)
    from app.services.ai_model_manager import ai_model_manager
    # ai_model_manager.clear_cache()  # Implement if needed

cleanup_memory()
```

#### 3. Model Loading Issues
```python
# Model loading diagnostics
from app.services.ai_model_manager import ai_model_manager, ModelType
import torch

def diagnose_model_loading():
    print("Diagnosing model loading...")
    
    # Check available models
    for model_type in ModelType:
        try:
            print(f"Testing {model_type.value}...")
            model = ai_model_manager.load_model(model_type)
            print(f"✓ {model_type.value}: Loaded successfully")
        except Exception as e:
            print(f"✗ {model_type.value}: {e}")
    
    # Check hardware
    print(f"\nHardware status:")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU memory: {torch.cuda.memory_allocated() / 1e9:.1f}GB used")

diagnose_model_loading()
```

#### 4. Network/Download Issues
```bash
# Test model download connectivity
python -c "
import requests
from transformers import AutoTokenizer

# Test Hugging Face connectivity
try:
    response = requests.get('https://huggingface.co', timeout=10)
    print(f'Hugging Face accessible: {response.status_code == 200}')
except Exception as e:
    print(f'Hugging Face connectivity issue: {e}')

# Test model download
try:
    tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased')
    print('✓ Model download working')
except Exception as e:
    print(f'✗ Model download failed: {e}')
"
```

### Rollback Procedures

#### Disable AI Services (Emergency)
```python
# Emergency disable script
def emergency_disable_ai():
    print("Emergency AI services disable...")
    
    # This would implement fallback to basic functionality
    # Implementation depends on your application architecture
    
    print("AI services disabled, using fallback systems")

# emergency_disable_ai()
```

### Support and Maintenance

#### Log Analysis
```bash
# Check AI service logs
grep -i "ai.*service" /path/to/logs/*.log
grep -i "model.*loading" /path/to/logs/*.log
grep -i "error\|exception" /path/to/logs/*.log | grep -i ai
```

#### Regular Maintenance Tasks
```bash
# Weekly maintenance script
#!/bin/bash

echo "=== AI Services Weekly Maintenance ==="

# 1. Health check
python -c "
import asyncio
from app.services.ai_service_init import run_ai_services_health_check
result = asyncio.run(run_ai_services_health_check())
print(f'Health status: {result[\"overall_health\"]}')
"

# 2. Memory usage check
python -c "
import psutil
memory = psutil.virtual_memory()
if memory.percent > 80:
    print('WARNING: High memory usage')
else:
    print('Memory usage normal')
"

# 3. Model cache cleanup (if needed)
# find /path/to/model/cache -type f -mtime +30 -delete

echo "=== Maintenance Complete ==="
```

This deployment guide ensures robust, production-ready AI services with comprehensive monitoring and troubleshooting capabilities.
