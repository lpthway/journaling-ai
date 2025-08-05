# backend/app/core/database.py - Enterprise PostgreSQL Database Configuration

import asyncio
import logging
from typing import AsyncGenerator, Optional, Dict, Any
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    AsyncSession, 
    AsyncEngine, 
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy import event, text
from sqlalchemy.exc import DisconnectionError
import time

from app.core.config import settings

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """
    Enterprise-grade PostgreSQL database configuration with:
    - Connection pooling and health checks
    - Retry mechanisms and error handling
    - Performance monitoring and optimization
    - ACID compliance and transaction management
    """
    
    def __init__(self):
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None
        self._connection_retry_count = 0
        self._max_retries = 3
        
    async def initialize(self) -> None:
        """Initialize database engine with enterprise configuration."""
        try:
            # Create async engine with connection pooling
            self.engine = create_async_engine(
                settings.DATABASE_URL,
                
                # Connection Pool Configuration (using default async pool)
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_pre_ping=True,  # Validate connections
                pool_recycle=settings.DB_POOL_RECYCLE,
                
                # Performance Configuration
                connect_args={
                    "command_timeout": settings.DB_COMMAND_TIMEOUT,
                    "server_settings": {
                        "application_name": "journaling_ai",
                        "jit": "off",  # Disable JIT for consistent performance
                    },
                },
                
                # Logging and Monitoring
                echo=settings.DB_ECHO,
                echo_pool=settings.DB_ECHO_POOL,
                
                # Error Handling
                pool_timeout=30,
                pool_reset_on_return='commit',
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,  # Manual transaction control
                autocommit=False,
            )
            
            # Set up event listeners for monitoring
            self._setup_event_listeners()
            
            # Validate initial connection
            await self._validate_connection()
            
            logger.info("✅ Database initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    def _setup_event_listeners(self) -> None:
        """Set up SQLAlchemy event listeners for monitoring and debugging."""
        
        @event.listens_for(self.engine.sync_engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            logger.debug("🔌 New database connection established")
            
        @event.listens_for(self.engine.sync_engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            logger.debug("📤 Connection checked out from pool")
            
        @event.listens_for(self.engine.sync_engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            logger.debug("📥 Connection returned to pool")
            
        @event.listens_for(self.engine.sync_engine, "invalidate")
        def on_invalidate(dbapi_connection, connection_record, exception):
            logger.warning(f"🚫 Connection invalidated: {exception}")
    
    async def _validate_connection(self) -> None:
        """Validate database connection and basic functionality."""
        try:
            async with self.session_factory() as session:
                result = await session.execute(text("SELECT 1"))
                assert result.scalar() == 1
                logger.info("✅ Database connection validation successful")
        except Exception as e:
            logger.error(f"❌ Database connection validation failed: {e}")
            raise
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session with automatic transaction management and retry logic.
        
        Features:
        - Automatic rollback on exceptions
        - Connection retry with exponential backoff
        - Performance monitoring
        - Error logging and context
        """
        if not self.session_factory:
            raise RuntimeError("Database not initialized. Call initialize() first.")
            
        session = self.session_factory()
        start_time = time.time()
        
        try:
            yield session
            await session.commit()
            
        except DisconnectionError as e:
            await session.rollback()
            logger.warning(f"🔄 Database disconnection, retrying: {e}")
            
            if self._connection_retry_count < self._max_retries:
                self._connection_retry_count += 1
                await asyncio.sleep(2 ** self._connection_retry_count)  # Exponential backoff
                
                # Retry with new session
                async with self.get_session() as retry_session:
                    yield retry_session
                    
            else:
                logger.error(f"❌ Max retries exceeded for database connection")
                raise
                
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Database transaction failed: {e}")
            raise
            
        finally:
            await session.close()
            
            # Performance monitoring
            duration = time.time() - start_time
            if duration > settings.DB_SLOW_QUERY_THRESHOLD:
                logger.warning(f"🐌 Slow database operation: {duration:.3f}s")
            
            # Reset retry count on successful operation
            self._connection_retry_count = 0
    
    async def health_check(self) -> dict:
        """
        Comprehensive database health check.
        
        Returns:
            dict: Health status including connection pool stats and performance metrics
        """
        try:
            start_time = time.time()
            
            async with self.get_session() as session:
                # Test basic connectivity
                await session.execute(text("SELECT 1"))
                
                # Test performance
                await session.execute(text("SELECT pg_database_size(current_database())"))
                
            duration = time.time() - start_time
            
            # Get pool statistics
            pool = self.engine.pool
            
            return {
                "status": "healthy",
                "response_time_ms": round(duration * 1000, 2),
                "pool_stats": {
                    "size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                    "total_connections": pool.size() + pool.overflow(),
                },
                "performance": {
                    "within_target": duration < (settings.DB_PERFORMANCE_TARGET_MS / 1000),
                    "target_ms": settings.DB_PERFORMANCE_TARGET_MS,
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "pool_stats": None,
            }
    
    async def get_pool_status(self) -> Dict[str, Any]:
        """Get database connection pool status for performance monitoring"""
        try:
            if not self.engine:
                return {"size": 0, "checked_in": 0, "checked_out": 0, "overflow": 0, "total_connections": 0}
            
            pool = self.engine.pool
            return {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "total_connections": pool.size() + pool.overflow(),
            }
        except Exception as e:
            logger.error(f"Error getting pool status: {e}")
            return {"size": 0, "checked_in": 0, "checked_out": 0, "overflow": 0, "total_connections": 0}
    
    async def close(self) -> None:
        """Gracefully close database connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("🔐 Database connections closed")

# Global database instance
database = DatabaseConfig()

# Dependency for FastAPI
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to get database session."""
    async with database.get_session() as session:
        yield session

# Health check endpoint dependency
async def get_db_health() -> dict:
    """FastAPI dependency for database health checks."""
    return await database.health_check()
