# Architecture Overview - Journaling AI Backend

## 1. **Architecture Overview**
- **Framework**: FastAPI (Python 3.11) - Modern async web framework
- **Database**: PostgreSQL with SQLAlchemy 2.0 + Alembic for migrations
- **Caching**: Redis with enterprise-grade connection pooling
- **Background Tasks**: Celery with Redis broker
- **Vector Storage**: ChromaDB for embeddings and semantic search
- **AI/ML**: PyTorch + Transformers with hardware-adaptive model selection
- **LLM Integration**: Ollama for local language model inference
- **Containerization**: Docker with CPU/GPU variants

## 2. **Main Components**

### Core Structure:
- **`app/`** - Main application package
  - **`api/`** - REST API endpoints (entries, insights, psychology, topics)
  - **`core/`** - Core infrastructure (config, database, exceptions, monitoring)
  - **`models/`** - SQLAlchemy ORM models and Pydantic schemas
  - **`repositories/`** - Data access layer with caching patterns
  - **`services/`** - Business logic (22+ services including AI, analytics, hardware)
  - **`tasks/`** - Celery background tasks (analytics, psychology, maintenance)

### Data Storage:
- **`data/`** - Runtime data storage
  - **`chroma_db/`** - Vector embeddings database
  - **`psychology_db/`** - Psychology knowledge base
  - **`analytics_cache/`** - Cached analytics results
- **`models/`** - Pre-trained AI models (8 different models for various tasks)

## 3. **Entry Points**
- **Primary**: `run.py` → `app/main.py` (FastAPI application)
- **Container**: Dockerfile runs `uvicorn app.main:app` 
- **Development**: `uvicorn` with auto-reload on port 8000
- **Production**: Containerized with proper health checks and monitoring

## 4. **Dependencies**

### Core Framework:
- `fastapi==0.104.1` + `uvicorn==0.24.0` - Web framework & ASGI server
- `asyncpg==0.30.0` + `sqlalchemy==2.0.35` - Async PostgreSQL driver

### AI/ML Stack:
- `torch==2.0.1` + `transformers==4.35.0` - Deep learning foundation
- `sentence-transformers==2.2.2` - Text embeddings
- `chromadb==0.4.15` - Vector database
- `ollama==0.1.9` - Local LLM inference

### Infrastructure:
- `redis==5.0.1` + `celery==5.3.4` - Caching & background processing
- `alembic==1.14.0` - Database migrations

## 5. **Potential Issues**

### ⚠️ **Red Flags Identified**:

1. **Hardcoded Secrets**: 
   - Default secret key in config.py:59 `"your-secret-key-change-in-production"`
   - Redis password hardcoded in multiple places

2. **Disabled Critical Features**:
   - Sessions API commented out (main.py:24, 185) due to "missing legacy dependencies"
   - Potential functionality gap

3. **Resource Intensive**:
   - 8 pre-trained AI models (~2GB+ storage)
   - Hardware-adaptive but may struggle on limited systems
   - Complex GPU/CPU fallback logic

4. **Configuration Complexity**:
   - Multiple overlapping config patterns (legacy + new)
   - Docker networking assumptions (`host.docker.internal`)

5. **Development-Focused**:
   - Debug settings, auto-reload enabled
   - CORS allows localhost only
   - Not production-hardened

### ✅ **Positive Architecture**:
- Clean separation of concerns
- Comprehensive health monitoring
- Enterprise-grade caching strategy
- Hardware-adaptive AI system
- Proper async patterns throughout

**Recommendation**: Address security configs and complete the sessions functionality before production deployment.
