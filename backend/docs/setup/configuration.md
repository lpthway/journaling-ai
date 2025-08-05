# Configuration Guide

## Overview

The Journaling AI backend uses environment-based configuration for maximum flexibility across development, testing, and production environments. This guide covers all configuration options and best practices.

## Environment Files

### Development Configuration (.env)
```bash
# =============================================================================
# JOURNALING AI BACKEND - DEVELOPMENT CONFIGURATION
# =============================================================================

# -----------------------------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------------------------
DATABASE_URL=postgresql://journaling_user:dev_password@localhost/journaling_ai
DB_HOST=localhost
DB_PORT=5432
DB_NAME=journaling_ai
DB_USER=journaling_user
DB_PASSWORD=dev_password
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_ECHO=False  # Set to True for SQL query logging

# -----------------------------------------------------------------------------
# Redis Configuration
# -----------------------------------------------------------------------------
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_MAX_CONNECTIONS=20
REDIS_RETRY_ON_TIMEOUT=True

# -----------------------------------------------------------------------------
# Application Settings
# -----------------------------------------------------------------------------
PROJECT_NAME=Journaling AI Backend
API_V1_STR=/api/v1
SECRET_KEY=your-development-secret-key-change-in-production
DEBUG=True
ENVIRONMENT=development
HOST=0.0.0.0
PORT=8000

# -----------------------------------------------------------------------------
# Security Configuration
# -----------------------------------------------------------------------------
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30
ALGORITHM=HS256
PASSWORD_MIN_LENGTH=8
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15

# -----------------------------------------------------------------------------
# CORS Settings (Frontend Development)
# -----------------------------------------------------------------------------
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:3000"]
ALLOWED_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
ALLOWED_HEADERS=["*"]
ALLOW_CREDENTIALS=True

# -----------------------------------------------------------------------------
# AI Model Configuration
# -----------------------------------------------------------------------------
MODELS_PATH=./models
HUGGINGFACE_CACHE_DIR=./models
SENTENCE_TRANSFORMERS_HOME=./models
MODELS_DEVICE=cpu  # Use 'cuda' if GPU available
MAX_SEQUENCE_LENGTH=512
BATCH_SIZE=32
MODEL_CACHE_TTL_HOURS=24

# Available Models (comma-separated)
SENTIMENT_MODELS=cardiffnlp/twitter-roberta-base-sentiment-latest,nlptown/bert-base-multilingual-uncased-sentiment
EMOTION_MODELS=j-hartmann/emotion-english-distilroberta-base
EMBEDDING_MODELS=sentence-transformers/all-MiniLM-L6-v2,sentence-transformers/all-mpnet-base-v2

# -----------------------------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------------------------
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
LOG_FILE=logs/app.log
LOG_MAX_SIZE_MB=50
LOG_BACKUP_COUNT=5
LOG_JSON_FORMAT=False

# -----------------------------------------------------------------------------
# File Upload Settings
# -----------------------------------------------------------------------------
MAX_UPLOAD_SIZE=10485760  # 10MB in bytes
ALLOWED_FILE_TYPES=["image/jpeg", "image/png", "image/gif", "text/plain"]
UPLOAD_PATH=./uploads
TEMP_PATH=./temp

# -----------------------------------------------------------------------------
# Rate Limiting
# -----------------------------------------------------------------------------
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_BURST=20
RATE_LIMIT_ENABLED=True

# -----------------------------------------------------------------------------
# Background Tasks
# -----------------------------------------------------------------------------
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
TASK_TIMEOUT_SECONDS=300
MAX_CONCURRENT_TASKS=5

# -----------------------------------------------------------------------------
# Monitoring and Health Checks
# -----------------------------------------------------------------------------
HEALTH_CHECK_INTERVAL_SECONDS=30
METRICS_ENABLED=True
PROMETHEUS_PORT=9090
```

### Production Configuration (.env.production)
```bash
# =============================================================================
# JOURNALING AI BACKEND - PRODUCTION CONFIGURATION
# =============================================================================

# -----------------------------------------------------------------------------
# Database Configuration (Production)
# -----------------------------------------------------------------------------
DATABASE_URL=postgresql://journaling_user:${DB_PASSWORD}@postgres-server:5432/journaling_ai
DB_HOST=postgres-server
DB_PORT=5432
DB_NAME=journaling_ai
DB_USER=journaling_user
DB_PASSWORD=${DB_PASSWORD}  # Set via environment or secrets
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=60
DB_ECHO=False
DB_SSL_MODE=require

# -----------------------------------------------------------------------------
# Redis Configuration (Production)
# -----------------------------------------------------------------------------
REDIS_URL=redis://:${REDIS_PASSWORD}@redis-server:6379/0
REDIS_HOST=redis-server
REDIS_PORT=6379
REDIS_PASSWORD=${REDIS_PASSWORD}  # Set via environment or secrets
REDIS_DB=0
REDIS_MAX_CONNECTIONS=50
REDIS_SSL=True

# -----------------------------------------------------------------------------
# Application Settings (Production)
# -----------------------------------------------------------------------------
PROJECT_NAME=Journaling AI Backend
API_V1_STR=/api/v1
SECRET_KEY=${SECRET_KEY}  # Must be 32+ character random string
DEBUG=False
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000

# -----------------------------------------------------------------------------
# Security Configuration (Production)
# -----------------------------------------------------------------------------
ACCESS_TOKEN_EXPIRE_MINUTES=30  # Shorter for production
REFRESH_TOKEN_EXPIRE_DAYS=7     # Shorter for production
ALGORITHM=HS256
PASSWORD_MIN_LENGTH=12          # Stronger password requirements
MAX_LOGIN_ATTEMPTS=3            # Stricter rate limiting
LOCKOUT_DURATION_MINUTES=30

# -----------------------------------------------------------------------------
# CORS Settings (Production)
# -----------------------------------------------------------------------------
ALLOWED_ORIGINS=["https://journaling-ai.com", "https://app.journaling-ai.com"]
ALLOWED_METHODS=["GET", "POST", "PUT", "DELETE", "PATCH"]
ALLOWED_HEADERS=["Content-Type", "Authorization", "X-Requested-With"]
ALLOW_CREDENTIALS=True

# -----------------------------------------------------------------------------
# AI Model Configuration (Production)
# -----------------------------------------------------------------------------
MODELS_PATH=/app/models
MODELS_DEVICE=cuda  # Use GPU in production if available
MAX_SEQUENCE_LENGTH=512
BATCH_SIZE=64       # Larger batch size for production efficiency
MODEL_CACHE_TTL_HOURS=168  # 1 week cache

# -----------------------------------------------------------------------------
# Logging Configuration (Production)
# -----------------------------------------------------------------------------
LOG_LEVEL=WARNING
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
LOG_FILE=/var/log/journaling-ai/app.log
LOG_MAX_SIZE_MB=100
LOG_BACKUP_COUNT=10
LOG_JSON_FORMAT=True  # Structured logging for production

# -----------------------------------------------------------------------------
# Performance Settings (Production)
# -----------------------------------------------------------------------------
WORKERS=4  # Number of Gunicorn workers
WORKER_CONNECTIONS=1000
WORKER_CLASS=uvicorn.workers.UvicornWorker
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=100

# -----------------------------------------------------------------------------
# Monitoring (Production)
# -----------------------------------------------------------------------------
SENTRY_DSN=${SENTRY_DSN}  # Error tracking
METRICS_ENABLED=True
PROMETHEUS_PORT=9090
HEALTH_CHECK_INTERVAL_SECONDS=15
```

### Testing Configuration (.env.test)
```bash
# =============================================================================
# JOURNALING AI BACKEND - TESTING CONFIGURATION
# =============================================================================

# Test Database (Separate from development)
DATABASE_URL=postgresql://test_user:test_password@localhost/journaling_ai_test
DB_HOST=localhost
DB_PORT=5432
DB_NAME=journaling_ai_test
DB_USER=test_user
DB_PASSWORD=test_password

# Test Redis
REDIS_URL=redis://localhost:6379/15  # Use different DB for tests
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=15

# Application Settings
PROJECT_NAME=Journaling AI Backend (Test)
SECRET_KEY=test-secret-key-not-for-production
DEBUG=True
ENVIRONMENT=test

# Disable external services in tests
MODELS_DEVICE=cpu
MODEL_CACHE_TTL_HOURS=1
BACKGROUND_TASKS_ENABLED=False
RATE_LIMIT_ENABLED=False

# Logging
LOG_LEVEL=ERROR  # Reduce noise in tests
LOG_FILE=tests/test.log
```

## Configuration Management

### Environment-Specific Loading
```python
# app/core/config.py
import os
from typing import List, Optional
from pydantic import BaseSettings, validator
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with environment-based configuration."""
    
    # Database settings
    DATABASE_URL: str
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "journaling_ai"
    DB_USER: str = "journaling_user"
    DB_PASSWORD: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False
    
    # Redis settings
    REDIS_URL: str
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_MAX_CONNECTIONS: int = 20
    
    # Application settings
    PROJECT_NAME: str = "Journaling AI Backend"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = ["*"]
    ALLOW_CREDENTIALS: bool = True
    
    # AI Model settings
    MODELS_PATH: str = "./models"
    HUGGINGFACE_CACHE_DIR: str = "./models"
    SENTENCE_TRANSFORMERS_HOME: str = "./models"
    MODELS_DEVICE: str = "cpu"
    MAX_SEQUENCE_LENGTH: int = 512
    BATCH_SIZE: int = 32
    MODEL_CACHE_TTL_HOURS: int = 24
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "logs/app.log"
    LOG_MAX_SIZE_MB: int = 50
    LOG_BACKUP_COUNT: int = 5
    LOG_JSON_FORMAT: bool = False
    
    # File upload settings
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_FILE_TYPES: List[str] = ["image/jpeg", "image/png", "text/plain"]
    UPLOAD_PATH: str = "./uploads"
    TEMP_PATH: str = "./temp"
    
    # Rate limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    RATE_LIMIT_BURST: int = 20
    RATE_LIMIT_ENABLED: bool = True
    
    # Monitoring
    HEALTH_CHECK_INTERVAL_SECONDS: int = 30
    METRICS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090
    SENTRY_DSN: Optional[str] = None
    
    @validator('SECRET_KEY', pre=True)
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters long')
        return v
    
    @validator('ALLOWED_ORIGINS', pre=True)
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "test"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    env_file = ".env"
    
    # Load environment-specific file if available
    if os.getenv("ENVIRONMENT") == "production":
        env_file = ".env.production"
    elif os.getenv("ENVIRONMENT") == "test":
        env_file = ".env.test"
    
    return Settings(_env_file=env_file)

# Global settings instance
settings = get_settings()
```

### Dynamic Configuration Loading
```python
# app/core/config_loader.py
import os
import json
from typing import Dict, Any
from pathlib import Path

class ConfigLoader:
    """Dynamic configuration loader for runtime settings."""
    
    def __init__(self):
        self.config_dir = Path("config")
        self.config_cache = {}
    
    def load_model_config(self) -> Dict[str, Any]:
        """Load AI model configuration."""
        config_file = self.config_dir / "models.json"
        
        if config_file.exists():
            with open(config_file) as f:
                return json.load(f)
        
        # Default model configuration
        return {
            "sentiment_models": [
                {
                    "name": "cardiffnlp/twitter-roberta-base-sentiment-latest",
                    "type": "sentiment",
                    "enabled": True,
                    "cache_embeddings": True
                },
                {
                    "name": "nlptown/bert-base-multilingual-uncased-sentiment",
                    "type": "sentiment",
                    "enabled": True,
                    "languages": ["multi"]
                }
            ],
            "embedding_models": [
                {
                    "name": "sentence-transformers/all-MiniLM-L6-v2",
                    "type": "embedding",
                    "dimension": 384,
                    "enabled": True
                },
                {
                    "name": "sentence-transformers/all-mpnet-base-v2",
                    "type": "embedding",
                    "dimension": 768,
                    "enabled": True
                }
            ]
        }
    
    def load_feature_flags(self) -> Dict[str, bool]:
        """Load feature flags from configuration."""
        config_file = self.config_dir / "features.json"
        
        if config_file.exists():
            with open(config_file) as f:
                return json.load(f)
        
        # Default feature flags
        return {
            "advanced_analytics": True,
            "psychology_insights": True,
            "export_functionality": True,
            "social_features": False,
            "premium_models": False
        }
    
    def load_database_config(self) -> Dict[str, Any]:
        """Load database-specific configuration."""
        return {
            "connection_pool": {
                "min_size": 5,
                "max_size": 20,
                "timeout": 30
            },
            "query_timeout": 30,
            "statement_timeout": "60s",
            "idle_timeout": "10min",
            "retries": 3
        }

# Global config loader instance
config_loader = ConfigLoader()
```

## Security Configuration

### JWT Configuration
```python
# app/core/security.py
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext

class SecurityConfig:
    """Security configuration and utilities."""
    
    def __init__(self, settings):
        self.settings = settings
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire, "type": "access"})
        
        return jwt.encode(
            to_encode, 
            self.settings.SECRET_KEY, 
            algorithm=self.settings.ALGORITHM
        )
    
    def create_refresh_token(self, data: dict):
        """Create JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(
            days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        to_encode.update({"exp": expire, "type": "refresh"})
        
        return jwt.encode(
            to_encode,
            self.settings.SECRET_KEY,
            algorithm=self.settings.ALGORITHM
        )
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return self.pwd_context.hash(password)
```

### Rate Limiting Configuration
```python
# app/middleware/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis
from app.core.config import settings

# Redis-backed rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,
    default_limits=[f"{settings.RATE_LIMIT_REQUESTS_PER_MINUTE}/minute"]
)

# Custom rate limiting strategies
class RateLimitConfig:
    """Rate limiting configuration for different endpoints."""
    
    LIMITS = {
        "auth": "5/minute",      # Authentication endpoints
        "upload": "10/hour",     # File upload endpoints
        "ai": "20/minute",       # AI processing endpoints
        "api": "100/minute",     # General API endpoints
        "health": "1000/minute"  # Health check endpoints
    }
    
    @classmethod
    def get_limit(cls, endpoint_type: str) -> str:
        """Get rate limit for endpoint type."""
        return cls.LIMITS.get(endpoint_type, "100/minute")
```

## Database Configuration

### Connection Pool Configuration
```python
# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

def create_database_engine():
    """Create database engine with optimized settings."""
    
    connect_args = {
        "server_settings": {
            "application_name": f"{settings.PROJECT_NAME}_{settings.ENVIRONMENT}",
            "jit": "off"
        }
    }
    
    # Add SSL configuration for production
    if settings.is_production:
        connect_args["ssl"] = "require"
    
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DB_ECHO,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=1800,  # Recycle connections every 30 minutes
        pool_pre_ping=True,  # Validate connections before use
        connect_args=connect_args
    )
    
    return engine

# Session factory
async_session_factory = sessionmaker(
    bind=create_database_engine(),
    class_=AsyncSession,
    expire_on_commit=False
)
```

### Redis Configuration
```python
# app/core/redis.py
import redis.asyncio as redis
from app.core.config import settings

class RedisConfig:
    """Redis configuration and connection management."""
    
    def __init__(self):
        self.settings = settings
        self._connection_pool = None
    
    async def get_connection_pool(self):
        """Get Redis connection pool."""
        if not self._connection_pool:
            self._connection_pool = redis.ConnectionPool.from_url(
                self.settings.REDIS_URL,
                max_connections=self.settings.REDIS_MAX_CONNECTIONS,
                retry_on_timeout=True,
                health_check_interval=30
            )
        return self._connection_pool
    
    async def get_redis_client(self):
        """Get Redis client with connection pool."""
        pool = await self.get_connection_pool()
        return redis.Redis(connection_pool=pool)

# Global Redis configuration
redis_config = RedisConfig()
```

## Logging Configuration

### Structured Logging Setup
```python
# app/core/logging.py
import logging
import logging.handlers
import json
from datetime import datetime
from typing import Dict, Any
from app.core.config import settings

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'duration'):
            log_entry['duration'] = record.duration
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)

def setup_logging():
    """Configure application logging."""
    
    # Create logs directory
    import os
    os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Remove default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=settings.LOG_MAX_SIZE_MB * 1024 * 1024,
        backupCount=settings.LOG_BACKUP_COUNT
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    
    # Choose formatter based on configuration
    if settings.LOG_JSON_FORMAT:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(settings.LOG_FORMAT)
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    
    return root_logger

# Setup logging on import
logger = setup_logging()
```

## Monitoring Configuration

### Health Check Configuration
```python
# app/api/health.py
from typing import Dict
import time
import psutil
from app.core.config import settings
from app.core.database import async_session_factory
from app.core.redis import redis_config

class HealthChecker:
    """Health check configuration and utilities."""
    
    async def check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            start_time = time.time()
            
            async with async_session_factory() as session:
                result = await session.execute("SELECT 1")
                await result.fetchone()
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance."""
        try:
            start_time = time.time()
            
            redis_client = await redis_config.get_redis_client()
            await redis_client.ping()
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }

health_checker = HealthChecker()
```

## Environment-Specific Overrides

### Docker Configuration
```dockerfile
# Dockerfile with configuration support
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV MODELS_PATH=/app/models
ENV LOG_FILE=/var/log/journaling-ai/app.log

# Create application user
RUN useradd --create-home --shell /bin/bash app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /var/log/journaling-ai /app/models /app/uploads \
    && chown -R app:app /app /var/log/journaling-ai

# Switch to application user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["python", "run.py"]
```

### Kubernetes Configuration
```yaml
# k8s-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: journaling-ai-config
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  MODELS_DEVICE: "cpu"
  RATE_LIMIT_ENABLED: "true"
---
apiVersion: v1
kind: Secret
metadata:
  name: journaling-ai-secrets
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:password@postgres:5432/journaling_ai"
  SECRET_KEY: "your-super-secret-production-key"
  REDIS_PASSWORD: "your-redis-password"
```

---

**Document Version**: 1.0  
**Last Updated**: August 5, 2025  
**Review Date**: September 5, 2025  
**Owner**: DevOps Configuration Team
