# backend/app/services/background_analytics.py - Background Processing for Analytics

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from contextlib import asynccontextmanager

from app.services.analytics_service import analytics_cache_service
from app.services.unified_database_service import unified_db_service
from app.models.analytics import AnalyticsType

logger = logging.getLogger(__name__)

class BackgroundAnalyticsProcessor:
    """
    Background processor that automatically analyzes new content
    and maintains analytics caches without blocking user requests.
    """
    
    def __init__(self):
        self.is_running = False
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.worker_tasks: List[asyncio.Task] = []
        self.scheduled_tasks: List[asyncio.Task] = []
        
    async def start(self):
        """Start background processing workers"""
        if self.is_running:
            return
            
        self.is_running = True
        logger.info("Starting background analytics processor")
        
        # Preload AI models for optimal performance
        try:
            from app.services.sentiment_service import sentiment_service
            await sentiment_service.preload_models()
        except Exception as e:
            logger.warning(f"Model preloading failed, will load on demand: {e}")
        
        # Start worker tasks for processing queue
        for i in range(2):  # 2 concurrent workers
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.worker_tasks.append(worker)
        
        # Start scheduled maintenance tasks
        maintenance = asyncio.create_task(self._scheduled_maintenance())
        self.scheduled_tasks.append(maintenance)
        
        logger.info("Background analytics processor started")
    
    async def stop(self):
        """Stop background processing"""
        if not self.is_running:
            return
            
        self.is_running = False
        logger.info("Stopping background analytics processor")
        
        # Cancel all tasks
        for task in self.worker_tasks + self.scheduled_tasks:
            task.cancel()
            
        # Wait for tasks to complete
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        if self.scheduled_tasks:
            await asyncio.gather(*self.scheduled_tasks, return_exceptions=True)
            
        logger.info("Background analytics processor stopped")
    
    async def queue_entry_analysis(self, entry_id: str, priority: int = 5):
        """Queue an entry for background analysis"""
        await self.task_queue.put({
            'type': 'analyze_entry',
            'entry_id': entry_id,
            'priority': priority,
            'queued_at': datetime.now()
        })
        logger.debug(f"Queued entry {entry_id} for analysis")
    
    async def queue_session_analysis(self, session_id: str, priority: int = 5):
        """Queue a session for background analysis"""
        await self.task_queue.put({
            'type': 'analyze_session',
            'session_id': session_id,
            'priority': priority,
            'queued_at': datetime.now()
        })
        logger.debug(f"Queued session {session_id} for analysis")
    
    async def queue_cache_refresh(self, analytics_type: AnalyticsType, priority: int = 3):
        """Queue a cache refresh operation"""
        await self.task_queue.put({
            'type': 'refresh_cache',
            'analytics_type': analytics_type,
            'priority': priority,
            'queued_at': datetime.now()
        })
        logger.debug(f"Queued cache refresh for {analytics_type.value}")
    
    async def _worker(self, worker_name: str):
        """Background worker that processes queued tasks"""
        logger.info(f"Starting background worker: {worker_name}")
        
        while self.is_running:
            try:
                # Wait for task with timeout
                task = await asyncio.wait_for(
                    self.task_queue.get(), 
                    timeout=5.0
                )
                
                await self._process_task(task, worker_name)
                
            except asyncio.TimeoutError:
                # No tasks in queue, continue
                continue
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_name} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(1)  # Brief pause on error
        
        logger.info(f"Worker {worker_name} stopped")
    
    async def _process_task(self, task: dict, worker_name: str):
        """Process a single background task"""
        try:
            task_type = task['type']
            start_time = datetime.now()
            
            if task_type == 'analyze_entry':
                await analytics_cache_service.analyze_entry_background(task['entry_id'])
                
            elif task_type == 'analyze_session':
                await analytics_cache_service.analyze_session_background(task['session_id'])
                
            elif task_type == 'refresh_cache':
                await analytics_cache_service._refresh_analytics_background(
                    task['analytics_type']
                )
            else:
                logger.warning(f"Unknown task type: {task_type}")
                return
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.debug(f"{worker_name} completed {task_type} in {duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Error processing task {task.get('type')}: {e}")
    
    async def _scheduled_maintenance(self):
        """Scheduled maintenance tasks for cache management"""
        logger.info("Starting scheduled maintenance")
        
        while self.is_running:
            try:
                # Run maintenance every hour
                await asyncio.sleep(3600)
                
                if not self.is_running:
                    break
                
                logger.info("Running scheduled cache maintenance")
                
                # Refresh important caches periodically
                important_types = [
                    AnalyticsType.MOOD_TRENDS,
                    AnalyticsType.SENTIMENT_ANALYSIS,
                    AnalyticsType.ENTRY_STATS,
                    AnalyticsType.CHAT_STATS
                ]
                
                for analytics_type in important_types:
                    await self.queue_cache_refresh(analytics_type, priority=2)
                    await asyncio.sleep(1)  # Stagger the requests
                
                # Clean up old analytics data (implementation specific)
                await self._cleanup_old_analytics()
                
                logger.info("Scheduled maintenance completed")
                
            except asyncio.CancelledError:
                logger.info("Scheduled maintenance cancelled")
                break
            except Exception as e:
                logger.error(f"Scheduled maintenance error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _cleanup_old_analytics(self):
        """Clean up old analytics data to manage storage"""
        try:
            # Remove analytics older than 90 days for individual entries
            cutoff_date = datetime.now() - timedelta(days=90)
            logger.info(f"Cleaning up analytics older than {cutoff_date}")
            
            # Implementation would depend on your database structure
            # This is a placeholder for the cleanup logic
            
        except Exception as e:
            logger.error(f"Error cleaning up old analytics: {e}")
    
    async def get_queue_status(self) -> dict:
        """Get current status of the background processing queue"""
        return {
            'is_running': self.is_running,
            'queue_size': self.task_queue.qsize(),
            'active_workers': len([t for t in self.worker_tasks if not t.done()]),
            'scheduled_tasks': len([t for t in self.scheduled_tasks if not t.done()])
        }


# Global instance
background_processor = BackgroundAnalyticsProcessor()

# Lifespan manager for FastAPI
@asynccontextmanager
async def analytics_lifespan(app):
    """FastAPI lifespan manager for background analytics"""
    # Startup
    await background_processor.start()
    logger.info("Analytics background processing started")
    
    yield
    
    # Shutdown
    await background_processor.stop()
    logger.info("Analytics background processing stopped")


# Hook functions to be called from entry/session APIs
async def on_entry_created(entry_id: str):
    """Call this when a new entry is created"""
    await background_processor.queue_entry_analysis(entry_id, priority=4)

async def on_entry_updated(entry_id: str):
    """Call this when an entry is updated"""
    await background_processor.queue_entry_analysis(entry_id, priority=3)

async def on_session_updated(session_id: str):
    """Call this when a session is updated (new messages)"""
    await background_processor.queue_session_analysis(session_id, priority=4)

async def on_session_completed(session_id: str):
    """Call this when a session is marked as completed"""
    await background_processor.queue_session_analysis(session_id, priority=2)
