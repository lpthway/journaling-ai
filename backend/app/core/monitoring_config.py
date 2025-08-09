# backend/app/core/monitoring_config.py
"""
Monitoring Configuration and Setup
Centralized configuration for monitoring, logging, and observability features
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path

try:
    from pydantic_settings import BaseSettings
    from pydantic import Field
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings, Field

class MonitoringSettings(BaseSettings):
    """Monitoring configuration settings"""
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="structured", description="Log format (structured/simple/detailed)")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    enable_console_logging: bool = Field(default=True, description="Enable console logging")
    
    # Request Tracing Configuration
    enable_request_tracing: bool = Field(default=True, description="Enable request tracing")
    enable_detailed_request_logging: bool = Field(default=True, description="Enable detailed request logging")
    max_trace_history: int = Field(default=1000, description="Maximum number of traces to keep in memory")
    
    # Performance Monitoring Configuration
    enable_performance_monitoring: bool = Field(default=True, description="Enable performance monitoring")
    performance_monitoring_interval: int = Field(default=60, description="Performance monitoring interval in seconds")
    
    # Performance Targets
    cache_hit_rate_target: float = Field(default=0.80, description="Cache hit rate target (80%)")
    redis_response_time_target_ms: float = Field(default=5.0, description="Redis response time target in ms")
    session_retrieval_time_target_ms: float = Field(default=10.0, description="Session retrieval time target in ms")
    db_query_time_target_ms: float = Field(default=50.0, description="Database query time target in ms")
    psychology_cache_time_target_ms: float = Field(default=2.0, description="Psychology cache time target in ms")
    
    # Alert Thresholds
    error_rate_warning_threshold: float = Field(default=0.05, description="Error rate warning threshold (5%)")
    error_rate_critical_threshold: float = Field(default=0.10, description="Error rate critical threshold (10%)")
    response_time_warning_threshold_ms: float = Field(default=1000, description="Response time warning threshold in ms")
    cpu_usage_threshold: float = Field(default=80.0, description="CPU usage threshold (%)")
    memory_usage_threshold: float = Field(default=85.0, description="Memory usage threshold (%)")
    
    # Retention Settings
    metrics_retention_hours: int = Field(default=24, description="Metrics retention in hours")
    trace_retention_hours: int = Field(default=1, description="Trace retention in hours")
    log_retention_days: int = Field(default=7, description="Log retention in days")
    
    # External Monitoring Integration
    enable_prometheus_metrics: bool = Field(default=False, description="Enable Prometheus metrics export")
    prometheus_metrics_port: int = Field(default=8001, description="Prometheus metrics port")
    
    enable_jaeger_tracing: bool = Field(default=False, description="Enable Jaeger distributed tracing")
    jaeger_agent_host: str = Field(default="localhost", description="Jaeger agent hostname")
    jaeger_agent_port: int = Field(default=6831, description="Jaeger agent port")
    
    # Health Check Configuration
    health_check_timeout_seconds: int = Field(default=30, description="Health check timeout")
    detailed_health_checks: bool = Field(default=True, description="Enable detailed health checks")
    
    class Config:
        env_prefix = "MONITORING_"
        case_sensitive = False

# Global settings instance
monitoring_settings = MonitoringSettings()

def get_monitoring_config() -> Dict[str, Any]:
    """Get complete monitoring configuration"""
    return {
        "logging": {
            "level": monitoring_settings.log_level,
            "format": monitoring_settings.log_format,
            "file": monitoring_settings.log_file,
            "console_enabled": monitoring_settings.enable_console_logging,
            "retention_days": monitoring_settings.log_retention_days
        },
        "tracing": {
            "enabled": monitoring_settings.enable_request_tracing,
            "detailed_logging": monitoring_settings.enable_detailed_request_logging,
            "max_history": monitoring_settings.max_trace_history,
            "retention_hours": monitoring_settings.trace_retention_hours
        },
        "performance": {
            "monitoring_enabled": monitoring_settings.enable_performance_monitoring,
            "monitoring_interval": monitoring_settings.performance_monitoring_interval,
            "targets": {
                "cache_hit_rate": monitoring_settings.cache_hit_rate_target,
                "redis_response_time_ms": monitoring_settings.redis_response_time_target_ms,
                "session_retrieval_time_ms": monitoring_settings.session_retrieval_time_target_ms,
                "db_query_time_ms": monitoring_settings.db_query_time_target_ms,
                "psychology_cache_time_ms": monitoring_settings.psychology_cache_time_target_ms
            },
            "retention_hours": monitoring_settings.metrics_retention_hours
        },
        "alerts": {
            "error_rate_warning": monitoring_settings.error_rate_warning_threshold,
            "error_rate_critical": monitoring_settings.error_rate_critical_threshold,
            "response_time_warning_ms": monitoring_settings.response_time_warning_threshold_ms,
            "cpu_threshold": monitoring_settings.cpu_usage_threshold,
            "memory_threshold": monitoring_settings.memory_usage_threshold
        },
        "health_checks": {
            "timeout_seconds": monitoring_settings.health_check_timeout_seconds,
            "detailed_enabled": monitoring_settings.detailed_health_checks
        },
        "external": {
            "prometheus": {
                "enabled": monitoring_settings.enable_prometheus_metrics,
                "port": monitoring_settings.prometheus_metrics_port
            },
            "jaeger": {
                "enabled": monitoring_settings.enable_jaeger_tracing,
                "agent_host": monitoring_settings.jaeger_agent_host,
                "agent_port": monitoring_settings.jaeger_agent_port
            }
        }
    }

def create_monitoring_directories():
    """Create necessary directories for monitoring"""
    base_dir = Path("/var/log/journaling-ai")
    
    # Create log directories
    if monitoring_settings.log_file:
        log_path = Path(monitoring_settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        # Default log directory
        base_dir.mkdir(parents=True, exist_ok=True)
        (base_dir / "application.log").touch(exist_ok=True)
    
    # Create metrics directory
    metrics_dir = base_dir / "metrics"
    metrics_dir.mkdir(exist_ok=True)
    
    # Create traces directory
    traces_dir = base_dir / "traces"
    traces_dir.mkdir(exist_ok=True)

def get_log_file_path() -> str:
    """Get the appropriate log file path"""
    if monitoring_settings.log_file:
        return monitoring_settings.log_file
    
    # Default path based on environment
    environment = os.getenv("ENVIRONMENT", "development").lower()
    base_dir = Path("/var/log/journaling-ai")
    
    if environment == "production":
        return str(base_dir / "application.log")
    elif environment == "development":
        return str(Path.cwd() / "logs" / "application.log")
    else:
        return str(base_dir / f"{environment}.log")

def validate_configuration() -> Dict[str, Any]:
    """Validate monitoring configuration and return status"""
    validation_results = {
        "valid": True,
        "warnings": [],
        "errors": []
    }
    
    # Check log file accessibility
    if monitoring_settings.log_file:
        try:
            log_path = Path(monitoring_settings.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            # Test write access
            test_file = log_path.parent / "test_write.tmp"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            validation_results["errors"].append(f"Cannot access log directory: {e}")
            validation_results["valid"] = False
    
    # Check performance targets
    if monitoring_settings.cache_hit_rate_target > 1.0 or monitoring_settings.cache_hit_rate_target < 0.0:
        validation_results["warnings"].append("Cache hit rate target should be between 0.0 and 1.0")
    
    # Check thresholds
    if monitoring_settings.error_rate_critical_threshold <= monitoring_settings.error_rate_warning_threshold:
        validation_results["warnings"].append("Critical error rate threshold should be higher than warning threshold")
    
    # Check external service configuration
    if monitoring_settings.enable_prometheus_metrics:
        # Check if port is available (basic check)
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', monitoring_settings.prometheus_metrics_port)) == 0:
                validation_results["warnings"].append(f"Prometheus port {monitoring_settings.prometheus_metrics_port} appears to be in use")
    
    return validation_results

# Environment-specific configuration presets
ENVIRONMENT_PRESETS = {
    "development": {
        "log_level": "DEBUG",
        "log_format": "detailed",
        "enable_console_logging": True,
        "log_file": None,
        "enable_detailed_request_logging": True,
        "performance_monitoring_interval": 30,
        "enable_prometheus_metrics": False,
        "enable_jaeger_tracing": False
    },
    "staging": {
        "log_level": "INFO",
        "log_format": "structured",
        "enable_console_logging": True,
        "log_file": "/var/log/journaling-ai/staging.log",
        "enable_detailed_request_logging": True,
        "performance_monitoring_interval": 60,
        "enable_prometheus_metrics": True,
        "enable_jaeger_tracing": True
    },
    "production": {
        "log_level": "INFO",
        "log_format": "structured",
        "enable_console_logging": False,
        "log_file": "/var/log/journaling-ai/application.log",
        "enable_detailed_request_logging": False,
        "performance_monitoring_interval": 60,
        "enable_prometheus_metrics": True,
        "enable_jaeger_tracing": True,
        "log_retention_days": 30,
        "metrics_retention_hours": 72
    }
}

def apply_environment_preset(environment: str = None):
    """Apply environment-specific configuration preset"""
    if not environment:
        environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment in ENVIRONMENT_PRESETS:
        preset = ENVIRONMENT_PRESETS[environment]
        
        # Update global settings with preset values
        for key, value in preset.items():
            if hasattr(monitoring_settings, key):
                setattr(monitoring_settings, key, value)

# Apply environment preset on import
apply_environment_preset()