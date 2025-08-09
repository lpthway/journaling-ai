# backend/app/core/performance_monitor.py
"""
Performance Monitoring and Metrics Collection for Phase 0B
Provides comprehensive monitoring for Redis and PostgreSQL performance
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from enum import Enum
import psutil
import json

from app.core.database import database

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of performance metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMING = "timing"

@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    tags: Dict[str, str]
    description: Optional[str] = None

@dataclass
class SystemMetrics:
    """System-level performance metrics"""
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_usage_percent: float
    timestamp: datetime

@dataclass
class DatabaseMetrics:
    """Database performance metrics"""
    connection_pool_size: int
    active_connections: int
    query_response_time_ms: float
    slow_queries_count: int
    errors_count: int
    timestamp: datetime

@dataclass
class CacheMetrics:
    """Redis cache performance metrics"""
    hit_rate: float
    miss_rate: float
    avg_response_time_ms: float
    memory_usage_mb: float
    connected_clients: int
    operations_per_second: float
    timestamp: datetime

class PerformanceMonitor:
    """
    Comprehensive performance monitoring system
    Tracks PostgreSQL, Redis, and system performance
    """
    
    def __init__(self):
        self._monitoring = False
        self._metrics_history: List[PerformanceMetric] = []
        self._max_history_size = 1000
        
        # Performance targets from Phase 0B requirements
        self.targets = {
            "cache_hit_rate": 0.80,           # >80% cache hit rate
            "redis_response_time": 5.0,       # <5ms Redis response time
            "session_retrieval_time": 10.0,   # <10ms session retrieval
            "db_query_time": 50.0,            # <50ms database queries
            "psychology_cache_time": 2.0      # <2ms psychology cache queries
        }
    
    @asynccontextmanager
    async def timed_operation(self, operation_name: str, tags: Dict[str, str] = None):
        """Context manager for timing operations"""
        start_time = time.time()
        error_occurred = False
        
        try:
            yield
        except Exception as e:
            error_occurred = True
            await self._record_metric(
                name=f"{operation_name}_error",
                value=1,
                metric_type=MetricType.COUNTER,
                tags=tags or {},
                description=f"Error in {operation_name}: {str(e)}"
            )
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            
            await self._record_metric(
                name=f"{operation_name}_duration",
                value=duration_ms,
                metric_type=MetricType.TIMING,
                tags=tags or {},
                description=f"Duration of {operation_name} operation"
            )
            
            # Check against performance targets
            await self._check_performance_target(operation_name, duration_ms)
    
    async def _record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        description: Optional[str] = None,
        tags: Dict[str, str] = None
    ) -> None:
        """Record performance metric with automatic history management"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            metric_type=metric_type,
            timestamp=datetime.utcnow(),
            tags=tags or {},
            description=description
        )
        
        # Add to history with size management
        self._metrics_history.append(metric)
        if len(self._metrics_history) > self._max_history_size:
            self._metrics_history.pop(0)
        
        # Store in Redis for distributed monitoring
        try:
            # Lazy import to avoid circular dependency
            from app.services.redis_service import redis_service
            await redis_service.set(
                f"metrics:{name}:{int(time.time())}",
                asdict(metric),
                ttl=3600  # 1 hour retention
            )
        except Exception as e:
            logger.warning(f"Failed to store metric in Redis: {e}")
    
    async def _check_performance_target(self, operation_name: str, duration_ms: float) -> None:
        """Check operation against performance targets and alert if exceeded"""
        target_key = None
        
        # Map operation names to performance targets
        if "redis" in operation_name.lower():
            target_key = "redis_response_time"
        elif "session" in operation_name.lower():
            target_key = "session_retrieval_time"
        elif "database" in operation_name.lower() or "db" in operation_name.lower():
            target_key = "db_query_time"
        elif "psychology" in operation_name.lower():
            target_key = "psychology_cache_time"
        
        if target_key and target_key in self.targets:
            target_ms = self.targets[target_key]
            
            if duration_ms > target_ms:
                logger.warning(
                    f"Performance target exceeded: {operation_name} took {duration_ms:.2f}ms "
                    f"(target: {target_ms}ms)"
                )
                
                # Record performance violation
                await self._record_metric(
                    name=f"{operation_name}_target_violation",
                    value=duration_ms - target_ms,
                    metric_type=MetricType.GAUGE,
                    tags={"target": str(target_ms), "actual": str(duration_ms)},
                    description=f"Performance target violation for {operation_name}"
                )
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect comprehensive system performance metrics"""
        try:
            # CPU and memory metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available_mb=memory.available / (1024 * 1024),
                disk_usage_percent=disk.percent,
                timestamp=datetime.utcnow()
            )
            
            # Store metrics
            await self._record_metric(
                name="system_cpu_percent",
                value=cpu_percent,
                metric_type=MetricType.GAUGE,
                tags={"component": "system"},
                description="CPU utilization percentage"
            )
            
            await self._record_metric(
                name="system_memory_percent",
                value=memory.percent,
                metric_type=MetricType.GAUGE,
                tags={"component": "system"},
                description="Memory utilization percentage"
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(0, 0, 0, 0, datetime.utcnow())
    
    async def collect_database_metrics(self) -> DatabaseMetrics:
        """Collect PostgreSQL performance metrics"""
        try:
            pool_status = await database.get_pool_status()
            
            # Measure query response time
            start_time = time.time()
            health_status = await database.health_check()
            query_time_ms = (time.time() - start_time) * 1000
            
            metrics = DatabaseMetrics(
                connection_pool_size=pool_status.get("size", 0),
                active_connections=pool_status.get("checked_out", 0),
                query_response_time_ms=query_time_ms,
                slow_queries_count=0,  # Would need query log analysis
                errors_count=0 if health_status else 1,
                timestamp=datetime.utcnow()
            )
            
            # Record individual metrics
            await self._record_metric(
                name="database_query_response_time",
                value=query_time_ms,
                metric_type=MetricType.TIMING,
                tags={"component": "postgresql"},
                description="Database query response time"
            )
            
            await self._record_metric(
                name="database_active_connections",
                value=pool_status.get("checked_out", 0),
                metric_type=MetricType.GAUGE,
                tags={"component": "postgresql"},
                description="Active database connections"
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
            return DatabaseMetrics(0, 0, 0, 0, 1, datetime.utcnow())
    
    async def collect_cache_metrics(self) -> CacheMetrics:
        """Collect Redis cache performance metrics"""
        try:
            # Lazy import to avoid circular dependency
            from app.services.redis_service import redis_service
            
            # Get Redis info and metrics
            redis_info = await redis_service.get_info()
            cache_metrics = await redis_service.get_metrics()
            
            # Calculate derived metrics
            hit_rate = cache_metrics.hit_rate
            miss_rate = 1.0 - hit_rate
            
            metrics = CacheMetrics(
                hit_rate=hit_rate,
                miss_rate=miss_rate,
                avg_response_time_ms=cache_metrics.avg_response_time * 1000,
                memory_usage_mb=self._parse_memory_usage(redis_info.get("used_memory", "0")),
                connected_clients=redis_info.get("connected_clients", 0),
                operations_per_second=self._calculate_ops_per_second(redis_info),
                timestamp=datetime.utcnow()
            )
            
            # Record cache hit rate (critical Phase 0B metric)
            await self._record_metric(
                name="cache_hit_rate",
                value=hit_rate,
                metric_type=MetricType.GAUGE,
                tags={"component": "redis", "target": "0.80"},
                description="Redis cache hit rate percentage"
            )
            
            # Check against 80% target
            if hit_rate < self.targets["cache_hit_rate"]:
                logger.warning(f"Cache hit rate below target: {hit_rate:.2%} < 80%")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting cache metrics: {e}")
            return CacheMetrics(0, 1, 0, 0, 0, 0, datetime.utcnow())
    
    def _parse_memory_usage(self, memory_str: str) -> float:
        """Parse Redis memory usage string to MB"""
        try:
            if isinstance(memory_str, str):
                if 'M' in memory_str:
                    return float(memory_str.replace('M', ''))
                elif 'K' in memory_str:
                    return float(memory_str.replace('K', '')) / 1024
                else:
                    return float(memory_str) / (1024 * 1024)
            return float(memory_str) / (1024 * 1024)
        except:
            return 0.0
    
    def _calculate_ops_per_second(self, redis_info: Dict[str, Any]) -> float:
        """Calculate Redis operations per second"""
        try:
            total_commands = redis_info.get("total_commands_processed", 0)
            uptime = redis_info.get("uptime_in_seconds", 1)
            return total_commands / max(uptime, 1)
        except:
            return 0.0
    
    async def start_monitoring(self, interval: int = 60) -> None:
        """Start continuous performance monitoring"""
        if self._monitoring:
            logger.warning("Performance monitoring already running")
            return
        
        self._monitoring = True
        logger.info(f"Starting performance monitoring with {interval}s interval")
        
        async def monitoring_loop():
            while self._monitoring:
                try:
                    # Collect all metrics
                    system_metrics = await self.collect_system_metrics()
                    db_metrics = await self.collect_database_metrics()
                    cache_metrics = await self.collect_cache_metrics()
                    
                    # Check performance targets
                    await self._check_all_targets(system_metrics, db_metrics, cache_metrics)
                    
                    await asyncio.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    await asyncio.sleep(interval)
        
        # Start monitoring in background
        asyncio.create_task(monitoring_loop())
    
    async def stop_monitoring(self) -> None:
        """Stop performance monitoring"""
        self._monitoring = False
        logger.info("Performance monitoring stopped")
    
    async def _check_all_targets(
        self, 
        system_metrics: SystemMetrics,
        db_metrics: DatabaseMetrics, 
        cache_metrics: CacheMetrics
    ) -> None:
        """Check all metrics against performance targets"""
        targets_met = {
            "cache_hit_rate": cache_metrics.hit_rate >= self.targets["cache_hit_rate"],
            "redis_response_time": cache_metrics.avg_response_time_ms <= self.targets["redis_response_time"],
            "db_query_time": db_metrics.query_response_time_ms <= self.targets["db_query_time"],
            "system_cpu": system_metrics.cpu_percent <= 80.0,  # 80% CPU threshold
            "system_memory": system_metrics.memory_percent <= 85.0,  # 85% memory threshold
        }
        
        # Log warnings for missed targets
        for target, met in targets_met.items():
            if not met:
                logger.warning(f"Performance target missed: {target}")
        
        # Store target compliance
        compliance_rate = sum(targets_met.values()) / len(targets_met)
        await self._record_metric(
            name="performance_target_compliance",
            value=compliance_rate,
            metric_type=MetricType.GAUGE,
            tags={"total_targets": str(len(targets_met))},
            description="Percentage of performance targets being met"
        )
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        try:
            # Collect current metrics
            system_metrics = await self.collect_system_metrics()
            db_metrics = await self.collect_database_metrics()
            cache_metrics = await self.collect_cache_metrics()
            
            # Calculate target compliance
            targets_status = {
                "cache_hit_rate": {
                    "current": cache_metrics.hit_rate,
                    "target": self.targets["cache_hit_rate"],
                    "status": "✅" if cache_metrics.hit_rate >= self.targets["cache_hit_rate"] else "❌"
                },
                "redis_response_time": {
                    "current": cache_metrics.avg_response_time_ms,
                    "target": self.targets["redis_response_time"],
                    "status": "✅" if cache_metrics.avg_response_time_ms <= self.targets["redis_response_time"] else "❌"
                },
                "db_query_time": {
                    "current": db_metrics.query_response_time_ms,
                    "target": self.targets["db_query_time"],
                    "status": "✅" if db_metrics.query_response_time_ms <= self.targets["db_query_time"] else "❌"
                }
            }
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "system": asdict(system_metrics),
                "database": asdict(db_metrics),
                "cache": asdict(cache_metrics),
                "targets": targets_status,
                "monitoring_active": self._monitoring,
                "metrics_history_size": len(self._metrics_history)
            }
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
    
    async def check_performance_targets(self) -> Dict[str, bool]:
        """Quick check of all performance targets"""
        try:
            cache_metrics = await self.collect_cache_metrics()
            db_metrics = await self.collect_database_metrics()
            
            return {
                "cache_hit_rate_target": cache_metrics.hit_rate >= self.targets["cache_hit_rate"],
                "redis_response_target": cache_metrics.avg_response_time_ms <= self.targets["redis_response_time"],
                "db_query_target": db_metrics.query_response_time_ms <= self.targets["db_query_time"],
                "overall_health": (
                    cache_metrics.hit_rate >= self.targets["cache_hit_rate"] and
                    cache_metrics.avg_response_time_ms <= self.targets["redis_response_time"] and
                    db_metrics.query_response_time_ms <= self.targets["db_query_time"]
                )
            }
            
        except Exception as e:
            logger.error(f"Error checking performance targets: {e}")
            return {"error": True, "overall_health": False}
    
    def monitor_endpoint(self, endpoint_name: str):
        """Decorator for monitoring API endpoint performance"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                async with self.timed_operation(f"endpoint_{endpoint_name}"):
                    return await func(*args, **kwargs)
            return wrapper
        return decorator

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Context manager for easy performance tracking
@asynccontextmanager
async def monitor_performance(operation_name: str, tags: Dict[str, str] = None):
    """Context manager for monitoring operation performance"""
    async with performance_monitor.timed_operation(operation_name, tags or {}):
        yield