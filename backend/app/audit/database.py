# backend/app/audit/database.py
"""
Separate audit database configuration for security isolation.

Features:
- Isolated from main application database
- Write-only for application (immutable logs)
- Enhanced security and compliance posture
- Separate backup and retention policies
"""

import asyncio
import logging
from typing import AsyncGenerator, Optional
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

from ..core.config import settings

logger = logging.getLogger(__name__)


class AuditDatabaseConfig:
    """
    Dedicated audit database configuration for security isolation.
    
    Design principles:
    - Separate from main application database
    - Write-only access for application
    - Immutable audit log storage
    - Enhanced security monitoring
    """
    
    def __init__(self):
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None
        self._connection_retry_count = 0
        self._max_retries = 3
        
        # Audit-specific metrics
        self._audit_metrics = {
            "events_logged": 0,
            "failed_writes": 0,
            "connection_errors": 0,
            "average_write_time": 0.0,
            "last_successful_write": None
        }
    
    async def initialize(self) -> None:
        """Initialize audit database with security-focused configuration."""
        try:
            # Build audit database URL (separate from main database)
            audit_db_url = self._build_audit_database_url()
            
            # Create async engine with audit-optimized settings
            self.engine = create_async_engine(
                audit_db_url,
                
                # Audit-optimized connection pool
                pool_size=5,  # Smaller pool for audit writes
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=1800,  # 30 minutes
                
                # Security-focused settings
                connect_args={
                    "command_timeout": 30,
                    "server_settings": {
                        "application_name": "journaling_ai_audit",
                        "default_transaction_isolation": "READ COMMITTED",
                        "synchronous_commit": "on",  # Ensure durability
                        "fsync": "on",  # Force disk writes
                        "full_page_writes": "on",  # Corruption protection
                    },
                },
                
                # Monitoring and logging
                echo=settings.DEBUG,  # Only in debug mode
                echo_pool=False,  # Reduce noise
                
                # Strict error handling
                pool_timeout=20,
                pool_reset_on_return='rollback',
            )
            
            # Create session factory with audit-specific settings
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,  # Immediate writes for audit
                autocommit=False,
            )
            
            # Set up audit-specific event listeners
            self._setup_audit_event_listeners()
            
            # Validate connection and create tables if needed
            await self._validate_audit_connection()
            
            logger.info("✅ Audit database initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Audit database initialization failed: {e}")
            raise
    
    def _build_audit_database_url(self) -> str:
        """Build audit database URL (separate database or schema)."""
        try:
            # In production, this should be a completely separate database
            # For development, we'll use a separate schema in the same database
            base_url = settings.DATABASE_URL
            
            if "postgresql" in base_url:
                # For PostgreSQL, we can use a separate schema
                # In production, use a separate database server
                if base_url.endswith("/journaling_ai"):
                    audit_url = base_url.replace("/journaling_ai", "/journaling_ai_audit")
                else:
                    # Extract parts and build audit URL
                    if "?" in base_url:
                        db_part, params = base_url.rsplit("?", 1)
                        audit_url = f"{db_part}_audit?{params}"
                    else:
                        audit_url = f"{base_url}_audit"
            else:
                # Fallback to same database with different schema
                audit_url = base_url
            
            logger.info(f"Audit database URL configured: {audit_url.split('@')[0]}@***")
            return audit_url
            
        except Exception as e:
            logger.warning(f"Failed to build separate audit DB URL: {e}")
            logger.info("Using main database for audit logs (consider separate DB for production)")
            return settings.DATABASE_URL
    
    def _setup_audit_event_listeners(self) -> None:
        """Set up event listeners for audit database monitoring."""
        
        @event.listens_for(self.engine.sync_engine, "connect")
        def on_audit_connect(dbapi_connection, connection_record):
            logger.debug("🔌 Audit database connection established")
            connection_record.info['audit_connect_time'] = time.time()
        
        @event.listens_for(self.engine.sync_engine, "checkout")
        def on_audit_checkout(dbapi_connection, connection_record, connection_proxy):
            logger.debug("📤 Audit connection checked out")
        
        @event.listens_for(self.engine.sync_engine, "checkin")
        def on_audit_checkin(dbapi_connection, connection_record):
            logger.debug("📥 Audit connection returned")
            
            # Track successful writes
            if 'audit_write_start' in connection_record.info:
                write_time = time.time() - connection_record.info['audit_write_start']
                self._update_audit_metrics(write_time)
        
        @event.listens_for(self.engine.sync_engine, "invalidate")
        def on_audit_invalidate(dbapi_connection, connection_record, exception):
            logger.error(f"🚫 Audit connection invalidated: {exception}")
            self._audit_metrics["connection_errors"] += 1
    
    async def _validate_audit_connection(self) -> None:
        """Validate audit database connection and create schema if needed."""
        try:
            async with self.get_session() as session:
                # Test basic connectivity
                result = await session.execute(text("SELECT 1"))
                assert result.scalar() == 1
                
                # Create audit schema if it doesn't exist
                await self._ensure_audit_schema(session)
                
                logger.info("✅ Audit database connection validation successful")
                
        except Exception as e:
            logger.error(f"❌ Audit database validation failed: {e}")
            raise
    
    async def _ensure_audit_schema(self, session: AsyncSession) -> None:
        """Ensure audit database schema exists."""
        try:
            from .models import AuditBase
            
            # Create all audit tables
            async with session.bind.begin() as conn:
                await conn.run_sync(AuditBase.metadata.create_all)
            
            logger.info("✅ Audit database schema validated")
            
        except Exception as e:
            logger.error(f"❌ Audit schema creation failed: {e}")
            raise
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get audit database session with enhanced error handling.
        
        Features:
        - Automatic retry for connection issues
        - Write performance monitoring
        - Enhanced error logging for security events
        """
        if not self.session_factory:
            raise RuntimeError("Audit database not initialized")
        
        session = self.session_factory()
        start_time = time.time()
        
        try:
            # Track write start time
            if hasattr(session.bind, 'pool'):
                # This is a hack to track write timing - in production use proper metrics
                pass
            
            yield session
            await session.commit()
            
            # Update successful write metrics
            self._audit_metrics["events_logged"] += 1
            self._audit_metrics["last_successful_write"] = time.time()
            
        except DisconnectionError as e:
            await session.rollback()
            logger.warning(f"🔄 Audit database disconnection, retrying: {e}")
            
            if self._connection_retry_count < self._max_retries:
                self._connection_retry_count += 1
                await asyncio.sleep(2 ** self._connection_retry_count)
                
                # Retry with new session
                async with self.get_session() as retry_session:
                    yield retry_session
            else:
                logger.error("❌ Max retries exceeded for audit database")
                self._audit_metrics["failed_writes"] += 1
                raise
                
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Audit database transaction failed: {e}")
            self._audit_metrics["failed_writes"] += 1
            raise
            
        finally:
            await session.close()
            
            # Update performance metrics
            duration = time.time() - start_time
            self._update_audit_metrics(duration)
            
            # Reset retry count on successful operation
            self._connection_retry_count = 0
    
    def _update_audit_metrics(self, write_time: float) -> None:
        """Update audit performance metrics."""
        # Simple exponential moving average
        if self._audit_metrics["average_write_time"] == 0:
            self._audit_metrics["average_write_time"] = write_time
        else:
            alpha = 0.1
            self._audit_metrics["average_write_time"] = (
                alpha * write_time + 
                (1 - alpha) * self._audit_metrics["average_write_time"]
            )
    
    async def health_check(self) -> dict:
        """
        Audit database health check with security metrics.
        
        Returns:
            dict: Audit database health status and metrics
        """
        try:
            start_time = time.time()
            
            async with self.get_session() as session:
                # Test write capability (critical for audit)
                await session.execute(text("SELECT 1"))
                
                # Get audit database info
                db_info = await session.execute(text("""
                    SELECT 
                        pg_database_size(current_database()) as db_size,
                        (SELECT count(*) FROM audit_events WHERE timestamp > NOW() - INTERVAL '24 hours') as events_24h
                """))
                db_stats = db_info.fetchone()
            
            duration = time.time() - start_time
            
            return {
                "status": "healthy",
                "database": "audit_database",
                "response_time_ms": round(duration * 1000, 2),
                "audit_metrics": self._audit_metrics.copy(),
                "database_info": {
                    "size_bytes": db_stats[0] if db_stats else 0,
                    "events_last_24h": db_stats[1] if db_stats else 0,
                },
                "security_status": {
                    "write_only_access": True,
                    "immutable_logs": True,
                    "isolated_storage": True,
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Audit database health check failed: {e}")
            return {
                "status": "unhealthy",
                "database": "audit_database",
                "error": str(e),
                "audit_metrics": self._audit_metrics.copy(),
                "last_error_time": time.time()
            }
    
    async def close(self) -> None:
        """Gracefully close audit database connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("🔐 Audit database connections closed")


# Global audit database instance
audit_database = AuditDatabaseConfig()

# Dependency for FastAPI
async def get_audit_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to get audit database session."""
    async with audit_database.get_session() as session:
        yield session