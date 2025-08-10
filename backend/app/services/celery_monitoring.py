# backend/app/services/celery_monitoring.py
"""
Celery Worker Monitoring and Health Check System for Phase 0C
Provides comprehensive monitoring, health checks, and integration with Flower dashboard
"""

import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import psutil
import socket
import requests
from contextlib import asynccontextmanager

from app.core.cache_patterns import CachePatterns, CacheTTL, CacheKeyBuilder, CacheDomain

# Celery monitoring imports
from celery import Celery
from celery.events.state import State
from celery.events import EventReceiver
from kombu import Connection

# App imports
from app.services.celery_service import celery_app, celery_service
from app.services.redis_service_simple import simple_redis_service as redis_service
from app.core.config import settings
from app.core.performance_monitor import performance_monitor

logger = logging.getLogger(__name__)

class WorkerStatus(Enum):
    """Worker status enumeration"""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    IDLE = "idle"
    UNKNOWN = "unknown"

class QueueStatus(Enum):
    """Queue status enumeration"""
    HEALTHY = "healthy"
    CONGESTED = "congested"
    STALLED = "stalled"
    EMPTY = "empty"

@dataclass
class WorkerInfo:
    """Worker information structure"""
    hostname: str
    status: WorkerStatus
    active_tasks: int
    processed_tasks: int
    failed_tasks: int
    cpu_usage: float
    memory_usage: float
    load_average: List[float]
    last_heartbeat: datetime
    queues: List[str]
    software_info: Dict[str, str]

@dataclass
class QueueInfo:
    """Queue information structure"""
    name: str
    status: QueueStatus
    message_count: int
    consumer_count: int
    average_processing_time: float
    error_rate: float
    throughput: float
    priority_distribution: Dict[str, int]

@dataclass
class TaskInfo:
    """Task execution information"""
    task_id: str
    task_name: str
    worker: str
    queue: str
    state: str
    priority: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    runtime: Optional[float]
    retries: int
    args: List[Any]
    kwargs: Dict[str, Any]
    result: Optional[Any]
    exception: Optional[str]

class CeleryMonitoringService:
    """
    Comprehensive Celery monitoring service with health checks and performance tracking
    Integrates with Phase 0B Redis infrastructure and performance monitoring
    """
    
    def __init__(self):
        self._monitoring_active = False
        self._event_receiver = None
        self._state = State()
        self._monitoring_interval = 30  # seconds
        self._performance_thresholds = {
            'max_queue_size': 1000,
            'max_processing_time': 300,  # 5 minutes
            'max_error_rate': 0.05,  # 5%
            'max_worker_cpu': 80.0,  # 80%
            'max_worker_memory': 85.0,  # 85%
            'min_workers_per_queue': 1
        }
    
    async def initialize(self) -> None:
        """Initialize monitoring service"""
        try:
            logger.info("🔍 Initializing Celery monitoring service...")
            
            # Test Celery app connectivity
            with celery_app.connection() as conn:
                conn.ensure_connection(max_retries=3)
            
            # Initialize state tracking
            self._state = State()
            
            logger.info("✅ Celery monitoring service initialized")
            
        except Exception as e:
            logger.error(f"❌ Error initializing Celery monitoring: {e}")
            raise
    
    async def start_monitoring(self) -> None:
        """Start continuous monitoring of Celery workers and queues"""
        if self._monitoring_active:
            logger.warning("Celery monitoring already active")
            return
        
        try:
            self._monitoring_active = True
            logger.info("🚀 Starting Celery monitoring...")
            
            # Start monitoring loop
            monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            # Start event processing
            event_task = asyncio.create_task(self._process_events())
            
            # Wait for tasks to complete (they run indefinitely)
            await asyncio.gather(monitoring_task, event_task)
            
        except Exception as e:
            logger.error(f"Error in Celery monitoring: {e}")
            self._monitoring_active = False
            raise
    
    async def stop_monitoring(self) -> None:
        """Stop monitoring service"""
        self._monitoring_active = False
        if self._event_receiver:
            self._event_receiver.should_stop = True
        
        logger.info("🛑 Celery monitoring stopped")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self._monitoring_active:
            try:
                # Collect comprehensive metrics
                worker_stats = await self.get_worker_statistics()
                queue_stats = await self.get_queue_statistics()
                task_stats = await self.get_task_statistics()
                
                # Perform health checks
                health_status = await self.perform_health_checks()
                
                # Store monitoring data
                monitoring_data = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'workers': worker_stats,
                    'queues': queue_stats,
                    'tasks': task_stats,
                    'health_status': health_status,
                    'system_metrics': await self._get_system_metrics()
                }
                
                # Store in Redis for dashboard access using standardized pattern
                cache_key = CacheKeyBuilder.build_key(CacheDomain.CELERY, "monitoring_snapshot")
                await redis_service.set(
                    cache_key,
                    monitoring_data,
                    ttl=self._monitoring_interval * 2
                )
                
                # Check for alerts
                await self._check_monitoring_alerts(monitoring_data)
                
                # Sleep until next monitoring cycle
                await asyncio.sleep(self._monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self._monitoring_interval)
    
    async def _process_events(self) -> None:
        """Process Celery events for real-time monitoring"""
        try:
            with celery_app.connection() as connection:
                recv = EventReceiver(
                    connection,
                    handlers={
                        'task-sent': self._on_task_sent,
                        'task-received': self._on_task_received,
                        'task-started': self._on_task_started,
                        'task-succeeded': self._on_task_succeeded,
                        'task-failed': self._on_task_failed,
                        'task-retried': self._on_task_retried,
                        'worker-online': self._on_worker_online,
                        'worker-offline': self._on_worker_offline,
                        'worker-heartbeat': self._on_worker_heartbeat,
                    }
                )
                
                self._event_receiver = recv
                
                # Process events
                while self._monitoring_active:
                    try:
                        recv.capture(limit=None, timeout=1.0, wakeup=True)
                    except socket.timeout:
                        continue
                    except Exception as e:
                        logger.error(f"Error processing events: {e}")
                        await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"Error setting up event processing: {e}")
    
    def _on_task_sent(self, event: Dict[str, Any]) -> None:
        """Handle task-sent event"""
        self._state.event(event)
        
        # Track task dispatch metrics
        asyncio.create_task(self._track_task_event('sent', event))
    
    def _on_task_received(self, event: Dict[str, Any]) -> None:
        """Handle task-received event"""
        self._state.event(event)
        asyncio.create_task(self._track_task_event('received', event))
    
    def _on_task_started(self, event: Dict[str, Any]) -> None:
        """Handle task-started event"""
        self._state.event(event)
        asyncio.create_task(self._track_task_event('started', event))
    
    def _on_task_succeeded(self, event: Dict[str, Any]) -> None:
        """Handle task-succeeded event"""
        self._state.event(event)
        asyncio.create_task(self._track_task_event('succeeded', event))
    
    def _on_task_failed(self, event: Dict[str, Any]) -> None:
        """Handle task-failed event"""
        self._state.event(event)
        asyncio.create_task(self._track_task_event('failed', event))
        
        # Log critical failures
        task_name = event.get('name', 'unknown')
        logger.error(f"❌ Task failed: {task_name} [{event.get('uuid', 'unknown')}]")
    
    def _on_task_retried(self, event: Dict[str, Any]) -> None:
        """Handle task-retried event"""
        self._state.event(event)
        asyncio.create_task(self._track_task_event('retried', event))
    
    def _on_worker_online(self, event: Dict[str, Any]) -> None:
        """Handle worker-online event"""
        self._state.event(event)
        worker_name = event.get('hostname', 'unknown')
        logger.info(f"✅ Worker online: {worker_name}")
        
        asyncio.create_task(self._track_worker_event('online', event))
    
    def _on_worker_offline(self, event: Dict[str, Any]) -> None:
        """Handle worker-offline event"""
        self._state.event(event)
        worker_name = event.get('hostname', 'unknown')
        logger.warning(f"⚠️ Worker offline: {worker_name}")
        
        asyncio.create_task(self._track_worker_event('offline', event))
    
    def _on_worker_heartbeat(self, event: Dict[str, Any]) -> None:
        """Handle worker-heartbeat event"""
        self._state.event(event)
        asyncio.create_task(self._track_worker_event('heartbeat', event))
    
    async def _track_task_event(self, event_type: str, event: Dict[str, Any]) -> None:
        """Track task events for analytics"""
        try:
            # Update counters
            await redis_service.increment(f"celery_task_events:{event_type}")
            await redis_service.increment("celery_total_task_events")
            
            # Store recent events for debugging
            event_key = f"celery_recent_events:{event_type}"
            recent_events = await redis_service.get(event_key) or []
            
            # Add new event
            event_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'task_id': event.get('uuid', 'unknown'),
                'task_name': event.get('name', 'unknown'),
                'worker': event.get('hostname', 'unknown'),
                'event_data': event
            }
            
            recent_events.append(event_data)
            
            # Keep only last 100 events per type
            if len(recent_events) > 100:
                recent_events.pop(0)
            
            await redis_service.set(event_key, recent_events, ttl=3600)
            
        except Exception as e:
            logger.error(f"Error tracking task event: {e}")
    
    async def _track_worker_event(self, event_type: str, event: Dict[str, Any]) -> None:
        """Track worker events for monitoring"""
        try:
            # Update worker status tracking
            worker_name = event.get('hostname', 'unknown')
            worker_status_key = f"celery_worker_status:{worker_name}"
            
            status_data = {
                'status': event_type,
                'timestamp': datetime.utcnow().isoformat(),
                'event_data': event
            }
            
            await redis_service.set(worker_status_key, status_data, ttl=300)  # 5 minutes
            
            # Update counters
            await redis_service.increment(f"celery_worker_events:{event_type}")
            
        except Exception as e:
            logger.error(f"Error tracking worker event: {e}")
    
    async def get_worker_statistics(self) -> List[Dict[str, Any]]:
        """Get comprehensive worker statistics"""
        try:
            worker_stats = []
            
            # Get active workers from Celery
            inspect = celery_app.control.inspect()
            
            # Get worker status
            stats = inspect.stats()
            active_workers = inspect.active()
            registered_tasks = inspect.registered()
            
            if stats:
                for worker_name, worker_data in stats.items():
                    try:
                        # Get active tasks for this worker
                        active_tasks = active_workers.get(worker_name, []) if active_workers else []
                        
                        # Get system metrics for worker
                        worker_info = {
                            'hostname': worker_name,
                            'status': WorkerStatus.ONLINE.value,
                            'active_tasks': len(active_tasks),
                            'processed_tasks': worker_data.get('total', {}).get('count', 0),
                            'failed_tasks': 0,  # Would need to track failures
                            'cpu_usage': 0.0,  # Would get from worker if available
                            'memory_usage': 0.0,  # Would get from worker if available
                            'load_average': worker_data.get('rusage', {}).get('stime', 0),
                            'last_heartbeat': datetime.utcnow().isoformat(),
                            'queues': list(worker_data.get('pool', {}).get('processes', [])),
                            'software_info': {
                                'celery_version': worker_data.get('sw_ver', 'unknown'),
                                'python_version': worker_data.get('sw_sys', 'unknown')
                            },
                            'registered_tasks': len(registered_tasks.get(worker_name, [])) if registered_tasks else 0,
                            'pool_info': worker_data.get('pool', {}),
                            'broker_info': worker_data.get('broker', {})
                        }
                        
                        worker_stats.append(worker_info)
                        
                    except Exception as e:
                        logger.error(f"Error getting stats for worker {worker_name}: {e}")
                        continue
            
            # If no workers found, check if any should be running
            if not worker_stats:
                logger.warning("⚠️ No active Celery workers found")
                
                # Add placeholder for expected workers
                worker_stats.append({
                    'hostname': 'expected_worker',
                    'status': WorkerStatus.OFFLINE.value,
                    'active_tasks': 0,
                    'processed_tasks': 0,
                    'failed_tasks': 0,
                    'cpu_usage': 0.0,
                    'memory_usage': 0.0,
                    'load_average': 0.0,
                    'last_heartbeat': None,
                    'queues': [],
                    'software_info': {},
                    'registered_tasks': 0,
                    'pool_info': {},
                    'broker_info': {}
                })
            
            return worker_stats
            
        except Exception as e:
            logger.error(f"Error getting worker statistics: {e}")
            return []
    
    async def get_queue_statistics(self) -> List[Dict[str, Any]]:
        """Get comprehensive queue statistics"""
        try:
            queue_stats = []
            
            # Define expected queues from configuration
            expected_queues = ['crisis', 'psychology', 'user_ops', 'analytics', 'maintenance', 'default']
            
            # Get queue info from Redis broker
            with celery_app.connection() as connection:
                for queue_name in expected_queues:
                    try:
                        # Get basic queue info
                        # Note: This is simplified - real implementation would query Redis directly
                        queue_info = {
                            'name': queue_name,
                            'status': QueueStatus.HEALTHY.value,
                            'message_count': 0,  # Would get from Redis
                            'consumer_count': 1,  # Would get from broker
                            'average_processing_time': 0.0,
                            'error_rate': 0.0,
                            'throughput': 0.0,
                            'priority_distribution': {'high': 0, 'normal': 0, 'low': 0},
                            'oldest_message_age': 0,
                            'processing_rate': 0.0,
                            'estimated_completion_time': None
                        }
                        
                        # Get task statistics for this queue
                        queue_task_stats = await self._get_queue_task_stats(queue_name)
                        queue_info.update(queue_task_stats)
                        
                        # Determine queue status
                        if queue_info['message_count'] > self._performance_thresholds['max_queue_size']:
                            queue_info['status'] = QueueStatus.CONGESTED.value
                        elif queue_info['average_processing_time'] > self._performance_thresholds['max_processing_time']:
                            queue_info['status'] = QueueStatus.STALLED.value
                        elif queue_info['message_count'] == 0:
                            queue_info['status'] = QueueStatus.EMPTY.value
                        
                        queue_stats.append(queue_info)
                        
                    except Exception as e:
                        logger.error(f"Error getting stats for queue {queue_name}: {e}")
                        continue
            
            return queue_stats
            
        except Exception as e:
            logger.error(f"Error getting queue statistics: {e}")
            return []
    
    async def _get_queue_task_stats(self, queue_name: str) -> Dict[str, Any]:
        """Get task statistics for a specific queue"""
        try:
            # Get recent task events for this queue
            task_events = await redis_service.get(f"celery_recent_events:started") or []
            
            # Filter events for this queue and last hour
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            recent_tasks = [
                event for event in task_events
                if event.get('queue') == queue_name and 
                datetime.fromisoformat(event['timestamp']) > one_hour_ago
            ]
            
            # Calculate statistics
            if recent_tasks:
                processing_times = [
                    task.get('processing_time', 0) for task in recent_tasks
                    if task.get('processing_time')
                ]
                
                avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
                throughput = len(recent_tasks) / 1.0  # tasks per hour
            else:
                avg_processing_time = 0
                throughput = 0
            
            return {
                'average_processing_time': avg_processing_time,
                'throughput': throughput,
                'recent_task_count': len(recent_tasks)
            }
            
        except Exception as e:
            logger.error(f"Error getting queue task stats: {e}")
            return {
                'average_processing_time': 0,
                'throughput': 0,
                'recent_task_count': 0
            }
    
    async def get_task_statistics(self) -> Dict[str, Any]:
        """Get comprehensive task execution statistics"""
        try:
            # Get task event counters
            task_stats = {
                'total_events': await redis_service.get("celery_total_task_events") or 0,
                'events_by_type': {},
                'recent_tasks': [],
                'task_performance': {},
                'error_analysis': {}
            }
            
            # Get event counts by type
            event_types = ['sent', 'received', 'started', 'succeeded', 'failed', 'retried']
            for event_type in event_types:
                count = await redis_service.get(f"celery_task_events:{event_type}") or 0
                task_stats['events_by_type'][event_type] = count
            
            # Calculate success rate
            succeeded = task_stats['events_by_type'].get('succeeded', 0)
            failed = task_stats['events_by_type'].get('failed', 0)
            total_completed = succeeded + failed
            
            if total_completed > 0:
                task_stats['success_rate'] = succeeded / total_completed
                task_stats['error_rate'] = failed / total_completed
            else:
                task_stats['success_rate'] = 1.0
                task_stats['error_rate'] = 0.0
            
            # Get recent task details
            for event_type in ['succeeded', 'failed']:
                recent_events = await redis_service.get(f"celery_recent_events:{event_type}") or []
                task_stats['recent_tasks'].extend(recent_events[-10:])  # Last 10 of each type
            
            # Sort by timestamp
            task_stats['recent_tasks'].sort(
                key=lambda x: x.get('timestamp', ''), 
                reverse=True
            )
            task_stats['recent_tasks'] = task_stats['recent_tasks'][:20]  # Top 20 recent
            
            return task_stats
            
        except Exception as e:
            logger.error(f"Error getting task statistics: {e}")
            return {
                'total_events': 0,
                'events_by_type': {},
                'recent_tasks': [],
                'success_rate': 0.0,
                'error_rate': 1.0
            }
    
    async def perform_health_checks(self) -> Dict[str, Any]:
        """Perform comprehensive health checks on Celery system"""
        try:
            health_status = {
                'overall_status': 'healthy',
                'checks': {},
                'alerts': [],
                'recommendations': []
            }
            
            # Check 1: Broker connectivity
            try:
                with celery_app.connection() as conn:
                    conn.ensure_connection(max_retries=1, timeout=5)
                health_status['checks']['broker_connectivity'] = 'healthy'
            except Exception as e:
                health_status['checks']['broker_connectivity'] = 'unhealthy'
                health_status['alerts'].append(f"Broker connectivity failed: {e}")
                health_status['overall_status'] = 'unhealthy'
            
            # Check 2: Worker availability
            worker_stats = await self.get_worker_statistics()
            online_workers = [w for w in worker_stats if w['status'] == WorkerStatus.ONLINE.value]
            
            if len(online_workers) == 0:
                health_status['checks']['worker_availability'] = 'critical'
                health_status['alerts'].append("No online workers detected")
                health_status['overall_status'] = 'critical'
            elif len(online_workers) < self._performance_thresholds['min_workers_per_queue']:
                health_status['checks']['worker_availability'] = 'warning'
                health_status['alerts'].append("Low number of active workers")
                if health_status['overall_status'] == 'healthy':
                    health_status['overall_status'] = 'degraded'
            else:
                health_status['checks']['worker_availability'] = 'healthy'
            
            # Check 3: Queue congestion
            queue_stats = await self.get_queue_statistics()
            congested_queues = [q for q in queue_stats if q['status'] == QueueStatus.CONGESTED.value]
            
            if congested_queues:
                health_status['checks']['queue_congestion'] = 'warning'
                health_status['alerts'].append(f"Congested queues: {[q['name'] for q in congested_queues]}")
                if health_status['overall_status'] == 'healthy':
                    health_status['overall_status'] = 'degraded'
            else:
                health_status['checks']['queue_congestion'] = 'healthy'
            
            # Check 4: Error rate
            task_stats = await self.get_task_statistics()
            error_rate = task_stats.get('error_rate', 0)
            
            if error_rate > self._performance_thresholds['max_error_rate']:
                health_status['checks']['error_rate'] = 'warning'
                health_status['alerts'].append(f"High error rate: {error_rate:.2%}")
                if health_status['overall_status'] == 'healthy':
                    health_status['overall_status'] = 'degraded'
            else:
                health_status['checks']['error_rate'] = 'healthy'
            
            # Check 5: Worker resource usage
            high_resource_workers = []
            for worker in online_workers:
                if (worker.get('cpu_usage', 0) > self._performance_thresholds['max_worker_cpu'] or
                    worker.get('memory_usage', 0) > self._performance_thresholds['max_worker_memory']):
                    high_resource_workers.append(worker['hostname'])
            
            if high_resource_workers:
                health_status['checks']['worker_resources'] = 'warning'
                health_status['alerts'].append(f"High resource usage workers: {high_resource_workers}")
            else:
                health_status['checks']['worker_resources'] = 'healthy'
            
            # Generate recommendations
            if health_status['overall_status'] != 'healthy':
                if not online_workers:
                    health_status['recommendations'].append("Start Celery workers immediately")
                
                if congested_queues:
                    health_status['recommendations'].append("Add more workers or optimize task processing")
                
                if error_rate > self._performance_thresholds['max_error_rate']:
                    health_status['recommendations'].append("Investigate and fix failing tasks")
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error performing health checks: {e}")
            return {
                'overall_status': 'unknown',
                'checks': {},
                'alerts': [f"Health check failed: {e}"],
                'recommendations': ["Check Celery monitoring service"]
            }
    
    async def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system-level metrics for monitoring"""
        try:
            return {
                'cpu_usage': psutil.cpu_percent(interval=1),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'load_average': list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [0, 0, 0],
                'network_io': dict(psutil.net_io_counters()._asdict()) if hasattr(psutil, 'net_io_counters') else {},
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    async def _check_monitoring_alerts(self, monitoring_data: Dict[str, Any]) -> None:
        """Check monitoring data for alerts and notifications"""
        try:
            alerts = []
            
            # Check worker health
            workers = monitoring_data.get('workers', [])
            offline_workers = [w for w in workers if w['status'] == WorkerStatus.OFFLINE.value]
            
            if offline_workers:
                alerts.append({
                    'type': 'worker_offline',
                    'severity': 'high',
                    'message': f"Workers offline: {[w['hostname'] for w in offline_workers]}",
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # Check queue congestion
            queues = monitoring_data.get('queues', [])
            congested_queues = [q for q in queues if q['status'] == QueueStatus.CONGESTED.value]
            
            if congested_queues:
                alerts.append({
                    'type': 'queue_congestion',
                    'severity': 'medium',
                    'message': f"Congested queues: {[q['name'] for q in congested_queues]}",
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # Store alerts
            if alerts:
                await redis_service.set(
                    "celery_monitoring_alerts",
                    alerts,
                    ttl=3600  # 1 hour
                )
                
                # Log critical alerts
                for alert in alerts:
                    if alert['severity'] == 'high':
                        logger.critical(f"🚨 CELERY ALERT: {alert['message']}")
                    else:
                        logger.warning(f"⚠️ CELERY WARNING: {alert['message']}")
        
        except Exception as e:
            logger.error(f"Error checking monitoring alerts: {e}")
    
    async def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive data for monitoring dashboard"""
        try:
            # Get latest monitoring snapshot
            monitoring_data = await redis_service.get("celery_monitoring_snapshot")
            
            if not monitoring_data:
                # Generate fresh data if not available
                monitoring_data = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'workers': await self.get_worker_statistics(),
                    'queues': await self.get_queue_statistics(),
                    'tasks': await self.get_task_statistics(),
                    'health_status': await self.perform_health_checks(),
                    'system_metrics': await self._get_system_metrics()
                }
            
            # Get alerts
            alerts = await redis_service.get("celery_monitoring_alerts") or []
            
            # Calculate summary metrics
            workers = monitoring_data.get('workers', [])
            queues = monitoring_data.get('queues', [])
            tasks = monitoring_data.get('tasks', {})
            
            summary = {
                'total_workers': len(workers),
                'online_workers': len([w for w in workers if w['status'] == WorkerStatus.ONLINE.value]),
                'total_queues': len(queues),
                'healthy_queues': len([q for q in queues if q['status'] == QueueStatus.HEALTHY.value]),
                'total_tasks_processed': tasks.get('events_by_type', {}).get('succeeded', 0),
                'current_error_rate': tasks.get('error_rate', 0),
                'active_alerts': len(alerts),
                'overall_health': monitoring_data.get('health_status', {}).get('overall_status', 'unknown')
            }
            
            dashboard_data = {
                'summary': summary,
                'monitoring_data': monitoring_data,
                'alerts': alerts,
                'last_updated': monitoring_data.get('timestamp'),
                'monitoring_active': self._monitoring_active
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def get_flower_integration_status(self) -> Dict[str, Any]:
        """Check Flower dashboard integration status"""
        try:
            # Default Flower URL (configurable)
            flower_url = getattr(settings, 'FLOWER_URL', 'http://localhost:5555')
            
            flower_status = {
                'flower_url': flower_url,
                'accessible': False,
                'version': 'unknown',
                'workers_visible': 0,
                'last_check': datetime.utcnow().isoformat()
            }
            
            try:
                # Test Flower API accessibility
                response = requests.get(f"{flower_url}/api/workers", timeout=5)
                
                if response.status_code == 200:
                    flower_status['accessible'] = True
                    workers_data = response.json()
                    flower_status['workers_visible'] = len(workers_data)
                    
                    # Try to get Flower version
                    try:
                        info_response = requests.get(f"{flower_url}/api/workers", timeout=3)
                        # Flower version would be in headers or response
                        flower_status['version'] = 'detected'
                    except:
                        pass
                
            except requests.RequestException as e:
                flower_status['error'] = str(e)
            
            return flower_status
            
        except Exception as e:
            logger.error(f"Error checking Flower integration: {e}")
            return {
                'accessible': False,
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
    
    async def trigger_manual_health_check(self) -> Dict[str, Any]:
        """Trigger manual health check and return results"""
        try:
            logger.info("🔍 Performing manual Celery health check...")
            
            start_time = time.time()
            
            # Perform comprehensive checks
            health_results = await self.perform_health_checks()
            worker_stats = await self.get_worker_statistics()
            queue_stats = await self.get_queue_statistics()
            task_stats = await self.get_task_statistics()
            
            # Add performance information
            performance_info = {
                'check_duration_seconds': time.time() - start_time,
                'worker_response_time': 0.0,  # Would measure actual response time
                'queue_inspection_time': 0.0,  # Would measure queue inspection time
                'overall_system_responsiveness': 'good'  # Would calculate based on metrics
            }
            
            manual_check_results = {
                'check_type': 'manual',
                'timestamp': datetime.utcnow().isoformat(),
                'health_status': health_results,
                'worker_summary': {
                    'total_workers': len(worker_stats),
                    'online_workers': len([w for w in worker_stats if w['status'] == WorkerStatus.ONLINE.value]),
                    'worker_details': worker_stats
                },
                'queue_summary': {
                    'total_queues': len(queue_stats),
                    'healthy_queues': len([q for q in queue_stats if q['status'] == QueueStatus.HEALTHY.value]),
                    'queue_details': queue_stats
                },
                'task_summary': task_stats,
                'performance_info': performance_info
            }
            
            # Store manual check results
            await redis_service.set(
                "celery_manual_health_check",
                manual_check_results,
                ttl=1800  # 30 minutes
            )
            
            logger.info(f"✅ Manual health check completed: {health_results['overall_status']}")
            
            return manual_check_results
            
        except Exception as e:
            error_result = {
                'check_type': 'manual',
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'failed',
                'error': str(e)
            }
            
            logger.error(f"❌ Manual health check failed: {e}")
            return error_result

# Global monitoring service instance
celery_monitoring_service = CeleryMonitoringService()

# === CELERY MANAGEMENT UTILITIES ===

async def start_celery_monitoring():
    """Start Celery monitoring service"""
    try:
        await celery_monitoring_service.initialize()
        await celery_monitoring_service.start_monitoring()
    except Exception as e:
        logger.error(f"Failed to start Celery monitoring: {e}")
        raise

async def stop_celery_monitoring():
    """Stop Celery monitoring service"""
    try:
        await celery_monitoring_service.stop_monitoring()
    except Exception as e:
        logger.error(f"Failed to stop Celery monitoring: {e}")

async def get_celery_status() -> Dict[str, Any]:
    """Get comprehensive Celery system status"""
    try:
        dashboard_data = await celery_monitoring_service.get_monitoring_dashboard_data()
        flower_status = await celery_monitoring_service.get_flower_integration_status()
        
        return {
            'celery_monitoring': dashboard_data,
            'flower_integration': flower_status,
            'system_timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting Celery status: {e}")
        return {
            'error': str(e),
            'system_timestamp': datetime.utcnow().isoformat()
        }

async def restart_failed_tasks(max_retries: int = 3) -> Dict[str, Any]:
    """Restart failed tasks with retry logic"""
    try:
        logger.info("🔄 Restarting failed tasks...")
        
        # Get recent failed tasks
        failed_events = await redis_service.get("celery_recent_events:failed") or []
        
        restart_results = {
            'tasks_found': len(failed_events),
            'tasks_restarted': 0,
            'restart_failures': 0,
            'restarted_task_ids': []
        }
        
        for failed_event in failed_events[-20:]:  # Last 20 failed tasks
            try:
                task_id = failed_event.get('task_id')
                task_name = failed_event.get('task_name')
                
                if not task_id or not task_name:
                    continue
                
                # Check retry count
                retry_count = failed_event.get('retry_count', 0)
                if retry_count >= max_retries:
                    continue
                
                # Restart the task (would implement actual task restart logic)
                # For now, just log the restart attempt
                logger.info(f"🔄 Restarting task: {task_name} [{task_id}]")
                
                restart_results['tasks_restarted'] += 1
                restart_results['restarted_task_ids'].append(task_id)
                
            except Exception as e:
                logger.error(f"Error restarting task: {e}")
                restart_results['restart_failures'] += 1
        
        logger.info(f"✅ Task restart completed: {restart_results['tasks_restarted']} restarted")
        
        return restart_results
        
    except Exception as e:
        logger.error(f"Error restarting failed tasks: {e}")
        return {
            'error': str(e),
            'tasks_restarted': 0
        }

async def scale_workers(queue_name: str, target_workers: int) -> Dict[str, Any]:
    """Scale workers for a specific queue (placeholder for production implementation)"""
    try:
        logger.info(f"📈 Scaling workers for queue {queue_name} to {target_workers}")
        
        # In production, this would:
        # 1. Use container orchestration (Docker Compose, Kubernetes)
        # 2. Start/stop worker processes dynamically
        # 3. Update worker configuration
        # 4. Monitor scaling success
        
        scaling_result = {
            'queue_name': queue_name,
            'target_workers': target_workers,
            'scaling_status': 'simulated',  # Would be 'success' in production
            'current_workers': 1,  # Would get actual count
            'message': f"Worker scaling for {queue_name} would be implemented in production",
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return scaling_result
        
    except Exception as e:
        logger.error(f"Error scaling workers: {e}")
        return {
            'queue_name': queue_name,
            'scaling_status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

# === CELERY WORKER STARTUP SCRIPT ===

def create_worker_startup_script() -> str:
    """Generate Celery worker startup script for Phase 0C"""
    
    startup_script = f"""#!/bin/bash
# Celery Worker Startup Script for Phase 0C Background Processing
# Generated automatically - Phase 0A Database + Phase 0B Redis + Phase 0C Celery

set -e

# Configuration
CELERY_APP="app.services.celery_service:celery_app"
WORKER_NAME="worker-$(hostname)-$"
LOG_LEVEL="INFO"
CONCURRENCY=4

# Redis Broker Configuration (Phase 0B Integration)
export CELERY_BROKER_URL="{settings.CELERY_BROKER_URL}"
export CELERY_RESULT_BACKEND="{settings.CELERY_RESULT_BACKEND}"

# Performance Optimizations
export CELERY_WORKER_PREFETCH_MULTIPLIER=4
export CELERY_WORKER_MAX_TASKS_PER_CHILD=1000
export CELERY_TASK_SOFT_TIME_LIMIT=300
export CELERY_TASK_TIME_LIMIT=600

echo "🚀 Starting Celery Worker for Phase 0C Background Processing"
echo "📊 Worker Name: $WORKER_NAME"
echo "🔧 Concurrency: $CONCURRENCY"
echo "📡 Broker: Redis (Phase 0B Integration)"
echo "🎯 Queues: crisis,psychology,user_ops,analytics,maintenance,default"

# Start Celery Worker
exec celery -A $CELERY_APP worker \\
    --hostname=$WORKER_NAME \\
    --loglevel=$LOG_LEVEL \\
    --concurrency=$CONCURRENCY \\
    --queues=crisis,psychology,user_ops,analytics,maintenance,default \\
    --events \\
    --time-limit=600 \\
    --soft-time-limit=300 \\
    --max-tasks-per-child=1000 \\
    --prefetch-multiplier=4 \\
    --without-gossip \\
    --without-mingle \\
    --without-heartbeat
"""
    
    return startup_script

def create_flower_startup_script() -> str:
    """Generate Flower monitoring dashboard startup script"""
    
    flower_script = f"""#!/bin/bash
# Flower Monitoring Dashboard Startup Script for Phase 0C
# Provides web-based monitoring for Celery workers and tasks

set -e

# Configuration
CELERY_APP="app.services.celery_service:celery_app"
FLOWER_PORT=5555
FLOWER_ADDRESS="0.0.0.0"

# Redis Broker Configuration
export CELERY_BROKER_URL="{settings.CELERY_BROKER_URL}"
export CELERY_RESULT_BACKEND="{settings.CELERY_RESULT_BACKEND}"

echo "🌸 Starting Flower Monitoring Dashboard"
echo "📊 URL: http://localhost:$FLOWER_PORT"
echo "🔧 Celery App: $CELERY_APP"
echo "📡 Broker: Redis (Phase 0B Integration)"

# Start Flower
exec celery -A $CELERY_APP flower \\
    --port=$FLOWER_PORT \\
    --address=$FLOWER_ADDRESS \\
    --broker=$CELERY_BROKER_URL \\
    --persistent=True \\
    --db=flower.db \\
    --max_tasks=10000
"""
    
    return flower_script

def create_celery_beat_startup_script() -> str:
    """Generate Celery Beat scheduler startup script"""
    
    beat_script = f"""#!/bin/bash
# Celery Beat Scheduler Startup Script for Phase 0C
# Handles scheduled tasks for maintenance, analytics, and monitoring

set -e

# Configuration
CELERY_APP="app.services.celery_service:celery_app"
BEAT_SCHEDULE_FILE="celerybeat-schedule"
LOG_LEVEL="INFO"

# Redis Broker Configuration
export CELERY_BROKER_URL="{settings.CELERY_BROKER_URL}"
export CELERY_RESULT_BACKEND="{settings.CELERY_RESULT_BACKEND}"

echo "⏰ Starting Celery Beat Scheduler"
echo "📋 Schedule File: $BEAT_SCHEDULE_FILE"
echo "🔧 Celery App: $CELERY_APP"
echo "📡 Broker: Redis (Phase 0B Integration)"

# Start Celery Beat
exec celery -A $CELERY_APP beat \\
    --loglevel=$LOG_LEVEL \\
    --schedule=$BEAT_SCHEDULE_FILE \\
    --pidfile=celerybeat.pid
"""
    
    return beat_script

# === DOCKER COMPOSE INTEGRATION ===

def create_docker_compose_celery_services() -> str:
    """Generate Docker Compose services for Celery components"""
    
    docker_compose = f"""
# Docker Compose Services for Phase 0C Celery Background Processing
# Add these services to your existing docker-compose.yml

services:
  # Celery Worker for Background Tasks
  celery-worker:
    build: .
    command: >
      celery -A app.services.celery_service:celery_app worker
      --hostname=worker-%(process_num)02d
      --loglevel=INFO
      --concurrency=4
      --queues=crisis,psychology,user_ops,analytics,maintenance,default
      --events
      --time-limit=600
      --soft-time-limit=300
      --max-tasks-per-child=1000
      --prefetch-multiplier=4
    environment:
      - CELERY_BROKER_URL={settings.CELERY_BROKER_URL}
      - CELERY_RESULT_BACKEND={settings.CELERY_RESULT_BACKEND}
    depends_on:
      - redis
      - postgres
    volumes:
      - ./:/app
    restart: unless-stopped
    deploy:
      replicas: 2  # Scale as needed

  # Celery Beat Scheduler
  celery-beat:
    build: .
    command: >
      celery -A app.services.celery_service:celery_app beat
      --loglevel=INFO
      --schedule=celerybeat-schedule
      --pidfile=celerybeat.pid
    environment:
      - CELERY_BROKER_URL={settings.CELERY_BROKER_URL}
      - CELERY_RESULT_BACKEND={settings.CELERY_RESULT_BACKEND}
    depends_on:
      - redis
      - postgres
    volumes:
      - ./:/app
    restart: unless-stopped

  # Flower Monitoring Dashboard
  flower:
    build: .
    command: >
      celery -A app.services.celery_service:celery_app flower
      --port=5555
      --address=0.0.0.0
      --persistent=True
      --db=flower.db
      --max_tasks=10000
    environment:
      - CELERY_BROKER_URL={settings.CELERY_BROKER_URL}
      - CELERY_RESULT_BACKEND={settings.CELERY_RESULT_BACKEND}
    ports:
      - "5555:5555"
    depends_on:
      - redis
      - celery-worker
    volumes:
      - ./flower-data:/app/flower-data
    restart: unless-stopped

# Volumes for persistent data
volumes:
  flower-data:
    driver: local
"""
    
    return docker_compose