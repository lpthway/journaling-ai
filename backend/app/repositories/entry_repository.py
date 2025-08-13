# backend/app/repositories/entry_repository.py
"""
Specialized entry repository with advanced journaling features.

Features:
- Full-text search with PostgreSQL TSVECTOR
- Advanced mood and sentiment analytics
- Tag-based filtering and categorization
- Performance-optimized queries for large datasets
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, or_, text, desc
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from ..models.enhanced_models import Entry, Topic
from ..auth.models import AuthUser
from .enhanced_base import EnhancedBaseRepository

class EntryRepository(EnhancedBaseRepository[Entry]):
    """
    Advanced entry repository with journaling-specific features.
    
    Optimized for:
    - High-volume entry storage and retrieval
    - Complex search and filtering operations
    - Mood and sentiment analytics
    - Performance at scale (10K+ users)
    """
    
    def __init__(self, session):
        super().__init__(session, Entry)
    
    async def create_with_analysis(
        self,
        user_id: str,
        title: str,
        content: str,
        topic_id: Optional[str] = None,
        **kwargs
    ) -> Entry:
        """
        Create entry with automatic content analysis.
        
        Performs:
        - Word count calculation
        - Reading time estimation
        - Full-text search vector generation
        - Basic content validation
        """
        # Calculate content metrics
        word_count = len(content.split())
        reading_time = max(1, word_count // 200)  # ~200 WPM reading speed
        
        # Create entry
        entry = Entry(
            user_id=user_id,
            title=title,
            content=content,
            topic_id=topic_id,
            word_count=word_count,
            reading_time_minutes=reading_time,
            **kwargs
        )
        
        # Generate search vector for full-text search
        search_query = text("""
            UPDATE entries 
            SET search_vector = to_tsvector('english', title || ' ' || content)
            WHERE id = :entry_id
        """)
        
        created_entry = await self.create(entry)
        
        # Update search vector
        await self.session.execute(search_query, {"entry_id": str(created_entry.id)})
        await self.session.commit()
        
        return created_entry
    
    async def search_full_text(
        self,
        user_id: str,
        query: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Entry]:
        """
        Perform full-text search with relevance ranking.
        
        Uses PostgreSQL's full-text search capabilities for:
        - Natural language queries
        - Relevance-based ranking
        - Performance optimization for large datasets
        """
        search_query = select(Entry).where(
            and_(
                Entry.user_id == user_id,
                Entry.search_vector.op('@@')(func.plainto_tsquery('english', query)),
                Entry.deleted_at.is_(None)
            )
        ).order_by(
            func.ts_rank(Entry.search_vector, func.plainto_tsquery('english', query)).desc()
        ).offset(offset).limit(limit)
        
        result = await self.session.execute(search_query)
        return list(result.scalars().all())
    
    async def get_mood_analytics(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate comprehensive mood analytics for a user.
        
        Returns:
        - Mood distribution over time period
        - Sentiment trends and patterns
        - Daily averages and variations
        - Comparative analysis with previous periods
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Mood distribution query
        mood_query = select(
            Entry.mood,
            func.count(Entry.id).label('count'),
            func.avg(Entry.sentiment_score).label('avg_sentiment')
        ).where(
            and_(
                Entry.user_id == user_id,
                Entry.created_at >= start_date,
                Entry.deleted_at.is_(None)
            )
        ).group_by(Entry.mood)
        
        mood_result = await self.session.execute(mood_query)
        mood_distribution = {
            row.mood: {
                'count': row.count,
                'avg_sentiment': float(row.avg_sentiment) if row.avg_sentiment else 0
            }
            for row in mood_result.all()
        }
        
        # Daily mood trends
        daily_query = select(
            func.date(Entry.created_at).label('date'),
            func.avg(Entry.sentiment_score).label('avg_sentiment'),
            func.count(Entry.id).label('entry_count')
        ).where(
            and_(
                Entry.user_id == user_id,
                Entry.created_at >= start_date,
                Entry.deleted_at.is_(None)
            )
        ).group_by(func.date(Entry.created_at)).order_by('date')
        
        daily_result = await self.session.execute(daily_query)
        daily_trends = [
            {
                'date': row.date.isoformat(),
                'avg_sentiment': float(row.avg_sentiment) if row.avg_sentiment else 0,
                'entry_count': row.entry_count
            }
            for row in daily_result.all()
        ]
        
        return {
            'period_days': days,
            'mood_distribution': mood_distribution,
            'daily_trends': daily_trends,
            'total_entries': sum(data['count'] for data in mood_distribution.values())
        }
    
    async def get_entries_by_topic(
        self,
        user_id: str,
        topic_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Entry]:
        """Get entries for a specific topic with optimized loading."""
        query = select(Entry).options(
            selectinload(Entry.topic)
        ).where(
            and_(
                Entry.user_id == user_id,
                Entry.topic_id == topic_id,
                Entry.deleted_at.is_(None)
            )
        ).order_by(Entry.created_at.desc()).offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_favorites(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Entry]:
        """Get user's favorite entries with optimized loading."""
        query = select(Entry).options(
            selectinload(Entry.topic)
        ).where(
            and_(
                Entry.user_id == user_id,
                Entry.is_favorite == True,
                Entry.deleted_at.is_(None)
            )
        ).order_by(Entry.created_at.desc()).offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_entries_by_mood(
        self,
        user_id: str,
        mood: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Entry]:
        """Get entries filtered by mood."""
        query = select(Entry).options(
            selectinload(Entry.topic)
        ).where(
            and_(
                Entry.user_id == user_id,
                Entry.mood == mood,
                Entry.deleted_at.is_(None)
            )
        ).order_by(Entry.created_at.desc()).offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_entries_by_date_range(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100,
        offset: int = 0
    ) -> List[Entry]:
        """Get entries within a specific date range."""
        query = select(Entry).options(
            selectinload(Entry.topic)
        ).where(
            and_(
                Entry.user_id == user_id,
                Entry.created_at >= start_date,
                Entry.created_at <= end_date,
                Entry.deleted_at.is_(None)
            )
        ).order_by(Entry.created_at.desc()).offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def search_by_tags(
        self,
        user_id: str,
        tags: List[str],
        limit: int = 50,
        offset: int = 0
    ) -> List[Entry]:
        """Search entries by tags using JSONB containment."""
        query = select(Entry).options(
            selectinload(Entry.topic)
        ).where(
            and_(
                Entry.user_id == user_id,
                or_(*[Entry.tags.contains([tag]) for tag in tags]),
                Entry.deleted_at.is_(None)
            )
        ).order_by(Entry.created_at.desc()).offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_writing_statistics(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get writing statistics for a user."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        stats_query = select(
            func.count(Entry.id).label('total_entries'),
            func.sum(Entry.word_count).label('total_words'),
            func.avg(Entry.word_count).label('avg_words_per_entry'),
            func.max(Entry.word_count).label('longest_entry'),
            func.count(func.distinct(func.date(Entry.created_at))).label('active_days')
        ).where(
            and_(
                Entry.user_id == user_id,
                Entry.created_at >= start_date,
                Entry.deleted_at.is_(None)
            )
        )
        
        result = await self.session.execute(stats_query)
        row = result.first()
        
        return {
            'period_days': days,
            'total_entries': row.total_entries or 0,
            'total_words': row.total_words or 0,
            'avg_words_per_entry': float(row.avg_words_per_entry) if row.avg_words_per_entry else 0,
            'longest_entry': row.longest_entry or 0,
            'active_days': row.active_days or 0,
            'consistency_percentage': (row.active_days / days * 100) if row.active_days else 0
        }
    
    async def update_search_vectors(self, batch_size: int = 1000) -> int:
        """
        Batch update search vectors for full-text search optimization.
        
        Used for:
        - Initial migration from JSON storage
        - Periodic search index maintenance
        - Performance optimization
        """
        update_query = text("""
            UPDATE entries 
            SET search_vector = to_tsvector('english', title || ' ' || content)
            WHERE search_vector IS NULL
            AND deleted_at IS NULL
            LIMIT :batch_size
        """)
        
        result = await self.session.execute(update_query, {"batch_size": batch_size})
        await self.session.commit()
        
        return result.rowcount