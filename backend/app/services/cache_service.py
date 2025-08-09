# backend/app/services/cache_service.py
"""
Unified Cache Service with Standardized Patterns
Provides easy-to-use interface for all caching operations across the application
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import asyncio

from app.core.cache_patterns import (
    CachePatterns, CacheTTL, CacheKeyBuilder, CacheDomain, 
    CacheInvalidationPatterns, CacheMetrics
)
from app.services.redis_service import redis_service

logger = logging.getLogger(__name__)


class UnifiedCacheService:
    """
    Unified cache service that provides standardized caching operations
    Replaces direct Redis calls with pattern-based caching
    """
    
    def __init__(self):
        self.redis = redis_service
        
    # =============================================================================
    # ANALYTICS DOMAIN METHODS
    # =============================================================================
    
    async def get_analytics_daily(self, user_id: str = None, date: str = None) -> Optional[Any]:
        """Get daily analytics from cache"""
        cache_key = CachePatterns.analytics_daily(user_id, date)
        return await self.redis.get(cache_key)
    
    async def set_analytics_daily(self, data: Any, user_id: str = None, date: str = None, 
                                 ttl: int = None) -> bool:
        """Set daily analytics in cache"""
        cache_key = CachePatterns.analytics_daily(user_id, date)
        ttl = ttl or CacheTTL.ANALYTICS_DEFAULT
        return await self.redis.set(cache_key, data, ttl=ttl)
    
    async def get_mood_trends(self, user_id: str, time_range: str = "7d") -> Optional[Any]:
        """Get mood trends from cache"""
        cache_key = CachePatterns.analytics_mood_trends(user_id, time_range)
        return await self.redis.get(cache_key)
    
    async def set_mood_trends(self, data: Any, user_id: str, time_range: str = "7d", 
                             ttl: int = None) -> bool:
        """Set mood trends in cache"""
        cache_key = CachePatterns.analytics_mood_trends(user_id, time_range)
        ttl = ttl or CacheTTL.ANALYTICS_DEFAULT
        return await self.redis.set(cache_key, data, ttl=ttl)
    
    async def get_writing_stats(self, user_id: str, days: int) -> Optional[Any]:
        """Get writing statistics from cache"""
        cache_key = CachePatterns.analytics_writing_stats(user_id, days)
        return await self.redis.get(cache_key)
    
    async def set_writing_stats(self, data: Any, user_id: str, days: int, 
                               ttl: int = None) -> bool:
        """Set writing statistics in cache"""
        cache_key = CachePatterns.analytics_writing_stats(user_id, days)
        ttl = ttl or CacheTTL.MEDIUM_SHORT  # 15 minutes for writing stats
        return await self.redis.set(cache_key, data, ttl=ttl)
    
    # =============================================================================
    # PSYCHOLOGY DOMAIN METHODS
    # =============================================================================
    
    async def get_psychology_profile(self, user_id: str) -> Optional[Any]:
        """Get user psychology profile from cache"""
        cache_key = CachePatterns.psychology_profile(user_id)
        return await self.redis.get(cache_key)
    
    async def set_psychology_profile(self, data: Any, user_id: str, ttl: int = None) -> bool:
        """Set user psychology profile in cache"""
        cache_key = CachePatterns.psychology_profile(user_id)
        ttl = ttl or CacheTTL.PSYCHOLOGY_DEFAULT
        return await self.redis.set(cache_key, data, ttl=ttl)
    
    async def get_psychology_content_analysis(self, content_id: str) -> Optional[Any]:
        """Get psychology content analysis from cache"""
        cache_key = CachePatterns.psychology_content_analysis(content_id)
        return await self.redis.get(cache_key)
    
    async def set_psychology_content_analysis(self, data: Any, content_id: str, 
                                            ttl: int = None) -> bool:
        """Set psychology content analysis in cache"""
        cache_key = CachePatterns.psychology_content_analysis(content_id)
        ttl = ttl or CacheTTL.CONTENT_DEFAULT
        return await self.redis.set(cache_key, data, ttl=ttl)
    
    async def get_psychology_insights(self, user_id: str, insight_type: str = "general") -> Optional[Any]:
        """Get psychology insights from cache"""
        cache_key = CachePatterns.psychology_insights(user_id, insight_type)
        return await self.redis.get(cache_key)
    
    async def set_psychology_insights(self, data: Any, user_id: str, 
                                    insight_type: str = "general", ttl: int = None) -> bool:
        """Set psychology insights in cache"""
        cache_key = CachePatterns.psychology_insights(user_id, insight_type)
        ttl = ttl or CacheTTL.PSYCHOLOGY_DEFAULT
        return await self.redis.set(cache_key, data, ttl=ttl)
    
    # =============================================================================
    # CRISIS DOMAIN METHODS
    # =============================================================================
    
    async def get_crisis_assessment(self, content_hash: str) -> Optional[Any]:
        """Get crisis assessment from cache"""
        cache_key = CachePatterns.crisis_assessment(content_hash)
        return await self.redis.get(cache_key)
    
    async def set_crisis_assessment(self, data: Any, content_hash: str, ttl: int = None) -> bool:
        """Set crisis assessment in cache"""
        cache_key = CachePatterns.crisis_assessment(content_hash)
        ttl = ttl or CacheTTL.CRISIS_DEFAULT
        return await self.redis.set(cache_key, data, ttl=ttl)
    
    async def get_crisis_user_risk(self, user_id: str) -> Optional[Any]:
        """Get user crisis risk profile from cache"""
        cache_key = CachePatterns.crisis_user_risk(user_id)
        return await self.redis.get(cache_key)
    
    async def set_crisis_user_risk(self, data: Any, user_id: str, ttl: int = None) -> bool:
        """Set user crisis risk profile in cache"""
        cache_key = CachePatterns.crisis_user_risk(user_id)
        ttl = ttl or CacheTTL.CRISIS_DEFAULT
        return await self.redis.set(cache_key, data, ttl=ttl)
    
    # =============================================================================
    # MAINTENANCE DOMAIN METHODS
    # =============================================================================
    
    async def get_system_health(self) -> Optional[Any]:
        """Get system health status from cache"""
        cache_key = CachePatterns.maintenance_system_health()
        return await self.redis.get(cache_key)
    
    async def set_system_health(self, data: Any, ttl: int = None) -> bool:
        """Set system health status in cache"""
        cache_key = CachePatterns.maintenance_system_health()
        ttl = ttl or CacheTTL.MAINTENANCE_DEFAULT
        return await self.redis.set(cache_key, data, ttl=ttl)
    
    async def get_component_status(self, component: str) -> Optional[Any]:
        """Get component status from cache"""
        cache_key = CachePatterns.maintenance_component_status(component)
        return await self.redis.get(cache_key)
    
    async def set_component_status(self, data: Any, component: str, ttl: int = None) -> bool:
        """Set component status in cache"""
        cache_key = CachePatterns.maintenance_component_status(component)
        ttl = ttl or CacheTTL.MAINTENANCE_DEFAULT
        return await self.redis.set(cache_key, data, ttl=ttl)
    
    # =============================================================================
    # SESSION DOMAIN METHODS
    # =============================================================================
    
    async def get_session_data(self, session_id: str) -> Optional[Any]:
        """Get session data from cache"""
        cache_key = CachePatterns.session_data(session_id)
        return await self.redis.get(cache_key)
    
    async def set_session_data(self, data: Any, session_id: str, ttl: int = None) -> bool:
        """Set session data in cache"""
        cache_key = CachePatterns.session_data(session_id)
        ttl = ttl or CacheTTL.SESSION_DEFAULT
        return await self.redis.set(cache_key, data, ttl=ttl)
    
    async def get_session_activity(self, user_id: str) -> Optional[Any]:
        """Get user session activity from cache"""
        cache_key = CachePatterns.session_activity(user_id)
        return await self.redis.get(cache_key)
    
    async def set_session_activity(self, data: Any, user_id: str, ttl: int = None) -> bool:
        """Set user session activity in cache"""
        cache_key = CachePatterns.session_activity(user_id)
        ttl = ttl or CacheTTL.SESSION_DEFAULT
        return await self.redis.set(cache_key, data, ttl=ttl)
    
    # =============================================================================
    # AI MODEL DOMAIN METHODS
    # =============================================================================
    
    async def get_ai_model_instance(self, model_name: str, version: str = "latest") -> Optional[Any]:
        """Get AI model instance from cache - DEPRECATED: Models should not be cached in Redis"""
        logger.warning("AI model instances should not be cached in Redis due to serialization issues")
        return None
    
    async def set_ai_model_instance(self, data: Any, model_name: str, version: str = "latest", 
                                   ttl: int = None) -> bool:
        """Set AI model instance in cache - DEPRECATED: Models should not be cached in Redis"""
        logger.warning("AI model instances should not be cached in Redis due to serialization issues")
        return False
    
    async def get_ai_analysis_result(self, cache_key: str) -> Optional[Any]:
        """Get AI analysis result from cache (for data objects, not model instances)"""
        return await self.redis.get(cache_key)
    
    async def set_ai_analysis_result(self, data: Any, cache_key: str, ttl: int = None) -> bool:
        """Set AI analysis result in cache (for data objects, not model instances)"""
        ttl = ttl or CacheTTL.AI_MODEL_DEFAULT
        return await self.redis.set(cache_key, data, ttl=ttl)
    
    async def get_ai_prompt_cache(self, prompt_hash: str, model: str) -> Optional[Any]:
        """Get AI prompt response from cache"""
        cache_key = CachePatterns.ai_prompt_cache(prompt_hash, model)
        return await self.redis.get(cache_key)
    
    async def set_ai_prompt_cache(self, data: Any, prompt_hash: str, model: str, 
                                 ttl: int = None) -> bool:
        """Set AI prompt response in cache"""
        cache_key = CachePatterns.ai_prompt_cache(prompt_hash, model)
        ttl = ttl or CacheTTL.HOURLY  # AI responses cache for 1 hour
        return await self.redis.set(cache_key, data, ttl=ttl)
    
    # =============================================================================
    # CELERY DOMAIN METHODS
    # =============================================================================
    
    async def get_celery_task_metrics(self, task_id: str) -> Optional[Any]:
        """Get Celery task metrics from cache"""
        cache_key = CachePatterns.celery_task_metrics(task_id)
        return await self.redis.get(cache_key)
    
    async def set_celery_task_metrics(self, data: Any, task_id: str, ttl: int = None) -> bool:
        """Set Celery task metrics in cache"""
        cache_key = CachePatterns.celery_task_metrics(task_id)
        ttl = ttl or CacheTTL.DAILY
        return await self.redis.set(cache_key, data, ttl=ttl)
    
    async def get_celery_worker_status(self, worker_name: str) -> Optional[Any]:
        """Get Celery worker status from cache"""
        cache_key = CachePatterns.celery_worker_status(worker_name)
        return await self.redis.get(cache_key)
    
    async def set_celery_worker_status(self, data: Any, worker_name: str, ttl: int = None) -> bool:
        """Set Celery worker status in cache"""
        cache_key = CachePatterns.celery_worker_status(worker_name)
        ttl = ttl or CacheTTL.SHORT  # Worker status changes frequently
        return await self.redis.set(cache_key, data, ttl=ttl)
    
    # =============================================================================
    # GENERIC CACHE OPERATIONS
    # =============================================================================
    
    async def get_with_pattern(self, domain: CacheDomain, resource: str, 
                              identifiers: Dict[str, Any] = None, suffix: str = None) -> Optional[Any]:
        """Get data using custom cache pattern"""
        cache_key = CacheKeyBuilder.build_key(domain, resource, identifiers, suffix)
        return await self.redis.get(cache_key)
    
    async def set_with_pattern(self, data: Any, domain: CacheDomain, resource: str, 
                              identifiers: Dict[str, Any] = None, suffix: str = None, 
                              ttl: int = None) -> bool:
        """Set data using custom cache pattern"""
        cache_key = CacheKeyBuilder.build_key(domain, resource, identifiers, suffix)
        if ttl is None:
            ttl = CacheMetrics.get_recommended_ttl(domain, resource)
        return await self.redis.set(cache_key, data, ttl=ttl)
    
    # =============================================================================
    # CACHE INVALIDATION METHODS
    # =============================================================================
    
    async def invalidate_user_cache(self, user_id: str) -> int:
        """Invalidate all cache entries related to a specific user"""
        patterns = CacheInvalidationPatterns.user_related_patterns(user_id)
        total_deleted = 0
        
        for pattern in patterns:
            keys = await self.redis.scan_keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                total_deleted += len(keys)
                logger.info(f"Invalidated {len(keys)} cache keys for pattern: {pattern}")
        
        return total_deleted
    
    async def invalidate_content_cache(self, content_id: str) -> int:
        """Invalidate all cache entries related to specific content"""
        patterns = CacheInvalidationPatterns.content_related_patterns(content_id)
        total_deleted = 0
        
        for pattern in patterns:
            keys = await self.redis.scan_keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                total_deleted += len(keys)
                logger.info(f"Invalidated {len(keys)} cache keys for pattern: {pattern}")
        
        return total_deleted
    
    async def invalidate_daily_cache(self, date: str = None) -> int:
        """Invalidate all cache entries for daily data"""
        patterns = CacheInvalidationPatterns.daily_patterns(date)
        total_deleted = 0
        
        for pattern in patterns:
            keys = await self.redis.scan_keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                total_deleted += len(keys)
                logger.info(f"Invalidated {len(keys)} cache keys for pattern: {pattern}")
        
        return total_deleted
    
    # =============================================================================
    # CACHE METRICS AND MONITORING
    # =============================================================================
    
    async def get_cache_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics by domain"""
        metrics = {}
        
        for domain in CacheDomain:
            pattern = CacheMetrics.get_domain_key_pattern(domain)
            keys = await self.redis.scan_keys(pattern)
            
            metrics[domain.value] = {
                "total_keys": len(keys),
                "pattern": pattern,
                "recommended_ttl": CacheMetrics.get_recommended_ttl(domain, "default")
            }
        
        return metrics
    
    async def cleanup_expired_cache(self) -> Dict[str, int]:
        """Clean up expired cache entries (placeholder for Redis automatic expiry)"""
        # Redis handles TTL automatically, but this can be extended for manual cleanup
        return {
            "expired_keys_cleaned": 0,
            "note": "Redis handles TTL expiry automatically"
        }


# =============================================================================
# GLOBAL CACHE SERVICE INSTANCE
# =============================================================================

# Global instance for easy import and use across the application
unified_cache_service = UnifiedCacheService()


# =============================================================================
# CONVENIENCE FUNCTIONS FOR BACKWARD COMPATIBILITY
# =============================================================================

async def get_cached_data(cache_key: str) -> Optional[Any]:
    """Backward compatibility function for direct cache key access"""
    return await redis_service.get(cache_key)

async def set_cached_data(cache_key: str, data: Any, ttl: int = CacheTTL.HOURLY) -> bool:
    """Backward compatibility function for direct cache key setting"""
    return await redis_service.set(cache_key, data, ttl=ttl)

async def delete_cached_data(cache_key: str) -> bool:
    """Backward compatibility function for direct cache key deletion"""
    return await redis_service.delete(cache_key)
