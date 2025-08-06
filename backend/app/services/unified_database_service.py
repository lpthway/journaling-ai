# backend/app/services/unified_database_service.py
"""
Unified Database Service with Redis Caching Integration
Replaces multiple database services with single, consistent interface
"""

import logging
import uuid
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from app.core.database import database
from app.core.exceptions import DatabaseException, NotFoundException
from app.core.service_interfaces import service_registry
from app.core.cache_patterns import CacheKeyBuilder, CacheDomain, CacheTTL, CachePatterns
from app.services.redis_service import redis_service, redis_session_service, redis_analytics_service
from app.repositories.base_cached_repository import RepositoryFactory
from app.models.enhanced_models import Entry, ChatSession, ChatMessage, Topic, User

logger = logging.getLogger(__name__)

# Default user UUID for single-user mode
DEFAULT_USER_UUID = uuid.UUID("00000000-0000-4000-8000-000000000001")

class UnifiedDatabaseService:
    """
    Unified database service combining PostgreSQL and Redis
    Provides single interface for all data operations with automatic caching
    """
    
    def __init__(self):
        self._initialized = False
    
    def _ensure_uuid(self, user_id: Union[str, uuid.UUID]) -> uuid.UUID:
        """Convert user_id string to UUID, using default for 'default_user'"""
        if isinstance(user_id, uuid.UUID):
            return user_id
        elif user_id == "default_user":
            return DEFAULT_USER_UUID
        else:
            try:
                return uuid.UUID(user_id)
            except ValueError:
                logger.warning(f"Invalid user_id format: {user_id}, using default")
                return DEFAULT_USER_UUID
    
    async def initialize(self) -> None:
        """Initialize database connections and caching"""
        if self._initialized:
            return
            
        try:
            # Initialize PostgreSQL database
            await database.initialize()
            
            # Initialize Redis caching
            await redis_service.initialize()
            
            # Register Redis as the caching strategy
            service_registry.set_cache_strategy(redis_service)
            
            self._initialized = True
            logger.info("✅ Unified Database Service initialized with Redis caching")
            
        except Exception as e:
            logger.error(f"❌ Unified Database Service initialization failed: {e}")
            raise DatabaseException(
                "Service initialization failed",
                context={"error": str(e)}
            )
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with automatic cleanup"""
        if not self._initialized:
            await self.initialize()
            
        async with database.get_session() as session:
            yield session
    
    # === ENTRY OPERATIONS WITH CACHING ===
    
    async def create_entry(
        self,
        title: str,
        content: str,
        user_id: str = "default_user",
        topic_id: Optional[str] = None,
        mood: Optional[str] = None,
        sentiment_score: Optional[float] = None,
        tags: Optional[List[str]] = None
    ) -> Entry:
        """Create entry with automatic caching and analytics"""
        async with self.get_session() as session:
            try:
                entry_repo = RepositoryFactory.create_entry_repository(session)
                
                # Convert user_id to proper UUID
                user_uuid = self._ensure_uuid(user_id)
                
                entry_data = {
                    "title": title,
                    "content": content,
                    "user_id": user_uuid,
                    "topic_id": topic_id,
                    "mood": mood,
                    "sentiment_score": sentiment_score,
                    "tags": tags or [],
                    "word_count": len(content.split()),
                    "reading_time_minutes": max(1, len(content.split()) // 200)
                }
                
                # Create entry with caching
                entry = await entry_repo.create(entry_data, invalidate_cache=True)
                await session.commit()
                
                # Update analytics counters
                await redis_analytics_service.increment_usage_counter("daily_entries")
                await redis_analytics_service.increment_usage_counter("total_entries")
                
                # Invalidate related analytics caches
                await redis_service.invalidate_pattern(f"analytics:*:{user_uuid}:*")
                
                logger.info(f"Created entry {entry.id} with caching")
                return entry
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error creating entry: {e}")
                raise DatabaseException(f"Failed to create entry", context={"error": str(e)})
    
    async def get_entry(self, entry_id: str, use_cache: bool = True) -> Optional[Entry]:
        """Get entry by ID with caching"""
        async with self.get_session() as session:
            entry_repo = RepositoryFactory.create_entry_repository(session)
            return await entry_repo.get_by_id(entry_id, use_cache=use_cache)
    
    async def get_entries(
        self,
        user_id: str = "default_user",
        skip: int = 0,
        limit: int = 100,
        topic_id: Optional[str] = None,
        mood_filter: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        use_cache: bool = True
    ) -> List[Entry]:
        """Get entries with advanced filtering and caching"""
        async with self.get_session() as session:
            entry_repo = RepositoryFactory.create_entry_repository(session)
            
            # Convert user_id to proper UUID
            user_uuid = self._ensure_uuid(user_id)
            
            filters = {"user_id": user_uuid}
            if topic_id:
                filters["topic_id"] = topic_id
            if mood_filter:
                filters["mood"] = mood_filter
            if date_from:
                filters["created_at__gte"] = date_from
            if date_to:
                filters["created_at__lte"] = date_to
            
            # Add pagination to filters for cache key generation
            filters["_skip"] = skip
            filters["_limit"] = limit
            
            return await entry_repo.search(filters, use_cache=use_cache)
    
    async def update_entry(
        self,
        entry_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        mood: Optional[str] = None,
        sentiment_score: Optional[float] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[Entry]:
        """Update entry with cache invalidation"""
        async with self.get_session() as session:
            try:
                entry_repo = RepositoryFactory.create_entry_repository(session)
                
                update_data = {}
                if title is not None:
                    update_data["title"] = title
                if content is not None:
                    update_data["content"] = content
                    update_data["word_count"] = len(content.split())
                    update_data["reading_time_minutes"] = max(1, len(content.split()) // 200)
                if mood is not None:
                    update_data["mood"] = mood
                if sentiment_score is not None:
                    update_data["sentiment_score"] = sentiment_score
                if tags is not None:
                    update_data["tags"] = tags
                
                entry = await entry_repo.update(entry_id, update_data, invalidate_cache=True)
                if entry:
                    await session.commit()
                    
                    # Invalidate analytics caches
                    await redis_service.invalidate_pattern(f"analytics:*:{entry.user_id}:*")
                
                return entry
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error updating entry: {e}")
                raise DatabaseException(f"Failed to update entry", context={"error": str(e)})
    
    async def delete_entry(self, entry_id: str) -> bool:
        """Delete entry with cache invalidation"""
        async with self.get_session() as session:
            try:
                entry_repo = RepositoryFactory.create_entry_repository(session)
                
                # Get entry first to get user_id for cache invalidation
                entry = await entry_repo.get_by_id(entry_id, use_cache=False)
                if not entry:
                    return False
                
                success = await entry_repo.delete(entry_id, invalidate_cache=True)
                if success:
                    await session.commit()
                    
                    # Invalidate analytics caches
                    await redis_service.invalidate_pattern(f"analytics:*:{entry.user_id}:*")
                
                return success
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error deleting entry: {e}")
                raise DatabaseException(f"Failed to delete entry", context={"error": str(e)})
    
    # === SESSION OPERATIONS WITH CACHING ===
    
    async def create_session(
        self,
        session_type: str,
        title: str,
        user_id: str = "default_user",
        description: Optional[str] = None,
        initial_message: str = "Hello! How can I help you today?"
    ) -> ChatSession:
        """Create chat session with Redis caching"""
        async with self.get_session() as session:
            try:
                session_repo = RepositoryFactory.create_session_repository(session)
                
                # Create session in database
                chat_session = await session_repo.create_with_initial_message(
                    user_id=user_id,
                    session_type=session_type,
                    title=title,
                    initial_message=initial_message,
                    description=description
                )
                await session.commit()
                
                # Cache session data in Redis
                session_data = {
                    "id": str(chat_session.id),
                    "title": chat_session.title,
                    "session_type": chat_session.session_type,
                    "user_id": chat_session.user_id,
                    "status": chat_session.status,
                    "created_at": chat_session.created_at.isoformat(),
                    "last_activity": chat_session.last_activity.isoformat() if chat_session.last_activity else None,
                    "message_count": chat_session.message_count or 0
                }
                
                await redis_session_service.store_session(str(chat_session.id), session_data)
                await redis_session_service.add_user_session(user_id, str(chat_session.id))
                
                # Update analytics
                await redis_analytics_service.increment_usage_counter("daily_sessions")
                await redis_analytics_service.increment_usage_counter("total_sessions")
                
                logger.info(f"Created session {chat_session.id} with Redis caching")
                return chat_session
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error creating session: {e}")
                raise DatabaseException(f"Failed to create session", context={"error": str(e)})
    
    async def get_chat_session(self, session_id: str, use_cache: bool = True) -> Optional[ChatSession]:
        """Get chat session with Redis caching"""
        # Try Redis cache first
        if use_cache:
            cached_data = await redis_session_service.get_session(session_id)
            if cached_data:
                logger.debug(f"Session {session_id} retrieved from Redis cache")
                # Convert cached data back to ChatSession object
                # Note: This is simplified - in production, you'd want proper deserialization
                return cached_data
        
        # Fall back to database
        async with self.get_session() as session:
            session_repo = RepositoryFactory.create_session_repository(session)
            chat_session = await session_repo.get_by_id(session_id, use_cache=False)
            
            # Cache in Redis for future requests
            if chat_session and use_cache:
                session_data = {
                    "id": str(chat_session.id),
                    "title": chat_session.title,
                    "session_type": chat_session.session_type,
                    "user_id": chat_session.user_id,
                    "status": chat_session.status,
                    "created_at": chat_session.created_at.isoformat(),
                    "last_activity": chat_session.last_activity.isoformat() if chat_session.last_activity else None,
                    "message_count": chat_session.message_count or 0
                }
                await redis_session_service.store_session(session_id, session_data)
            
            return chat_session
    
    async def add_message(
        self,
        session_id: str,
        content: str,
        role: str = "user",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """Add message to session with caching updates"""
        async with self.get_session() as session:
            try:
                session_repo = RepositoryFactory.create_session_repository(session)
                
                message = await session_repo.add_message(
                    session_id=session_id,
                    content=content,
                    role=role,
                    metadata=metadata or {}
                )
                await session.commit()
                
                # Update session cache with new message count and activity
                await redis_session_service.update_session(session_id, {
                    "last_activity": datetime.utcnow().isoformat(),
                    "message_count": message.session.message_count
                })
                
                # Update analytics
                await redis_analytics_service.increment_usage_counter("daily_messages")
                await redis_analytics_service.increment_usage_counter("total_messages")
                
                return message
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error adding message: {e}")
                raise DatabaseException(f"Failed to add message", context={"error": str(e)})
    
    # === ANALYTICS WITH REDIS CACHING ===
    
    async def get_mood_statistics(
        self,
        user_id: str = "default_user",
        days: int = 30,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Get mood statistics with Redis caching"""
        # Check cache first
        if use_cache:
            cached_stats = await redis_analytics_service.get_cached_mood_statistics(user_id, days)
            if cached_stats:
                logger.debug(f"Mood statistics retrieved from cache for user {user_id}")
                return cached_stats
        
        # Calculate from database
        async with self.get_session() as session:
            try:
                entry_repo = RepositoryFactory.create_entry_repository(session)
                stats = await entry_repo.get_mood_analytics(user_id, days)
                
                # Cache results
                if use_cache:
                    await redis_analytics_service.cache_mood_statistics(user_id, days, stats)
                
                return stats
                
            except Exception as e:
                logger.error(f"Error getting mood statistics: {e}")
                raise DatabaseException(f"Failed to get mood statistics", context={"error": str(e)})
    
    async def get_writing_statistics(
        self,
        user_id: str = "default_user",
        days: int = 30,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Get writing statistics with caching"""
        
        # Check cache first using standardized pattern
        cache_key = CachePatterns.analytics_writing_stats(user_id, days)
        if use_cache:
            cached_stats = await redis_service.get(cache_key)
            if cached_stats:
                return cached_stats
        
        # Calculate from database
        async with self.get_session() as session:
            try:
                entry_repo = RepositoryFactory.create_entry_repository(session)
                stats = await entry_repo.get_writing_statistics(user_id, days)
                
                # Cache results using standardized TTL
                if use_cache:
                    await redis_service.set(cache_key, stats, ttl=CacheTTL.MEDIUM_SHORT)  # 15 minutes
                
                return stats
                
            except Exception as e:
                logger.error(f"Error getting writing statistics: {e}")
                raise DatabaseException(f"Failed to get writing statistics", context={"error": str(e)})
    
    # === TOPIC OPERATIONS WITH CACHING ===
    
    async def create_topic(
        self,
        topic_data: Dict[str, Any],
        user_id: str = "default_user"
    ) -> Topic:
        """Create a new topic with caching"""
        async with self.get_session() as session:
            try:
                from app.models.enhanced_models import Topic
                
                # Convert user_id to proper UUID
                user_uuid = self._ensure_uuid(user_id)
                
                topic = Topic(
                    user_id=user_uuid,
                    name=topic_data.get('name', 'Untitled Topic'),
                    description=topic_data.get('description'),
                    color=topic_data.get('color', '#3B82F6'),
                    icon=topic_data.get('icon'),
                    tags=topic_data.get('tags', []),
                    metadata_info=topic_data.get('metadata', {})
                )
                
                session.add(topic)
                await session.flush()
                await session.refresh(topic)
                await session.commit()
                
                # Invalidate topics cache
                await redis_service.invalidate_pattern(f"topics:*:{user_id}:*")
                
                logger.info(f"Created topic {topic.id} with caching")
                return topic
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error creating topic: {e}")
                raise DatabaseException(f"Failed to create topic", context={"error": str(e)})
    
    async def get_topics(
        self,
        user_id: str = "default_user",
        include_entry_count: bool = True,
        use_cache: bool = True
    ) -> List[Topic]:
        """Get all topics for a user with caching"""
        
        # Convert user_id to proper UUID
        user_uuid = self._ensure_uuid(user_id)
        
        if use_cache:
            cache_key = CacheKeyBuilder.build_key(CacheDomain.CONTENT, "topics", {"user": str(user_uuid)})
            cached_topics = await redis_service.get(cache_key)
            if cached_topics:
                return cached_topics
        
        async with self.get_session() as session:
            try:
                from app.models.enhanced_models import Topic
                from sqlalchemy import select, and_
                from sqlalchemy.orm import selectinload
                
                query = select(Topic).where(
                    and_(
                        Topic.user_id == user_uuid,
                        Topic.deleted_at.is_(None)
                    )
                ).order_by(Topic.name)
                
                if include_entry_count:
                    query = query.options(selectinload(Topic.entries))
                
                result = await session.execute(query)
                topics = list(result.scalars().all())
                
                # Cache the results using standardized TTL
                if use_cache:
                    await redis_service.set(cache_key, topics, ttl=CacheTTL.HOURLY)
                
                return topics
                
            except Exception as e:
                logger.error(f"Error getting topics: {e}")
                raise DatabaseException(f"Failed to get topics", context={"error": str(e)})
    
    async def get_topic(self, topic_id: str, use_cache: bool = True) -> Optional[Topic]:
        """Get topic by ID with caching"""
        if use_cache:
            cache_key = CacheKeyBuilder.build_key(CacheDomain.CONTENT, "topic", {"id": topic_id})
            cached_topic = await redis_service.get(cache_key)
            if cached_topic:
                return cached_topic
        
        async with self.get_session() as session:
            try:
                from app.models.enhanced_models import Topic
                from sqlalchemy import select
                
                query = select(Topic).where(Topic.id == topic_id)
                result = await session.execute(query)
                topic = result.scalar_one_or_none()
                
                # Cache the result using standardized TTL
                if topic and use_cache:
                    await redis_service.set(cache_key, topic, ttl=CacheTTL.HOURLY)
                
                return topic
                
            except Exception as e:
                logger.error(f"Error getting topic {topic_id}: {e}")
                return None
    
    async def update_topic(
        self,
        topic_id: str,
        topic_update: Dict[str, Any]
    ) -> Optional[Topic]:
        """Update a topic with cache invalidation"""
        async with self.get_session() as session:
            try:
                from app.models.enhanced_models import Topic
                from sqlalchemy import select
                
                query = select(Topic).where(Topic.id == topic_id)
                result = await session.execute(query)
                topic = result.scalar_one_or_none()
                
                if not topic:
                    return None
                
                # Update topic fields
                for field, value in topic_update.items():
                    if hasattr(topic, field):
                        setattr(topic, field, value)
                
                await session.commit()
                await session.refresh(topic)
                
                # Invalidate caches
                await redis_service.invalidate_pattern(f"topic:{topic_id}")
                await redis_service.invalidate_pattern(f"topics:*:{topic.user_id}:*")
                
                return topic
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error updating topic: {e}")
                raise DatabaseException(f"Failed to update topic", context={"error": str(e)})
    
    async def delete_topic(self, topic_id: str) -> bool:
        """Delete a topic (soft delete) with cache invalidation"""
        async with self.get_session() as session:
            try:
                from app.models.enhanced_models import Topic
                from sqlalchemy import select
                
                query = select(Topic).where(Topic.id == topic_id)
                result = await session.execute(query)
                topic = result.scalar_one_or_none()
                
                if not topic:
                    return False
                
                # Soft delete
                topic.deleted_at = datetime.utcnow()
                await session.commit()
                
                # Invalidate caches
                await redis_service.invalidate_pattern(f"topic:{topic_id}")
                await redis_service.invalidate_pattern(f"topics:*:{topic.user_id}:*")
                
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error deleting topic: {e}")
                return False

    # === HEALTH CHECK AND MONITORING ===
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for PostgreSQL and Redis"""
        health_status = {
            "status": "healthy",
            "components": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # PostgreSQL health check
        try:
            pg_health = await database.health_check()
            health_status["components"]["postgresql"] = {
                "status": "healthy" if pg_health else "unhealthy",
                "details": pg_health
            }
        except Exception as e:
            health_status["components"]["postgresql"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Redis health check
        try:
            await redis_service._health_check()
            redis_info = await redis_service.get_info()
            health_status["components"]["redis"] = {
                "status": "healthy",
                "details": redis_info
            }
        except Exception as e:
            health_status["components"]["redis"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Cache performance metrics
        try:
            cache_metrics = await redis_service.get_metrics()
            health_status["components"]["cache_performance"] = {
                "hit_rate": cache_metrics.hit_rate,
                "avg_response_time": cache_metrics.avg_response_time,
                "total_operations": cache_metrics.hits + cache_metrics.misses,
                "errors": cache_metrics.errors
            }
        except Exception as e:
            logger.warning(f"Could not get cache metrics: {e}")
        
        return health_status
    
    async def cleanup_expired_data(self) -> Dict[str, int]:
        """Clean up expired data and optimize performance"""
        cleanup_results = {
            "expired_sessions": 0,
            "cache_keys_cleaned": 0
        }
        
        try:
            # Clean up expired session references in Redis
            cleanup_results["expired_sessions"] = await redis_session_service.cleanup_expired_sessions()
            
            # Additional cleanup operations can be added here
            
            logger.info(f"Cleanup completed: {cleanup_results}")
            return cleanup_results
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return cleanup_results

# Global unified service instance
unified_db_service = UnifiedDatabaseService()