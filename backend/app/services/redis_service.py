# backend/app/services/redis_service.py
"""
Enterprise Redis Service for Phase 0B Integration
Provides high-performance caching with connection pooling and monitoring
"""

import redis.asyncio as redis
import json
import logging
import asyncio
from typing import Any, Optional, Union, List, Dict, Pattern
from datetime import timedelta
from contextlib import asynccontextmanager
import time
from dataclasses import dataclass
from enum import Enum

from app.core.config import settings
from app.core.exceptions import CacheException
from app.core.service_interfaces import CacheStrategy

logger = logging.getLogger(__name__)

class SerializationStrategy(Enum):
    """Serialization strategies for different data types"""
    JSON = "json"
    RAW = "raw"

@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    hits: int = 0
    misses: int = 0
    errors: int = 0
    avg_response_time: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

class RedisService(CacheStrategy):
    """
    Enterprise Redis service with connection pooling and monitoring
    Implements CacheStrategy interface for consistent caching operations
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.connection_pool: Optional[redis.ConnectionPool] = None
        self._initialized = False
        self._metrics = CacheMetrics()
        
        # Configuration from settings
        self.redis_url = settings.redis.url
        self.max_connections = settings.redis.max_connections
        self.retry_on_timeout = settings.redis.retry_on_timeout
        self.health_check_interval = settings.redis.health_check_interval
        
        # Performance settings
        self.default_ttl = 3600  # 1 hour
        self.max_ttl = 86400     # 24 hours
        self.serialization_strategy = SerializationStrategy.JSON
    
    async def initialize(self) -> None:
        """Initialize Redis connection with enterprise-grade configuration"""
        if self._initialized:
            return
            
        try:
            # Create connection pool with optimized settings
            self.connection_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                retry_on_timeout=self.retry_on_timeout,
                health_check_interval=self.health_check_interval,
                decode_responses=False,  # Handle encoding manually for flexibility
                socket_keepalive=True,
                socket_keepalive_options={},
            )
            
            # Create Redis client
            self.redis_client = redis.Redis(
                connection_pool=self.connection_pool,
                decode_responses=False
            )
            
            # Test connection
            await self._health_check()
            
            self._initialized = True
            logger.info("✅ Redis service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Redis initialization failed: {e}")
            raise CacheException(
                "Redis initialization failed",
                context={"error": str(e), "redis_url": self.redis_url}
            )
    
    async def close(self) -> None:
        """Gracefully close Redis connections"""
        if self.redis_client:
            await self.redis_client.close()
        if self.connection_pool:
            await self.connection_pool.disconnect()
        
        self._initialized = False
        logger.info("🔐 Redis connections closed")
    
    @asynccontextmanager
    async def _timed_operation(self, operation_name: str):
        """Context manager for timing and error tracking"""
        start_time = time.time()
        try:
            yield
            self._metrics.hits += 1
        except Exception as e:
            self._metrics.errors += 1
            logger.error(f"Redis {operation_name} error: {e}")
            raise
        finally:
            duration = time.time() - start_time
            self._update_avg_response_time(duration)
    
    def _update_avg_response_time(self, duration: float):
        """Update average response time with exponential moving average"""
        alpha = 0.1  # Smoothing factor
        if self._metrics.avg_response_time == 0:
            self._metrics.avg_response_time = duration
        else:
            self._metrics.avg_response_time = (
                alpha * duration + (1 - alpha) * self._metrics.avg_response_time
            )
    
    def _serialize_value(self, value: Any, strategy: SerializationStrategy = None) -> bytes:
        """Serialize value based on strategy"""
        if strategy is None:
            strategy = self.serialization_strategy
            
        try:
            if strategy == SerializationStrategy.JSON:
                return json.dumps(value, default=str).encode('utf-8')
            elif strategy == SerializationStrategy.RAW:
                if isinstance(value, str):
                    return value.encode('utf-8')
                elif isinstance(value, bytes):
                    return value
                else:
                    return str(value).encode('utf-8')
            else:
                raise ValueError(f"Unknown serialization strategy: {strategy}")
                
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            raise CacheException(f"Failed to serialize value", context={"error": str(e)})
    
    def _deserialize_value(self, data: bytes, strategy: SerializationStrategy = None) -> Any:
        """Deserialize value based on strategy"""
        if strategy is None:
            strategy = self.serialization_strategy
            
        try:
            if strategy == SerializationStrategy.JSON:
                return json.loads(data.decode('utf-8'))
            elif strategy == SerializationStrategy.RAW:
                return data.decode('utf-8')
            else:
                raise ValueError(f"Unknown serialization strategy: {strategy}")
                
        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            raise CacheException(f"Failed to deserialize value", context={"error": str(e)})
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        if not self._initialized:
            await self.initialize()
            
        async with self._timed_operation("get"):
            try:
                data = await self.redis_client.get(key)
                if data is None:
                    self._metrics.misses += 1
                    return None
                    
                return self._deserialize_value(data)
                
            except Exception as e:
                logger.error(f"Redis GET error for key {key}: {e}")
                return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        strategy: SerializationStrategy = None
    ) -> bool:
        """Set value in Redis cache with optional TTL"""
        if not self._initialized:
            await self.initialize()
            
        async with self._timed_operation("set"):
            try:
                # Use default TTL if not specified
                if ttl is None:
                    ttl = self.default_ttl
                elif ttl > self.max_ttl:
                    ttl = self.max_ttl
                
                # Serialize value
                serialized_data = self._serialize_value(value, strategy)
                
                # Set with expiration
                success = await self.redis_client.setex(key, ttl, serialized_data)
                return bool(success)
                
            except Exception as e:
                logger.error(f"Redis SET error for key {key}: {e}")
                return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis cache"""
        if not self._initialized:
            await self.initialize()
            
        async with self._timed_operation("delete"):
            try:
                result = await self.redis_client.delete(key)
                return result > 0
                
            except Exception as e:
                logger.error(f"Redis DELETE error for key {key}: {e}")
                return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        if not self._initialized:
            await self.initialize()
            
        try:
            result = await self.redis_client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        if not self._initialized:
            await self.initialize()
            
        async with self._timed_operation("invalidate_pattern"):
            try:
                # Use SCAN to find matching keys (memory efficient)
                keys_deleted = 0
                async for key in self.redis_client.scan_iter(match=pattern, count=100):
                    await self.redis_client.delete(key)
                    keys_deleted += 1
                
                logger.info(f"Invalidated {keys_deleted} keys matching pattern: {pattern}")
                return keys_deleted
                
            except Exception as e:
                logger.error(f"Redis pattern invalidation error for {pattern}: {e}")
                return 0
    
    async def get_multiple(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values in a single operation"""
        if not self._initialized:
            await self.initialize()
            
        async with self._timed_operation("mget"):
            try:
                values = await self.redis_client.mget(keys)
                results = {}
                
                for key, value in zip(keys, values):
                    if value is not None:
                        try:
                            results[key] = self._deserialize_value(value)
                        except:
                            logger.warning(f"Failed to deserialize value for key: {key}")
                            
                return results
                
            except Exception as e:
                logger.error(f"Redis MGET error: {e}")
                return {}
    
    async def set_multiple(
        self, 
        key_value_pairs: Dict[str, Any], 
        ttl: Optional[int] = None
    ) -> bool:
        """Set multiple key-value pairs efficiently"""
        if not self._initialized:
            await self.initialize()
            
        async with self._timed_operation("mset"):
            try:
                # Serialize all values
                serialized_pairs = {}
                for key, value in key_value_pairs.items():
                    serialized_pairs[key] = self._serialize_value(value)
                
                # Use pipeline for efficiency
                async with self.redis_client.pipeline() as pipeline:
                    await pipeline.mset(serialized_pairs)
                    
                    # Set expiration for all keys if TTL specified
                    if ttl:
                        for key in serialized_pairs.keys():
                            await pipeline.expire(key, ttl)
                    
                    await pipeline.execute()
                
                return True
                
            except Exception as e:
                logger.error(f"Redis MSET error: {e}")
                return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment numeric value atomically"""
        if not self._initialized:
            await self.initialize()
            
        try:
            result = await self.redis_client.incrby(key, amount)
            return result
        except Exception as e:
            logger.error(f"Redis INCREMENT error for key {key}: {e}")
            return 0
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for existing key"""
        if not self._initialized:
            await self.initialize()
            
        try:
            result = await self.redis_client.expire(key, ttl)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key {key}: {e}")
            return False
    
    async def get_ttl(self, key: str) -> int:
        """Get TTL for key (-1 if no expiration, -2 if key doesn't exist)"""
        if not self._initialized:
            await self.initialize()
            
        try:
            return await self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL error for key {key}: {e}")
            return -2
    
    async def _health_check(self) -> bool:
        """Perform Redis health check"""
        try:
            # Test basic connectivity
            response = await self.redis_client.ping()
            if not response:
                raise CacheException("Redis PING failed")
            
            # Test read/write operations
            test_key = "health_check"
            test_value = {"timestamp": time.time(), "status": "healthy"}
            
            await self.redis_client.setex(test_key, 10, json.dumps(test_value))
            retrieved = await self.redis_client.get(test_key)
            
            if not retrieved:
                raise CacheException("Redis health check read/write test failed")
            
            await self.redis_client.delete(test_key)
            
            logger.info("✅ Redis health check passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Redis health check failed: {e}")
            raise CacheException(f"Redis health check failed: {e}")
    
    async def get_metrics(self) -> CacheMetrics:
        """Get current cache performance metrics"""
        return self._metrics
    
    async def get_info(self) -> Dict[str, Any]:
        """Get Redis server information"""
        if not self._initialized:
            await self.initialize()
            
        try:
            info = await self.redis_client.info()
            return {
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0)
            }
        except Exception as e:
            logger.error(f"Error getting Redis info: {e}")
            return {}
    
    async def flush_db(self, confirm: bool = False) -> bool:
        """Flush all keys from current database (use with caution)"""
        if not confirm:
            logger.warning("flush_db called without confirmation - ignoring")
            return False
            
        if not self._initialized:
            await self.initialize()
            
        try:
            await self.redis_client.flushdb()
            logger.warning("🗑️ Redis database flushed")
            return True
        except Exception as e:
            logger.error(f"Error flushing Redis database: {e}")
            return False

# Session-specific Redis operations
class RedisSessionService:
    """Redis operations specifically for session management"""
    
    def __init__(self, redis_service: RedisService):
        self.redis = redis_service
        self.session_prefix = "session"
        self.user_sessions_prefix = "user_sessions"
        self.session_ttl = 7200  # 2 hours
    
    async def store_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Store complete session data"""
        key = f"{self.session_prefix}:{session_id}"
        return await self.redis.set(key, session_data, ttl=self.session_ttl)
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve complete session data"""
        key = f"{self.session_prefix}:{session_id}"
        return await self.redis.get(key)
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update specific session fields"""
        key = f"{self.session_prefix}:{session_id}"
        
        # Get current session data
        current_data = await self.redis.get(key)
        if current_data is None:
            return False
        
        # Merge updates
        current_data.update(updates)
        
        # Store updated data
        return await self.redis.set(key, current_data, ttl=self.session_ttl)
    
    async def add_user_session(self, user_id: str, session_id: str) -> bool:
        """Track session for a user"""
        key = f"{self.user_sessions_prefix}:{user_id}"
        
        # Add session to user's session set
        try:
            await self.redis.redis_client.sadd(key, session_id)
            await self.redis.expire(key, self.session_ttl)
            return True
        except Exception as e:
            logger.error(f"Error adding user session: {e}")
            return False
    
    async def get_user_sessions(self, user_id: str) -> List[str]:
        """Get all active sessions for a user"""
        key = f"{self.user_sessions_prefix}:{user_id}"
        
        try:
            session_ids = await self.redis.redis_client.smembers(key)
            return [sid.decode('utf-8') for sid in session_ids]
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired session references"""
        try:
            # Find all user session keys
            pattern = f"{self.user_sessions_prefix}:*"
            cleaned = 0
            
            async for key in self.redis.redis_client.scan_iter(match=pattern):
                # Get all session IDs for this user
                session_ids = await self.redis.redis_client.smembers(key)
                
                for session_id in session_ids:
                    session_key = f"{self.session_prefix}:{session_id.decode('utf-8')}"
                    
                    # Check if session still exists
                    if not await self.redis.exists(session_key):
                        # Remove expired session from user's set
                        await self.redis.redis_client.srem(key, session_id)
                        cleaned += 1
            
            logger.info(f"Cleaned up {cleaned} expired session references")
            return cleaned
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0

# Analytics caching for mood statistics and insights
class RedisAnalyticsService:
    """Redis operations for caching analytics and statistics"""
    
    def __init__(self, redis_service: RedisService):
        self.redis = redis_service
        self.analytics_prefix = "analytics"
        self.stats_ttl = 900  # 15 minutes
    
    async def cache_mood_statistics(
        self, 
        user_id: str, 
        days: int, 
        stats: Dict[str, Any]
    ) -> bool:
        """Cache mood statistics for specific time period"""
        key = f"{self.analytics_prefix}:mood_stats:{user_id}:{days}d"
        return await self.redis.set(key, stats, ttl=self.stats_ttl)
    
    async def get_cached_mood_statistics(
        self, 
        user_id: str, 
        days: int
    ) -> Optional[Dict[str, Any]]:
        """Get cached mood statistics"""
        key = f"{self.analytics_prefix}:mood_stats:{user_id}:{days}d"
        return await self.redis.get(key)
    
    async def cache_writing_statistics(
        self, 
        user_id: str, 
        stats: Dict[str, Any]
    ) -> bool:
        """Cache writing/entry statistics"""
        key = f"{self.analytics_prefix}:writing_stats:{user_id}"
        return await self.redis.set(key, stats, ttl=self.stats_ttl)
    
    async def increment_usage_counter(self, metric_name: str) -> int:
        """Increment usage counters for analytics"""
        key = f"{self.analytics_prefix}:counters:{metric_name}"
        count = await self.redis.increment(key)
        
        # Set expiration for daily counters
        if "daily" in metric_name:
            await self.redis.expire(key, 86400)  # 24 hours
        
        return count

# Global Redis service instances
redis_service = RedisService()
redis_session_service = RedisSessionService(redis_service)
redis_analytics_service = RedisAnalyticsService(redis_service)