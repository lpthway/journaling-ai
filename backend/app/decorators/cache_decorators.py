# backend/app/decorators/cache_decorators.py
"""
Enterprise Cache Decorators for Seamless Redis Integration
Provides transparent caching capabilities for existing services
"""

import functools
import logging
import time
import hashlib
import json
from typing import Any, Callable, Dict, List, Optional, Union, TypeVar
from datetime import timedelta
import asyncio

from app.core.service_interfaces import service_registry
from app.core.exceptions import CacheException
from app.core.performance_monitor import performance_monitor

logger = logging.getLogger(__name__)

T = TypeVar('T')

class CacheConfig:
    """Configuration for cache decorators"""
    
    def __init__(
        self,
        ttl: int = 3600,
        key_prefix: str = "cache",
        version: str = "v1",
        serialization_strategy: str = "json",
        invalidation_patterns: Optional[List[str]] = None,
        monitor_performance: bool = True,
        fallback_on_error: bool = True
    ):
        self.ttl = ttl
        self.key_prefix = key_prefix
        self.version = version
        self.serialization_strategy = serialization_strategy
        self.invalidation_patterns = invalidation_patterns or []
        self.monitor_performance = monitor_performance
        self.fallback_on_error = fallback_on_error

def generate_cache_key(*args, key_prefix: str = "cache", **kwargs) -> str:
    """
    Generate consistent cache key from function arguments
    
    Args:
        *args: Function positional arguments
        key_prefix: Prefix for the cache key
        **kwargs: Function keyword arguments
        
    Returns:
        Consistent cache key string
    """
    # Create deterministic representation of arguments
    key_data = {
        'args': [str(arg) for arg in args],
        'kwargs': {k: str(v) for k, v in sorted(kwargs.items())}
    }
    
    # Generate hash for consistent key
    key_string = json.dumps(key_data, sort_keys=True)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()[:8]
    
    return f"{key_prefix}:{key_hash}"

def cached(
    ttl: int = 3600,
    key_prefix: str = "cache",
    key_generator: Optional[Callable] = None,
    invalidation_patterns: Optional[List[str]] = None,
    monitor_performance: bool = True,
    fallback_on_error: bool = True,
    version: str = "v1"
):
    """
    Decorator for automatic caching of function results
    
    Features:
    - Intelligent cache key generation
    - Configurable TTL and invalidation patterns
    - Performance monitoring integration
    - Graceful error handling with fallback
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys
        key_generator: Custom function for generating cache keys
        invalidation_patterns: Patterns to invalidate when data changes
        monitor_performance: Enable performance monitoring
        fallback_on_error: Fall back to function execution on cache errors
        version: Cache version for invalidation
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            cache_strategy = service_registry.get_cache_strategy()
            
            # Generate cache key
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                cache_key = generate_cache_key(*args, key_prefix=key_prefix, **kwargs)
            
            # Add version to cache key
            versioned_key = f"{cache_key}:{version}"
            
            # Performance monitoring
            operation_name = f"cache_get_{func.__name__}"
            tags = {"function": func.__name__, "key_prefix": key_prefix}
            
            try:
                # Try to get from cache first
                if cache_strategy and monitor_performance:
                    async with performance_monitor.timed_operation(operation_name, tags):
                        cached_result = await cache_strategy.get(versioned_key)
                elif cache_strategy:
                    cached_result = await cache_strategy.get(versioned_key)
                else:
                    cached_result = None
                
                if cached_result is not None:
                    logger.debug(f"Cache hit for {func.__name__}: {versioned_key}")
                    return cached_result
                
                # Cache miss - execute function
                logger.debug(f"Cache miss for {func.__name__}: {versioned_key}")
                
                if monitor_performance:
                    async with performance_monitor.timed_operation(f"function_{func.__name__}", tags):
                        result = await func(*args, **kwargs)
                else:
                    result = await func(*args, **kwargs)
                
                # Store result in cache
                if cache_strategy:
                    try:
                        await cache_strategy.set(versioned_key, result, ttl)
                        logger.debug(f"Cached result for {func.__name__}: {versioned_key}")
                    except Exception as cache_error:
                        logger.warning(f"Failed to cache result for {func.__name__}: {cache_error}")
                
                return result
                
            except Exception as e:
                if fallback_on_error:
                    logger.warning(f"Cache error for {func.__name__}, falling back to function: {e}")
                    return await func(*args, **kwargs)
                else:
                    raise CacheException(f"Cache operation failed for {func.__name__}", context={"error": str(e)})
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            # For synchronous functions, convert to async internally
            async def async_version():
                return await async_wrapper(*args, **kwargs)
            
            # Run in event loop
            try:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(async_version())
            except RuntimeError:
                # No event loop running, create new one
                return asyncio.run(async_version())
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def cache_invalidate(
    patterns: List[str],
    immediate: bool = True,
    cascade: bool = False
):
    """
    Decorator for automatic cache invalidation after function execution
    
    Args:
        patterns: List of cache key patterns to invalidate
        immediate: Invalidate immediately after function execution
        cascade: Also invalidate related cache patterns
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            cache_strategy = service_registry.get_cache_strategy()
            
            # Execute function first
            result = await func(*args, **kwargs)
            
            # Invalidate cache patterns
            if cache_strategy and immediate:
                try:
                    for pattern in patterns:
                        invalidated_count = await cache_strategy.invalidate_pattern(pattern)
                        logger.info(f"Invalidated {invalidated_count} cache keys for pattern: {pattern}")
                        
                        # Cascade invalidation if requested
                        if cascade:
                            cascade_patterns = _generate_cascade_patterns(pattern)
                            for cascade_pattern in cascade_patterns:
                                cascade_count = await cache_strategy.invalidate_pattern(cascade_pattern)
                                logger.debug(f"Cascade invalidated {cascade_count} keys for: {cascade_pattern}")
                                
                except Exception as e:
                    logger.warning(f"Cache invalidation failed for {func.__name__}: {e}")
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            async def async_version():
                return await async_wrapper(*args, **kwargs)
            
            try:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(async_version())
            except RuntimeError:
                return asyncio.run(async_version())
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def timed_operation(
    operation_name: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
    track_errors: bool = True,
    log_slow_operations: bool = True,
    slow_threshold_ms: float = 100.0
):
    """
    Decorator for performance monitoring and timing
    
    Args:
        operation_name: Name for the operation (defaults to function name)
        tags: Additional tags for metrics
        track_errors: Track errors in performance metrics
        log_slow_operations: Log operations that exceed threshold
        slow_threshold_ms: Threshold for slow operation logging
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            op_name = operation_name or func.__name__
            op_tags = tags or {}
            op_tags.update({"function": func.__name__})
            
            try:
                async with performance_monitor.timed_operation(op_name, op_tags):
                    return await func(*args, **kwargs)
            except Exception as e:
                if track_errors:
                    logger.error(f"Error in timed operation {op_name}: {e}")
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            op_name = operation_name or func.__name__
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # Log slow operations
                duration_ms = (time.time() - start_time) * 1000
                if log_slow_operations and duration_ms > slow_threshold_ms:
                    logger.warning(f"Slow operation {op_name}: {duration_ms:.2f}ms")
                
                return result
                
            except Exception as e:
                if track_errors:
                    logger.error(f"Error in timed operation {op_name}: {e}")
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def redis_session_cache(
    session_ttl: int = 7200,  # 2 hours
    auto_refresh: bool = True,
    track_activity: bool = True
):
    """
    Specialized decorator for session-related caching
    
    Args:
        session_ttl: Session time to live in seconds
        auto_refresh: Automatically refresh session TTL on access
        track_activity: Track session activity for analytics
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            cache_strategy = service_registry.get_cache_strategy()
            
            # Extract session_id if available
            session_id = None
            if args and hasattr(args[0], 'session_id'):
                session_id = args[0].session_id
            elif 'session_id' in kwargs:
                session_id = kwargs['session_id']
            
            # Generate session-specific cache key
            session_key = f"session:{session_id}:{func.__name__}" if session_id else f"session_cache:{func.__name__}"
            
            try:
                # Check session cache
                if cache_strategy:
                    cached_result = await cache_strategy.get(session_key)
                    
                    if cached_result is not None:
                        # Auto-refresh TTL on access
                        if auto_refresh:
                            await cache_strategy.expire(session_key, session_ttl)
                        
                        # Track activity
                        if track_activity and session_id:
                            activity_key = f"session_activity:{session_id}"
                            await cache_strategy.set(activity_key, time.time(), ttl=session_ttl)
                        
                        return cached_result
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                
                if cache_strategy:
                    await cache_strategy.set(session_key, result, session_ttl)
                
                return result
                
            except Exception as e:
                logger.warning(f"Session cache error for {func.__name__}: {e}")
                return await func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            # Convert to async for session handling
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                async def async_version():
                    return await async_wrapper(*args, **kwargs)
                
                try:
                    loop = asyncio.get_event_loop()
                    return loop.run_until_complete(async_version())
                except RuntimeError:
                    return asyncio.run(async_version())
            
            return sync_wrapper
    
    return decorator

def psychology_cache(
    knowledge_ttl: int = 86400,  # 24 hours for psychology content
    domain_specific: bool = True,
    high_priority: bool = True
):
    """
    Specialized caching for psychology knowledge queries
    Optimized for <2ms response times as per Phase 0B requirements
    
    Args:
        knowledge_ttl: TTL for psychology knowledge cache
        domain_specific: Enable domain-specific cache partitioning
        high_priority: Use high-priority cache storage
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            cache_strategy = service_registry.get_cache_strategy()
            
            # Generate psychology-specific cache key
            domain = kwargs.get('domain', 'general')
            query_hash = hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()[:12]
            
            if domain_specific:
                cache_key = f"psychology:{domain}:{func.__name__}:{query_hash}"
            else:
                cache_key = f"psychology:{func.__name__}:{query_hash}"
            
            # Performance monitoring with psychology-specific target
            tags = {"component": "psychology", "domain": domain, "target_ms": "2"}
            
            try:
                async with performance_monitor.timed_operation(f"psychology_{func.__name__}", tags):
                    if cache_strategy:
                        cached_result = await cache_strategy.get(cache_key)
                        if cached_result is not None:
                            return cached_result
                    
                    # Execute function with performance tracking
                    result = await func(*args, **kwargs)
                    
                    # Cache with psychology-specific TTL
                    if cache_strategy:
                        await cache_strategy.set(cache_key, result, knowledge_ttl)
                    
                    return result
                    
            except Exception as e:
                logger.warning(f"Psychology cache error for {func.__name__}: {e}")
                return await func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                async def async_version():
                    return await async_wrapper(*args, **kwargs)
                
                try:
                    loop = asyncio.get_event_loop()
                    return loop.run_until_complete(async_version())
                except RuntimeError:
                    return asyncio.run(async_version())
            
            return sync_wrapper
    
    return decorator

def _generate_cascade_patterns(base_pattern: str) -> List[str]:
    """Generate cascade invalidation patterns"""
    cascade_patterns = []
    
    # Remove specific parts to create broader patterns
    if ':' in base_pattern:
        parts = base_pattern.split(':')
        # Create patterns with fewer specificity
        for i in range(len(parts) - 1, 0, -1):
            cascade_pattern = ':'.join(parts[:i]) + ':*'
            cascade_patterns.append(cascade_pattern)
    
    return cascade_patterns

# Utility functions for cache management
async def warm_cache(func: Callable, cache_key: str, *args, **kwargs):
    """Warm up cache by pre-loading data"""
    cache_strategy = service_registry.get_cache_strategy()
    
    if cache_strategy:
        try:
            result = await func(*args, **kwargs)
            await cache_strategy.set(cache_key, result)
            logger.info(f"Warmed cache for key: {cache_key}")
        except Exception as e:
            logger.error(f"Cache warming failed for {cache_key}: {e}")

async def invalidate_user_cache(user_id: str):
    """Invalidate all cache entries for a specific user"""
    cache_strategy = service_registry.get_cache_strategy()
    
    if cache_strategy:
        patterns = [
            f"cache:*user_id*{user_id}*",
            f"session:{user_id}:*",
            f"analytics:*:{user_id}:*",
            f"user_data:{user_id}:*"
        ]
        
        total_invalidated = 0
        for pattern in patterns:
            count = await cache_strategy.invalidate_pattern(pattern)
            total_invalidated += count
        
        logger.info(f"Invalidated {total_invalidated} cache entries for user {user_id}")
        return total_invalidated

async def get_cache_stats() -> Dict[str, Any]:
    """Get comprehensive cache statistics"""
    cache_strategy = service_registry.get_cache_strategy()
    
    if not cache_strategy:
        return {"error": "No cache strategy available"}
    
    try:
        if hasattr(cache_strategy, 'get_metrics'):
            metrics = await cache_strategy.get_metrics()
            return {
                "hit_rate": metrics.hit_rate,
                "avg_response_time": metrics.avg_response_time,
                "total_operations": metrics.hits + metrics.misses,
                "errors": metrics.errors
            }
        else:
            return {"status": "Cache strategy available but no metrics"}
            
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {"error": str(e)}

# Example usage patterns for different service types
class CachePatterns:
    """Common cache decorator patterns for different service types"""
    
    # Entry operations
    ENTRY_READ = cached(ttl=3600, key_prefix="entry", monitor_performance=True)
    ENTRY_SEARCH = cached(ttl=900, key_prefix="entry_search", monitor_performance=True)  # 15 min
    ENTRY_ANALYTICS = cached(ttl=1800, key_prefix="entry_analytics")  # 30 min
    
    # Session operations
    SESSION_READ = redis_session_cache(session_ttl=7200, auto_refresh=True)
    SESSION_ACTIVITY = redis_session_cache(session_ttl=3600, track_activity=True)
    
    # Psychology knowledge
    PSYCHOLOGY_QUERY = psychology_cache(knowledge_ttl=86400, domain_specific=True)
    PSYCHOLOGY_TECHNIQUE = psychology_cache(knowledge_ttl=172800, high_priority=True)  # 48 hours
    
    # Analytics and statistics
    ANALYTICS_DAILY = cached(ttl=86400, key_prefix="analytics_daily")  # 24 hours
    ANALYTICS_HOURLY = cached(ttl=3600, key_prefix="analytics_hourly")  # 1 hour
    
    # Invalidation patterns
    INVALIDATE_USER_DATA = cache_invalidate(patterns=["user_data:*", "analytics:*"])
    INVALIDATE_ENTRIES = cache_invalidate(patterns=["entry:*", "entry_search:*", "entry_analytics:*"])
    INVALIDATE_SESSIONS = cache_invalidate(patterns=["session:*"], immediate=True)