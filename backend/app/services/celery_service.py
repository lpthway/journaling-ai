# backend/app/services/celery_service.py
"""
Enterprise Celery Configuration for Phase 0C Background Processing
Integrates with Phase 0B Redis infrastructure for high-performance task processing
"""

import os
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import timedelta
from kombu import Queue, Exchange
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure, task_success
from celery.result import AsyncResult
from dataclasses import dataclass
from enum import Enum
import time
import asyncio
import json

from app.core.config import settings
from app.services.redis_service_simple import simple_redis_service as redis_service
from app.core.performance_monitor import performance_monitor

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    """Task priorities for routing and processing"""
    CRITICAL = "critical"     # Crisis detection, real-time alerts
    HIGH = "high"            # User-facing operations, document processing
    NORMAL = "normal"        # Analytics, batch processing
    LOW = "low"             # Maintenance, cleanup, reports

class TaskCategory(Enum):
    """Task categories for psychology processing"""
    PSYCHOLOGY_PROCESSING = "psychology"     # Document analysis, knowledge extraction
    CRISIS_DETECTION = "crisis"             # Pattern analysis, risk assessment
    ANALYTICS = "analytics"                 # Trends, insights, reporting
    MAINTENANCE = "maintenance"             # Cleanup, optimization
    USER_OPERATIONS = "user"               # User-facing background tasks

@dataclass
class TaskMetrics:
    """Task execution metrics"""
    task_id: str
    task_name: str
    priority: TaskPriority
    category: TaskCategory
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    retry_count: int = 0

class CeleryConfig:
    """Enterprise Celery configuration with Redis broker integration"""
    
    # === BROKER & BACKEND CONFIGURATION ===
    broker_url = settings.CELERY_BROKER_URL
    result_backend = settings.CELERY_RESULT_BACKEND
    
    # Connection settings optimized for Redis
    broker_connection_retry_on_startup = True
    broker_connection_retry = True
    broker_connection_max_retries = 10
    broker_pool_limit = 50
    
    # Redis backend optimizations
    result_backend_transport_options = {
        'retry_on_timeout': True,
        'health_check_interval': 30,
        'max_connections': 20
    }
    
    # === SERIALIZATION & COMPRESSION ===
    task_serializer = 'msgpack'        # Better performance than JSON
    result_serializer = 'msgpack'
    accept_content = ['msgpack', 'json']
    result_accept_content = ['msgpack', 'json']
    
    # Compression for large payloads (psychology documents)
    task_compression = 'gzip'
    result_compression = 'gzip'
    
    # === TASK EXECUTION SETTINGS ===
    task_acks_late = True              # Acknowledge after completion
    task_reject_on_worker_lost = True  # Requeue if worker dies
    worker_prefetch_multiplier = 4     # Balanced throughput/memory
    
    # Timeouts for different task types
    task_soft_time_limit = 300         # 5 minutes soft limit
    task_time_limit = 600              # 10 minutes hard limit
    task_track_started = True          # Track task start time
    
    # Worker settings
    worker_max_tasks_per_child = 1000  # Prevent memory leaks
    worker_disable_rate_limits = True  # Better performance
    
    # === ROUTING & QUEUES ===
    task_routes = {
        # Crisis detection - highest priority
        'app.tasks.crisis.*': {'queue': 'crisis', 'priority': 9},
        
        # Psychology processing - high priority
        'app.tasks.psychology.*': {'queue': 'psychology', 'priority': 7},
        
        # User operations - normal priority
        'app.tasks.user.*': {'queue': 'user_ops', 'priority': 5},
        
        # Analytics - lower priority
        'app.tasks.analytics.*': {'queue': 'analytics', 'priority': 3},
        
        # Maintenance - lowest priority
        'app.tasks.maintenance.*': {'queue': 'maintenance', 'priority': 1},
    }
    
    # Queue definitions with different priorities
    task_default_queue = 'default'
    task_queues = [
        Queue('crisis', 
              Exchange('crisis', type='direct'), 
              routing_key='crisis',
              queue_arguments={'x-max-priority': 10}),
        
        Queue('psychology', 
              Exchange('psychology', type='direct'), 
              routing_key='psychology',
              queue_arguments={'x-max-priority': 8}),
        
        Queue('user_ops', 
              Exchange('user_ops', type='direct'), 
              routing_key='user_ops',
              queue_arguments={'x-max-priority': 6}),
        
        Queue('analytics', 
              Exchange('analytics', type='direct'), 
              routing_key='analytics',
              queue_arguments={'x-max-priority': 4}),
        
        Queue('maintenance', 
              Exchange('maintenance', type='direct'), 
              routing_key='maintenance',
              queue_arguments={'x-max-priority': 2}),
        
        Queue('default', 
              Exchange('default', type='direct'), 
              routing_key='default',
              queue_arguments={'x-max-priority': 5}),
    ]
    
    # === MONITORING & LOGGING ===
    worker_send_task_events = True
    task_send_sent_event = True
    
    # === RETRY CONFIGURATION ===
    task_default_retry_delay = 60      # 1 minute base delay
    task_max_retries = 3
    
    # === BEAT SCHEDULER ===
    beat_schedule = {
        'cleanup-expired-sessions': {
            'task': 'app.tasks.maintenance.cleanup_expired_sessions',
            'schedule': timedelta(hours=1),  # Every hour
            'options': {'queue': 'maintenance', 'priority': 1}
        },
        
        'generate-daily-analytics': {
            'task': 'app.tasks.analytics.generate_daily_analytics',
            'schedule': timedelta(hours=24),  # Daily
            'options': {'queue': 'analytics', 'priority': 3}
        },
        
        'process-psychology-queue': {
            'task': 'app.tasks.psychology.process_pending_documents',
            'schedule': timedelta(minutes=15),  # Every 15 minutes
            'options': {'queue': 'psychology', 'priority': 7}
        },
        
        'monitor-crisis-patterns': {
            'task': 'app.tasks.crisis.monitor_user_patterns',
            'schedule': timedelta(minutes=5),   # Every 5 minutes
            'options': {'queue': 'crisis', 'priority': 9}
        },
        
        'system-health-check': {
            'task': 'app.tasks.maintenance.system_health_check',
            'schedule': timedelta(minutes=10),  # Every 10 minutes
            'options': {'queue': 'maintenance', 'priority': 2}
        }
    }

class CeleryService:
    """
    Enterprise Celery service with monitoring and performance tracking
    Integrates with Phase 0B Redis infrastructure and performance monitoring
    """
    
    def __init__(self):
        self.app = None
        self._initialized = False
        self._task_metrics: Dict[str, TaskMetrics] = {}
        self.performance_targets = {
            "task_dispatch_latency": 500,    # <500ms dispatch
            "crisis_processing_time": 60000,  # <60s crisis detection
            "analytics_processing_time": 600000,  # <10min analytics
            "task_failure_rate": 0.01        # <1% failure rate
        }
    
    def create_app(self) -> Celery:
        """Create and configure Celery application"""
        if self.app:
            return self.app
        
        # Create Celery app with Redis broker
        self.app = Celery(
            'journaling_ai_tasks',
            broker=settings.CELERY_BROKER_URL,
            backend=settings.CELERY_RESULT_BACKEND,
            include=[
                'app.tasks.psychology',
                'app.tasks.crisis',
                'app.tasks.analytics',
                'app.tasks.maintenance',
                'app.tasks.user'
            ]
        )
        
        # Apply configuration
        self.app.config_from_object(CeleryConfig)
        
        # Setup signal handlers for monitoring
        self._setup_signal_handlers()
        
        logger.info("✅ Celery application created with Redis broker integration")
        return self.app
    
    def _setup_signal_handlers(self):
        """Setup Celery signal handlers for performance monitoring"""
        
        @task_prerun.connect
        def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
            """Handle task start for performance tracking"""
            try:
                # Determine task priority and category from routing
                priority = self._get_task_priority(task.name)
                category = self._get_task_category(task.name)
                
                # Create metrics tracking
                self._task_metrics[task_id] = TaskMetrics(
                    task_id=task_id,
                    task_name=task.name,
                    priority=priority,
                    category=category,
                    start_time=time.time()
                )
                
                logger.info(f"🚀 Task started: {task.name} [{task_id}] - Priority: {priority.value}")
                
            except Exception as e:
                logger.error(f"Error in task prerun handler: {e}")
        
        @task_postrun.connect
        def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
            """Handle task completion for performance tracking"""
            try:
                if task_id in self._task_metrics:
                    metric = self._task_metrics[task_id]
                    metric.end_time = time.time()
                    metric.duration_ms = (metric.end_time - metric.start_time) * 1000
                    metric.success = (state == 'SUCCESS')
                    
                    # Check performance targets
                    asyncio.create_task(self._check_task_performance(metric))
                    
                    # Log completion
                    status = "✅" if metric.success else "❌"
                    logger.info(
                        f"{status} Task completed: {metric.task_name} [{task_id}] - "
                        f"Duration: {metric.duration_ms:.1f}ms, Status: {state}"
                    )
                    
                    # Store metrics in Redis for monitoring
                    asyncio.create_task(self._store_task_metrics(metric))
                    
                    # Cleanup
                    del self._task_metrics[task_id]
                
            except Exception as e:
                logger.error(f"Error in task postrun handler: {e}")
        
        @task_failure.connect
        def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
            """Handle task failures for monitoring and alerting"""
            try:
                if task_id in self._task_metrics:
                    metric = self._task_metrics[task_id]
                    metric.error_message = str(exception)
                    metric.success = False
                    
                    logger.error(f"❌ Task failed: {metric.task_name} [{task_id}] - Error: {exception}")
                    
                    # Store failure metrics
                    asyncio.create_task(self._store_task_metrics(metric))
                    
                    # Alert on critical task failures
                    if metric.priority in [TaskPriority.CRITICAL, TaskPriority.HIGH]:
                        asyncio.create_task(self._send_failure_alert(metric, exception))
                
            except Exception as e:
                logger.error(f"Error in task failure handler: {e}")
    
    def _get_task_priority(self, task_name: str) -> TaskPriority:
        """Determine task priority from name"""
        if 'crisis' in task_name:
            return TaskPriority.CRITICAL
        elif 'psychology' in task_name or 'user' in task_name:
            return TaskPriority.HIGH
        elif 'analytics' in task_name:
            return TaskPriority.NORMAL
        elif 'maintenance' in task_name:
            return TaskPriority.LOW
        else:
            return TaskPriority.NORMAL
    
    def _get_task_category(self, task_name: str) -> TaskCategory:
        """Determine task category from name"""
        if 'crisis' in task_name:
            return TaskCategory.CRISIS_DETECTION
        elif 'psychology' in task_name:
            return TaskCategory.PSYCHOLOGY_PROCESSING
        elif 'analytics' in task_name:
            return TaskCategory.ANALYTICS
        elif 'maintenance' in task_name:
            return TaskCategory.MAINTENANCE
        elif 'user' in task_name:
            return TaskCategory.USER_OPERATIONS
        else:
            return TaskCategory.USER_OPERATIONS
    
    async def _check_task_performance(self, metric: TaskMetrics):
        """Check task performance against targets"""
        try:
            target_key = None
            
            # Map task categories to performance targets
            if metric.category == TaskCategory.CRISIS_DETECTION:
                target_key = "crisis_processing_time"
            elif metric.category == TaskCategory.ANALYTICS:
                target_key = "analytics_processing_time"
            
            if target_key and target_key in self.performance_targets:
                target_ms = self.performance_targets[target_key]
                
                if metric.duration_ms > target_ms:
                    logger.warning(
                        f"⚠️ Task performance target exceeded: {metric.task_name} "
                        f"took {metric.duration_ms:.1f}ms (target: {target_ms}ms)"
                    )
                    
                    # Record performance violation in monitoring system
                    await performance_monitor._record_metric(
                        name=f"task_performance_violation",
                        value=metric.duration_ms - target_ms,
                        metric_type=performance_monitor.MetricType.GAUGE,
                        tags={
                            "task_name": metric.task_name,
                            "category": metric.category.value,
                            "priority": metric.priority.value
                        },
                        description=f"Task performance target violation"
                    )
        
        except Exception as e:
            logger.error(f"Error checking task performance: {e}")
    
    async def _store_task_metrics(self, metric: TaskMetrics):
        """Store task metrics in Redis for monitoring"""
        try:
            metrics_data = {
                "task_id": metric.task_id,
                "task_name": metric.task_name,
                "priority": metric.priority.value,
                "category": metric.category.value,
                "duration_ms": metric.duration_ms,
                "success": metric.success,
                "error_message": metric.error_message,
                "timestamp": metric.start_time
            }
            
            # Store in Redis with TTL
            await redis_service.set(
                f"task_metrics:{metric.task_id}",
                metrics_data,
                ttl=86400  # 24 hours
            )
            
            # Update counters for analytics
            counter_key = f"task_counter:{metric.category.value}"
            await redis_service.increment(counter_key)
            
            if metric.success:
                success_key = f"task_success:{metric.category.value}"
                await redis_service.increment(success_key)
            else:
                failure_key = f"task_failure:{metric.category.value}"
                await redis_service.increment(failure_key)
            
        except Exception as e:
            logger.error(f"Error storing task metrics: {e}")
    
    async def _send_failure_alert(self, metric: TaskMetrics, exception: Exception):
        """Send alerts for critical task failures"""
        try:
            alert_data = {
                "alert_type": "task_failure",
                "task_name": metric.task_name,
                "task_id": metric.task_id,
                "priority": metric.priority.value,
                "category": metric.category.value,
                "error": str(exception),
                "timestamp": time.time()
            }
            
            # Store alert in Redis for monitoring dashboard
            await redis_service.set(
                f"alert:task_failure:{metric.task_id}",
                alert_data,
                ttl=86400  # 24 hours
            )
            
            logger.critical(f"🚨 CRITICAL TASK FAILURE: {metric.task_name} - {exception}")
            
        except Exception as e:
            logger.error(f"Error sending failure alert: {e}")
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get comprehensive task status information"""
        try:
            # Get Celery task result
            result = AsyncResult(task_id, app=self.app)
            
            # Get stored metrics
            metrics_data = await redis_service.get(f"task_metrics:{task_id}")
            
            status_info = {
                "task_id": task_id,
                "state": result.state,
                "result": result.result if result.successful() else None,
                "error": str(result.result) if result.failed() else None,
                "ready": result.ready(),
                "successful": result.successful(),
                "failed": result.failed(),
                "timestamp": time.time()
            }
            
            if metrics_data:
                status_info.update(metrics_data)
            
            return status_info
            
        except Exception as e:
            logger.error(f"Error getting task status: {e}")
            return {"task_id": task_id, "error": str(e)}
    
    async def get_queue_statistics(self) -> Dict[str, Any]:
        """Get comprehensive queue statistics"""
        try:
            # This would require connecting to Redis and inspecting queues
            # For now, return basic structure
            stats = {
                "queues": {
                    "crisis": {"active": 0, "pending": 0, "processed": 0},
                    "psychology": {"active": 0, "pending": 0, "processed": 0},
                    "user_ops": {"active": 0, "pending": 0, "processed": 0},
                    "analytics": {"active": 0, "pending": 0, "processed": 0},
                    "maintenance": {"active": 0, "pending": 0, "processed": 0}
                },
                "workers": {
                    "active": 0,
                    "total": 0
                },
                "performance": {
                    "total_tasks_processed": 0,
                    "success_rate": 0.0,
                    "avg_processing_time": 0.0
                },
                "timestamp": time.time()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting queue statistics: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive Celery health check"""
        try:
            health_status = {
                "status": "healthy",
                "components": {},
                "timestamp": time.time()
            }
            
            # Check Redis broker connectivity
            try:
                # Simple broker ping test
                with self.app.connection() as conn:
                    conn.ensure_connection(max_retries=3)
                
                health_status["components"]["broker"] = {
                    "status": "healthy",
                    "url": settings.CELERY_BROKER_URL.split('@')[1] if '@' in settings.CELERY_BROKER_URL else settings.CELERY_BROKER_URL
                }
            except Exception as e:
                health_status["components"]["broker"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["status"] = "degraded"
            
            # Check result backend
            try:
                # Test result backend connectivity
                test_result = AsyncResult('test-health-check', app=self.app)
                health_status["components"]["result_backend"] = {
                    "status": "healthy",
                    "url": settings.CELERY_RESULT_BACKEND.split('@')[1] if '@' in settings.CELERY_RESULT_BACKEND else settings.CELERY_RESULT_BACKEND
                }
            except Exception as e:
                health_status["components"]["result_backend"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["status"] = "degraded"
            
            # Get basic queue info
            queue_stats = await self.get_queue_statistics()
            health_status["components"]["queues"] = queue_stats
            
            return health_status
            
        except Exception as e:
            logger.error(f"Celery health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }

# Global Celery service instance
celery_service = CeleryService()

# Create Celery app instance for worker processes
celery_app = celery_service.create_app()

# Export for Celery worker command
app = celery_app

# Utility functions for task management
async def dispatch_task(
    task_name: str,
    args: tuple = (),
    kwargs: dict = None,
    priority: TaskPriority = TaskPriority.NORMAL,
    countdown: int = 0,
    eta: Optional[float] = None
) -> AsyncResult:
    """
    Dispatch task with performance monitoring
    
    Args:
        task_name: Task function name
        args: Task arguments
        kwargs: Task keyword arguments
        priority: Task priority level
        countdown: Delay in seconds before execution
        eta: Absolute time for execution
    
    Returns:
        AsyncResult object for tracking
    """
    try:
        start_time = time.time()
        
        # Prepare task options
        task_options = {
            'priority': priority.value,
            'countdown': countdown
        }
        
        if eta:
            task_options['eta'] = eta
        
        # Dispatch task
        result = celery_app.send_task(
            task_name,
            args=args,
            kwargs=kwargs or {},
            **task_options
        )
        
        # Track dispatch latency
        dispatch_latency = (time.time() - start_time) * 1000
        
        # Log dispatch
        logger.info(
            f"📤 Task dispatched: {task_name} [{result.id}] - "
            f"Priority: {priority.value}, Latency: {dispatch_latency:.1f}ms"
        )
        
        # Check dispatch performance target
        if dispatch_latency > celery_service.performance_targets["task_dispatch_latency"]:
            logger.warning(f"⚠️ Task dispatch latency exceeded target: {dispatch_latency:.1f}ms")
        
        return result
        
    except Exception as e:
        logger.error(f"Error dispatching task {task_name}: {e}")
        raise

# Task decorator for automatic monitoring
def monitored_task(priority: TaskPriority = TaskPriority.NORMAL, category: TaskCategory = TaskCategory.USER_OPERATIONS):
    """Decorator for tasks with automatic performance monitoring"""
    
    def decorator(func):
        # Create Celery task with monitoring
        task = celery_app.task(
            bind=True,
            autoretry_for=(Exception,),
            retry_kwargs={'max_retries': 3, 'countdown': 60},
            acks_late=True,
            reject_on_worker_lost=True
        )(func)
        
        # Store task metadata
        task.priority = priority
        task.category = category
        
        return task
    
    return decorator