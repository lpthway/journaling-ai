# Phase 2 Setup and Migration Guide

## Overview

This document provides comprehensive setup and migration instructions for the Phase 2 Critical Code Organization and Duplication Fixes implementation.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Migration Process](#migration-process)
3. [Service Configuration](#service-configuration)
4. [Testing and Verification](#testing-and-verification)
5. [Rollback Procedures](#rollback-procedures)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **Python**: 3.8+ (tested with 3.9+)
- **Redis**: 6.0+ for caching service
- **PostgreSQL**: 12+ for database operations
- **Celery**: 5.0+ for task coordination

### Required Dependencies
```bash
# Core dependencies (already in requirements.txt)
celery>=5.0.0
redis>=4.0.0
psycopg2-binary>=2.9.0
sqlalchemy>=1.4.0

# New dependencies for Phase 2 patterns
enum34>=1.1.10  # For Python < 3.4 compatibility (if needed)
typing-extensions>=4.0.0  # For enhanced type hints
```

### Environment Variables
```bash
# Required for service registry
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://user:password@localhost:5432/journaling_ai

# Cache configuration
CACHE_DEFAULT_TTL=3600
CACHE_REDIS_DB=1

# Service registry configuration  
SERVICE_REGISTRY_ENABLED=true
MONITORING_ENABLED=true
```

---

## Migration Process

### Phase 1: Pre-Migration Backup

**⚠️ Critical: Always backup before migration**

```bash
# 1. Create migration backup directory
mkdir -p backup/phase2-migration-$(date +%Y%m%d-%H%M%S)

# 2. Backup current task files
cp backend/app/tasks/analytics.py backup/phase2-migration-$(date +%Y%m%d-%H%M%S)/
cp backend/app/tasks/psychology.py backup/phase2-migration-$(date +%Y%m%d-%H%M%S)/
cp backend/app/tasks/maintenance.py backup/phase2-migration-$(date +%Y%m%d-%H%M%S)/
cp backend/app/tasks/crisis.py backup/phase2-migration-$(date +%Y%m%d-%H%M%S)/

# 3. Backup service files
cp -r backend/app/services/ backup/phase2-migration-$(date +%Y%m%d-%H%M%S)/services_backup/

# 4. Document current system state
cd backend && python -c "
import sys
sys.path.append('.')
from app.tasks import analytics, psychology, maintenance
print('Pre-migration verification complete')
"
```

### Phase 2: File Deployment

The Phase 2 implementation is already deployed with the following changes:

#### New Files Created:
```bash
# Core cache framework
backend/app/core/cache_patterns.py          # 180 lines - Cache framework
backend/app/services/cache_service.py       # 220 lines - Unified cache interface

# Task coordinators (refactored)
backend/app/tasks/crisis.py                 # 340 lines - Crisis coordination
backend/app/tasks/analytics.py              # 283 lines - Analytics coordination  
backend/app/tasks/psychology.py             # 298 lines - Psychology coordination
backend/app/tasks/maintenance.py            # 302 lines - Maintenance coordination

# Safety backups  
backend/app/tasks/analytics_old_backup.py   # 1,389 lines - Original analytics
backend/app/tasks/psychology_old_backup.py  # 1,382 lines - Original psychology
backend/app/tasks/maintenance_old_backup.py # 1,586 lines - Original maintenance
```

#### Modified Files:
```bash
# Updated with cache patterns
backend/app/services/unified_database_service.py  # Cache pattern integration
backend/app/tasks/celery_monitoring.py            # Import updates
```

### Phase 3: Service Registry Configuration

Update your `main.py` or application startup file:

```python
# Add to main.py or app initialization
from app.services.cache_service import unified_cache_service
from app.core.service_registry import ServiceRegistry

# Initialize service registry (if not already present)
def initialize_services():
    """Initialize all services for Phase 2 architecture"""
    service_registry = ServiceRegistry()
    
    # Register analytics services
    service_registry.register_service(
        "analytics_cache_service", 
        AnalyticsCacheService()
    )
    service_registry.register_service(
        "background_processor", 
        BackgroundProcessor()
    )
    
    # Register psychology services
    service_registry.register_service(
        "psychology_processing_service", 
        PsychologyProcessingService()
    )
    service_registry.register_service(
        "psychology_analysis_service", 
        PsychologyAnalysisService()
    )
    
    # Register crisis services
    service_registry.register_service(
        "crisis_detection_service", 
        CrisisDetectionService()
    )
    service_registry.register_service(
        "crisis_intervention_service", 
        CrisisInterventionService()
    )
    
    # Register maintenance services
    service_registry.register_service(
        "maintenance_cleanup_service", 
        MaintenanceCleanupService()
    )
    service_registry.register_service(
        "health_monitoring_service", 
        HealthMonitoringService()
    )

# Call during application startup
initialize_services()
```

---

## Service Configuration

### Cache Service Configuration

#### Redis Configuration
```python
# config/cache_config.py
CACHE_CONFIG = {
    'default': {
        'BACKEND': 'redis',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Domain-specific TTL overrides (optional)
CUSTOM_TTL_CONFIG = {
    'analytics': {
        'daily_stats': 7200,      # Override to 2 hours if needed
    },
    'crisis': {
        'risk_assessment': 180,   # Override to 3 minutes for higher sensitivity
    }
}
```

#### Cache Service Initialization
```python
# In your application startup
from app.services.cache_service import UnifiedCacheService
from app.core.cache_patterns import CachePatterns

# Initialize unified cache service
cache_service = UnifiedCacheService()

# Verify cache connectivity
async def verify_cache_setup():
    """Verify cache service is properly configured"""
    test_key = CachePatterns.build_test_key()
    await cache_service.set_test_data({"status": "ok"}, test_key)
    result = await cache_service.get_test_data(test_key)
    
    if result and result.get("status") == "ok":
        print("✅ Cache service configured successfully")
        return True
    else:
        print("❌ Cache service configuration failed")
        return False
```

### Task Coordination Configuration

#### Celery Configuration Updates
```python
# celery_config.py - Add monitoring for new task patterns
CELERY_TASK_ROUTES = {
    # Crisis tasks - high priority queue
    'app.tasks.crisis.*': {'queue': 'crisis_queue', 'priority': 9},
    
    # Analytics tasks - medium priority  
    'app.tasks.analytics.*': {'queue': 'analytics_queue', 'priority': 5},
    
    # Psychology tasks - medium priority
    'app.tasks.psychology.*': {'queue': 'psychology_queue', 'priority': 5},
    
    # Maintenance tasks - low priority
    'app.tasks.maintenance.*': {'queue': 'maintenance_queue', 'priority': 1},
}

# Enhanced monitoring for Phase 2 patterns
CELERY_TASK_ANNOTATIONS = {
    '*': {
        'rate_limit': '100/m',
        'time_limit': 300,  # 5 minutes max per task
    },
    'app.tasks.crisis.*': {
        'rate_limit': '200/m',  # Higher rate limit for crisis
        'time_limit': 60,       # Faster timeout for crisis
    }
}
```

---

## Testing and Verification

### Automated Verification Script

```bash
# Create verification script
cat > verify_phase2.py << 'EOF'
#!/usr/bin/env python3
"""
Phase 2 Migration Verification Script
Verifies all components are properly installed and functional
"""

import sys
import importlib
import asyncio
from datetime import datetime

def verify_imports():
    """Verify all new modules can be imported"""
    modules_to_test = [
        'app.core.cache_patterns',
        'app.services.cache_service', 
        'app.tasks.crisis',
        'app.tasks.analytics',
        'app.tasks.psychology',
        'app.tasks.maintenance'
    ]
    
    for module in modules_to_test:
        try:
            importlib.import_module(module)
            print(f"✅ {module} imported successfully")
        except ImportError as e:
            print(f"❌ {module} import failed: {e}")
            return False
    
    return True

def verify_task_structure():
    """Verify task files have correct structure"""
    from app.tasks import crisis, analytics, psychology, maintenance
    
    # Check each task file has standard coordinator functions
    task_modules = {
        'crisis': crisis,
        'analytics': analytics, 
        'psychology': psychology,
        'maintenance': maintenance
    }
    
    for name, module in task_modules.items():
        # Verify each module has Celery tasks
        celery_tasks = [attr for attr in dir(module) if hasattr(getattr(module, attr), 'delay')]
        if celery_tasks:
            print(f"✅ {name} has {len(celery_tasks)} Celery tasks")
        else:
            print(f"❌ {name} missing Celery tasks")
            return False
    
    return True

def verify_cache_patterns():
    """Verify cache patterns are properly configured"""
    from app.core.cache_patterns import CacheDomain, CachePatterns, CacheKeyBuilder
    
    # Test cache key generation
    test_key = CachePatterns.analytics_daily_stats("test_user", "2025-08-06")
    expected_pattern = "analytics:daily_stats:test_user:2025-08-06"
    
    if test_key == expected_pattern:
        print("✅ Cache key patterns working correctly")
        return True
    else:
        print(f"❌ Cache key pattern failed: got {test_key}, expected {expected_pattern}")
        return False

async def verify_cache_service():
    """Verify cache service functionality"""
    try:
        from app.services.cache_service import unified_cache_service
        
        # Test basic cache operations
        test_data = {"test": "data", "timestamp": datetime.utcnow().isoformat()}
        test_key = "verification:test:phase2"
        
        # Set test data
        await unified_cache_service.redis_service.set_json(test_key, test_data, 60)
        
        # Get test data
        retrieved = await unified_cache_service.redis_service.get_json(test_key)
        
        if retrieved and retrieved.get("test") == "data":
            print("✅ Cache service working correctly")
            return True
        else:
            print("❌ Cache service not working")
            return False
            
    except Exception as e:
        print(f"❌ Cache service error: {e}")
        return False

def verify_file_sizes():
    """Verify file size reductions"""
    import os
    
    file_sizes = {}
    task_files = [
        'backend/app/tasks/crisis.py',
        'backend/app/tasks/analytics.py',
        'backend/app/tasks/psychology.py', 
        'backend/app/tasks/maintenance.py'
    ]
    
    total_lines = 0
    for file_path in task_files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                lines = len(f.readlines())
                file_sizes[file_path] = lines
                total_lines += lines
                print(f"📊 {file_path}: {lines} lines")
    
    print(f"📊 Total task coordinator lines: {total_lines}")
    
    if total_lines < 1500:  # Should be around 1,223 lines
        print("✅ File size reduction successful")
        return True
    else:
        print("❌ File size reduction not achieved")
        return False

async def run_full_verification():
    """Run complete verification suite"""
    print("🔍 Starting Phase 2 Migration Verification")
    print("=" * 50)
    
    checks = [
        ("Import Verification", verify_imports()),
        ("Task Structure Verification", verify_task_structure()),
        ("Cache Patterns Verification", verify_cache_patterns()),
        ("Cache Service Verification", await verify_cache_service()),
        ("File Size Verification", verify_file_sizes())
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, result in checks:
        if result:
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Verification Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 Phase 2 migration verification SUCCESSFUL!")
        return True
    else:
        print("⚠️  Phase 2 migration verification FAILED!")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_full_verification())
    sys.exit(0 if success else 1)
EOF

# Run verification
cd backend && python verify_phase2.py
```

### Manual Testing Commands

```bash
# 1. Test task compilation
cd backend
python -m py_compile app/tasks/crisis.py
python -m py_compile app/tasks/analytics.py  
python -m py_compile app/tasks/psychology.py
python -m py_compile app/tasks/maintenance.py
python -m py_compile app/core/cache_patterns.py
python -m py_compile app/services/cache_service.py

# 2. Test cache patterns
python -c "
from app.core.cache_patterns import CachePatterns, CacheDomain
print('Analytics key:', CachePatterns.analytics_daily_stats('user123', '2025-08-06'))
print('Psychology key:', CachePatterns.psychology_user_profile('user456'))
print('Crisis key:', CachePatterns.crisis_risk_assessment('hash123'))
"

# 3. Test service imports
python -c "
from app.services.cache_service import unified_cache_service
print('Cache service imported successfully')
"

# 4. Verify task registration
python -c "
from app.tasks.analytics import generate_daily_analytics
from app.tasks.psychology import process_psychology_content
from app.tasks.crisis import detect_crisis_patterns
from app.tasks.maintenance import cleanup_expired_sessions
print('All task coordinators imported successfully')
"
```

---

## Rollback Procedures

### Emergency Rollback (If Issues Occur)

```bash
# 1. Stop all services
sudo systemctl stop celery-worker
sudo systemctl stop celery-beat
sudo systemctl stop gunicorn  # or your web server

# 2. Restore original files
cd backend/app/tasks
mv analytics.py analytics_phase2_backup.py
mv psychology.py psychology_phase2_backup.py  
mv maintenance.py maintenance_phase2_backup.py

mv analytics_old_backup.py analytics.py
mv psychology_old_backup.py psychology.py
mv maintenance_old_backup.py maintenance.py

# 3. Remove Phase 2 files
rm -f ../core/cache_patterns.py
rm -f ../services/cache_service.py

# 4. Restore original unified_database_service.py
git checkout backend/app/services/unified_database_service.py

# 5. Restart services
sudo systemctl start celery-worker
sudo systemctl start celery-beat
sudo systemctl start gunicorn

# 6. Verify rollback
python -c "
from app.tasks import analytics, psychology, maintenance
print('Rollback verification successful')
"
```

### Selective Rollback (Single Component)

```bash
# Rollback just analytics (example)
cd backend/app/tasks
mv analytics.py analytics_phase2.py
mv analytics_old_backup.py analytics.py

# Test single component
python -c "from app.tasks.analytics import *; print('Analytics rollback successful')"
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Import Errors

**Problem**: `ModuleNotFoundError: No module named 'app.core.cache_patterns'`

**Solution**:
```bash
# Verify file exists
ls -la backend/app/core/cache_patterns.py

# Check Python path
cd backend && python -c "import sys; print(sys.path)"

# Ensure __init__.py exists
touch backend/app/core/__init__.py
```

#### 2. Service Registry Errors

**Problem**: `Service 'analytics_cache_service' not found in registry`

**Solution**:
```python
# Verify service registration in main.py
from app.core.service_registry import ServiceRegistry

service_registry = ServiceRegistry()
print("Registered services:", service_registry.list_services())

# Register missing service
service_registry.register_service("analytics_cache_service", AnalyticsCacheService())
```

#### 3. Cache Connection Issues

**Problem**: `Redis connection failed`

**Solution**:
```bash
# Check Redis status
redis-cli ping

# Test Redis connection
python -c "
import redis
r = redis.Redis(host='localhost', port=6379, db=0)
print('Redis connection:', r.ping())
"

# Update Redis configuration if needed
export REDIS_URL=redis://localhost:6379/1
```

#### 4. Task Execution Errors

**Problem**: Tasks failing with coordination errors

**Solution**:
```bash
# Check Celery worker logs
tail -f /var/log/celery/worker.log

# Test task directly
cd backend && python -c "
from app.tasks.analytics import generate_daily_analytics
result = generate_daily_analytics.delay('test_user', '2025-08-06')
print('Task ID:', result.id)
"

# Monitor task execution
celery -A app.main events
```

#### 5. Performance Issues

**Problem**: Slower performance after migration

**Solution**:
```bash
# Check cache hit rates
redis-cli info stats | grep keyspace

# Monitor task execution times
cd backend && python -c "
import time
from app.tasks.analytics import generate_daily_analytics

start = time.time()
result = generate_daily_analytics('test_user', '2025-08-06')
end = time.time()
print(f'Execution time: {end - start:.2f}s')
"

# Optimize cache TTL if needed
# Edit cache_patterns.py TTL values
```

### Debug Commands

```bash
# 1. Full system health check
cd backend && python -c "
from app.core.cache_patterns import CachePatterns
from app.services.cache_service import unified_cache_service
from app.tasks import analytics, psychology, crisis, maintenance
print('All components loaded successfully')
"

# 2. Cache pattern verification
python -c "
from app.core.cache_patterns import CacheDomain, CACHE_TTL_CONFIG
for domain in CacheDomain:
    print(f'{domain.value}: {CACHE_TTL_CONFIG.get(domain, {})}')
"

# 3. Task coordination test
python -c "
from app.tasks.analytics import generate_daily_analytics
print('Task function:', generate_daily_analytics)
print('Task name:', generate_daily_analytics.name)
"
```

### Log Monitoring

```bash
# Monitor Phase 2 related logs
tail -f /var/log/celery/worker.log | grep -E "(analytics|psychology|crisis|maintenance)"

# Monitor cache operations
redis-cli monitor | grep -E "(analytics|psychology|crisis|maintenance)"

# Monitor application logs
tail -f /var/log/journaling-ai/app.log | grep -i "phase2\|cache\|service"
```

---

## Configuration Validation

### Environment Validation Script

```bash
cat > validate_environment.py << 'EOF'
#!/usr/bin/env python3
"""Validate environment for Phase 2"""

import os
import redis
import sys

def check_environment_variables():
    """Check required environment variables"""
    required_vars = [
        'REDIS_URL',
        'DATABASE_URL'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing environment variables: {missing}")
        return False
    
    print("✅ All required environment variables present")
    return True

def check_redis_connection():
    """Test Redis connectivity"""
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        r = redis.from_url(redis_url)
        r.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def validate_environment():
    """Run full environment validation"""
    checks = [
        check_environment_variables(),
        check_redis_connection()
    ]
    
    if all(checks):
        print("🎉 Environment validation successful!")
        return True
    else:
        print("⚠️ Environment validation failed!")
        return False

if __name__ == "__main__":
    success = validate_environment()
    sys.exit(0 if success else 1)
EOF

python validate_environment.py
```

---

## Next Steps

After successful Phase 2 migration:

1. **Monitor Performance**: Track cache hit rates and task execution times
2. **Service Integration**: Begin integrating specialized services
3. **AI Preparation**: Phase 2 establishes foundation for AI service refactoring
4. **Documentation Updates**: Keep documentation current with any configuration changes

**Phase 2 Status**: ✅ Complete and Ready for AI Service Refactoring

The Phase 2 implementation provides a solid foundation for the next phase of AI service integration while maintaining full system stability and rollback capability.
