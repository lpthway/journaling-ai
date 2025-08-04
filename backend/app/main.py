### app/main.py - Enhanced FastAPI Application with Enterprise Architecture

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import logging
import os
from pathlib import Path

# Enhanced imports for enterprise architecture
from app.core.config import settings
from app.core.exceptions import JournalingAIException
from app.core.enhanced_database import DatabaseManager, DatabaseConfig
from app.api import entries, topics, insights, insights_v2, sessions, psychology
from app.services.background_analytics import analytics_lifespan

# Configure enhanced logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(correlation_id)s' if settings.LOG_FORMAT == 'json' else '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Global database manager instance with proper configuration
db_config = DatabaseConfig(
    url=settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    query_timeout=30,
    statement_timeout=60,
    echo=settings.DEBUG
)
db_manager = DatabaseManager(db_config)

# Create FastAPI app with enhanced configuration
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Enterprise-grade journaling and coaching assistant with AI insights",
    version="2.0.0",
    lifespan=analytics_lifespan  # Enable background analytics processing
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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers - ORDER MATTERS! New optimized endpoints first
app.include_router(insights_v2.router, prefix=f"{settings.API_V1_STR}/insights", tags=["insights"])
app.include_router(insights.router, prefix=f"{settings.API_V1_STR}/insights-legacy", tags=["insights-legacy"])
app.include_router(entries.router, prefix=f"{settings.API_V1_STR}/entries", tags=["entries"])
app.include_router(topics.router, prefix=f"{settings.API_V1_STR}/topics", tags=["topics"])
app.include_router(sessions.router, prefix=f"{settings.API_V1_STR}/sessions", tags=["sessions"])
app.include_router(psychology.router, prefix=f"{settings.API_V1_STR}/psychology", tags=["psychology"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "journaling-assistant",
        "version": "1.0.0"
    }

@app.get(f"{settings.API_V1_STR}/health")
async def health_check_v1():
    """Health check endpoint for v1 API"""
    return {
        "status": "healthy",
        "service": "journaling-assistant",
        "version": "1.0.0"
    }

# Serve static files (for production)
static_path = Path("static")
if static_path.exists():
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Journaling Assistant API...")
    
    # Ensure data directories exist
    os.makedirs("./data", exist_ok=True)
    os.makedirs("./data/chroma_db", exist_ok=True)
    
    logger.info("API started successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Journaling Assistant API...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )