# backend/app/services/performance_cache_service.py
"""
Advanced caching service for performance optimization
"""

import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import hashlib
import asyncio

from app.core.config import settings
from app.services.redis_service_simple import simple_redis_service as redis_service

logger = logging.getLogger(__name__)

@dataclass
class CacheMetadata:
    """Metadata for cached items"""
    key: str
    created_at: datetime
    expires_at: Optional[datetime]
    size_bytes: int
    access_count: int
    last_accessed: datetime
    tags: List[str]

class PerformanceCacheService:
    """
    High-performance caching service with intelligent cache management
    """
    
    def __init__(self):
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0
        }
        self.default_ttl = 3600  # 1 hour
        
        # Cache namespaces for different data types
        self.namespaces = {
            'entries': 'pe:entries:',
            'insights': 'pe:insights:',
            'search': 'pe:search:',
            'user_data': 'pe:user:',
            'computed': 'pe:computed:',
            'api_responses': 'pe:api:'
        }
    
    def _generate_cache_key(self, namespace: str, identifier: str, **kwargs) -> str:
        """Generate a consistent cache key"""
        base_key = f"{self.namespaces.get(namespace, 'pe:generic:')}{identifier}"
        
        if kwargs:
            # Sort kwargs for consistent key generation
            sorted_params = sorted(kwargs.items())
            params_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
            # Hash long parameter strings to keep keys manageable
            if len(params_str) > 100:
                params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
                base_key = f"{base_key}:h:{params_hash}"
            else:
                base_key = f"{base_key}:{params_str}"
        
        return base_key
    
    async def get(
        self, 
        namespace: str, 
        identifier: str, 
        default: Any = None,
        **kwargs
    ) -> Optional[Any]:
        """Get cached item with automatic deserialization"""
        try:
            cache_key = self._generate_cache_key(namespace, identifier, **kwargs)
            
            if not await redis_service.is_connected():
                logger.warning("Redis not connected, cache miss")
                self.cache_stats['misses'] += 1
                return default
            
            cached_data = await redis_service.get_json(cache_key)
            
            if cached_data is not None:
                self.cache_stats['hits'] += 1
                
                # Update access metadata if tracking is enabled
                if settings.ENABLE_CACHE_ANALYTICS:
                    await self._update_access_metadata(cache_key)
                
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_data
            else:
                self.cache_stats['misses'] += 1
                logger.debug(f"Cache miss for key: {cache_key}")
                return default
                
        except Exception as e:
            logger.error(f"Error getting cached item: {e}")
            self.cache_stats['misses'] += 1
            return default
    
    async def set(
        self,
        namespace: str,
        identifier: str,
        data: Any,
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> bool:
        """Set cached item with metadata tracking"""
        try:
            cache_key = self._generate_cache_key(namespace, identifier, **kwargs)
            
            if not await redis_service.is_connected():
                logger.warning("Redis not connected, cache set failed")
                return False
            
            ttl = ttl or self.default_ttl
            
            # Set the data
            success = await redis_service.set_json(cache_key, data, expire=ttl)
            
            if success:
                self.cache_stats['sets'] += 1
                
                # Store metadata if tracking is enabled
                if settings.ENABLE_CACHE_ANALYTICS:
                    await self._store_cache_metadata(cache_key, data, ttl, tags or [])
                
                # Handle cache tags for invalidation
                if tags:
                    await self._associate_tags(cache_key, tags)
                
                logger.debug(f"Cache set for key: {cache_key}")
                return True
            else:
                logger.warning(f"Failed to set cache for key: {cache_key}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting cached item: {e}")
            return False
    
    async def delete(self, namespace: str, identifier: str, **kwargs) -> bool:
        """Delete cached item"""
        try:
            cache_key = self._generate_cache_key(namespace, identifier, **kwargs)
            
            if not await redis_service.is_connected():
                return False
            
            success = await redis_service.delete(cache_key)
            
            if success:
                self.cache_stats['deletes'] += 1
                
                # Clean up metadata
                if settings.ENABLE_CACHE_ANALYTICS:
                    await self._delete_cache_metadata(cache_key)
                
                logger.debug(f"Cache deleted for key: {cache_key}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting cached item: {e}")
            return False
    
    async def invalidate_by_tags(self, tags: List[str]) -> int:
        """Invalidate all cached items with specified tags"""
        try:
            if not await redis_service.is_connected():
                return 0
            
            deleted_count = 0
            
            for tag in tags:
                tag_key = f"cache_tag:{tag}"
                
                # Get all keys associated with this tag
                associated_keys = await redis_service.client.smembers(tag_key)
                
                if associated_keys:
                    # Delete all associated cache entries
                    pipeline = redis_service.client.pipeline()
                    for key in associated_keys:
                        pipeline.delete(key)
                    
                    # Delete the tag set itself
                    pipeline.delete(tag_key)
                    
                    results = await pipeline.execute()
                    deleted_count += len([r for r in results if r])
            
            self.cache_stats['deletes'] += deleted_count
            logger.info(f"Invalidated {deleted_count} cache entries by tags: {tags}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error invalidating cache by tags: {e}")
            return 0
    
    async def get_or_compute(
        self,
        namespace: str,
        identifier: str,
        compute_func,
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> Any:
        """Get from cache or compute and cache the result"""
        # Try to get from cache first
        cached_result = await self.get(namespace, identifier, **kwargs)
        
        if cached_result is not None:
            return cached_result
        
        # Compute the result
        try:
            if asyncio.iscoroutinefunction(compute_func):
                result = await compute_func()
            else:
                result = compute_func()
            
            # Cache the computed result
            await self.set(
                namespace, 
                identifier, 
                result, 
                ttl=ttl, 
                tags=tags,
                **kwargs
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error computing cache value: {e}")
            raise
    
    async def warm_cache(self, cache_configs: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Warm cache with predefined configurations"""
        results = {}
        
        for config in cache_configs:
            try:
                namespace = config['namespace']
                identifier = config['identifier']
                compute_func = config['compute_func']
                ttl = config.get('ttl')
                tags = config.get('tags')
                kwargs = config.get('kwargs', {})
                
                # Warm the cache
                await self.get_or_compute(
                    namespace, identifier, compute_func, ttl, tags, **kwargs
                )
                
                results[f"{namespace}:{identifier}"] = True
                
            except Exception as e:
                logger.error(f"Error warming cache for config {config}: {e}")
                results[f"{namespace}:{identifier}"] = False
        
        return results
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        try:
            # Basic stats
            hit_ratio = (
                self.cache_stats['hits'] / 
                (self.cache_stats['hits'] + self.cache_stats['misses'])
                if (self.cache_stats['hits'] + self.cache_stats['misses']) > 0 
                else 0
            )
            
            stats = {
                **self.cache_stats,
                'hit_ratio': round(hit_ratio * 100, 2),
                'redis_connected': await redis_service.is_connected()
            }
            
            # Redis memory stats if available
            if await redis_service.is_connected():
                try:
                    info = await redis_service.client.info('memory')
                    stats['redis_memory'] = {
                        'used_memory': info.get('used_memory'),
                        'used_memory_human': info.get('used_memory_human'),
                        'max_memory': info.get('maxmemory'),
                        'evicted_keys': info.get('evicted_keys', 0)
                    }
                except Exception as e:
                    logger.warning(f"Could not get Redis memory info: {e}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return self.cache_stats
    
    async def clear_namespace(self, namespace: str) -> int:
        """Clear all cache entries in a namespace"""
        try:
            if not await redis_service.is_connected():
                return 0
            
            pattern = f"{self.namespaces.get(namespace, 'pe:generic:')}*"
            keys = []
            
            async for key in redis_service.client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted_count = await redis_service.client.delete(*keys)
                self.cache_stats['deletes'] += deleted_count
                logger.info(f"Cleared {deleted_count} cache entries from namespace: {namespace}")
                return deleted_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Error clearing namespace {namespace}: {e}")
            return 0
    
    async def _update_access_metadata(self, cache_key: str) -> None:
        """Update access metadata for cache analytics"""
        try:
            metadata_key = f"cache_meta:{cache_key}"
            
            # Increment access count and update last accessed time
            pipeline = redis_service.client.pipeline()
            pipeline.hincrby(metadata_key, 'access_count', 1)
            pipeline.hset(metadata_key, 'last_accessed', datetime.utcnow().isoformat())
            await pipeline.execute()
            
        except Exception as e:
            logger.debug(f"Error updating access metadata: {e}")
    
    async def _store_cache_metadata(
        self, 
        cache_key: str, 
        data: Any, 
        ttl: int, 
        tags: List[str]
    ) -> None:
        """Store metadata for cache analytics"""
        try:
            metadata_key = f"cache_meta:{cache_key}"
            
            now = datetime.utcnow()
            expires_at = now + timedelta(seconds=ttl)
            
            # Estimate size
            data_size = len(json.dumps(data, default=str).encode('utf-8'))
            
            metadata = {
                'key': cache_key,
                'created_at': now.isoformat(),
                'expires_at': expires_at.isoformat(),
                'size_bytes': data_size,
                'access_count': 0,
                'last_accessed': now.isoformat(),
                'tags': json.dumps(tags)
            }
            
            await redis_service.client.hset(metadata_key, mapping=metadata)
            await redis_service.client.expire(metadata_key, ttl + 3600)  # Keep metadata a bit longer
            
        except Exception as e:
            logger.debug(f"Error storing cache metadata: {e}")
    
    async def _associate_tags(self, cache_key: str, tags: List[str]) -> None:
        """Associate cache key with tags for invalidation"""
        try:
            pipeline = redis_service.client.pipeline()
            
            for tag in tags:
                tag_key = f"cache_tag:{tag}"
                pipeline.sadd(tag_key, cache_key)
                pipeline.expire(tag_key, self.default_ttl + 3600)  # Keep tags a bit longer
            
            await pipeline.execute()
            
        except Exception as e:
            logger.debug(f"Error associating tags: {e}")
    
    async def _delete_cache_metadata(self, cache_key: str) -> None:
        """Delete cache metadata"""
        try:
            metadata_key = f"cache_meta:{cache_key}"
            await redis_service.client.delete(metadata_key)
        except Exception as e:
            logger.debug(f"Error deleting cache metadata: {e}")

# Global instance
performance_cache = PerformanceCacheService()