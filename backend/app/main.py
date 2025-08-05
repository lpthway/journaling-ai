# backend/app/main.py - Enhanced FastAPI Application with Redis Integration

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path

# Enhanced architecture imports
from app.core.config import settings
from app.core.exceptions import JournalingAIException
from app.core.database import database
from app.core.performance_monitor import performance_monitor
from app.services.unified_database_service import unified_db_service
from app.services.redis_service import redis_service
from app.core.service_interfaces import service_registry

# API routers
from app.api import entries, topics, insights, insights_v2, sessions, psychology

# Configure enhanced logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Enhanced application lifespan with Redis and performance monitoring
    Manages initialization and cleanup of all enterprise services
    """
    logger.info("🚀 Starting Journaling Assistant API with Redis Integration...")
    
    try:
        # Phase 1: Initialize core infrastructure
        logger.info("📊 Initializing core infrastructure...")
        
        # Initialize PostgreSQL database
        await database.initialize()
        logger.info("✅ PostgreSQL database initialized")
        
        # Initialize Redis service
        await redis_service.initialize()
        logger.info("✅ Redis service initialized")
        
        # Register Redis as caching strategy
        service_registry.set_cache_strategy(redis_service)
        logger.info("✅ Redis registered as caching strategy")
        
        # Phase 2: Initialize unified database service
        logger.info("🔧 Initializing unified database service...")
        await unified_db_service.initialize()
        logger.info("✅ Unified database service initialized")
        
        # Phase 3: Start performance monitoring
        logger.info("📈 Starting performance monitoring...")
        await performance_monitor.start_monitoring(interval=60)  # Monitor every minute
        logger.info("✅ Performance monitoring started")
        
        # Phase 4: Verify system health
        logger.info("🔍 Performing system health checks...")
        health_status = await unified_db_service.health_check()
        
        if health_status.get("status") == "healthy":
            logger.info("✅ System health check passed")
        else:
            logger.warning(f"⚠️ System health check warnings: {health_status}")
        
        # Phase 5: Create data directories
        os.makedirs("./data", exist_ok=True)
        os.makedirs("./data/chroma_db", exist_ok=True)
        logger.info("✅ Data directories verified")
        
        # System ready
        logger.info("🎉 Journaling Assistant API fully initialized and ready!")
        logger.info("📊 Phase 0B Redis Integration: OPERATIONAL")
        
        # Print startup summary
        logger.info("=" * 60)
        logger.info("🚀 ENTERPRISE JOURNALING ASSISTANT - READY")
        logger.info("=" * 60)
        logger.info(f"📍 Environment: {settings.ENVIRONMENT}")
        logger.info(f"🔧 PostgreSQL: Connected with connection pooling")
        logger.info(f"⚡ Redis: Connected with enterprise caching")
        logger.info(f"📈 Performance Monitoring: Active")
        logger.info(f"🎯 Phase 0B Targets: Monitored automatically")
        logger.info("=" * 60)
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Application startup failed: {e}")
        raise
    
    finally:
        # Cleanup on shutdown
        logger.info("🔄 Shutting down Journaling Assistant API...")
        
        try:
            # Stop performance monitoring
            await performance_monitor.stop_monitoring()
            logger.info("✅ Performance monitoring stopped")
            
            # Close Redis connections
            await redis_service.close()
            logger.info("✅ Redis connections closed")
            
            # Close database connections
            await database.close()
            logger.info("✅ Database connections closed")
            
            logger.info("👋 Journaling Assistant API shutdown complete")
            
        except Exception as e:
            logger.error(f"⚠️ Error during shutdown: {e}")

# Create FastAPI app with enhanced configuration
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Enterprise-grade journaling and coaching assistant with Redis caching",
    version="2.0.0",
    lifespan=lifespan
)

# Enhanced exception handler for structured error responses
@app.exception_handler(JournalingAIException)
async def journaling_ai_exception_handler(request: Request, exc: JournalingAIException):
    """Handle custom application exceptions with structured responses."""
    logger.error(f"Application error: {exc.message}", extra={
        "correlation_id": exc.correlation_id,
        "error_code": exc.error_code,
        "context": exc.context
    })
    
    return JSONResponse(
        status_code=getattr(exc, 'http_status_code', 500),
        content=exc.to_dict()
    )

# Global exception handler for unexpected errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with correlation ID."""
    import uuid
    correlation_id = str(uuid.uuid4())
    
    logger.error(f"Unexpected error: {str(exc)}", extra={
        "correlation_id": correlation_id,
        "request_url": str(request.url),
        "request_method": request.method
    })
    
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "correlation_id": correlation_id
        }
    )

# Configure CORS for development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers with proper ordering
app.include_router(insights_v2.router, prefix=f"{settings.API_V1_STR}/insights", tags=["insights"])
app.include_router(insights.router, prefix=f"{settings.API_V1_STR}/insights-legacy", tags=["insights-legacy"])
app.include_router(entries.router, prefix=f"{settings.API_V1_STR}/entries", tags=["entries"])
app.include_router(topics.router, prefix=f"{settings.API_V1_STR}/topics", tags=["topics"])
app.include_router(sessions.router, prefix=f"{settings.API_V1_STR}/sessions", tags=["sessions"])
app.include_router(psychology.router, prefix=f"{settings.API_V1_STR}/psychology", tags=["psychology"])

# Enhanced health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "journaling-assistant",
        "version": "2.0.0",
        "redis_integration": "active"
    }

@app.get(f"{settings.API_V1_STR}/health")
async def health_check_v1():
    """Detailed health check with Redis and PostgreSQL status"""
    try:
        # Get comprehensive health status
        health_status = await unified_db_service.health_check()
        
        # Add performance metrics
        performance_targets = await performance_monitor.check_performance_targets()
        
        # Get cache metrics
        from app.decorators.cache_decorators import get_cache_stats
        cache_stats = await get_cache_stats()
        
        return {
            "status": health_status.get("status", "unknown"),
            "service": "journaling-assistant",
            "version": "2.0.0",
            "timestamp": health_status.get("timestamp"),
            "components": health_status.get("components", {}),
            "performance_targets": performance_targets,
            "cache_performance": cache_stats,
            "phase_0b_status": "operational"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "journaling-assistant",
            "error": str(e),
            "timestamp": "unknown"
        }

@app.get(f"{settings.API_V1_STR}/health/performance")
async def performance_health_check():
    """Dedicated performance monitoring endpoint"""
    try:
        performance_report = await performance_monitor.get_performance_report()
        return performance_report
        
    except Exception as e:
        logger.error(f"Performance health check failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@app.get(f"{settings.API_V1_STR}/health/cache")
async def cache_health_check():
    """Dedicated cache performance endpoint"""
    try:
        from app.decorators.cache_decorators import get_cache_stats
        cache_stats = await get_cache_stats()
        
        # Get Redis info
        redis_info = await redis_service.get_info()
        redis_metrics = await redis_service.get_metrics()
        
        return {
            "status": "healthy",
            "cache_stats": cache_stats,
            "redis_info": redis_info,
            "redis_metrics": {
                "hit_rate": redis_metrics.hit_rate,
                "avg_response_time": redis_metrics.avg_response_time,
                "total_operations": redis_metrics.hits + redis_metrics.misses,
                "errors": redis_metrics.errors
            },
            "phase_0b_compliance": {
                "cache_hit_rate_target": redis_metrics.hit_rate >= 0.80,
                "response_time_target": redis_metrics.avg_response_time <= 0.005  # 5ms
            }
        }
        
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.post(f"{settings.API_V1_STR}/admin/cleanup")
async def admin_cleanup():
    """Administrative endpoint for system cleanup"""
    try:
        cleanup_results = await unified_db_service.cleanup_expired_data()
        
        return {
            "status": "completed",
            "cleanup_results": cleanup_results,
            "timestamp": "now"
        }
        
    except Exception as e:
        logger.error(f"Admin cleanup failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }

@app.get(f"{settings.API_V1_STR}/admin/performance/report")
async def admin_performance_report():
    """Administrative endpoint for detailed performance report"""
    try:
        report = await performance_monitor.get_performance_report()
        return report
        
    except Exception as e:
        logger.error(f"Performance report failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

# Serve static files (for production)
static_path = Path("static")
if static_path.exists():
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

# Development server configuration
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )