# backend/app/tasks/analytics.py
"""
Analytics Task Coordinators for Phase 0C
Lightweight task definitions that delegate to analytics services
Follows enterprise architecture: Tasks coordinate, Services contain business logic
"""

import logging
import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Celery and app imports
from app.services.celery_service import celery_app, monitored_task, TaskPriority, TaskCategory
from app.services.analytics_service import analytics_cache_service
from app.services.background_analytics import background_processor
from app.core.performance_monitor import performance_monitor

logger = logging.getLogger(__name__)

# === ANALYTICS TASK COORDINATORS ===

@monitored_task(priority=TaskPriority.NORMAL, category=TaskCategory.ANALYTICS)
def generate_daily_analytics(self, target_date: str = None) -> Dict[str, Any]:
    """
    Task coordinator for daily analytics generation
    Delegates to analytics_cache_service for business logic
    
    Args:
        target_date: Date to generate analytics for (defaults to yesterday)
    
    Returns:
        Daily analytics results with trends and insights
    """
    try:
        start_time = time.time()
        
        logger.info(f"📊 Coordinating daily analytics generation for {target_date or 'yesterday'}")
        
        # Delegate to analytics service for actual processing
        analytics_result = asyncio.run(
            analytics_cache_service.generate_daily_analytics(target_date)
        )
        
        # Add task coordination metadata
        analytics_result.update({
            "task_coordination": {
                "task_id": self.request.id,
                "coordinator": "generate_daily_analytics",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        logger.info(f"✅ Daily analytics coordination complete in {analytics_result['task_coordination']['processing_time_ms']}ms")
        
        return analytics_result
        
    except Exception as e:
        logger.error(f"❌ Daily analytics coordination failed: {e}")
        return {
            "error": str(e),
            "task_id": self.request.id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat()
        }

@monitored_task(priority=TaskPriority.NORMAL, category=TaskCategory.ANALYTICS)
def generate_weekly_analytics(self, week_start_date: str = None) -> Dict[str, Any]:
    """
    Task coordinator for weekly analytics generation
    
    Args:
        week_start_date: Start of week to analyze (defaults to last week)
    
    Returns:
        Weekly analytics results
    """
    try:
        start_time = time.time()
        
        logger.info(f"📊 Coordinating weekly analytics generation")
        
        # Delegate to analytics service
        analytics_result = asyncio.run(
            analytics_cache_service.generate_weekly_analytics(week_start_date)
        )
        
        analytics_result.update({
            "task_coordination": {
                "task_id": self.request.id,
                "coordinator": "generate_weekly_analytics",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        return analytics_result
        
    except Exception as e:
        logger.error(f"❌ Weekly analytics coordination failed: {e}")
        return {
            "error": str(e),
            "task_id": self.request.id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat()
        }

@monitored_task(priority=TaskPriority.NORMAL, category=TaskCategory.ANALYTICS)
def generate_mood_trends(self, days: int = 30) -> Dict[str, Any]:
    """
    Task coordinator for mood trend analysis
    
    Args:
        days: Number of days to analyze
    
    Returns:
        Mood trend analysis results
    """
    try:
        start_time = time.time()
        
        logger.info(f"📈 Coordinating mood trends analysis for {days} days")
        
        # Delegate to analytics service
        analytics_result = asyncio.run(
            analytics_cache_service.generate_mood_trends(days)
        )
        
        analytics_result.update({
            "task_coordination": {
                "task_id": self.request.id,
                "coordinator": "generate_mood_trends",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        return analytics_result
        
    except Exception as e:
        logger.error(f"❌ Mood trends coordination failed: {e}")
        return {
            "error": str(e),
            "task_id": self.request.id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat()
        }

@monitored_task(priority=TaskPriority.LOW, category=TaskCategory.ANALYTICS)
def refresh_analytics_cache(self, analytics_types: List[str] = None) -> Dict[str, Any]:
    """
    Task coordinator for refreshing analytics caches
    
    Args:
        analytics_types: Specific analytics types to refresh (optional)
    
    Returns:
        Cache refresh results
    """
    try:
        start_time = time.time()
        
        logger.info(f"🔄 Coordinating analytics cache refresh")
        
        # Delegate to analytics service
        refresh_result = asyncio.run(
            analytics_cache_service.refresh_analytics_cache(analytics_types)
        )
        
        refresh_result.update({
            "task_coordination": {
                "task_id": self.request.id,
                "coordinator": "refresh_analytics_cache",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        return refresh_result
        
    except Exception as e:
        logger.error(f"❌ Analytics cache refresh coordination failed: {e}")
        return {
            "error": str(e),
            "task_id": self.request.id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat()
        }

@monitored_task(priority=TaskPriority.HIGH, category=TaskCategory.ANALYTICS)
def analyze_entry_patterns(self, user_id: str, entry_id: str) -> Dict[str, Any]:
    """
    Task coordinator for analyzing individual entry patterns
    
    Args:
        user_id: User identifier
        entry_id: Entry to analyze
    
    Returns:
        Entry pattern analysis results
    """
    try:
        start_time = time.time()
        
        logger.info(f"🔍 Coordinating entry pattern analysis for user {user_id}, entry {entry_id}")
        
        # Delegate to background processor for entry analysis
        analysis_result = asyncio.run(
            background_processor.analyze_entry_patterns(user_id, entry_id)
        )
        
        analysis_result.update({
            "task_coordination": {
                "task_id": self.request.id,
                "coordinator": "analyze_entry_patterns",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"❌ Entry pattern analysis coordination failed: {e}")
        return {
            "error": str(e),
            "task_id": self.request.id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat()
        }

@monitored_task(priority=TaskPriority.LOW, category=TaskCategory.MAINTENANCE)
def cleanup_old_analytics(self, days_to_keep: int = 90) -> Dict[str, Any]:
    """
    Task coordinator for cleaning up old analytics data
    
    Args:
        days_to_keep: Number of days of analytics to retain
    
    Returns:
        Cleanup results
    """
    try:
        start_time = time.time()
        
        logger.info(f"🧹 Coordinating analytics cleanup - keeping {days_to_keep} days")
        
        # Delegate to analytics service for cleanup
        cleanup_result = asyncio.run(
            analytics_cache_service.cleanup_old_analytics(days_to_keep)
        )
        
        cleanup_result.update({
            "task_coordination": {
                "task_id": self.request.id,
                "coordinator": "cleanup_old_analytics",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        return cleanup_result
        
    except Exception as e:
        logger.error(f"❌ Analytics cleanup coordination failed: {e}")
        return {
            "error": str(e),
            "task_id": self.request.id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat()
        }

# Export tasks for Celery discovery
__all__ = [
    'generate_daily_analytics',
    'generate_weekly_analytics', 
    'generate_mood_trends',
    'refresh_analytics_cache',
    'analyze_entry_patterns',
    'cleanup_old_analytics'
]
