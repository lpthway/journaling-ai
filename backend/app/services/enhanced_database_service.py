# backend/app/services/enhanced_database_service.py
"""
Enhanced database service with PostgreSQL backend and enterprise features.

Replaces the original JSON-based database service with:
- Async SQLAlchemy operations
- Advanced querying capabilities
- Performance optimization
- Comprehensive error handling
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload, joinedload

from ..core.database import DatabaseManager
from ..models.enhanced_models import User, Topic, Entry, ChatSession, ChatMessage
from ..repositories.entry_repository import EntryRepository
from ..repositories.session_repository import SessionRepository

class EnhancedDatabaseService:
    """
    Enterprise database service with PostgreSQL backend.
    
    Features:
    - Repository pattern for clean separation
    - Advanced querying and filtering
    - Performance optimization with eager loading
    - Comprehensive analytics and reporting
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    # Entry Management
    async def create_entry(
        self, 
        entry_data: Dict[str, Any], 
        mood: Optional[str] = None, 
        sentiment_score: Optional[float] = None,
        user_id: Optional[str] = None
    ) -> Entry:
        """Create a new journal entry with full analysis."""
        async with self.db_manager.get_session() as session:
            repo = EntryRepository(session)
            
            # Use default user if not specified (single-user system)
            if not user_id:
                user_id = await self._get_default_user_id(session)
            
            entry = await repo.create_with_analysis(
                user_id=user_id,
                title=entry_data.get('title', 'Untitled Entry'),
                content=entry_data.get('content', ''),
                topic_id=entry_data.get('topic_id'),
                entry_type=entry_data.get('entry_type', 'journal'),
                mood=mood,
                sentiment_score=sentiment_score,
                tags=entry_data.get('tags', []),
                template_id=entry_data.get('template_id')
            )
            
            await session.commit()
            return entry
    
    async def get_entry(self, entry_id: str) -> Optional[Entry]:
        """Get entry by ID with relationships."""
        async with self.db_manager.get_session() as session:
            repo = EntryRepository(session)
            return await repo.get_by_id(entry_id, load_relationships=['topic'])
    
    async def get_entries(
        self,
        skip: int = 0,
        limit: int = 100,
        topic_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        user_id: Optional[str] = None
    ) -> List[Entry]:
        """Get entries with filtering and pagination."""
        async with self.db_manager.get_session() as session:
            repo = EntryRepository(session)
            
            if not user_id:
                user_id = await self._get_default_user_id(session)
            
            filters = {'user_id': user_id}
            if topic_id:
                filters['topic_id'] = topic_id
            if date_from:
                filters['created_at__gte'] = date_from
            if date_to:
                filters['created_at__lte'] = date_to
            
            return await repo.get_all(
                skip=skip,
                limit=limit,
                filters=filters,
                order_by='-created_at',
                load_relationships=['topic']
            )
    
    async def search_entries_full_text(
        self,
        query: str,
        limit: int = 20,
        user_id: Optional[str] = None
    ) -> List[Entry]:
        """Full-text search across entries."""
        async with self.db_manager.get_session() as session:
            repo = EntryRepository(session)
            
            if not user_id:
                user_id = await self._get_default_user_id(session)
            
            return await repo.search_full_text(user_id, query, limit)
    
    async def update_entry(
        self,
        entry_id: str,
        entry_update: Dict[str, Any],
        mood: Optional[str] = None,
        sentiment_score: Optional[float] = None
    ) -> Optional[Entry]:
        """Update an existing entry."""
        async with self.db_manager.get_session() as session:
            repo = EntryRepository(session)
            
            update_data = entry_update.copy()
            if mood:
                update_data['mood'] = mood
            if sentiment_score is not None:
                update_data['sentiment_score'] = sentiment_score
            
            entry = await repo.update(entry_id, **update_data)
            if entry:
                await session.commit()
            return entry
    
    async def delete_entry(self, entry_id: str) -> bool:
        """Delete an entry (soft delete)."""
        async with self.db_manager.get_session() as session:
            repo = EntryRepository(session)
            success = await repo.delete(entry_id, soft_delete=True)
            if success:
                await session.commit()
            return success
    
    async def get_mood_statistics(
        self,
        days: int = 30,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive mood analytics."""
        async with self.db_manager.get_session() as session:
            repo = EntryRepository(session)
            
            if not user_id:
                user_id = await self._get_default_user_id(session)
            
            return await repo.get_mood_analytics(user_id, days)
    
    async def get_favorite_entries(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[str] = None
    ) -> List[Entry]:
        """Get user's favorite entries."""
        async with self.db_manager.get_session() as session:
            repo = EntryRepository(session)
            
            if not user_id:
                user_id = await self._get_default_user_id(session)
            
            return await repo.get_favorites(user_id, limit, skip)
    
    async def toggle_entry_favorite(self, entry_id: str) -> Optional[Entry]:
        """Toggle favorite status of an entry."""
        async with self.db_manager.get_session() as session:
            repo = EntryRepository(session)
            
            entry = await repo.get_by_id(entry_id)
            if not entry:
                return None
            
            entry = await repo.update(entry_id, is_favorite=not entry.is_favorite)
            if entry:
                await session.commit()
            return entry
    
    async def search_entries_advanced(
        self,
        search_filters: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> List[Entry]:
        """Advanced search with multiple filters."""
        async with self.db_manager.get_session() as session:
            repo = EntryRepository(session)
            
            if not user_id:
                user_id = await self._get_default_user_id(session)
            
            filters = {'user_id': user_id}
            filters.update(search_filters)
            
            return await repo.get_all(
                skip=search_filters.get('offset', 0),
                limit=search_filters.get('limit', 50),
                filters=filters,
                load_relationships=['topic']
            )
    
    # Session Management
    async def create_session(self, session_data: Dict[str, Any]) -> ChatSession:
        """Create a new chat session."""
        async with self.db_manager.get_session() as session:
            repo = SessionRepository(session)
            
            user_id = await self._get_default_user_id(session)
            
            new_session = await repo.create_with_initial_message(
                user_id=user_id,
                session_type=session_data.get('session_type', 'free_chat'),
                title=session_data.get('title', f"New {session_data.get('session_type', 'chat')} session"),
                initial_message="Hello! How can I help you today?",
                description=session_data.get('description'),
                metadata=session_data.get('metadata', {})
            )
            
            await session.commit()
            return new_session
    
    async def add_message(self, session_id: str, message_data: Dict[str, Any]) -> ChatMessage:
        """Add a message to a chat session."""
        async with self.db_manager.get_session() as session:
            repo = SessionRepository(session)
            
            message = await repo.add_message(
                session_id=session_id,
                content=message_data.get('content', ''),
                role=message_data.get('role', 'user'),
                metadata=message_data.get('metadata', {})
            )
            
            await session.commit()
            return message
    
    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get session by ID."""
        async with self.db_manager.get_session() as session:
            repo = SessionRepository(session)
            return await repo.get_by_id(session_id)
    
    async def get_sessions(
        self,
        limit: int = 50,
        status: Optional[str] = None,
        session_type: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[ChatSession]:
        """Get sessions with filtering."""
        async with self.db_manager.get_session() as session:
            repo = SessionRepository(session)
            
            if not user_id:
                user_id = await self._get_default_user_id(session)
            
            filters = {'user_id': user_id}
            if status:
                filters['status'] = status
            if session_type:
                filters['session_type'] = session_type
            
            return await repo.get_all(
                limit=limit,
                filters=filters,
                order_by='-last_activity'
            )
    
    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[ChatMessage]:
        """Get messages for a session."""
        async with self.db_manager.get_session() as session:
            repo = SessionRepository(session)
            return await repo.get_messages(session_id, limit, offset)
    
    async def close_session(self, session_id: str) -> bool:
        """Close a chat session."""
        async with self.db_manager.get_session() as session:
            repo = SessionRepository(session)
            success = await repo.close_session(session_id)
            if success:
                await session.commit()
            return success
    
    # Topic Management
    async def create_topic(
        self,
        topic_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Topic:
        """Create a new topic."""
        async with self.db_manager.get_session() as session:
            if not user_id:
                user_id = await self._get_default_user_id(session)
            
            topic = Topic(
                user_id=user_id,
                name=topic_data.get('name', 'Untitled Topic'),
                description=topic_data.get('description'),
                color=topic_data.get('color', '#3B82F6'),
                icon=topic_data.get('icon'),
                tags=topic_data.get('tags', []),
                metadata=topic_data.get('metadata', {})
            )
            
            session.add(topic)
            await session.flush()
            await session.refresh(topic)
            await session.commit()
            
            return topic
    
    async def get_topics(
        self,
        user_id: Optional[str] = None,
        include_entry_count: bool = True
    ) -> List[Topic]:
        """Get all topics for a user."""
        async with self.db_manager.get_session() as session:
            if not user_id:
                user_id = await self._get_default_user_id(session)
            
            query = select(Topic).where(
                and_(
                    Topic.user_id == user_id,
                    Topic.deleted_at.is_(None)
                )
            ).order_by(Topic.name)
            
            if include_entry_count:
                query = query.options(selectinload(Topic.entries))
            
            result = await session.execute(query)
            return list(result.scalars().all())
    
    async def update_topic(
        self,
        topic_id: str,
        topic_update: Dict[str, Any]
    ) -> Optional[Topic]:
        """Update a topic."""
        async with self.db_manager.get_session() as session:
            topic = await session.get(Topic, topic_id)
            if not topic:
                return None
            
            for key, value in topic_update.items():
                if hasattr(topic, key):
                    setattr(topic, key, value)
            
            topic.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(topic)
            
            return topic
    
    async def delete_topic(self, topic_id: str) -> bool:
        """Delete a topic (soft delete)."""
        async with self.db_manager.get_session() as session:
            topic = await session.get(Topic, topic_id)
            if not topic:
                return False
            
            topic.deleted_at = datetime.utcnow()
            await session.commit()
            return True
    
    # Analytics and Statistics
    async def get_user_analytics(
        self,
        days: int = 30,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive user analytics."""
        async with self.db_manager.get_session() as session:
            if not user_id:
                user_id = await self._get_default_user_id(session)
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Entry statistics
            entry_stats = await session.execute(
                select(
                    func.count(Entry.id).label('total_entries'),
                    func.sum(Entry.word_count).label('total_words'),
                    func.avg(Entry.word_count).label('avg_words_per_entry')
                ).where(
                    and_(
                        Entry.user_id == user_id,
                        Entry.created_at >= start_date,
                        Entry.deleted_at.is_(None)
                    )
                )
            )
            entry_row = entry_stats.first()
            
            # Session statistics
            session_stats = await session.execute(
                select(
                    func.count(ChatSession.id).label('total_sessions'),
                    func.sum(ChatSession.message_count).label('total_messages'),
                    func.avg(ChatSession.total_duration_minutes).label('avg_session_duration')
                ).where(
                    and_(
                        ChatSession.user_id == user_id,
                        ChatSession.created_at >= start_date,
                        ChatSession.deleted_at.is_(None)
                    )
                )
            )
            session_row = session_stats.first()
            
            return {
                'period_days': days,
                'entries': {
                    'total': entry_row.total_entries or 0,
                    'total_words': entry_row.total_words or 0,
                    'avg_words_per_entry': float(entry_row.avg_words_per_entry) if entry_row.avg_words_per_entry else 0
                },
                'sessions': {
                    'total': session_row.total_sessions or 0,
                    'total_messages': session_row.total_messages or 0,
                    'avg_duration': float(session_row.avg_session_duration) if session_row.avg_session_duration else 0
                }
            }
    
    async def get_writing_streak(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Calculate writing streak statistics."""
        async with self.db_manager.get_session() as session:
            if not user_id:
                user_id = await self._get_default_user_id(session)
            
            # Get dates with entries in the last 100 days
            query = select(
                func.date(Entry.created_at).label('entry_date')
            ).where(
                and_(
                    Entry.user_id == user_id,
                    Entry.created_at >= datetime.utcnow() - timedelta(days=100),
                    Entry.deleted_at.is_(None)
                )
            ).group_by(func.date(Entry.created_at)).order_by(func.date(Entry.created_at).desc())
            
            result = await session.execute(query)
            entry_dates = [row.entry_date for row in result.all()]
            
            if not entry_dates:
                return {'current_streak': 0, 'longest_streak': 0, 'total_active_days': 0}
            
            # Calculate current streak
            current_streak = 0
            today = datetime.utcnow().date()
            check_date = today
            
            for entry_date in entry_dates:
                if entry_date == check_date or entry_date == check_date - timedelta(days=1):
                    current_streak += 1
                    check_date = entry_date - timedelta(days=1)
                else:
                    break
            
            # Calculate longest streak
            longest_streak = 0
            current_run = 1
            
            for i in range(1, len(entry_dates)):
                if entry_dates[i-1] - entry_dates[i] == timedelta(days=1):
                    current_run += 1
                else:
                    longest_streak = max(longest_streak, current_run)
                    current_run = 1
            
            longest_streak = max(longest_streak, current_run)
            
            return {
                'current_streak': current_streak,
                'longest_streak': longest_streak,
                'total_active_days': len(entry_dates)
            }
    
    # Helper Methods
    async def _get_default_user_id(self, session: AsyncSession) -> str:
        """Get the default user ID for single-user system."""
        result = await session.execute(
            select(User.id).where(User.username == 'default_user')
        )
        user_id = result.scalar_one_or_none()
        
        if not user_id:
            # Create default user if not exists
            user = User(
                username='default_user',
                display_name='Journal User',
                preferences={'theme': 'light', 'language': 'en'},
                psychology_profile={}
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)
            user_id = user.id
        
        return str(user_id)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        try:
            async with self.db_manager.get_session() as session:
                # Test basic connectivity
                await session.execute(select(1))
                
                # Get basic statistics
                user_count = await session.scalar(select(func.count(User.id)))
                entry_count = await session.scalar(select(func.count(Entry.id)))
                session_count = await session.scalar(select(func.count(ChatSession.id)))
                
                return {
                    'status': 'healthy',
                    'statistics': {
                        'users': user_count,
                        'entries': entry_count,
                        'sessions': session_count
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }