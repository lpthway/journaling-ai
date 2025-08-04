### app/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import os
from pathlib import Path

from app.core.config import settings
from app.api import entries, topics, insights, sessions, psychology

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="A local-first journaling and coaching assistant with AI insights",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(entries.router, prefix=f"{settings.API_V1_STR}/entries", tags=["entries"])
app.include_router(topics.router, prefix=f"{settings.API_V1_STR}/topics", tags=["topics"])
app.include_router(insights.router, prefix=f"{settings.API_V1_STR}/insights", tags=["insights"])
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