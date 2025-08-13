# backend/app/repositories/enhanced_session_repository.py
"""
Enhanced Session Repository with Redis Integration
Real-time session management with Redis-backed state caching
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_, desc, text, update
from sqlalchemy.orm import selectinload
from contextlib import asynccontextmanager

from app.repositories.base_cached_repository import EnhancedBaseRepository
from app.models.enhanced_models import ChatSession, ChatMessage
from app.auth.models import AuthUser
from app.decorators.cache_decorators import cached, cache_invalidate, redis_session_cache, timed_operation, CachePatterns
from app.core.exceptions import RepositoryException, NotFoundException
from app.core.performance_monitor import performance_monitor
from app.services.redis_service import redis_session_service

logger = logging.getLogger(__name__)

class EnhancedSessionRepository(EnhancedBaseRepository[ChatSession]):
    """
    Specialized session repository with Redis integration
    
    Features:
    - Real-time session state caching in Redis
    - Message threading with conversation context
    - Performance-optimized conversation retrieval
    - Automatic session cleanup and maintenance
    """
    
    def __init__(self, session):
        super().__init__(session, ChatSession, "session")
        self.session_cache_ttl = 7200    # 2 hours for active sessions
        self.message_cache_ttl = 3600    # 1 hour for message context
        self.analytics_cache_ttl = 1800  # 30 minutes for session analytics
    
    @redis_session_cache(session_ttl=7200, auto_refresh=True, track_activity=True)
    async def get_by_id(self, session_id: str, use_cache: bool = True) -> Optional[ChatSession]:
        """Get session by ID with Redis caching and activity tracking"""
        try:
            query = select(ChatSession).options(
                selectinload(ChatSession.user),
                selectinload(ChatSession.messages).selectinload(ChatMessage.session)
            ).where(
                and_(
                    ChatSession.id == session_id,
                    ChatSession.deleted_at.is_(None)
                )
            )
            
            result = await self.session.execute(query)
            chat_session = result.scalar_one_or_none()
            
            if chat_session and use_cache:
                # Update activity timestamp in Redis
                await self._update_session_activity(session_id)
            
            return chat_session
            
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            raise RepositoryException(f"Failed to get session", context={"id": session_id, "error": str(e)})
    
    @CachePatterns.INVALIDATE_SESSIONS
    @timed_operation("create_session_with_message", track_errors=True)
    async def create_with_initial_message(
        self,
        user_id: str,
        session_type: str,
        title: str,
        initial_message: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ChatSession:
        """Create session with initial AI greeting and Redis caching"""
        try:
            # Create session
            session_data = {
                'user_id': user_id,
                'session_type': session_type,
                'title': title,
                'description': description,
                'status': 'active',
                'last_activity': datetime.utcnow(),
                'session_metadata': metadata or {},
                'message_count': 1,  # Will have initial message
                **kwargs
            }
            
            chat_session = ChatSession(**session_data)
            self.session.add(chat_session)
            await self.session.flush()
            await self.session.refresh(chat_session)
            
            # Add initial message
            initial_msg = ChatMessage(
                session_id=chat_session.id,
                content=initial_message,
                role='assistant',
                word_count=len(initial_message.split()),
                character_count=len(initial_message),
                timestamp=datetime.utcnow()
            )
            
            self.session.add(initial_msg)
            await self.session.flush()
            
            # Cache session in Redis
            await self._cache_session_state(chat_session)
            
            # Track user session
            await redis_session_service.add_user_session(user_id, str(chat_session.id))
            
            logger.info(f"Created session {chat_session.id} with initial message")
            return chat_session
            
        except Exception as e:
            logger.error(f"Error creating session with initial message: {e}")
            raise RepositoryException(f"Session creation failed", context={"title": title, "error": str(e)})
    
    @redis_session_cache(session_ttl=7200, track_activity=True)
    @timed_operation("add_message", track_errors=True)
    async def add_message(
        self,
        session_id: str,
        content: str,
        role: str = "user",
        metadata: Optional[Dict[str, Any]] = None,
        response_time_ms: Optional[int] = None,
        **kwargs
    ) -> ChatMessage:
        """Add message to session with real-time caching updates"""
        try:
            # Create message
            message_data = {
                'session_id': session_id,
                'content': content,
                'role': role,
                'word_count': len(content.split()),
                'character_count': len(content),
                'timestamp': datetime.utcnow(),
                'message_metadata': metadata or {},
                'response_time_ms': response_time_ms,
                **kwargs
            }
            
            message = ChatMessage(**message_data)
            self.session.add(message)
            await self.session.flush()
            
            # Update session activity and message count
            session_update_query = update(ChatSession).where(
                ChatSession.id == session_id
            ).values(
                last_activity=datetime.utcnow(),
                message_count=ChatSession.message_count + 1,
                updated_at=datetime.utcnow()
            )
            
            await self.session.execute(session_update_query)
            await self.session.flush()
            
            # Update Redis session cache
            await self._update_session_cache_after_message(session_id, message)
            
            logger.debug(f"Added {role} message to session {session_id}: {len(content)} chars")
            return message
            
        except Exception as e:
            logger.error(f"Error adding message to session: {e}")
            raise RepositoryException(f"Message creation failed", context={"session_id": session_id, "error": str(e)})
    
    @cached(ttl=300, key_prefix="session_messages", monitor_performance=True)
    async def get_messages(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0,
        include_metadata: bool = False
    ) -> List[ChatMessage]:
        """Get messages for a session with caching"""
        try:
            query_options = []
            if include_metadata:
                query_options.append(selectinload(ChatMessage.session))
            
            query = select(ChatMessage)
            if query_options:
                query = query.options(*query_options)
            
            query = query.where(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.timestamp.asc()).offset(offset).limit(limit)
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Error getting messages for session {session_id}: {e}")
            return []
    
    @cached(ttl=180, key_prefix="recent_messages", monitor_performance=True)
    async def get_recent_messages(
        self,
        session_id: str,
        count: int = 10,
        for_context: bool = True
    ) -> List[ChatMessage]:
        """Get recent messages for AI context generation"""
        try:
            query = select(ChatMessage).where(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.timestamp.desc()).limit(count)
            
            result = await self.session.execute(query)
            messages = list(result.scalars().all())
            
            # Return in chronological order for context
            if for_context:
                messages.reverse()
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting recent messages: {e}")
            return []
    
    @cached(ttl=600, key_prefix="user_sessions", monitor_performance=True)
    async def get_sessions_by_user(
        self,
        user_id: str,
        status: Optional[str] = None,
        session_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        include_recent_activity: bool = True
    ) -> List[ChatSession]:
        """Get sessions for a user with filtering and caching"""
        try:
            conditions = [
                ChatSession.user_id == user_id,
                ChatSession.deleted_at.is_(None)
            ]
            
            if status:
                conditions.append(ChatSession.status == status)
            if session_type:
                conditions.append(ChatSession.session_type == session_type)
            
            query = select(ChatSession)
            if include_recent_activity:
                query = query.options(selectinload(ChatSession.messages))
            
            query = query.where(and_(*conditions)).order_by(
                ChatSession.last_activity.desc()
            ).offset(offset).limit(limit)
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Error getting sessions for user {user_id}: {e}")
            return []
    
    @cached(ttl=1800, key_prefix="session_analytics", monitor_performance=True)
    async def get_session_analytics(
        self,
        user_id: str,
        days: int = 30,
        include_patterns: bool = True
    ) -> Dict[str, Any]:
        """Comprehensive session analytics with caching"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            base_conditions = [
                ChatSession.user_id == user_id,
                ChatSession.created_at >= start_date,
                ChatSession.deleted_at.is_(None)
            ]
            
            async with performance_monitor.timed_operation("session_analytics", {"days": days, "user_id": user_id}):
                # Session type distribution
                type_query = select(
                    ChatSession.session_type,
                    func.count(ChatSession.id).label('count'),
                    func.avg(ChatSession.message_count).label('avg_messages'),
                    func.sum(ChatSession.total_duration_minutes).label('total_duration'),
                    func.avg(ChatSession.total_duration_minutes).label('avg_duration')
                ).where(and_(*base_conditions)).group_by(ChatSession.session_type)
                
                type_result = await self.session.execute(type_query)
                session_types = {}
                
                for row in type_result.all():
                    session_types[row.session_type] = {
                        'count': row.count,
                        'avg_messages': float(row.avg_messages) if row.avg_messages else 0,
                        'total_duration_minutes': row.total_duration or 0,
                        'avg_duration_minutes': float(row.avg_duration) if row.avg_duration else 0
                    }
                
                # Daily patterns if requested
                daily_patterns = []
                if include_patterns:
                    daily_query = select(
                        func.date(ChatSession.created_at).label('date'),
                        func.count(ChatSession.id).label('sessions_created'),
                        func.sum(ChatSession.message_count).label('total_messages'),
                        func.avg(ChatSession.message_count).label('avg_messages_per_session')
                    ).where(and_(*base_conditions)).group_by(
                        func.date(ChatSession.created_at)
                    ).order_by('date')
                    
                    daily_result = await self.session.execute(daily_query)
                    for row in daily_result.all():
                        daily_patterns.append({
                            'date': row.date.isoformat(),
                            'sessions_created': row.sessions_created,
                            'total_messages': row.total_messages or 0,
                            'avg_messages_per_session': float(row.avg_messages_per_session) if row.avg_messages_per_session else 0
                        })
                
                # Overall statistics
                stats_query = select(
                    func.count(ChatSession.id).label('total_sessions'),
                    func.sum(ChatSession.message_count).label('total_messages'),
                    func.avg(ChatSession.message_count).label('avg_messages_per_session'),
                    func.sum(ChatSession.total_duration_minutes).label('total_time_minutes'),
                    func.count(func.distinct(func.date(ChatSession.created_at))).label('active_days')
                ).where(and_(*base_conditions))
                
                stats_result = await self.session.execute(stats_query)
                stats_row = stats_result.first()
            
            analytics_data = {
                'period_days': days,
                'session_types': session_types,
                'daily_patterns': daily_patterns,
                'statistics': {
                    'total_sessions': stats_row.total_sessions or 0,
                    'total_messages': stats_row.total_messages or 0,
                    'avg_messages_per_session': float(stats_row.avg_messages_per_session) if stats_row.avg_messages_per_session else 0,
                    'total_time_minutes': stats_row.total_time_minutes or 0,
                    'active_days': stats_row.active_days or 0,
                    'avg_sessions_per_active_day': (stats_row.total_sessions / stats_row.active_days) if stats_row.active_days else 0
                },
                'engagement_metrics': {
                    'avg_session_length': (stats_row.total_time_minutes / stats_row.total_sessions) if stats_row.total_sessions else 0,
                    'message_frequency': (stats_row.total_messages / stats_row.total_time_minutes) if stats_row.total_time_minutes else 0,
                    'consistency_percentage': (stats_row.active_days / days * 100) if stats_row.active_days else 0
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Generated session analytics for user {user_id}: {stats_row.total_sessions} sessions over {days} days")
            return analytics_data
            
        except Exception as e:
            logger.error(f"Error generating session analytics: {e}")
            raise RepositoryException(f"Session analytics failed", context={"user_id": user_id, "days": days, "error": str(e)})
    
    @CachePatterns.INVALIDATE_SESSIONS
    async def update_session_status(
        self,
        session_id: str,
        status: str,
        update_activity: bool = True
    ) -> Optional[ChatSession]:
        """Update session status with cache invalidation"""
        try:
            session = await self.get_by_id(session_id, use_cache=False)
            if not session:
                return None
            
            session.status = status
            session.updated_at = datetime.utcnow()
            
            if update_activity:
                session.last_activity = datetime.utcnow()
            
            await self.session.flush()
            await self.session.refresh(session)
            
            # Update Redis cache
            await self._cache_session_state(session)
            
            logger.info(f"Updated session {session_id} status to {status}")
            return session
            
        except Exception as e:
            logger.error(f"Error updating session status: {e}")
            raise RepositoryException(f"Session status update failed", context={"session_id": session_id, "error": str(e)})
    
    @timed_operation("close_session", track_errors=True)
    async def close_session(self, session_id: str, summary: Optional[str] = None) -> bool:
        """Close session with optional summary and cleanup"""
        try:
            session = await self.get_by_id(session_id, use_cache=False)
            if not session:
                return False
            
            # Update session
            session.status = 'closed'
            session.updated_at = datetime.utcnow()
            
            if summary:
                session.session_metadata = session.session_metadata or {}
                session.session_metadata['closing_summary'] = summary
            
            await self.session.flush()
            
            # Remove from active Redis cache but keep for analytics
            await self._archive_session_in_redis(session_id)
            
            logger.info(f"Closed session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error closing session: {e}")
            return False
    
    async def search_sessions(
        self,
        user_id: str,
        query: str,
        session_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[ChatSession]:
        """Search sessions by title, description, or message content"""
        try:
            conditions = [
                ChatSession.user_id == user_id,
                ChatSession.deleted_at.is_(None)
            ]
            
            # Text search conditions
            if query.strip():
                search_conditions = or_(
                    ChatSession.title.ilike(f'%{query}%'),
                    ChatSession.description.ilike(f'%{query}%')
                )
                conditions.append(search_conditions)
            
            if session_type:
                conditions.append(ChatSession.session_type == session_type)
            
            search_query = select(ChatSession).options(
                selectinload(ChatSession.messages)
            ).where(and_(*conditions)).order_by(
                ChatSession.last_activity.desc()
            ).offset(offset).limit(limit)
            
            result = await self.session.execute(search_query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Error searching sessions: {e}")
            return []
    
    async def get_active_sessions(
        self,
        user_id: str,
        activity_threshold_hours: int = 24,
        limit: int = 10
    ) -> List[ChatSession]:
        """Get recently active sessions"""
        try:
            threshold_time = datetime.utcnow() - timedelta(hours=activity_threshold_hours)
            
            query = select(ChatSession).where(
                and_(
                    ChatSession.user_id == user_id,
                    ChatSession.status == 'active',
                    ChatSession.last_activity >= threshold_time,
                    ChatSession.deleted_at.is_(None)
                )
            ).order_by(ChatSession.last_activity.desc()).limit(limit)
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return []
    
    @timed_operation("cleanup_sessions", track_errors=True)
    async def cleanup_expired_sessions(
        self,
        inactive_days: int = 30,
        batch_size: int = 100
    ) -> Dict[str, int]:
        """Clean up expired and inactive sessions"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=inactive_days)
            
            # Find sessions to clean up
            cleanup_query = select(ChatSession.id).where(
                and_(
                    ChatSession.last_activity < cutoff_date,
                    ChatSession.status.in_(['inactive', 'closed']),
                    ChatSession.deleted_at.is_(None)
                )
            ).limit(batch_size)
            
            result = await self.session.execute(cleanup_query)
            session_ids = [row.id for row in result.all()]
            
            cleaned_sessions = 0
            cleaned_messages = 0
            
            for session_id in session_ids:
                # Count messages before deletion
                message_count_query = select(func.count(ChatMessage.id)).where(
                    ChatMessage.session_id == session_id
                )
                message_count_result = await self.session.execute(message_count_query)
                message_count = message_count_result.scalar() or 0
                
                # Soft delete session
                session_update = update(ChatSession).where(
                    ChatSession.id == session_id
                ).values(deleted_at=datetime.utcnow())
                
                await self.session.execute(session_update)
                
                # Archive in Redis before cleanup
                await self._archive_session_in_redis(str(session_id))
                
                cleaned_sessions += 1
                cleaned_messages += message_count
            
            if cleaned_sessions > 0:
                await self.session.commit()
            
            logger.info(f"Cleaned up {cleaned_sessions} sessions and {cleaned_messages} messages")
            
            return {
                'cleaned_sessions': cleaned_sessions,
                'cleaned_messages': cleaned_messages,
                'batch_size': batch_size
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
            return {'cleaned_sessions': 0, 'cleaned_messages': 0, 'error': str(e)}
    
    # Private helper methods for Redis integration
    
    async def _cache_session_state(self, session: ChatSession) -> None:
        """Cache session state in Redis"""
        try:
            session_data = {
                'id': str(session.id),
                'title': session.title,
                'session_type': session.session_type,
                'user_id': str(session.user_id),
                'status': session.status,
                'created_at': session.created_at.isoformat(),
                'last_activity': session.last_activity.isoformat() if session.last_activity else None,
                'message_count': session.message_count or 0,
                'total_duration_minutes': session.total_duration_minutes or 0,
                'cached_at': datetime.utcnow().isoformat()
            }
            
            await redis_session_service.store_session(str(session.id), session_data)
            
        except Exception as e:
            logger.warning(f"Failed to cache session state: {e}")
    
    async def _update_session_activity(self, session_id: str) -> None:
        """Update session activity timestamp in Redis"""
        try:
            activity_data = {
                'last_activity': datetime.utcnow().isoformat(),
                'activity_updated_at': datetime.utcnow().isoformat()
            }
            
            await redis_session_service.update_session(session_id, activity_data)
            
        except Exception as e:
            logger.warning(f"Failed to update session activity: {e}")
    
    async def _update_session_cache_after_message(self, session_id: str, message: ChatMessage) -> None:
        """Update session cache after new message"""
        try:
            # Get current session data from Redis
            session_data = await redis_session_service.get_session(session_id)
            
            if session_data:
                # Update message count and activity
                session_data['message_count'] = (session_data.get('message_count', 0) + 1)
                session_data['last_activity'] = datetime.utcnow().isoformat()
                session_data['last_message_role'] = message.role
                session_data['last_message_timestamp'] = message.timestamp.isoformat()
                
                await redis_session_service.store_session(session_id, session_data)
            
        except Exception as e:
            logger.warning(f"Failed to update session cache after message: {e}")
    
    async def _archive_session_in_redis(self, session_id: str) -> None:
        """Archive session data before cleanup"""
        try:
            # Move session data to archive key with longer TTL
            session_data = await redis_session_service.get_session(session_id)
            
            if session_data:
                session_data['archived_at'] = datetime.utcnow().isoformat()
                archive_key = f"archived_session:{session_id}"
                
                # Store with 7-day TTL for potential recovery
                await redis_session_service.redis.set(archive_key, session_data, ttl=604800)
            
            # Remove from active session cache
            await redis_session_service.redis.delete(f"session:{session_id}")
            
        except Exception as e:
            logger.warning(f"Failed to archive session in Redis: {e}")
    
    @cached(ttl=300, key_prefix="sessions_with_messages", monitor_performance=True)
    async def get_sessions_with_recent_messages(
        self,
        user_id: str,
        limit: int = 20,
        status: Optional[str] = None,
        session_type: Optional[str] = None,
        message_limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get sessions with recent messages using optimized bulk loading
        Fixes N+1 query pattern in sessions API
        """
        try:
            # Build conditions
            conditions = [
                ChatSession.user_id == user_id,
                ChatSession.deleted_at.is_(None)
            ]
            
            if status:
                conditions.append(ChatSession.status == status)
            if session_type:
                conditions.append(ChatSession.session_type == session_type)
            
            # Get sessions with eager loading
            sessions_query = select(ChatSession).options(
                selectinload(ChatSession.user)
            ).where(and_(*conditions)).order_by(
                ChatSession.last_activity.desc()
            ).limit(limit)
            
            result = await self.session.execute(sessions_query)
            sessions = list(result.scalars().all())
            
            if not sessions:
                return []
            
            # Get all session IDs for bulk message loading
            session_ids = [str(session.id) for session in sessions]
            
            # Bulk load recent messages for all sessions
            # This uses a single query instead of N queries
            messages_query = select(
                ChatMessage.session_id,
                ChatMessage.id,
                ChatMessage.content,
                ChatMessage.role,
                ChatMessage.timestamp,
                ChatMessage.message_metadata,
                func.row_number().over(
                    partition_by=ChatMessage.session_id,
                    order_by=ChatMessage.timestamp.desc()
                ).label('rn')
            ).where(
                ChatMessage.session_id.in_(session_ids)
            )
            
            # Create subquery to get only the most recent messages
            messages_subquery = messages_query.subquery()
            recent_messages_query = select(messages_subquery).where(
                messages_subquery.c.rn <= message_limit
            ).order_by(
                messages_subquery.c.session_id,
                messages_subquery.c.timestamp.asc()
            )
            
            messages_result = await self.session.execute(recent_messages_query)
            messages_by_session = {}
            
            for row in messages_result.all():
                session_id = str(row.session_id)
                if session_id not in messages_by_session:
                    messages_by_session[session_id] = []
                
                messages_by_session[session_id].append({
                    'id': str(row.id),
                    'content': row.content,
                    'role': row.role,
                    'timestamp': row.timestamp,
                    'metadata': row.message_metadata or {}
                })
            
            # Combine sessions with their messages
            result_list = []
            for session in sessions:
                session_id = str(session.id)
                session_data = {
                    'session': {
                        'id': session_id,
                        'session_type': session.session_type,
                        'title': session.title,
                        'description': session.description,
                        'status': session.status,
                        'created_at': session.created_at,
                        'updated_at': session.updated_at,
                        'last_activity': session.last_activity,
                        'message_count': session.message_count or 0,
                        'tags': session.tags or [],
                        'session_metadata': session.session_metadata or {}
                    },
                    'recent_messages': messages_by_session.get(session_id, [])
                }
                result_list.append(session_data)
            
            logger.info(f"Bulk loaded {len(sessions)} sessions with messages using optimized query")
            return result_list
            
        except Exception as e:
            logger.error(f"Error bulk loading sessions with messages: {e}")
            raise RepositoryException(f"Bulk session loading failed", context={"user_id": user_id, "error": str(e)})
    
    @cached(ttl=600, key_prefix="session_count")
    async def get_session_count(self, user_id: str, **filters) -> int:
        """Get session count with caching for pagination"""
        try:
            conditions = [
                ChatSession.user_id == user_id,
                ChatSession.deleted_at.is_(None)
            ]
            
            # Apply filters
            for key, value in filters.items():
                if hasattr(ChatSession, key) and value is not None:
                    conditions.append(getattr(ChatSession, key) == value)
            
            count_query = select(func.count(ChatSession.id)).where(and_(*conditions))
            result = await self.session.execute(count_query)
            
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error getting session count: {e}")
            return 0