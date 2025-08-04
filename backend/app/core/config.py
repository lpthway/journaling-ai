# backend/app/core/config.py - Enterprise PostgreSQL Configuration

from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "Local Journaling Assistant"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # === POSTGRESQL DATABASE CONFIGURATION ===
    # Primary Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/journaling_ai"
    
    # Database Pool Configuration (Enterprise-grade)
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 0
    DB_POOL_RECYCLE: int = 3600  # 1 hour
    DB_COMMAND_TIMEOUT: int = 30  # seconds
    DB_ECHO: bool = False
    DB_ECHO_POOL: bool = False
    
    # Performance Targets (<50ms for 95th percentile)
    DB_PERFORMANCE_TARGET_MS: int = 50
    DB_SLOW_QUERY_THRESHOLD: float = 0.1  # 100ms threshold
    
    # Migration Configuration (Dual-write pattern)
    ENABLE_DUAL_WRITE: bool = True  # Enable during migration period
    JSON_DATA_PATH: str = "data"
    MIGRATION_BATCH_SIZE: int = 1000
    MIGRATION_VALIDATION_ENABLED: bool = True
    
    # === AI MODEL CONFIGURATION ===
    # Ollama Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"  # ⬆️ UPGRADED: Newer, better reasoning
    
    # Vector Database Settings
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma_db"
    
    # Embedding Model - KEEP THIS! Perfect for German/English
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-large"  # ✅ EXCELLENT choice
    
    # Sentiment Analysis - UPGRADED for multilingual emotion detection
    SENTIMENT_MODEL: str = "j-hartmann/emotion-english-distilroberta-base"  # ⬆️ 6 emotions instead of 3
    
    # Vector Search
    VECTOR_SIMILARITY_THRESHOLD: float = 0.7
    VECTOR_SEARCH_LIMIT: int = 50
    
    # === EXTERNAL APIS ===
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # === CACHING & PERFORMANCE ===
    REDIS_URL: str = "redis://localhost:6379/0"
    ANALYTICS_CACHE_ENABLED: bool = True
    ANALYTICS_CACHE_TTL: int = 3600  # 1 hour
    
    # Background Tasks
    BACKGROUND_TASKS_ENABLED: bool = True
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # === LOGGING & MONITORING ===
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # === FILE STORAGE ===
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".txt", ".md", ".pdf"]
    
    # Psychology Integration
    PSYCHOLOGY_DB_ENABLED: bool = True
    PSYCHOLOGY_CONTENT_PATH: str = "data/psychology_db"
    
    class Config:
        case_sensitive = True
        # Remove .env file dependency - all config in this file
        env_file = None

settings = Settings()

# Model Performance Info
MODEL_SPECS = {
    "embedding": {
        "model": "intfloat/multilingual-e5-large",
        "size": "2.24GB",
        "languages": "100+ including German & English",
        "quality": "⭐⭐⭐⭐⭐ Excellent",
        "best_for": "Multilingual semantic search",
        "why_chosen": "Best multilingual embedding model available"
    },
    "sentiment": {
        "model": "j-hartmann/emotion-english-distilroberta-base", 
        "size": "255MB",
        "emotions": ["joy", "sadness", "anger", "fear", "surprise", "disgust"],
        "languages": "English (primary)",
        "upgrade_from": "3 sentiments → 6 detailed emotions",
        "alternative": "nlptown/bert-base-multilingual-uncased-sentiment (for German)"
    },
    "llm": {
        "model": "llama3.2",
        "improvement": "Better reasoning, updated knowledge",
        "languages": "Multilingual including German"
    }
}