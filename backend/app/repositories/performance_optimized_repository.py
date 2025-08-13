# backend/app/repositories/performance_optimized_repository.py
"""
Performance-optimized repository patterns for high-frequency operations
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_, desc, text, asc, column
from sqlalchemy.orm import selectinload, load_only
from contextlib import asynccontextmanager

from app.models.enhanced_models import Entry, Topic, ChatSession
from app.auth.models import AuthUser
from app.core.database import get_db_session

logger = logging.getLogger(__name__)

class PerformanceOptimizedRepository:
    """
    Repository focused on high-performance queries with minimal data transfer
    """
    
    def __init__(self):
        self.default_entry_fields = [
            'id', 'title', 'content', 'mood', 'created_at', 
            'updated_at', 'word_count', 'is_favorite'
        ]
        self.lightweight_entry_fields = [
            'id', 'title', 'mood', 'created_at', 'word_count', 'is_favorite'
        ]
    
    async def get_entries_lightweight(
        self, 
        user_id: str, 
        limit: int = 20,
        offset: int = 0,
        include_content: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get entries with minimal data transfer for list views
        """
        try:
            async with get_db_session() as session:
                fields = self.default_entry_fields if include_content else self.lightweight_entry_fields
                
                # Use load_only to fetch only required columns
                query = select(Entry).options(
                    load_only(*fields)
                ).where(
                    and_(
                        Entry.user_id == user_id,
                        Entry.deleted_at.is_(None)
                    )
                ).order_by(desc(Entry.created_at)).limit(limit).offset(offset)
                
                result = await session.execute(query)
                entries = result.scalars().all()
                
                # Convert to lightweight dictionaries
                return [
                    {
                        'id': str(entry.id),
                        'title': entry.title,
                        'mood': entry.mood,
                        'created_at': entry.created_at.isoformat(),
                        'word_count': entry.word_count,
                        'is_favorite': entry.is_favorite,
                        **(
                            {'content': entry.content[:200] + '...' if len(entry.content) > 200 else entry.content} 
                            if include_content and hasattr(entry, 'content') else {}
                        )
                    }
                    for entry in entries
                ]
        except Exception as e:
            logger.error(f"Error fetching lightweight entries: {e}")
            return []
    
    async def get_entry_content_only(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        Get only entry content for detail view (lazy loading)
        """
        try:
            async with get_db_session() as session:
                query = select(Entry).options(
                    load_only(Entry.id, Entry.content, Entry.tags)
                ).where(
                    and_(
                        Entry.id == entry_id,
                        Entry.deleted_at.is_(None)
                    )
                )
                
                result = await session.execute(query)
                entry = result.scalar_one_or_none()
                
                if entry:
                    return {
                        'id': str(entry.id),
                        'content': entry.content,
                        'tags': entry.tags or []
                    }
                return None
        except Exception as e:
            logger.error(f"Error fetching entry content {entry_id}: {e}")
            return None
    
    async def get_mood_stats_optimized(
        self, 
        user_id: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Optimized mood statistics with minimal query overhead
        """
        try:
            async with get_db_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                # Single aggregation query for all mood stats
                query = select(
                    func.count(Entry.id).label('total_entries'),
                    func.avg(
                        func.case(
                            (Entry.mood == 'very_happy', 5),
                            (Entry.mood == 'happy', 4),
                            (Entry.mood == 'neutral', 3),
                            (Entry.mood == 'sad', 2),
                            (Entry.mood == 'very_sad', 1),
                            else_=3
                        )
                    ).label('avg_mood_score'),
                    func.mode().within_group(Entry.mood.asc()).label('most_common_mood')
                ).where(
                    and_(
                        Entry.user_id == user_id,
                        Entry.created_at >= cutoff_date,
                        Entry.deleted_at.is_(None)
                    )
                )
                
                result = await session.execute(query)
                stats = result.fetchone()
                
                if stats and stats.total_entries > 0:
                    return {
                        'total_entries': stats.total_entries,
                        'average_mood_score': round(float(stats.avg_mood_score or 3), 2),
                        'most_common_mood': stats.most_common_mood or 'neutral',
                        'period_days': days
                    }
                else:
                    return {
                        'total_entries': 0,
                        'average_mood_score': 3.0,
                        'most_common_mood': 'neutral',
                        'period_days': days
                    }
        except Exception as e:
            logger.error(f"Error fetching mood stats: {e}")
            return {'total_entries': 0, 'average_mood_score': 3.0, 'most_common_mood': 'neutral', 'period_days': days}
    
    async def get_topics_with_entry_counts(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get topics with entry counts in single query
        """
        try:
            async with get_db_session() as session:
                query = select(
                    Topic.id,
                    Topic.name,
                    Topic.color,
                    func.count(Entry.id).label('entry_count'),
                    func.max(Entry.created_at).label('last_entry_date')
                ).outerjoin(
                    Entry, and_(
                        Entry.topic_id == Topic.id,
                        Entry.deleted_at.is_(None)
                    )
                ).where(
                    Topic.user_id == user_id
                ).group_by(
                    Topic.id, Topic.name, Topic.color
                ).order_by(desc('entry_count'))
                
                result = await session.execute(query)
                topics = result.fetchall()
                
                return [
                    {
                        'id': str(topic.id),
                        'name': topic.name,
                        'color': topic.color,
                        'entry_count': topic.entry_count,
                        'last_entry_date': topic.last_entry_date.isoformat() if topic.last_entry_date else None
                    }
                    for topic in topics
                ]
        except Exception as e:
            logger.error(f"Error fetching topics with counts: {e}")
            return []
    
    async def search_entries_fast(
        self, 
        user_id: str, 
        query: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fast search with content preview only
        """
        try:
            async with get_db_session() as session:
                search_query = select(Entry).options(
                    load_only(
                        Entry.id, Entry.title, Entry.content, 
                        Entry.mood, Entry.created_at, Entry.word_count
                    )
                ).where(
                    and_(
                        Entry.user_id == user_id,
                        Entry.deleted_at.is_(None),
                        or_(
                            Entry.title.ilike(f'%{query}%'),
                            Entry.content.ilike(f'%{query}%')
                        )
                    )
                ).order_by(desc(Entry.created_at)).limit(limit)
                
                result = await session.execute(search_query)
                entries = result.scalars().all()
                
                return [
                    {
                        'id': str(entry.id),
                        'title': entry.title,
                        'content_preview': entry.content[:150] + '...' if len(entry.content) > 150 else entry.content,
                        'mood': entry.mood,
                        'created_at': entry.created_at.isoformat(),
                        'word_count': entry.word_count,
                        'relevance_score': self._calculate_relevance(query, entry.title, entry.content)
                    }
                    for entry in entries
                ]
        except Exception as e:
            logger.error(f"Error in fast search: {e}")
            return []
    
    def _calculate_relevance(self, query: str, title: str, content: str) -> float:
        """Simple relevance scoring"""
        query_words = query.lower().split()
        title_lower = title.lower()
        content_lower = content.lower()
        
        score = 0.0
        for word in query_words:
            if word in title_lower:
                score += 2.0  # Title matches are more important
            if word in content_lower:
                score += 1.0
        
        return round(score / len(query_words), 2)
    
    async def get_session_summary_lightweight(
        self, 
        user_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get chat session summaries without full message content
        """
        try:
            async with get_db_session() as session:
                query = select(
                    ChatSession.id,
                    ChatSession.session_type,
                    ChatSession.status,
                    ChatSession.created_at,
                    ChatSession.updated_at,
                    func.count(func.distinct(column('messages.id'))).label('message_count')
                ).outerjoin(
                    'messages'  # Assuming messages relationship exists
                ).where(
                    ChatSession.user_id == user_id
                ).group_by(
                    ChatSession.id
                ).order_by(desc(ChatSession.updated_at)).limit(limit)
                
                result = await session.execute(query)
                sessions = result.fetchall()
                
                return [
                    {
                        'id': str(session.id),
                        'session_type': session.session_type,
                        'status': session.status,
                        'created_at': session.created_at.isoformat(),
                        'updated_at': session.updated_at.isoformat(),
                        'message_count': session.message_count
                    }
                    for session in sessions
                ]
        except Exception as e:
            logger.error(f"Error fetching session summaries: {e}")
            return []

# Global instance
performance_repo = PerformanceOptimizedRepository()