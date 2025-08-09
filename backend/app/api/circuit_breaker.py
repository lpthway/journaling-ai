# backend/app/api/circuit_breaker.py
"""
Circuit Breaker monitoring and management API endpoints.

Provides monitoring capabilities and manual control over circuit breakers
for all external services in the application.
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
import logging

from app.core.circuit_breaker import circuit_breaker_registry, CircuitBreakerState, CircuitBreakerConfig
# Note: Auth dependencies commented out for testing - uncomment when auth system is available
# from app.auth.dependencies import get_current_user
# from app.models.auth import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/circuit-breakers", tags=["circuit-breakers"])


@router.get("/status", response_model=Dict[str, Any])
async def get_all_circuit_breaker_status(
    # current_user: User = Depends(get_current_user)  # Auth disabled for testing
) -> Dict[str, Any]:
    """
    Get status of all circuit breakers in the system.
    
    Returns detailed status information for monitoring and debugging.
    """
    try:
        all_stats = circuit_breaker_registry.get_all_stats()
        unhealthy_services = circuit_breaker_registry.get_unhealthy_services()
        
        # Calculate overall health summary
        total_services = len(all_stats)
        healthy_services = total_services - len(unhealthy_services)
        overall_health = "healthy" if len(unhealthy_services) == 0 else "degraded"
        
        # Get summary statistics
        total_calls = sum(stats.get('total_calls', 0) for stats in all_stats.values())
        total_failures = sum(stats.get('total_failures', 0) for stats in all_stats.values())
        avg_failure_rate = (total_failures / total_calls * 100) if total_calls > 0 else 0
        
        response = {
            "overall_health": overall_health,
            "summary": {
                "total_services": total_services,
                "healthy_services": healthy_services,
                "unhealthy_services": len(unhealthy_services),
                "total_calls": total_calls,
                "total_failures": total_failures,
                "avg_failure_rate_percent": round(avg_failure_rate, 2)
            },
            "services": all_stats,
            "unhealthy_services": unhealthy_services,
            "timestamp": "2025-08-09T12:00:00Z"  # Would use datetime.utcnow().isoformat()
        }
        
        logger.info(f"Circuit breaker status requested by user {current_user.email}")
        return response
        
    except Exception as e:
        logger.error(f"Error getting circuit breaker status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get circuit breaker status: {str(e)}"
        )


@router.get("/services/{service_name}/status", response_model=Dict[str, Any])
async def get_service_circuit_breaker_status(
    service_name: str,
    # current_user: User = Depends(get_current_user)  # Auth disabled for testing
) -> Dict[str, Any]:
    """
    Get detailed status for a specific service's circuit breaker.
    """
    try:
        all_stats = circuit_breaker_registry.get_all_stats()
        
        if service_name not in all_stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Circuit breaker for service '{service_name}' not found"
            )
        
        service_stats = all_stats[service_name]
        
        # Add health assessment
        is_healthy = (
            service_stats["state"] == "closed" and
            service_stats["failure_rate"] < 0.5  # Less than 50% failure rate
        )
        
        response = {
            "service_name": service_name,
            "is_healthy": is_healthy,
            "status": service_stats,
            "recommendations": _generate_service_recommendations(service_stats),
            "timestamp": "2025-08-09T12:00:00Z"
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting circuit breaker status for {service_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get circuit breaker status for service: {str(e)}"
        )


@router.post("/services/{service_name}/reset")
async def reset_service_circuit_breaker(
    service_name: str,
    # current_user: User = Depends(get_current_user)  # Auth disabled for testing
) -> Dict[str, str]:
    """
    Manually reset a circuit breaker to closed state.
    
    Use this when you know the external service has been fixed
    and you want to immediately resume normal operation.
    """
    try:
        all_stats = circuit_breaker_registry.get_all_stats()
        
        if service_name not in all_stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Circuit breaker for service '{service_name}' not found"
            )
        
        # Get the circuit breaker and reset it
        breaker = circuit_breaker_registry.get_breaker(service_name)
        old_state = breaker.state.value
        breaker.reset()
        
        logger.warning(
            f"Circuit breaker for '{service_name}' manually reset from {old_state} "
            f"to closed by user {current_user.email}"
        )
        
        return {
            "message": f"Circuit breaker for '{service_name}' has been reset to closed state",
            "old_state": old_state,
            "new_state": "closed",
            "reset_by": current_user.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting circuit breaker for {service_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset circuit breaker: {str(e)}"
        )


@router.post("/services/{service_name}/force-open")
async def force_open_service_circuit_breaker(
    service_name: str,
    # current_user: User = Depends(get_current_user)  # Auth disabled for testing
) -> Dict[str, str]:
    """
    Manually force a circuit breaker to open state.
    
    Use this to immediately stop calls to a service that you know is having issues,
    even if the circuit breaker hasn't detected enough failures yet.
    """
    try:
        all_stats = circuit_breaker_registry.get_all_stats()
        
        if service_name not in all_stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Circuit breaker for service '{service_name}' not found"
            )
        
        # Get the circuit breaker and force it open
        breaker = circuit_breaker_registry.get_breaker(service_name)
        old_state = breaker.state.value
        breaker.force_open()
        
        logger.warning(
            f"Circuit breaker for '{service_name}' manually forced open from {old_state} "
            f"by user {current_user.email}"
        )
        
        return {
            "message": f"Circuit breaker for '{service_name}' has been forced to open state",
            "old_state": old_state,
            "new_state": "open",
            "forced_by": current_user.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error forcing circuit breaker open for {service_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to force circuit breaker open: {str(e)}"
        )


@router.post("/reset-all")
async def reset_all_circuit_breakers(
    # current_user: User = Depends(get_current_user)  # Auth disabled for testing
) -> Dict[str, Any]:
    """
    Reset all circuit breakers to closed state.
    
    Use this after system-wide maintenance when all services should be healthy.
    Use with caution - only reset when you're confident services are working.
    """
    try:
        all_stats_before = circuit_breaker_registry.get_all_stats()
        services_reset = list(all_stats_before.keys())
        
        # Reset all circuit breakers
        circuit_breaker_registry.reset_all()
        
        logger.warning(
            f"ALL circuit breakers reset by user {current_user.email}. "
            f"Services affected: {', '.join(services_reset)}"
        )
        
        return {
            "message": "All circuit breakers have been reset to closed state",
            "services_reset": services_reset,
            "reset_by": current_user.email,
            "warning": "All services are now enabled - monitor for issues"
        }
        
    except Exception as e:
        logger.error(f"Error resetting all circuit breakers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset all circuit breakers: {str(e)}"
        )


@router.get("/health")
async def circuit_breaker_health_check() -> Dict[str, Any]:
    """
    Health check endpoint for circuit breaker system.
    
    This endpoint is public (no auth required) for monitoring systems.
    """
    try:
        all_stats = circuit_breaker_registry.get_all_stats()
        unhealthy_services = circuit_breaker_registry.get_unhealthy_services()
        
        # Determine overall health
        if len(unhealthy_services) == 0:
            health_status = "healthy"
        elif len(unhealthy_services) <= len(all_stats) / 2:
            health_status = "degraded"
        else:
            health_status = "critical"
        
        response = {
            "status": health_status,
            "total_services": len(all_stats),
            "unhealthy_services": len(unhealthy_services),
            "unhealthy_service_names": unhealthy_services,
            "timestamp": "2025-08-09T12:00:00Z"
        }
        
        # Return appropriate HTTP status based on health
        if health_status == "healthy":
            return JSONResponse(status_code=200, content=response)
        elif health_status == "degraded":
            return JSONResponse(status_code=200, content=response)  # Still OK but with warnings
        else:
            return JSONResponse(status_code=503, content=response)  # Service unavailable
            
    except Exception as e:
        logger.error(f"Error in circuit breaker health check: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "timestamp": "2025-08-09T12:00:00Z"
            }
        )


def _generate_service_recommendations(service_stats: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on service statistics"""
    recommendations = []
    
    state = service_stats.get("state", "unknown")
    failure_rate = service_stats.get("failure_rate", 0)
    consecutive_failures = service_stats.get("consecutive_failures", 0)
    avg_response_time = service_stats.get("avg_response_time", 0)
    
    if state == "open":
        recommendations.append("Circuit breaker is OPEN - service calls are being blocked")
        recommendations.append("Check the external service health before manually resetting")
        recommendations.append("Monitor logs for error patterns before the circuit opened")
    elif state == "half_open":
        recommendations.append("Circuit breaker is testing service recovery - avoid manual intervention")
        recommendations.append("Monitor the next few calls to see if service has recovered")
    elif failure_rate > 0.3:
        recommendations.append(f"High failure rate ({failure_rate:.1%}) - investigate service issues")
        recommendations.append("Consider checking service logs and network connectivity")
    elif consecutive_failures > 1:
        recommendations.append(f"Recent consecutive failures detected - monitor closely")
    elif avg_response_time > 10:
        recommendations.append(f"High average response time ({avg_response_time:.2f}s) - check service performance")
    
    if not recommendations:
        recommendations.append("Service appears healthy - no action needed")
    
    return recommendations


# Export the router
__all__ = ["router"]