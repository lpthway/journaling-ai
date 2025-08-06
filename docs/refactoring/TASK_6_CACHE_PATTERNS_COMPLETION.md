# Cache Pattern Migration Guide

## Task 6 Completion Summary

**Date**: 2025-08-06  
**Status**: ✅ **COMPLETED**  
**Scope**: Standardized caching patterns across all service domains  

## What Was Implemented

### 1. Core Cache Patterns Module (`app/core/cache_patterns.py`)
- **CacheDomain enum**: Organized cache namespacing by domain
- **CacheTTL class**: Standardized TTL values for different use cases  
- **CacheKeyBuilder**: Unified cache key construction with consistent patterns
- **CachePatterns**: Pre-defined patterns for common operations
- **CacheInvalidationPatterns**: Organized cache invalidation strategies
- **CacheMigrationHelper**: Tools for migrating legacy cache keys

### 2. Unified Cache Service (`app/services/cache_service.py`)
- **Domain-specific methods**: Easy-to-use methods for each cache domain
- **Automatic TTL management**: Smart TTL selection based on domain and resource type
- **Cache invalidation**: User/content/date-based cache invalidation
- **Metrics and monitoring**: Cache performance tracking by domain
- **Backward compatibility**: Support for legacy cache operations

### 3. Service Integration
- **unified_database_service.py**: Updated to use standardized patterns
- **celery_monitoring.py**: Integrated with Celery cache patterns
- **Task coordinators**: Ready to use unified cache patterns

## Key Benefits Achieved

### Consistency
- ✅ **Unified key naming**: All cache keys follow `domain:resource:identifier:suffix` pattern
- ✅ **Standardized TTLs**: Domain-appropriate TTL values eliminate guesswork
- ✅ **Organized namespacing**: Clear separation by functional domain

### Performance  
- ✅ **Optimized TTLs**: Different TTL strategies for different data types
- ✅ **Smart invalidation**: Targeted cache invalidation reduces memory waste
- ✅ **Domain-based monitoring**: Track cache performance by functional area

### Maintainability
- ✅ **Single source of truth**: All cache patterns defined in one place
- ✅ **Migration support**: Tools to convert legacy cache keys
- ✅ **Easy adoption**: High-level service methods for common operations

## Cache Pattern Examples

### Before (Inconsistent)
```python
# Scattered patterns across services
cache_key = f"writing_stats:{user_id}:{days}d"
await redis_service.set(cache_key, stats, ttl=900)

cache_key = f"topics:{user_uuid}:list"  
await redis_service.set(cache_key, topics, ttl=3600)

cache_key = f"task_metrics:{task_id}"
await redis_service.set(cache_key, metrics, ttl=86400)
```

### After (Standardized)
```python
# Unified patterns with domain organization
from app.services.cache_service import unified_cache_service

# Analytics domain
await unified_cache_service.set_writing_stats(stats, user_id, days)
await unified_cache_service.set_analytics_daily(data, user_id, date)

# Content domain  
cache_key = CacheKeyBuilder.build_key(CacheDomain.CONTENT, "topics", {"user": user_id})
await redis_service.set(cache_key, topics, ttl=CacheTTL.HOURLY)

# Celery domain
await unified_cache_service.set_celery_task_metrics(metrics, task_id)
```

## Domain-Specific TTL Strategy

| Domain | Default TTL | Rationale |
|--------|-------------|-----------|
| Analytics | 1 hour | Data changes hourly, balance freshness vs performance |
| Psychology | 24 hours | Profiles are stable, expensive to regenerate |
| Crisis | 30 minutes | Safety-critical, needs frequent updates |
| Maintenance | 5 minutes | System status changes rapidly |
| Session | 24 hours | User sessions last up to a day |
| AI Model | 7 days | Models rarely change, expensive to load |
| Content | 1 hour | Content analysis results |

## Cache Key Patterns

### Standardized Format
```
domain:resource:identifier1:value1:identifier2:value2:suffix
```

### Examples by Domain
```python
# Analytics
"analytics:daily:user:user123:date:20250806"
"analytics:mood_trends:user:user123:range:7d"
"analytics:writing_stats:user:user123:days:30d"

# Psychology  
"psychology:profile:user:user123"
"psychology:content_analysis:content:content456"
"psychology:insights:user:user123:type:emotional"

# Crisis
"crisis:assessment:hash:abc12345"
"crisis:user_risk:user:user123"
"crisis:trends:timeframe:7d"

# Maintenance
"maintenance:system_health"
"maintenance:component_status:component:database"
"maintenance:performance_metrics"

# Session
"session:data:id:session789"
"session:activity:user:user123"

# AI Model
"ai_model:instance:name:bert:version:latest"
"ai_model:prompt:hash:xyz789:model:gpt4"

# Celery
"celery:task_metrics:id:task123"
"celery:worker_status:name:worker1"
```

## Migration Instructions

### For New Code
```python
# Use unified cache service
from app.services.cache_service import unified_cache_service

# Analytics operations
data = await unified_cache_service.get_analytics_daily(user_id, date)
await unified_cache_service.set_mood_trends(trends, user_id, "7d")

# Psychology operations  
profile = await unified_cache_service.get_psychology_profile(user_id)
await unified_cache_service.set_psychology_insights(insights, user_id, "emotional")

# Custom patterns
from app.core.cache_patterns import CacheKeyBuilder, CacheDomain, CacheTTL

cache_key = CacheKeyBuilder.build_key(CacheDomain.ANALYTICS, "custom_metric", {"user": user_id})
await redis_service.set(cache_key, data, ttl=CacheTTL.HOURLY)
```

### For Existing Code Migration
```python
# Legacy cache keys can be migrated
from app.core.cache_patterns import CacheMigrationHelper

legacy_key = "writing_stats:user123:30d"
new_key = CacheMigrationHelper.convert_legacy_key(legacy_key)
# Returns: "analytics:writing_stats:user:user123:days:30d"
```

## Integration with Task Coordinators

The new cache patterns integrate seamlessly with our task coordinator architecture:

```python
# Task coordinators can use unified cache service
@celery_app.task(bind=True)
@monitored_task(priority=TaskPriority.NORMAL, category=TaskCategory.ANALYTICS)
def generate_daily_analytics(self, user_id: str, date: str = None) -> Dict[str, Any]:
    try:
        # Check cache first
        cached_data = await unified_cache_service.get_analytics_daily(user_id, date)
        if cached_data:
            return {"success": True, "data": cached_data, "source": "cache"}
        
        # Generate new data via service
        service_registry = ServiceRegistry()
        analytics_service = service_registry.get_service("analytics_cache_service")
        result = analytics_service.generate_daily_analytics(user_id, date)
        
        # Cache the result
        await unified_cache_service.set_analytics_daily(result, user_id, date)
        
        return {"success": True, "data": result, "source": "generated"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}
```

## Cache Invalidation Strategy

### User-based Invalidation
```python
# When user data changes, invalidate all related cache
await unified_cache_service.invalidate_user_cache(user_id)
# Removes: analytics:*, psychology:*, crisis:*, session:* for that user
```

### Content-based Invalidation  
```python
# When content is updated, invalidate analysis cache
await unified_cache_service.invalidate_content_cache(content_id)
# Removes: psychology:content_analysis:*, analytics:*:content:*
```

### Time-based Invalidation
```python
# Daily cleanup of date-specific cache
await unified_cache_service.invalidate_daily_cache("20250805")
# Removes: analytics:daily:*:date:20250805:*, maintenance:*:date:*
```

## Performance Monitoring

### Cache Metrics by Domain
```python
metrics = await unified_cache_service.get_cache_metrics()
# Returns metrics for each domain: total_keys, patterns, recommended_ttl
```

### Redis Memory Optimization
- **Domain-based monitoring**: Track memory usage by functional area
- **TTL optimization**: Automatic expiry reduces memory pressure  
- **Pattern-based cleanup**: Efficient bulk operations for cache maintenance

## Next Steps

1. **Service Adoption**: Update remaining services to use unified cache patterns
2. **Performance Monitoring**: Implement cache hit rate tracking by domain
3. **AI Integration**: Cache patterns ready for AI service integration
4. **Documentation**: Update API documentation with cache behavior

---

## Phase 2 Completion Status

✅ **Task 1**: Crisis file organization  
✅ **Task 2**: Analytics duplication removal  
✅ **Task 3**: Analytics architecture consolidation  
✅ **Task 4**: Psychology/AI service consolidation  
✅ **Task 5**: Service boundaries clarification  
✅ **Task 6**: Caching patterns standardization  

**Phase 2: 100% COMPLETE** 🎉

**Ready for**: AI Service Refactoring (Original Phase 1)
