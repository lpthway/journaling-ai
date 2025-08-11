# backend/app/services/redis_service_simple.py
"""
Simplified Redis Service to avoid recursion issues
Uses basic connection without complex pooling
"""

import redis.asyncio as redis
import json
import logging
from typing import Any, Optional, Dict
from datetime import datetime
from dataclasses import dataclass, asdict
import time
from decimal import Decimal
from enum import Enum

from app.core.config import settings
from app.core.exceptions import CacheException
from app.core.service_interfaces import CacheStrategy

logger = logging.getLogger(__name__)

class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle enums, Decimal, datetime, and other objects"""
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)

@dataclass
class CacheMetrics:
    hits: int = 0
    misses: int = 0
    errors: int = 0
    operations: int = 0
    avg_response_time: float = 0.0
    memory_usage_mb: float = 0.0
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

class SimpleRedisService(CacheStrategy):
    """Enhanced Redis service with connection pooling and advanced features"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._initialized = False
        self._metrics = CacheMetrics()
        
        # Phase 3: Enhanced configuration with connection pooling
        self.redis_url = "redis://:password@localhost:6379/0"
        self.max_connections = 20
        self.retry_on_timeout = True
        self.socket_keepalive = True
        self.default_ttl = 3600  # 1 hour
        self.max_ttl = 86400     # 24 hours
        
        # Log URL format for debugging (mask password)
        masked_url = self.redis_url.replace('password', '***')
        logger.info(f"Enhanced Redis service initialized with URL: {masked_url}, pool_size: {self.max_connections}")

    async def initialize(self) -> None:
        """Initialize Redis connection with enhanced connection pooling"""
        if self._initialized:
            return
            
        try:
            # Phase 3: Create Redis client with connection pooling and enhanced features
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=False,
                retry_on_timeout=self.retry_on_timeout,
                socket_keepalive=self.socket_keepalive,
                socket_keepalive_options={},
                max_connections=self.max_connections,
                encoding='utf-8',
                encoding_errors='strict'
            )
            
            # Enhanced connection test with health check
            await self._perform_health_check()
            
            self._initialized = True
            logger.info(f"✅ Enhanced Redis service initialized with connection pool (max_connections: {self.max_connections})")
            
        except Exception as e:
            logger.error(f"❌ Enhanced Redis initialization failed: {e}")
            raise CacheException(f"Enhanced Redis initialization failed: {e}")

    async def close(self) -> None:
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
        self._initialized = False
        logger.info("🔐 Simple Redis connection closed")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._initialized:
            return None
            
        try:
            start_time = time.time()
            result = await self.redis_client.get(key)
            response_time = (time.time() - start_time) * 1000
            
            if result:
                self._metrics.hits += 1
                try:
                    return json.loads(result)
                except json.JSONDecodeError:
                    return result.decode('utf-8') if isinstance(result, bytes) else result
            else:
                self._metrics.misses += 1
                return None
                
        except Exception as e:
            self._metrics.errors += 1
            logger.warning(f"Redis GET error for key {key}: {e}")
            return None

    async def _perform_health_check(self) -> None:
        """Perform comprehensive health check"""
        # Basic connectivity test
        await self.redis_client.ping()
        
        # Read/write test
        test_key = f"health_check_{int(time.time())}"
        test_value = "health_check_value"
        
        # Test write
        await self.redis_client.set(test_key, test_value, ex=10)  # 10 second TTL
        
        # Test read
        result = await self.redis_client.get(test_key)
        if result.decode('utf-8') != test_value:
            raise CacheException("Health check read/write test failed")
        
        # Cleanup test key
        await self.redis_client.delete(test_key)
        
        logger.debug("✅ Redis health check passed")
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        if not self._initialized:
            return False
            
        try:
            start_time = time.time()
            
            # Serialize value with custom encoder
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, cls=JSONEncoder)
            else:
                serialized_value = str(value)
            
            # Phase 3: Enhanced TTL handling with validation
            if ttl:
                # Validate TTL bounds
                if ttl > self.max_ttl:
                    ttl = self.max_ttl
                    logger.warning(f"TTL capped to max_ttl ({self.max_ttl}s) for key {key}")
                result = await self.redis_client.setex(key, ttl, serialized_value)
            else:
                # Use default TTL for better cache management
                result = await self.redis_client.setex(key, self.default_ttl, serialized_value)
            
            response_time = (time.time() - start_time) * 1000
            self._metrics.operations += 1
            
            return bool(result)
            
        except Exception as e:
            self._metrics.errors += 1
            logger.warning(f"Redis SET error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._initialized:
            return False
            
        try:
            result = await self.redis_client.delete(key)
            self._metrics.operations += 1
            return bool(result)
        except Exception as e:
            self._metrics.errors += 1
            logger.warning(f"Redis DELETE error for key {key}: {e}")
            return False

    async def flush_db(self) -> bool:
        """
        Flush all data from the current database
        ⚠️ WARNING: This will delete ALL cached data!
        """
        if not self._initialized:
            return False
            
        try:
            logger.warning("🗑️ Flushing Redis database - ALL data will be deleted!")
            result = await self.redis_client.flushdb()
            self._metrics.operations += 1
            logger.info("✅ Redis database flushed successfully")
            return bool(result)
        except Exception as e:
            self._metrics.errors += 1
            logger.error(f"Redis FLUSHDB error: {e}")
            return False

    async def ping(self) -> bool:
        """
        Ping Redis server to check connectivity
        """
        if not self._initialized:
            return False
            
        try:
            result = await self.redis_client.ping()
            return bool(result)
        except Exception as e:
            logger.error(f"Redis PING error: {e}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate keys matching pattern"""
        if not self._initialized:
            return 0
            
        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                self._metrics.operations += len(keys)
                return deleted
            return 0
            
        except Exception as e:
            self._metrics.errors += 1
            logger.warning(f"Redis INVALIDATE_PATTERN error for pattern {pattern}: {e}")
            return 0

    async def get_metrics(self) -> CacheMetrics:
        """Get current cache performance metrics"""
        return self._metrics

    async def get_info(self) -> Dict[str, Any]:
        """Get comprehensive Redis server information"""
        if not self._initialized:
            return {}
            
        try:
            info = await self.redis_client.info()
            
            # Phase 3: Enhanced metrics collection
            return {
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "used_memory_peak": info.get("used_memory_peak_human"),
                "connected_clients": info.get("connected_clients"),
                "blocked_clients": info.get("blocked_clients", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0),
                "role": info.get("role", "unknown"),
                # Connection pool metrics
                "max_connections": self.max_connections,
                "connection_pool_created": info.get("total_connections_received", 0),
                # Cache configuration
                "default_ttl": self.default_ttl,
                "max_ttl": self.max_ttl
            }
        except Exception as e:
            logger.error(f"Error getting enhanced Redis info: {e}")
            return {}
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        try:
            if hasattr(self.redis_client, 'connection_pool'):
                pool = self.redis_client.connection_pool
                return {
                    "created_connections": getattr(pool, '_created_connections', 0),
                    "available_connections": len(getattr(pool, '_available_connections', [])),
                    "in_use_connections": len(getattr(pool, '_in_use_connections', {})),
                    "max_connections": self.max_connections
                }
            return {"status": "no_pool_info"}
        except Exception as e:
            logger.error(f"Error getting connection stats: {e}")
            return {"error": str(e)}

# Global simple service instance
simple_redis_service = SimpleRedisService()