# backend/app/api/monitoring.py
"""
Monitoring and Observability API Endpoints
Provides comprehensive monitoring data, metrics, and observability features
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from app.core.performance_monitor import performance_monitor
from app.core.request_tracing import get_request_tracer, trace_metrics
from app.core.logging_config import logging_metrics
from app.services.unified_database_service import unified_db_service
from app.services.redis_service import redis_service
from app.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/metrics")
async def get_application_metrics():
    """Get comprehensive application metrics"""
    try:
        # Get performance metrics
        performance_report = await performance_monitor.get_performance_report()
        
        # Get tracing metrics
        tracing_metrics = trace_metrics.get_metrics()
        
        # Get logging metrics
        log_metrics = logging_metrics.get_metrics()
        
        # Get system health status
        health_status = await unified_db_service.health_check()
        
        # Get Redis metrics
        redis_metrics = await redis_service.get_metrics()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "performance": performance_report,
            "requests": tracing_metrics,
            "logging": log_metrics,
            "system_health": health_status,
            "cache": {
                "hit_rate": redis_metrics.hit_rate,
                "avg_response_time_ms": redis_metrics.avg_response_time * 1000,
                "total_operations": redis_metrics.hits + redis_metrics.misses,
                "error_count": redis_metrics.errors
            },
            "summary": {
                "overall_health": _calculate_overall_health(performance_report, tracing_metrics, log_metrics),
                "performance_score": _calculate_performance_score(performance_report),
                "error_rate": tracing_metrics.get("error_rate", 0),
                "avg_response_time": tracing_metrics.get("avg_response_time_ms", 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Error collecting application metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to collect metrics: {str(e)}")

@router.get("/traces")
async def get_active_traces(
    limit: int = Query(50, description="Maximum number of traces to return"),
    user_id: Optional[str] = Query(None, description="Filter by user ID")
):
    """Get active request traces"""
    try:
        tracer = get_request_tracer()
        if not tracer:
            return {"traces": [], "message": "Request tracing not enabled"}
        
        traces = tracer.get_active_traces()
        
        # Filter by user_id if provided
        if user_id:
            traces = {k: v for k, v in traces.items() if v.user_id == user_id}
        
        # Convert to list and limit
        trace_list = list(traces.values())[-limit:]
        
        # Convert to serializable format
        serialized_traces = []
        for trace in trace_list:
            serialized_traces.append({
                "request_id": trace.request_id,
                "method": trace.method,
                "path": trace.path,
                "user_id": trace.user_id,
                "session_id": trace.session_id,
                "start_time": trace.start_time.isoformat(),
                "end_time": trace.end_time.isoformat() if trace.end_time else None,
                "duration_ms": trace.duration_ms,
                "status_code": trace.status_code,
                "ip_address": trace.ip_address,
                "error": trace.error
            })
        
        return {
            "traces": serialized_traces,
            "total_active": len(traces),
            "filtered_count": len(trace_list)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving traces: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve traces: {str(e)}")

@router.get("/traces/{request_id}")
async def get_trace_by_id(request_id: str):
    """Get specific trace by request ID"""
    try:
        tracer = get_request_tracer()
        if not tracer:
            raise HTTPException(status_code=404, detail="Request tracing not enabled")
        
        trace = tracer.get_trace_by_id(request_id)
        if not trace:
            raise HTTPException(status_code=404, detail="Trace not found")
        
        return {
            "trace": {
                "request_id": trace.request_id,
                "method": trace.method,
                "path": trace.path,
                "user_agent": trace.user_agent,
                "user_id": trace.user_id,
                "session_id": trace.session_id,
                "start_time": trace.start_time.isoformat(),
                "end_time": trace.end_time.isoformat() if trace.end_time else None,
                "duration_ms": trace.duration_ms,
                "status_code": trace.status_code,
                "response_size": trace.response_size,
                "ip_address": trace.ip_address,
                "error": trace.error
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving trace {request_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve trace: {str(e)}")

@router.get("/performance/targets")
async def get_performance_targets():
    """Get current performance targets and compliance"""
    try:
        targets_status = await performance_monitor.check_performance_targets()
        
        return {
            "targets": {
                "cache_hit_rate": {
                    "target": "≥80%",
                    "current_status": targets_status.get("cache_hit_rate_target", False)
                },
                "redis_response_time": {
                    "target": "≤5ms",
                    "current_status": targets_status.get("redis_response_target", False)
                },
                "database_query_time": {
                    "target": "≤50ms",
                    "current_status": targets_status.get("db_query_target", False)
                }
            },
            "overall_compliance": targets_status.get("overall_health", False),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error checking performance targets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check targets: {str(e)}")

@router.get("/alerts")
async def get_monitoring_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity (critical, warning, info)"),
    since: Optional[str] = Query(None, description="Get alerts since timestamp (ISO format)")
):
    """Get monitoring alerts and warnings"""
    try:
        alerts = []
        
        # Check performance targets
        targets_status = await performance_monitor.check_performance_targets()
        if not targets_status.get("overall_health", True):
            alerts.append({
                "severity": "warning",
                "type": "performance",
                "message": "Performance targets not being met",
                "details": targets_status,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Check error rates
        trace_stats = trace_metrics.get_metrics()
        error_rate = trace_stats.get("error_rate", 0)
        if error_rate > 0.05:  # >5% error rate
            alerts.append({
                "severity": "critical" if error_rate > 0.10 else "warning",
                "type": "error_rate",
                "message": f"High error rate: {error_rate:.1%}",
                "details": {"error_rate": error_rate, "threshold": 0.05},
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Check response times
        avg_response_time = trace_stats.get("avg_response_time_ms", 0)
        if avg_response_time > 1000:  # >1s average response time
            alerts.append({
                "severity": "warning",
                "type": "response_time",
                "message": f"High average response time: {avg_response_time:.0f}ms",
                "details": {"avg_response_time_ms": avg_response_time, "threshold": 1000},
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Filter by severity if provided
        if severity:
            alerts = [alert for alert in alerts if alert["severity"] == severity]
        
        # Filter by timestamp if provided
        if since:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            alerts = [
                alert for alert in alerts
                if datetime.fromisoformat(alert["timestamp"].replace("Z", "+00:00")) >= since_dt
            ]
        
        return {
            "alerts": alerts,
            "total_count": len(alerts),
            "summary": {
                "critical": len([a for a in alerts if a["severity"] == "critical"]),
                "warning": len([a for a in alerts if a["severity"] == "warning"]),
                "info": len([a for a in alerts if a["severity"] == "info"])
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve alerts: {str(e)}")

@router.post("/performance/benchmark")
async def run_performance_benchmark(_user = Depends(get_current_user)):
    """Run performance benchmark tests"""
    try:
        # Run various performance tests
        benchmark_results = {
            "database": await _benchmark_database(),
            "cache": await _benchmark_cache(),
            "system": await _benchmark_system(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return benchmark_results
        
    except Exception as e:
        logger.error(f"Error running performance benchmark: {e}")
        raise HTTPException(status_code=500, detail=f"Benchmark failed: {str(e)}")

async def _benchmark_database() -> Dict[str, Any]:
    """Benchmark database performance"""
    import time
    
    results = []
    for i in range(10):
        start_time = time.time()
        await unified_db_service.health_check()
        duration = (time.time() - start_time) * 1000
        results.append(duration)
    
    return {
        "avg_response_time_ms": sum(results) / len(results),
        "min_response_time_ms": min(results),
        "max_response_time_ms": max(results),
        "test_count": len(results)
    }

async def _benchmark_cache() -> Dict[str, Any]:
    """Benchmark cache performance"""
    import time
    
    results = []
    test_key = f"benchmark_test_{int(time.time())}"
    test_value = {"test": "data", "timestamp": time.time()}
    
    for i in range(10):
        start_time = time.time()
        await redis_service.set(test_key, test_value, ttl=60)
        await redis_service.get(test_key)
        duration = (time.time() - start_time) * 1000
        results.append(duration)
    
    # Cleanup
    await redis_service.delete(test_key)
    
    return {
        "avg_response_time_ms": sum(results) / len(results),
        "min_response_time_ms": min(results),
        "max_response_time_ms": max(results),
        "test_count": len(results)
    }

async def _benchmark_system() -> Dict[str, Any]:
    """Benchmark system performance"""
    system_metrics = await performance_monitor.collect_system_metrics()
    
    return {
        "cpu_percent": system_metrics.cpu_percent,
        "memory_percent": system_metrics.memory_percent,
        "disk_usage_percent": system_metrics.disk_usage_percent,
        "memory_available_mb": system_metrics.memory_available_mb
    }

def _calculate_overall_health(performance_report: Dict, tracing_metrics: Dict, log_metrics: Dict) -> str:
    """Calculate overall health status"""
    issues = []
    
    # Check performance
    if not performance_report.get("monitoring_active", False):
        issues.append("monitoring_inactive")
    
    # Check error rates
    error_rate = tracing_metrics.get("error_rate", 0)
    if error_rate > 0.10:
        issues.append("high_error_rate")
    elif error_rate > 0.05:
        issues.append("elevated_error_rate")
    
    # Check response times
    avg_response = tracing_metrics.get("avg_response_time_ms", 0)
    if avg_response > 2000:
        issues.append("slow_response_times")
    
    # Check log errors
    log_error_rate = log_metrics.get("error_rate", 0)
    if log_error_rate > 0.01:  # >1% log errors
        issues.append("high_log_errors")
    
    if not issues:
        return "healthy"
    elif len(issues) == 1 and issues[0] in ["elevated_error_rate"]:
        return "warning"
    else:
        return "unhealthy"

def _calculate_performance_score(performance_report: Dict) -> float:
    """Calculate performance score (0-100)"""
    score = 100.0
    
    # Deduct points for performance issues
    cache_data = performance_report.get("cache", {})
    if cache_data.get("hit_rate", 0) < 0.8:
        score -= 20
    
    system_data = performance_report.get("system", {})
    cpu_percent = system_data.get("cpu_percent", 0)
    if cpu_percent > 80:
        score -= 15
    
    memory_percent = system_data.get("memory_percent", 0)
    if memory_percent > 85:
        score -= 15
    
    return max(0, score)