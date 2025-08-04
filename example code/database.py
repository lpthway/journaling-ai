# backend/app/core/database.py
"""
Enterprise PostgreSQL configuration with advanced connection pooling and health monitoring.

Design Principles:
- Async-first architecture for maximum concurrency
- Connection pooling optimized for 10K+ concurrent users
- Comprehensive error handling and retry mechanisms
- Health checks and monitoring integration
"""

from sqlalchemy.ext.asyncio import (
    AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import QueuePool
from sqlalchemy import event, text
from sqlalchemy.exc import DisconnectionError, TimeoutError
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import asyncio
import logging
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Advanced database configuration with performance tuning."""
    url: str
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600  # 1 hour
    pool_pre_ping: bool = True
    query_timeout: int = 30
    statement_timeout: int = 60
    echo: bool = False
    echo_pool: bool = False

class DatabaseManager:
    """
    Enterprise database manager with advanced connection pooling and monitoring.
    
    Features:
    - Async SQLAlchemy 2.0 with optimized connection pooling
    - Health checks and connection monitoring
    - Automatic retry mechanisms with exponential backoff
    - Performance metrics and query optimization
    """
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._connection_health = True
        self._last_health_check = 0
        
    async def initialize(self) -> None:
        """Initialize database engine and session factory with advanced configuration."""
        try:
            self.engine = create_async_engine(
                self.config.url,
                # Connection pooling optimization
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=self.config.pool_pre_ping,
                
                # Query optimization
                query_cache_size=1200,
                
                # Logging and debugging
                echo=self.config.echo,
                echo_pool=self.config.echo_pool,
                
                # Connection parameters
                connect_args={
                    "command_timeout": self.config.query_timeout,
                    "statement_timeout": self.config.statement_timeout * 1000,  # milliseconds
                    "application_name": "journaling_assistant",
                }
            )
            
            # Configure session factory
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False
            )
            
            # Set up event listeners for monitoring
            self._setup_event_listeners()
            
            # Verify connection
            await self.health_check()
            
            logger.info("✅ Database manager initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database manager: {e}")
            raise
    
    def _setup_event_listeners(self) -> None:
        """Set up SQLAlchemy event listeners for monitoring and optimization."""
        
        @event.listens_for(self.engine.sync_engine, "connect")
        def set_postgres_pragmas(dbapi_connection, connection_record):
            """Optimize PostgreSQL connection settings."""
            with dbapi_connection.cursor() as cursor:
                # Optimize for our workload
                cursor.execute("SET statement_timeout = %s", (self.config.statement_timeout * 1000,))
                cursor.execute("SET lock_timeout = '10s'")
                cursor.execute("SET idle_in_transaction_session_timeout = '30s'")
        
        @event.listens_for(self.engine.sync_engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Log slow queries for optimization."""
            context._query_start_time = time.time()
        
        @event.listens_for(self.engine.sync_engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Monitor query performance."""
            total = time.time() - context._query_start_time
            if total > 0.1:  # Log queries taking more than 100ms
                logger.warning(f"Slow query ({total:.3f}s): {statement[:100]}...")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session with comprehensive error handling and retry logic.
        
        Implements exponential backoff for connection errors and automatic
        session cleanup with proper transaction management.
        """
        if not self.session_factory:
            raise RuntimeError("Database manager not initialized")
        
        max_retries = 3
        base_delay = 0.1
        
        for attempt in range(max_retries + 1):
            try:
                async with self.session_factory() as session:
                    # Test connection health
                    await session.execute(text("SELECT 1"))
                    self._connection_health = True
                    yield session
                    return
                    
            except (DisconnectionError, TimeoutError) as e:
                self._connection_health = False
                
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Database connection error (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Database connection failed after {max_retries} retries: {e}")
                    raise
            
            except Exception as e:
                logger.error(f"Unexpected database error: {e}")
                raise
    
    async def health_check(self) -> bool:
        """
        Comprehensive database health check with connection validation.
        
        Returns:
            bool: True if database is healthy and responsive
        """
        current_time = time.time()
        
        # Rate limit health checks
        if current_time - self._last_health_check < 30:  # 30 second cache
            return self._connection_health
        
        try:
            async with self.get_session() as session:
                # Test basic connectivity
                result = await session.execute(text("SELECT 1 as health_check"))
                assert result.scalar() == 1
                
                # Test database responsiveness
                start_time = time.time()
                await session.execute(text("SELECT pg_database_size(current_database())"))
                response_time = time.time() - start_time
                
                if response_time > 1.0:
                    logger.warning(f"Database responding slowly: {response_time:.3f}s")
                
                self._connection_health = True
                self._last_health_check = current_time
                
                logger.debug("✅ Database health check passed")
                return True
                
        except Exception as e:
            self._connection_health = False
            logger.error(f"❌ Database health check failed: {e}")
            return False
    
    async def get_pool_status(self) -> dict:
        """Get connection pool status for monitoring."""
        if not self.engine:
            return {"status": "not_initialized"}
        
        pool = self.engine.pool
        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
            "health": self._connection_health
        }
    
    async def close(self) -> None:
        """Gracefully close database connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("🔄 Database connections closed")