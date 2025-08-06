# backend/app/core/cache_patterns.py
"""
Standardized Caching Patterns for Enterprise Service Architecture
Provides unified cache key naming conventions, TTL strategies, and invalidation patterns
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import hashlib
import json


class CacheDomain(Enum):
    """Cache domains for organized key namespacing"""
    ANALYTICS = "analytics"
    PSYCHOLOGY = "psychology"
    CRISIS = "crisis"
    MAINTENANCE = "maintenance"
    SESSION = "session"
    USER = "user"
    CONTENT = "content"
    SYSTEM = "system"
    AI_MODEL = "ai_model"
    CELERY = "celery"


class CacheTTL:
    """Standardized TTL values in seconds"""
    
    # Short-term caching (real-time data)
    REALTIME = 60           # 1 minute
    SHORT = 300             # 5 minutes
    MEDIUM_SHORT = 900      # 15 minutes
    MEDIUM = 1800           # 30 minutes
    
    # Medium-term caching (session-based data)
    HOURLY = 3600           # 1 hour
    HALF_DAY = 43200        # 12 hours
    DAILY = 86400           # 24 hours
    
    # Long-term caching (stable data)
    WEEKLY = 604800         # 7 days
    MONTHLY = 2592000       # 30 days
    
    # Domain-specific standard TTLs
    ANALYTICS_DEFAULT = HOURLY          # Analytics data changes hourly
    PSYCHOLOGY_DEFAULT = DAILY          # Psychology profiles stable daily
    CRISIS_DEFAULT = MEDIUM             # Crisis assessments need frequent updates
    MAINTENANCE_DEFAULT = SHORT         # System status changes quickly
    SESSION_DEFAULT = DAILY             # User sessions last up to a day
    AI_MODEL_DEFAULT = WEEKLY           # Models rarely change
    CONTENT_DEFAULT = HOURLY            # Content analysis results


class CacheKeyBuilder:
    """Unified cache key builder with domain-specific patterns"""
    
    @staticmethod
    def build_key(domain: CacheDomain, resource: str, identifiers: Dict[str, Any] = None, 
                  suffix: str = None) -> str:
        """
        Build standardized cache key
        Pattern: domain:resource:identifier1:identifier2:suffix
        
        Args:
            domain: Cache domain from CacheDomain enum
            resource: Resource type (e.g., 'daily_analytics', 'mood_trends')
            identifiers: Dict of key-value pairs for unique identification
            suffix: Optional suffix for variants (e.g., 'summary', 'details')
            
        Returns:
            Standardized cache key string
        """
        parts = [domain.value, resource]
        
        if identifiers:
            for key in sorted(identifiers.keys()):  # Sorted for consistency
                value = identifiers[key]
                if isinstance(value, datetime):
                    value = value.strftime("%Y%m%d")
                parts.append(f"{key}:{value}")
        
        if suffix:
            parts.append(suffix)
            
        return ":".join(parts)
    
    @staticmethod
    def build_content_hash_key(domain: CacheDomain, resource: str, content: str) -> str:
        """Build cache key with content hash for unique content identification"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return CacheKeyBuilder.build_key(domain, resource, {"hash": content_hash})


class CachePatterns:
    """Pre-defined cache patterns for common use cases"""
    
    # =============================================================================
    # ANALYTICS DOMAIN PATTERNS
    # =============================================================================
    
    @staticmethod
    def analytics_daily(user_id: str = None, date: str = None) -> str:
        """Daily analytics cache key"""
        identifiers = {}
        if user_id:
            identifiers["user"] = user_id
        if date:
            identifiers["date"] = date
        return CacheKeyBuilder.build_key(CacheDomain.ANALYTICS, "daily", identifiers)
    
    @staticmethod
    def analytics_mood_trends(user_id: str, time_range: str = "7d") -> str:
        """Mood trends cache key"""
        return CacheKeyBuilder.build_key(
            CacheDomain.ANALYTICS, "mood_trends", 
            {"user": user_id, "range": time_range}
        )
    
    @staticmethod
    def analytics_engagement(user_id: str, period: str = "daily") -> str:
        """Engagement metrics cache key"""
        return CacheKeyBuilder.build_key(
            CacheDomain.ANALYTICS, "engagement", 
            {"user": user_id, "period": period}
        )
    
    @staticmethod
    def analytics_writing_stats(user_id: str, days: int) -> str:
        """Writing statistics cache key"""
        return CacheKeyBuilder.build_key(
            CacheDomain.ANALYTICS, "writing_stats", 
            {"user": user_id, "days": f"{days}d"}
        )
    
    # =============================================================================
    # PSYCHOLOGY DOMAIN PATTERNS
    # =============================================================================
    
    @staticmethod
    def psychology_profile(user_id: str) -> str:
        """User psychology profile cache key"""
        return CacheKeyBuilder.build_key(
            CacheDomain.PSYCHOLOGY, "profile", {"user": user_id}
        )
    
    @staticmethod
    def psychology_content_analysis(content_id: str) -> str:
        """Psychology content analysis cache key"""
        return CacheKeyBuilder.build_key(
            CacheDomain.PSYCHOLOGY, "content_analysis", {"content": content_id}
        )
    
    @staticmethod
    def psychology_insights(user_id: str, insight_type: str = "general") -> str:
        """Psychology insights cache key"""
        return CacheKeyBuilder.build_key(
            CacheDomain.PSYCHOLOGY, "insights", 
            {"user": user_id, "type": insight_type}
        )
    
    @staticmethod
    def psychology_patterns(user_id: str, pattern_type: str) -> str:
        """Psychology patterns cache key"""
        return CacheKeyBuilder.build_key(
            CacheDomain.PSYCHOLOGY, "patterns", 
            {"user": user_id, "type": pattern_type}
        )
    
    # =============================================================================
    # CRISIS DOMAIN PATTERNS
    # =============================================================================
    
    @staticmethod
    def crisis_assessment(content_hash: str) -> str:
        """Crisis assessment cache key"""
        return CacheKeyBuilder.build_key(
            CacheDomain.CRISIS, "assessment", {"hash": content_hash}
        )
    
    @staticmethod
    def crisis_user_risk(user_id: str) -> str:
        """User crisis risk profile cache key"""
        return CacheKeyBuilder.build_key(
            CacheDomain.CRISIS, "user_risk", {"user": user_id}
        )
    
    @staticmethod
    def crisis_intervention_history(user_id: str) -> str:
        """Crisis intervention history cache key"""
        return CacheKeyBuilder.build_key(
            CacheDomain.CRISIS, "intervention_history", {"user": user_id}
        )
    
    @staticmethod
    def crisis_trends(timeframe: str = "7d") -> str:
        """Crisis trends analysis cache key"""
        return CacheKeyBuilder.build_key(
            CacheDomain.CRISIS, "trends", {"timeframe": timeframe}
        )
    
    # =============================================================================
    # MAINTENANCE DOMAIN PATTERNS
    # =============================================================================
    
    @staticmethod
    def maintenance_system_health() -> str:
        """System health status cache key"""
        return CacheKeyBuilder.build_key(CacheDomain.MAINTENANCE, "system_health")
    
    @staticmethod
    def maintenance_component_status(component: str) -> str:
        """Component status cache key"""
        return CacheKeyBuilder.build_key(
            CacheDomain.MAINTENANCE, "component_status", {"component": component}
        )
    
    @staticmethod
    def maintenance_cleanup_history(operation: str) -> str:
        """Cleanup operation history cache key"""
        return CacheKeyBuilder.build_key(
            CacheDomain.MAINTENANCE, "cleanup_history", {"operation": operation}
        )
    
    @staticmethod
    def maintenance_performance_metrics() -> str:
        """Performance metrics cache key"""
        return CacheKeyBuilder.build_key(CacheDomain.MAINTENANCE, "performance_metrics")
    
    # =============================================================================
    # SESSION DOMAIN PATTERNS
    # =============================================================================
    
    @staticmethod
    def session_data(session_id: str) -> str:
        """Session data cache key"""
        return CacheKeyBuilder.build_key(CacheDomain.SESSION, "data", {"id": session_id})
    
    @staticmethod
    def session_activity(user_id: str) -> str:
        """User session activity cache key"""
        return CacheKeyBuilder.build_key(CacheDomain.SESSION, "activity", {"user": user_id})
    
    @staticmethod
    def session_preferences(user_id: str) -> str:
        """User session preferences cache key"""
        return CacheKeyBuilder.build_key(CacheDomain.SESSION, "preferences", {"user": user_id})
    
    # =============================================================================
    # AI MODEL DOMAIN PATTERNS
    # =============================================================================
    
    @staticmethod
    def ai_model_instance(model_name: str, version: str = "latest") -> str:
        """AI model instance cache key"""
        return CacheKeyBuilder.build_key(
            CacheDomain.AI_MODEL, "instance", 
            {"name": model_name, "version": version}
        )
    
    @staticmethod
    def ai_prompt_cache(prompt_hash: str, model: str) -> str:
        """AI prompt response cache key"""
        return CacheKeyBuilder.build_key(
            CacheDomain.AI_MODEL, "prompt", 
            {"hash": prompt_hash, "model": model}
        )
    
    @staticmethod
    def ai_embedding_cache(text_hash: str, model: str) -> str:
        """Text embedding cache key"""
        return CacheKeyBuilder.build_key(
            CacheDomain.AI_MODEL, "embedding", 
            {"hash": text_hash, "model": model}
        )
    
    # =============================================================================
    # CELERY DOMAIN PATTERNS  
    # =============================================================================
    
    @staticmethod
    def celery_task_metrics(task_id: str) -> str:
        """Celery task metrics cache key"""
        return CacheKeyBuilder.build_key(CacheDomain.CELERY, "task_metrics", {"id": task_id})
    
    @staticmethod
    def celery_worker_status(worker_name: str) -> str:
        """Celery worker status cache key"""
        return CacheKeyBuilder.build_key(CacheDomain.CELERY, "worker_status", {"name": worker_name})
    
    @staticmethod
    def celery_recent_events(event_type: str) -> str:
        """Celery recent events cache key"""
        return CacheKeyBuilder.build_key(CacheDomain.CELERY, "recent_events", {"type": event_type})


class CacheInvalidationPatterns:
    """Standardized cache invalidation patterns"""
    
    @staticmethod
    def user_related_patterns(user_id: str) -> List[str]:
        """Get all cache key patterns related to a specific user"""
        return [
            f"analytics:*:user:{user_id}:*",
            f"psychology:*:user:{user_id}:*",
            f"crisis:*:user:{user_id}:*",
            f"session:*:user:{user_id}:*"
        ]
    
    @staticmethod
    def content_related_patterns(content_id: str) -> List[str]:
        """Get all cache key patterns related to specific content"""
        return [
            f"psychology:content_analysis:content:{content_id}",
            f"analytics:*:content:{content_id}:*"
        ]
    
    @staticmethod
    def daily_patterns(date: str = None) -> List[str]:
        """Get all cache key patterns for daily data"""
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        return [
            f"analytics:daily:*:date:{date}:*",
            f"maintenance:*:date:{date}:*"
        ]


class CacheMetrics:
    """Cache performance and usage metrics"""
    
    @staticmethod
    def get_domain_key_pattern(domain: CacheDomain) -> str:
        """Get Redis key pattern for a specific cache domain"""
        return f"{domain.value}:*"
    
    @staticmethod
    def get_recommended_ttl(domain: CacheDomain, resource_type: str) -> int:
        """Get recommended TTL for domain and resource type"""
        domain_defaults = {
            CacheDomain.ANALYTICS: CacheTTL.ANALYTICS_DEFAULT,
            CacheDomain.PSYCHOLOGY: CacheTTL.PSYCHOLOGY_DEFAULT,
            CacheDomain.CRISIS: CacheTTL.CRISIS_DEFAULT,
            CacheDomain.MAINTENANCE: CacheTTL.MAINTENANCE_DEFAULT,
            CacheDomain.SESSION: CacheTTL.SESSION_DEFAULT,
            CacheDomain.AI_MODEL: CacheTTL.AI_MODEL_DEFAULT,
            CacheDomain.CONTENT: CacheTTL.CONTENT_DEFAULT
        }
        
        # Special cases for specific resource types
        if resource_type in ["realtime", "status", "health"]:
            return CacheTTL.REALTIME
        elif resource_type in ["daily", "trends"]:
            return CacheTTL.DAILY
        elif resource_type in ["profile", "preferences"]:
            return CacheTTL.WEEKLY
        
        return domain_defaults.get(domain, CacheTTL.HOURLY)


# =============================================================================
# DECORATOR PATTERNS FOR EASY CACHE INTEGRATION
# =============================================================================

def cache_with_pattern(pattern_func, ttl: int = None, domain: CacheDomain = None):
    """
    Decorator for automatic caching using standardized patterns
    
    Usage:
        @cache_with_pattern(CachePatterns.analytics_daily, ttl=CacheTTL.HOURLY)
        async def get_daily_analytics(user_id: str, date: str):
            # Function implementation
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract parameters for cache key generation
            cache_key = pattern_func(*args, **kwargs)
            
            # Determine TTL
            if ttl is None and domain:
                cache_ttl = CacheMetrics.get_recommended_ttl(domain, func.__name__)
            else:
                cache_ttl = ttl or CacheTTL.HOURLY
            
            # Cache implementation would go here
            # This is a placeholder for the actual caching logic
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# =============================================================================
# MIGRATION UTILITIES
# =============================================================================

class CacheMigrationHelper:
    """Helper utilities for migrating existing cache patterns"""
    
    # Legacy key patterns to new patterns mapping
    LEGACY_MAPPINGS = {
        # Unified database service patterns
        r"writing_stats:(.+):(\d+)d": lambda m: CachePatterns.analytics_writing_stats(m.group(1), int(m.group(2))),
        r"topics:(.+):list": lambda m: CacheKeyBuilder.build_key(CacheDomain.CONTENT, "topics", {"user": m.group(1)}),
        r"topic:(.+)": lambda m: CacheKeyBuilder.build_key(CacheDomain.CONTENT, "topic", {"id": m.group(1)}),
        
        # Celery monitoring patterns
        r"task_metrics:(.+)": lambda m: CachePatterns.celery_task_metrics(m.group(1)),
        r"celery_recent_events:(.+)": lambda m: CachePatterns.celery_recent_events(m.group(1)),
        r"celery_worker_status:(.+)": lambda m: CachePatterns.celery_worker_status(m.group(1)),
    }
    
    @staticmethod
    def convert_legacy_key(legacy_key: str) -> Optional[str]:
        """Convert legacy cache key to new standardized format"""
        import re
        
        for pattern, converter in CacheMigrationHelper.LEGACY_MAPPINGS.items():
            match = re.match(pattern, legacy_key)
            if match:
                return converter(match)
        
        return None
    
    @staticmethod
    def get_migration_plan() -> Dict[str, str]:
        """Get complete migration plan for legacy cache keys"""
        return {
            "writing_stats:*": "Use CachePatterns.analytics_writing_stats()",
            "topics:*": "Use CacheKeyBuilder with CONTENT domain",
            "task_metrics:*": "Use CachePatterns.celery_task_metrics()",
            "celery_*": "Use CachePatterns.celery_* methods"
        }
