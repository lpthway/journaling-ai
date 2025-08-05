# backend/app/api/health.py - Comprehensive Health API with Performance Monitoring

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.services.unified_database_service import unified_db_service
from app.core.performance_monitor import performance_monitor
from app.decorators.cache_decorators import get_cache_stats
from app.services.redis_service import redis_service
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
async def basic_health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "journaling-assistant",
        "version": "2.0.0",
        "phase_0b": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/detailed")
async def detailed_health_check():
    """Comprehensive health check with all system components"""
    try:
        # Get unified service health
        health_status = await unified_db_service.health_check()
        
        # Get performance monitoring status
        performance_targets = await performance_monitor.check_performance_targets()
        performance_report = await performance_monitor.get_performance_report()
        
        # Get cache performance
        cache_stats = await get_cache_stats()
        
        # Get Redis metrics
        redis_info = await redis_service.get_info()
        redis_metrics = await redis_service.get_metrics()
        
        return {
            "status": health_status.get("status", "unknown"),
            "service": "journaling-assistant",
            "version": "2.0.0",
            "timestamp": health_status.get("timestamp"),
            "components": health_status.get("components", {}),
            "performance": {
                "targets_met": performance_targets,
                "monitoring_active": performance_report.get("monitoring_active", False),
                "system_metrics": performance_report.get("system", {}),
                "database_metrics": performance_report.get("database", {}),
                "cache_metrics": performance_report.get("cache", {})
            },
            "cache_performance": {
                "stats": cache_stats,
                "redis_info": redis_info,
                "hit_rate": redis_metrics.hit_rate,
                "avg_response_time_ms": redis_metrics.avg_response_time * 1000,
                "phase_0b_compliance": {
                    "cache_hit_rate_target": redis_metrics.hit_rate >= 0.80,
                    "response_time_target": redis_metrics.avg_response_time <= 0.005
                }
            },
            "phase_0b_status": {
                "integration_complete": True,
                "performance_monitoring": True,
                "redis_integration": True,
                "targets_monitored": list(performance_targets.keys())
            }
        }
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "journaling-assistant",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/performance")
async def performance_status():
    """Dedicated performance monitoring endpoint"""
    try:
        performance_report = await performance_monitor.get_performance_report()
        performance_targets = await performance_monitor.check_performance_targets()
        
        return {
            "status": "healthy" if performance_targets.get("overall_health", False) else "degraded",
            "performance_report": performance_report,
            "targets_compliance": performance_targets,
            "phase_0b_targets": {
                "cache_hit_rate": ">80%",
                "redis_response": "<5ms", 
                "session_retrieval": "<10ms",
                "db_queries": "<50ms",
                "psychology_cache": "<2ms"
            }
        }
        
    except Exception as e:
        logger.error(f"Performance status check failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/cache")
async def cache_status():
    """Dedicated cache performance endpoint"""
    try:
        cache_stats = await get_cache_stats()
        redis_info = await redis_service.get_info()
        redis_metrics = await redis_service.get_metrics()
        
        return {
            "status": "healthy",
            "cache_stats": cache_stats,
            "redis_info": redis_info,
            "performance_metrics": {
                "hit_rate": redis_metrics.hit_rate,
                "miss_rate": 1.0 - redis_metrics.hit_rate,
                "avg_response_time_ms": redis_metrics.avg_response_time * 1000,
                "total_operations": redis_metrics.hits + redis_metrics.misses,
                "errors": redis_metrics.errors
            },
            "phase_0b_compliance": {
                "cache_hit_rate_met": redis_metrics.hit_rate >= 0.80,
                "response_time_met": redis_metrics.avg_response_time <= 0.005,
                "overall_compliant": (
                    redis_metrics.hit_rate >= 0.80 and 
                    redis_metrics.avg_response_time <= 0.005
                )
            }
        }
        
    except Exception as e:
        logger.error(f"Cache status check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.get("/system")
async def system_status():
    """System resource status"""
    try:
        performance_report = await performance_monitor.get_performance_report()
        
        return {
            "status": "healthy",
            "system_metrics": performance_report.get("system", {}),
            "database_metrics": performance_report.get("database", {}),
            "timestamp": performance_report.get("timestamp")
        }
        
    except Exception as e:
        logger.error(f"System status check failed: {e}")
        return {
            "status": "unhealthy", 
            "error": str(e)
        }

@router.post("/cleanup")
async def trigger_cleanup():
    """Administrative endpoint for system cleanup"""
    try:
        cleanup_results = await unified_db_service.cleanup_expired_data()
        
        return {
            "status": "completed",
            "cleanup_results": cleanup_results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"System cleanup failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }