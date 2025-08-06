# backend/app/tasks/maintenance.py
"""
Enterprise Maintenance and System Health Tasks for Phase 0C
Consolidated task coordinators that delegate to maintenance services
"""

import logging
from typing import Dict, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

from celery import current_app as celery_app
from app.core.service_interfaces import ServiceRegistry
from app.services.celery_service import monitored_task, TaskPriority, TaskCategory

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """System health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning" 
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class MaintenanceLevel(Enum):
    """Maintenance operation levels"""
    LIGHT = "light"
    STANDARD = "standard"
    DEEP = "deep"

@dataclass
class SystemResource:
    """System resource status"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    load_average: float

@dataclass
class MaintenanceResult:
    """Maintenance operation result"""
    operation: str
    status: HealthStatus
    cleaned_items: int
    performance_gain: float
    recommendations: list
    duration_seconds: float
    timestamp: datetime

# =============================================================================
# MAINTENANCE TASK COORDINATORS
# =============================================================================

@celery_app.task(bind=True)
@monitored_task(priority=TaskPriority.LOW, category=TaskCategory.MAINTENANCE)
def cleanup_expired_sessions(self) -> Dict[str, Any]:
    """
    Coordinate expired session cleanup
    Delegates to maintenance cleanup service
    """
    try:
        logger.info("Starting expired session cleanup coordination")
        
        # Get maintenance service
        service_registry = ServiceRegistry()
        maintenance_service = service_registry.get_service("maintenance_cleanup_service")
        
        # Delegate to service
        result = maintenance_service.cleanup_expired_sessions()
        
        logger.info(f"Session cleanup completed: {result.get('cleaned_count', 0)} sessions cleaned")
        return {
            "success": True,
            "operation": "session_cleanup",
            "cleaned_count": result.get("cleaned_count", 0),
            "performance_gain": result.get("performance_gain", 0.0),
            "recommendations": result.get("recommendations", []),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Session cleanup coordination failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "operation": "session_cleanup",
            "timestamp": datetime.utcnow().isoformat()
        }

@celery_app.task(bind=True)
@monitored_task(priority=TaskPriority.LOW, category=TaskCategory.MAINTENANCE)
def system_health_check(self) -> Dict[str, Any]:
    """
    Coordinate comprehensive system health assessment
    Delegates to health monitoring service
    """
    try:
        logger.info("Starting system health check coordination")
        
        # Get health monitoring service
        service_registry = ServiceRegistry()
        health_service = service_registry.get_service("health_monitoring_service")
        
        # Delegate to service
        health_report = health_service.perform_comprehensive_health_check()
        
        logger.info(f"Health check completed: {health_report.get('overall_status')} status")
        return {
            "success": True,
            "operation": "health_check",
            "overall_status": health_report.get("overall_status"),
            "health_score": health_report.get("health_score"),
            "component_statuses": health_report.get("component_statuses"),
            "recommendations": health_report.get("recommendations"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check coordination failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "operation": "health_check",
            "timestamp": datetime.utcnow().isoformat()
        }

@celery_app.task(bind=True)
@monitored_task(priority=TaskPriority.LOW, category=TaskCategory.MAINTENANCE)
def database_maintenance(self, maintenance_level: str = MaintenanceLevel.STANDARD.value) -> Dict[str, Any]:
    """
    Coordinate database maintenance operations
    Delegates to database maintenance service
    """
    try:
        logger.info(f"Starting database maintenance coordination (level: {maintenance_level})")
        
        # Get database maintenance service
        service_registry = ServiceRegistry()
        db_maintenance_service = service_registry.get_service("database_maintenance_service")
        
        # Delegate to service
        maintenance_result = db_maintenance_service.perform_maintenance(maintenance_level)
        
        logger.info(f"Database maintenance completed: {maintenance_result.get('operations_completed')} operations")
        return {
            "success": True,
            "operation": "database_maintenance",
            "maintenance_level": maintenance_level,
            "operations_completed": maintenance_result.get("operations_completed"),
            "performance_improvements": maintenance_result.get("performance_improvements"),
            "recommendations": maintenance_result.get("recommendations"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Database maintenance coordination failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "operation": "database_maintenance",
            "maintenance_level": maintenance_level,
            "timestamp": datetime.utcnow().isoformat()
        }

@celery_app.task(bind=True)
@monitored_task(priority=TaskPriority.LOW, category=TaskCategory.MAINTENANCE)
def optimize_system_performance(self, optimization_level: str = "standard") -> Dict[str, Any]:
    """
    Coordinate system performance optimization
    Delegates to performance optimization service
    """
    try:
        logger.info(f"Starting system optimization coordination (level: {optimization_level})")
        
        # Get performance optimization service
        service_registry = ServiceRegistry()
        optimization_service = service_registry.get_service("performance_optimization_service")
        
        # Delegate to service
        optimization_result = optimization_service.optimize_system_performance(optimization_level)
        
        logger.info(f"System optimization completed: {optimization_result.get('optimizations_applied')} optimizations applied")
        return {
            "success": True,
            "operation": "system_optimization",
            "optimization_level": optimization_level,
            "optimizations_applied": optimization_result.get("optimizations_applied"),
            "performance_gains": optimization_result.get("performance_gains"),
            "resource_improvements": optimization_result.get("resource_improvements"),
            "recommendations": optimization_result.get("recommendations"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"System optimization coordination failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "operation": "system_optimization",
            "optimization_level": optimization_level,
            "timestamp": datetime.utcnow().isoformat()
        }

@celery_app.task(bind=True)
@monitored_task(priority=TaskPriority.LOW, category=TaskCategory.MAINTENANCE)
def cache_maintenance(self) -> Dict[str, Any]:
    """
    Coordinate cache cleanup and optimization
    Delegates to cache maintenance service
    """
    try:
        logger.info("Starting cache maintenance coordination")
        
        # Get cache maintenance service
        service_registry = ServiceRegistry()
        cache_service = service_registry.get_service("cache_maintenance_service")
        
        # Delegate to service
        cache_result = cache_service.perform_cache_maintenance()
        
        logger.info(f"Cache maintenance completed: {cache_result.get('cleaned_entries')} entries cleaned")
        return {
            "success": True,
            "operation": "cache_maintenance",
            "cleaned_entries": cache_result.get("cleaned_entries"),
            "memory_freed": cache_result.get("memory_freed"),
            "hit_rate_improvement": cache_result.get("hit_rate_improvement"),
            "recommendations": cache_result.get("recommendations"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cache maintenance coordination failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "operation": "cache_maintenance",
            "timestamp": datetime.utcnow().isoformat()
        }

@celery_app.task(bind=True)
@monitored_task(priority=TaskPriority.LOW, category=TaskCategory.MAINTENANCE)
def analytics_data_cleanup(self) -> Dict[str, Any]:
    """
    Coordinate analytics data cleanup
    Delegates to analytics cleanup service
    """
    try:
        logger.info("Starting analytics data cleanup coordination")
        
        # Get analytics cleanup service
        service_registry = ServiceRegistry()
        analytics_cleanup_service = service_registry.get_service("analytics_cleanup_service")
        
        # Delegate to service
        cleanup_result = analytics_cleanup_service.cleanup_old_analytics_data()
        
        logger.info(f"Analytics cleanup completed: {cleanup_result.get('records_cleaned')} records cleaned")
        return {
            "success": True,
            "operation": "analytics_cleanup",
            "records_cleaned": cleanup_result.get("records_cleaned"),
            "storage_freed": cleanup_result.get("storage_freed"),
            "performance_improvement": cleanup_result.get("performance_improvement"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Analytics cleanup coordination failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "operation": "analytics_cleanup",
            "timestamp": datetime.utcnow().isoformat()
        }

# =============================================================================
# TASK COORDINATION UTILITIES
# =============================================================================

def get_maintenance_service(service_name: str):
    """Helper to get maintenance services from registry"""
    service_registry = ServiceRegistry()
    return service_registry.get_service(service_name)

def format_maintenance_result(operation: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """Standardize maintenance operation result format"""
    return {
        "operation": operation,
        "success": result.get("success", False),
        "timestamp": datetime.utcnow().isoformat(),
        "details": result
    }

def log_maintenance_completion(operation: str, success: bool, details: Dict[str, Any]):
    """Standardized maintenance operation logging"""
    if success:
        logger.info(f"Maintenance operation '{operation}' completed successfully", extra=details)
    else:
        logger.error(f"Maintenance operation '{operation}' failed", extra=details)
