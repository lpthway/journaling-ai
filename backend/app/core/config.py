# backend/app/core/config.py - Enterprise PostgreSQL Configuration

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional, List, Dict, Any
from pathlib import Path
import os

class DatabaseSettings(BaseSettings):
    """Database configuration with PostgreSQL optimization."""
    
    # Connection settings
    url: str = Field(
        default_factory=lambda: os.getenv(
            "DB_URL", 
            "postgresql+asyncpg://postgres:secure_password@localhost:5432/journaling_ai"
        ),
        description="PostgreSQL connection URL"
    )
    
    # Connection pool settings
    pool_size: int = Field(default=20, ge=1, le=100)
    max_overflow: int = Field(default=0, ge=0, le=50)  
    pool_timeout: int = Field(default=30, ge=1, le=300)
    pool_recycle: int = Field(default=3600, ge=300, le=86400)
    pool_pre_ping: bool = Field(default=True)
    
    # Query settings
    query_timeout: int = Field(default=30, ge=1, le=300)
    statement_timeout: int = Field(default=60, ge=1, le=600)
    
    # Development settings
    echo: bool = Field(default=False)
    echo_pool: bool = Field(default=False)
    
    class Config:
        env_prefix = "DB_"

class RedisSettings(BaseSettings):
    """Redis configuration for caching and sessions."""
    
    url: str = Field(
        default_factory=lambda: os.getenv(
            "REDIS_URL", 
            "redis://:password@localhost:6379/0"  # Match docker-compose.yml password
        ),
        description="Redis connection URL"
    )
    password: Optional[str] = Field(
        default_factory=lambda: os.getenv("REDIS_PASSWORD", "password")  # Match docker-compose.yml
    )
    db: int = Field(default=0, ge=0, le=15)
    
    # Connection pool settings
    max_connections: int = Field(default=20, ge=1, le=100)
    retry_on_timeout: bool = Field(default=True)
    health_check_interval: int = Field(default=30, ge=10, le=300)
    
    class Config:
        env_prefix = "REDIS_"

class SecuritySettings(BaseSettings):
    """Security and authentication configuration."""
    
    # JWT settings
    secret_key: str = Field(
        default_factory=lambda: os.getenv(
            "SECURITY_SECRET_KEY", 
            "change-this-secret-key-in-production-environment"
        ),
        description="Secret key for JWT tokens"
    )
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=1440, ge=15, le=10080)  # 24 hours default
    
    # Password settings
    password_min_length: int = Field(default=8, ge=6, le=128)
    password_require_uppercase: bool = Field(default=True)
    password_require_lowercase: bool = Field(default=True)
    password_require_numbers: bool = Field(default=True)
    
    class Config:
        env_prefix = "SECURITY_"

class Settings(BaseSettings):
    """Main application settings with enhanced enterprise features."""
    
    # Application
    PROJECT_NAME: str = "Local Journaling Assistant"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Enhanced Database Configuration
    database: DatabaseSettings = DatabaseSettings()
    
    # Redis Configuration
    redis: RedisSettings = RedisSettings()
    
    # Security Configuration
    security: SecuritySettings = SecuritySettings()
    
    # Legacy database settings (for backward compatibility)
    DATABASE_URL: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL", 
            "postgresql+asyncpg://postgres:password@localhost:5432/journaling_ai"
        )
    )
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10  # Allow overflow for better performance
    DB_POOL_RECYCLE: int = 3600
    DB_COMMAND_TIMEOUT: int = 30
    DB_ECHO: bool = False
    DB_ECHO_POOL: bool = False
    
    # Performance Targets
    DB_PERFORMANCE_TARGET_MS: int = 50
    DB_SLOW_QUERY_THRESHOLD: float = 0.1
    
    # Migration Configuration
    ENABLE_DUAL_WRITE: bool = True
    JSON_DATA_PATH: str = "data"
    MIGRATION_BATCH_SIZE: int = 1000
    MIGRATION_VALIDATION_ENABLED: bool = True
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
        # === AI MODEL CONFIGURATION ===
    # Note: Models are now selected automatically based on hardware capabilities
    # See app/services/hardware_service.py for adaptive model selection
    
    # LLM Configuration (Ollama on host)
    OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
    OLLAMA_MODEL: str = "llama3.2"
    
    # Fallback model configurations (used if hardware detection fails)
    # Embedding Model
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Sentiment Analysis Model
    SENTIMENT_MODEL: str = "j-hartmann/emotion-english-distilroberta-base"
    
    # Vector Search
    VECTOR_SIMILARITY_THRESHOLD: float = 0.7
    VECTOR_SEARCH_LIMIT: int = 50
    
    # === EXTERNAL APIS ===
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # === CACHING & PERFORMANCE ===
    REDIS_URL: str = Field(
        default_factory=lambda: os.getenv(
            "REDIS_URL", 
            "redis://:password@localhost:6379/0"  # Match docker-compose.yml password
        ),
        description="Redis connection URL with authentication for Docker Redis"
    )
    ANALYTICS_CACHE_ENABLED: bool = True
    ANALYTICS_CACHE_TTL: int = 3600
    
    # Background Tasks
    BACKGROUND_TASKS_ENABLED: bool = True
    CELERY_BROKER_URL: str = Field(
        default_factory=lambda: os.getenv(
            "CELERY_BROKER_URL", 
            "redis://:password@localhost:6379/0"  # Match docker-compose.yml password
        ),
        description="Celery broker URL with authentication for Docker Redis"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default_factory=lambda: os.getenv(
            "CELERY_RESULT_BACKEND", 
            "redis://:password@localhost:6379/0"  # Match docker-compose.yml password
        ),
        description="Celery result backend with authentication for Docker Redis"
    )
    
    # === LOGGING & MONITORING ===
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60
    
    # === FILE STORAGE ===
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".txt", ".md", ".pdf"]
    
    # === VECTOR DATABASE (ChromaDB) ===
    CHROMA_PERSIST_DIRECTORY: str = Field(
        default="./data/chroma_db",
        description="ChromaDB persistence directory for vector storage"
    )
    CHROMA_COLLECTION_NAME: str = "journal_entries"
    
    # Psychology Integration
    PSYCHOLOGY_DB_ENABLED: bool = True
    PSYCHOLOGY_CONTENT_PATH: str = "data/psychology_db"
    
    # Validation for production
    @validator('security')
    def validate_security_settings(cls, v, values):
        """Validate security settings for production."""
        if values.get('ENVIRONMENT') == 'production':
            if v.secret_key == "change-this-secret-key-in-production-environment":
                raise ValueError("Secret key must be changed for production")
        return v
    
    @validator('DEBUG')
    def validate_debug_mode(cls, v, values):
        """Validate debug mode for production."""
        if values.get('ENVIRONMENT') == 'production' and v:
            raise ValueError("Debug mode must be disabled in production")
        return v
    
    class Config:
        case_sensitive = True
        env_file = None  # Remove .env dependency

settings = Settings()

# Hardware-Adaptive Model Performance Info
# Models are automatically selected based on your hardware capabilities
MODEL_SPECS = {
    "RTX_3500_Ada_Optimal": {
        "embedding_model": "intfloat/multilingual-e5-large",
        "emotion_model": "microsoft/DialoGPT-medium", 
        "sentiment_model": "microsoft/deberta-v3-base",
        "classification_model": "microsoft/deberta-v2-xlarge-mnli",
        "gpu_memory_required": "8GB+",
        "performance_gain": "5-10x faster",
        "why_chosen": "Optimized for RTX 3500 Ada with 12GB VRAM - enterprise-tier models"
    },
    "fallback_cpu": {
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "emotion_model": "j-hartmann/emotion-english-distilroberta-base", 
        "sentiment_model": "cardiffnlp/twitter-roberta-base-sentiment-latest",
        "classification_model": "facebook/bart-large-mnli",
        "gpu_memory_required": "0GB",
        "performance_gain": "baseline",
        "why_chosen": "CPU-optimized lightweight models for compatibility"
    },
    "llm_service": {
        "model": "llama3.2",
        "inference_engine": "ollama",
        "deployment": "host_gpu",
        "why_chosen": "Host GPU deployment for maximum LLM performance"
    }
}