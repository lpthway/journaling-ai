# backend/app/core/logging_config.py
"""
Structured Logging Configuration for Journaling AI Application
Provides centralized logging setup with structured output, log levels, and monitoring integration
"""

import logging
import logging.config
import json
import sys
import os
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

class StructuredJSONFormatter(logging.Formatter):
    """Custom formatter to output structured JSON logs"""
    
    def format(self, record):
        """Format log record as structured JSON"""
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "levelname", "levelno", "pathname",
                          "filename", "module", "exc_info", "exc_text", "stack_info",
                          "lineno", "funcName", "created", "msecs", "relativeCreated",
                          "thread", "threadName", "processName", "process", "message"]:
                log_obj[key] = value
        
        return json.dumps(log_obj, default=str)

class ContextFilter(logging.Filter):
    """Filter to add contextual information to log records"""
    
    def filter(self, record):
        """Add context information to log record"""
        record.service = "journaling-ai"
        record.environment = os.getenv("ENVIRONMENT", "development")
        record.version = os.getenv("APP_VERSION", "2.0.0")
        
        # Add request context if available (would be set by middleware)
        record.request_id = getattr(record, 'request_id', None)
        record.user_id = getattr(record, 'user_id', None)
        record.session_id = getattr(record, 'session_id', None)
        
        return True

def setup_logging(
    log_level: str = "INFO",
    log_format: str = "structured",
    log_file: Optional[str] = None,
    enable_console: bool = True
) -> None:
    """
    Setup comprehensive logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ('structured' for JSON, 'simple' for text)
        log_file: Optional log file path
        enable_console: Whether to enable console logging
    """
    
    # Ensure logs directory exists
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure formatters
    formatters = {
        "structured": {
            "()": StructuredJSONFormatter
        },
        "simple": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s"
        }
    }
    
    # Configure handlers
    handlers = {}
    
    if enable_console:
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": log_format,
            "stream": sys.stdout,
            "filters": ["context_filter"]
        }
    
    if log_file:
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": log_format,
            "filename": log_file,
            "maxBytes": 50 * 1024 * 1024,  # 50MB
            "backupCount": 5,
            "filters": ["context_filter"]
        }
        
        # Add error-specific log file
        handlers["error_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": log_format,
            "filename": str(Path(log_file).parent / "errors.log"),
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 3,
            "filters": ["context_filter"]
        }
    
    # Configure filters
    filters = {
        "context_filter": {
            "()": ContextFilter
        }
    }
    
    # Configure loggers
    loggers = {
        "": {  # Root logger
            "level": log_level,
            "handlers": list(handlers.keys()),
            "propagate": False
        },
        "app": {
            "level": log_level,
            "handlers": list(handlers.keys()),
            "propagate": False,
            "qualname": "app"
        },
        "sqlalchemy": {
            "level": "WARNING",  # Reduce SQLAlchemy noise
            "handlers": list(handlers.keys()),
            "propagate": False
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": list(handlers.keys()),
            "propagate": False
        },
        "fastapi": {
            "level": "INFO",
            "handlers": list(handlers.keys()),
            "propagate": False
        }
    }
    
    # Apply configuration
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "filters": filters,
        "handlers": handlers,
        "loggers": loggers
    }
    
    logging.config.dictConfig(logging_config)
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

def add_request_context(
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None
) -> logging.LoggerAdapter:
    """
    Create a logger adapter with request context
    
    Args:
        request_id: Unique request identifier
        user_id: User identifier
        session_id: Session identifier
        
    Returns:
        Logger adapter with context
    """
    logger = logging.getLogger("app")
    
    extra = {}
    if request_id:
        extra["request_id"] = request_id
    if user_id:
        extra["user_id"] = user_id
    if session_id:
        extra["session_id"] = session_id
    
    return logging.LoggerAdapter(logger, extra)

class LoggingMetrics:
    """Collect logging metrics for monitoring"""
    
    def __init__(self):
        self.log_counts = {
            "DEBUG": 0,
            "INFO": 0,
            "WARNING": 0,
            "ERROR": 0,
            "CRITICAL": 0
        }
        self.error_patterns = {}
    
    def record_log(self, level: str, message: str) -> None:
        """Record log event for metrics"""
        self.log_counts[level] = self.log_counts.get(level, 0) + 1
        
        if level in ["ERROR", "CRITICAL"]:
            # Track error patterns
            error_key = message.split(":")[0] if ":" in message else "unknown"
            self.error_patterns[error_key] = self.error_patterns.get(error_key, 0) + 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get logging metrics"""
        return {
            "log_counts": self.log_counts.copy(),
            "error_patterns": self.error_patterns.copy(),
            "total_logs": sum(self.log_counts.values()),
            "error_rate": (
                (self.log_counts.get("ERROR", 0) + self.log_counts.get("CRITICAL", 0))
                / max(sum(self.log_counts.values()), 1)
            )
        }

# Global metrics instance
logging_metrics = LoggingMetrics()

class MetricsHandler(logging.Handler):
    """Custom handler to collect logging metrics"""
    
    def emit(self, record):
        """Emit log record and collect metrics"""
        logging_metrics.record_log(record.levelname, record.getMessage())

def setup_production_logging():
    """Setup logging configuration optimized for production"""
    log_dir = Path("/var/log/journaling-ai")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    setup_logging(
        log_level="INFO",
        log_format="structured",
        log_file=str(log_dir / "application.log"),
        enable_console=False
    )

def setup_development_logging():
    """Setup logging configuration optimized for development"""
    setup_logging(
        log_level="DEBUG",
        log_format="detailed",
        log_file=None,
        enable_console=True
    )

# Auto-configure based on environment
def auto_configure():
    """Auto-configure logging based on environment"""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        setup_production_logging()
    elif environment == "testing":
        setup_logging(
            log_level="WARNING",
            log_format="simple",
            log_file=None,
            enable_console=True
        )
    else:
        setup_development_logging()

# Initialize logging on import
auto_configure()