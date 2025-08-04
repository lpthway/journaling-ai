# backend/app/core/config.py
"""
Application configuration with PostgreSQL database settings.

Supports multiple environments (development, staging, production)  
with secure credential management and feature flags.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional, List, Dict, Any
from pathlib import Path
import os

class DatabaseSettings(BaseSettings):
    """Database configuration with PostgreSQL optimization."""
    
    # Connection settings
    url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/journaling_assistant",
        description="PostgreSQL connection URL"
    )
    
    # Connection pool settings
    pool_size: int = Field(default=20, ge=1, le=100)
    max_overflow: int = Field(default=10, ge=0, le=50)  
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
        default="redis://localhost:6379",
        description="Redis connection URL"
    )
    password: Optional[str] = Field(default=None)
    db: int = Field(default=0, ge=0, le=15)
    
    # Connection pool settings
    max_connections: int = Field(default=20, ge=1, le=100)
    retry_on_timeout: bool = Field(default=True)
    health_check_interval: int = Field(default=30, ge=10, le=300)
    
    class Config:
        env_prefix = "REDIS_"

class AISettings(BaseSettings):
    """AI service configuration."""
    
    # OpenAI settings
    openai_api_key: Optional[str] = Field(default=None)
    openai_model: str = Field(default="gpt-3.5-turbo")
    openai_max_tokens: int = Field(default=1000, ge=100, le=4000)
    openai_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    
    # Anthropic settings  
    anthropic_api_key: Optional[str] = Field(default=None)
    anthropic_model: str = Field(default="claude-3-sonnet-20240229")
    
    # Rate limiting
    max_requests_per_minute: int = Field(default=60, ge=1, le=1000)
    max_tokens_per_day: int = Field(default=100000, ge=1000, le=1000000)
    
    # Feature flags
    enable_sentiment_analysis: bool = Field(default=True)
    enable_mood_detection: bool = Field(default=True)
    enable_psychology_insights: bool = Field(default=True)
    
    class Config:
        env_prefix = "AI_"

class SecuritySettings(BaseSettings):
    """Security and authentication configuration."""
    
    # JWT settings
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT tokens"
    )
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=1440, ge=15, le=10080)  # 24 hours default
    
    # Password settings
    password_min_length: int = Field(default=8, ge=6, le=128)
    password_require_uppercase: bool = Field(default=True)
    password_require_lowercase: bool = Field(default=True)
    password_require_numbers: bool = Field(default=True)
    password_require_special: bool = Field(default=True)
    
    # Rate limiting
    login_rate_limit: int = Field(default=5, ge=1, le=20)  # attempts per minute
    api_rate_limit: int = Field(default=1000, ge=100, le=10000)  # requests per hour
    
    # CORS settings
    cors_origins: List[str] = Field(default=["http://localhost:3000", "http://localhost:8080"])
    cors_methods: List[str] = Field(default=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    cors_headers: List[str] = Field(default=["*"])
    
    class Config:
        env_prefix = "SECURITY_"

class LoggingSettings(BaseSettings):
    """Logging configuration."""
    
    level: str = Field(default="INFO", regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # File logging
    enable_file_logging: bool = Field(default=True)
    log_file: str = Field(default="logs/app.log")
    max_file_size: int = Field(default=10485760, ge=1048576, le=104857600)  # 10MB default
    backup_count: int = Field(default=5, ge=1, le=20)
    
    # Structured logging
    enable_json_logging: bool = Field(default=False)
    enable_request_logging: bool = Field(default=True)
    enable_db_query_logging: bool = Field(default=False)
    
    # External logging
    sentry_dsn: Optional[str] = Field(default=None)
    log_to_stdout: bool = Field(default=True)
    
    class Config:
        env_prefix = "LOG_"

class ApplicationSettings(BaseSettings):
    """Main application configuration."""
    
    # Basic app info
    name: str = Field(default="Journaling Assistant")
    version: str = Field(default="1.0.0")
    description: str = Field(default="AI-powered journaling and mental health companion")
    
    # Environment
    environment: str = Field(default="development", regex="^(development|staging|production)$")
    debug: bool = Field(default=True)
    testing: bool = Field(default=False)
    
    # Server settings
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1024, le=65535)
    workers: int = Field(default=1, ge=1, le=16)
    
    # API settings
    api_v1_prefix: str = Field(default="/api/v1")
    docs_url: str = Field(default="/docs")
    redoc_url: str = Field(default="/redoc")
    openapi_url: str = Field(default="/openapi.json")
    
    # File handling
    max_upload_size: int = Field(default=10485760, ge=1048576, le=104857600)  # 10MB
    allowed_file_types: List[str] = Field(default=["json", "txt", "csv", "pdf"])
    data_directory: str = Field(default="./data")
    backup_directory: str = Field(default="./backups")
    
    # Feature flags
    enable_web_interface: bool = Field(default=True)
    enable_api_docs: bool = Field(default=True)
    enable_metrics: bool = Field(default=True)
    enable_health_checks: bool = Field(default=True)
    enable_background_tasks: bool = Field(default=True)
    
    # Monitoring
    prometheus_metrics: bool = Field(default=True)
    health_check_interval: int = Field(default=30, ge=10, le=300)
    
    @validator('environment')
    def validate_environment(cls, v):
        if v == 'production':
            # Additional production validations can be added here
            pass
        return v
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def is_staging(self) -> bool:
        return self.environment == "staging"

class MigrationSettings(BaseSettings):
    """Database migration configuration."""
    
    # Source data settings
    source_data_dir: str = Field(default="./data")
    backup_before_migration: bool = Field(default=True)
    backup_directory: str = Field(default="./backups")
    
    # Migration settings
    batch_size: int = Field(default=1000, ge=100, le=10000)
    validate_before_migrate: bool = Field(default=True)
    enable_progress_tracking: bool = Field(default=True)
    
    # Safety settings
    max_retry_attempts: int = Field(default=3, ge=1, le=10)
    rollback_on_failure: bool = Field(default=True)
    create_migration_log: bool = Field(default=True)
    
    class Config:
        env_prefix = "MIGRATION_"

class Settings(BaseSettings):
    """Main settings class combining all configuration sections."""
    
    # Core settings
    app: ApplicationSettings = ApplicationSettings()
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    ai: AISettings = AISettings()
    security: SecuritySettings = SecuritySettings()
    logging: LoggingSettings = LoggingSettings()
    migration: MigrationSettings = MigrationSettings()
    
    class Config:
        env_file = [".env.local", ".env"]
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()
        self._validate_production_settings()
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        directories = [
            self.app.data_directory,
            self.app.backup_directory,
            self.migration.backup_directory,
            Path(self.logging.log_file).parent
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _validate_production_settings(self):
        """Validate settings for production environment."""
        if self.app.is_production:
            if self.security.secret_key == "your-secret-key-change-in-production":
                raise ValueError("Secret key must be changed for production")
            
            if self.app.debug:
                raise ValueError("Debug mode must be disabled in production")
            
            if self.database.echo or self.database.echo_pool:
                raise ValueError("Database echo must be disabled in production")
    
    @property
    def database_url(self) -> str:
        """Get the database URL."""
        return self.database.url
    
    @property
    def redis_url(self) -> str:
        """Get the Redis URL."""
        if self.redis.password:
            # Insert password into URL
            url_parts = self.redis.url.split('://')
            return f"{url_parts[0]}://:{self.redis.password}@{url_parts[1]}"
        return self.redis.url

# Global settings instance
settings = Settings()

# Environment-specific configurations
def get_development_settings() -> Settings:
    """Get development-specific settings."""
    return Settings(
        app=ApplicationSettings(
            environment="development",
            debug=True,
            enable_api_docs=True
        ),
        database=DatabaseSettings(
            echo=True,
            pool_size=5
        ),
        logging=LoggingSettings(
            level="DEBUG",
            enable_db_query_logging=True
        )
    )

def get_production_settings() -> Settings:
    """Get production-specific settings."""
    return Settings(
        app=ApplicationSettings(
            environment="production",
            debug=False,
            enable_api_docs=False
        ),
        database=DatabaseSettings(
            echo=False,
            pool_size=20,
            max_overflow=10
        ),
        logging=LoggingSettings(
            level="INFO",
            enable_json_logging=True,
            enable_db_query_logging=False
        ),
        security=SecuritySettings(
            cors_origins=["https://yourdomain.com"]
        )
    )

def get_test_settings() -> Settings:
    """Get test-specific settings."""
    return Settings(
        app=ApplicationSettings(
            environment="development",
            testing=True,
            debug=True
        ),
        database=DatabaseSettings(
            url="postgresql+asyncpg://postgres:password@localhost:5432/journaling_test",
            echo=False,
            pool_size=1
        ),
        logging=LoggingSettings(
            level="WARNING",
            enable_file_logging=False
        )
    )