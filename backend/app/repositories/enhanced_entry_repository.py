# backend/app/repositories/enhanced_entry_repository.py
"""
Enhanced Entry Repository with Specialized Caching
Optimized for journaling operations with intelligent cache management
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_, desc, text, asc
from sqlalchemy.orm import selectinload
from contextlib import asynccontextmanager

from app.repositories.base_cached_repository import EnhancedBaseRepository
from app.models.enhanced_models import Entry, Topic, User
from app.decorators.cache_decorators import cached, cache_invalidate, timed_operation, CachePatterns
from app.core.exceptions import RepositoryException, NotFoundException
from app.core.performance_monitor import performance_monitor

logger = logging.getLogger(__name__)

class EnhancedEntryRepository(EnhancedBaseRepository[Entry]):
    """
    Specialized entry repository with advanced caching and analytics
    
    Features:
    - Full-text search with PostgreSQL TSVECTOR caching
    - Mood analytics with intelligent cache invalidation
    - Performance-optimized queries for large datasets
    - Real-time cache management for user experience
    """
    
    def __init__(self, session):
        super().__init__(session, Entry, "entry")
        self.search_cache_ttl = 900    # 15 minutes for search results
        self.analytics_cache_ttl = 1800  # 30 minutes for analytics
        self.entry_cache_ttl = 3600     # 1 hour for individual entries
    
    @CachePatterns.ENTRY_READ
    async def get_by_id(self, entry_id: str, use_cache: bool = True) -> Optional[Entry]:
        """Get entry by ID with optimized caching and relationships"""
        try:
            query = select(Entry).options(
                selectinload(Entry.topic),
                selectinload(Entry.user)
            ).where(
                and_(
                    Entry.id == entry_id,
                    Entry.deleted_at.is_(None)
                )
            )
            
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting entry {entry_id}: {e}")
            raise RepositoryException(f"Failed to get entry", context={"id": entry_id, "error": str(e)})
    
    @CachePatterns.ENTRY_SEARCH
    async def search_full_text(
        self,
        user_id: str,
        query: str,
        limit: int = 20,
        offset: int = 0,
        mood_filter: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Entry]:
        """
        Full-text search with caching and performance optimization
        Uses PostgreSQL's full-text search with relevance ranking
        """
        try:
            # Build search query with filters
            search_conditions = [
                Entry.user_id == user_id,
                Entry.deleted_at.is_(None)
            ]
            
            # Full-text search condition
            if query.strip():
                search_conditions.append(
                    Entry.search_vector.op('@@')(func.plainto_tsquery('english', query))
                )
            
            # Additional filters
            if mood_filter:
                search_conditions.append(Entry.mood == mood_filter)
            if date_from:
                search_conditions.append(Entry.created_at >= date_from)
            if date_to:
                search_conditions.append(Entry.created_at <= date_to)
            
            # Execute search with relevance ranking
            if query.strip():
                search_query = select(Entry).options(
                    selectinload(Entry.topic)
                ).where(
                    and_(*search_conditions)
                ).order_by(
                    func.ts_rank(Entry.search_vector, func.plainto_tsquery('english', query)).desc(),
                    Entry.created_at.desc()
                ).offset(offset).limit(limit)
            else:
                # No search query, just filtered results
                search_query = select(Entry).options(
                    selectinload(Entry.topic)
                ).where(
                    and_(*search_conditions)
                ).order_by(Entry.created_at.desc()).offset(offset).limit(limit)
            
            async with performance_monitor.timed_operation("full_text_search", {"query_length": len(query)}):
                result = await self.session.execute(search_query)
                entries = list(result.scalars().all())
            
            logger.info(f"Full-text search returned {len(entries)} results for query: '{query[:50]}...'")
            return entries
            
        except Exception as e:
            logger.error(f"Error in full-text search: {e}")
            raise RepositoryException(f"Full-text search failed", context={"query": query, "error": str(e)})
    
    @CachePatterns.ENTRY_ANALYTICS
    async def get_mood_analytics(
        self,
        user_id: str,
        days: int = 30,
        include_trends: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive mood analytics with intelligent caching
        Optimized for dashboard and insights display
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Base conditions
            base_conditions = [
                Entry.user_id == user_id,
                Entry.created_at >= start_date,
                Entry.deleted_at.is_(None)
            ]
            
            async with performance_monitor.timed_operation("mood_analytics", {"days": days, "user_id": user_id}):
                # Mood distribution query
                mood_query = select(
                    Entry.mood,
                    func.count(Entry.id).label('count'),
                    func.avg(Entry.sentiment_score).label('avg_sentiment'),
                    func.min(Entry.created_at).label('first_entry'),
                    func.max(Entry.created_at).label('last_entry')
                ).where(
                    and_(*base_conditions, Entry.mood.is_not(None))
                ).group_by(Entry.mood)
                
                mood_result = await self.session.execute(mood_query)
                mood_distribution = {}
                
                for row in mood_result.all():
                    mood_distribution[row.mood] = {
                        'count': row.count,
                        'percentage': 0,  # Will calculate after total
                        'avg_sentiment': float(row.avg_sentiment) if row.avg_sentiment else 0,
                        'first_entry': row.first_entry.isoformat() if row.first_entry else None,
                        'last_entry': row.last_entry.isoformat() if row.last_entry else None
                    }
                
                # Calculate percentages
                total_mood_entries = sum(data['count'] for data in mood_distribution.values())
                for mood_data in mood_distribution.values():
                    mood_data['percentage'] = (mood_data['count'] / total_mood_entries * 100) if total_mood_entries > 0 else 0
                
                # Daily trends if requested
                daily_trends = []
                if include_trends:
                    daily_query = select(
                        func.date(Entry.created_at).label('date'),
                        func.count(Entry.id).label('entry_count'),
                        func.avg(Entry.sentiment_score).label('avg_sentiment'),
                        func.array_agg(Entry.mood).label('moods')
                    ).where(
                        and_(*base_conditions)
                    ).group_by(func.date(Entry.created_at)).order_by('date')
                    
                    daily_result = await self.session.execute(daily_query)
                    for row in daily_result.all():
                        daily_trends.append({
                            'date': row.date.isoformat(),
                            'entry_count': row.entry_count,
                            'avg_sentiment': float(row.avg_sentiment) if row.avg_sentiment else 0,
                            'dominant_mood': max(set(row.moods), key=row.moods.count) if row.moods else None
                        })
                
                # Overall statistics
                stats_query = select(
                    func.count(Entry.id).label('total_entries'),
                    func.avg(Entry.sentiment_score).label('overall_sentiment'),
                    func.sum(Entry.word_count).label('total_words'),
                    func.avg(Entry.word_count).label('avg_words_per_entry'),
                    func.count(func.distinct(func.date(Entry.created_at))).label('active_days')
                ).where(and_(*base_conditions))
                
                stats_result = await self.session.execute(stats_query)
                stats_row = stats_result.first()
            
            analytics_data = {
                'period_days': days,
                'mood_distribution': mood_distribution,
                'daily_trends': daily_trends,
                'statistics': {
                    'total_entries': stats_row.total_entries or 0,
                    'overall_sentiment': float(stats_row.overall_sentiment) if stats_row.overall_sentiment else 0,
                    'total_words': stats_row.total_words or 0,
                    'avg_words_per_entry': float(stats_row.avg_words_per_entry) if stats_row.avg_words_per_entry else 0,
                    'active_days': stats_row.active_days or 0,
                    'consistency_percentage': (stats_row.active_days / days * 100) if stats_row.active_days else 0
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Generated mood analytics for user {user_id}: {stats_row.total_entries} entries over {days} days")
            return analytics_data
            
        except Exception as e:
            logger.error(f"Error generating mood analytics: {e}")
            raise RepositoryException(f"Mood analytics failed", context={"user_id": user_id, "days": days, "error": str(e)})
    
    @cached(ttl=3600, key_prefix="entry_favorites", monitor_performance=True)
    async def get_favorites(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Entry]:
        """Get user's favorite entries with caching"""
        try:
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
            
        except Exception as e:
            logger.error(f"Error getting favorite entries: {e}")
            raise RepositoryException(f"Failed to get favorites", context={"user_id": user_id, "error": str(e)})
    
    @cached(ttl=1800, key_prefix="entry_by_topic", monitor_performance=True)
    async def get_entries_by_topic(
        self,
        user_id: str,
        topic_id: str,
        limit: int = 50,
        offset: int = 0,
        include_analytics: bool = False
    ) -> Dict[str, Any]:
        """Get entries for a specific topic with optional analytics"""
        try:
            # Get entries
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
            entries = list(result.scalars().all())
            
            response = {
                'entries': entries,
                'total_count': len(entries)
            }
            
            # Include analytics if requested
            if include_analytics:
                analytics_query = select(
                    func.count(Entry.id).label('total_entries'),
                    func.avg(Entry.sentiment_score).label('avg_sentiment'),
                    func.sum(Entry.word_count).label('total_words'),
                    func.min(Entry.created_at).label('first_entry'),
                    func.max(Entry.created_at).label('last_entry')
                ).where(
                    and_(
                        Entry.user_id == user_id,
                        Entry.topic_id == topic_id,
                        Entry.deleted_at.is_(None)
                    )
                )
                
                analytics_result = await self.session.execute(analytics_query)
                analytics_row = analytics_result.first()
                
                response['analytics'] = {
                    'total_entries': analytics_row.total_entries or 0,
                    'avg_sentiment': float(analytics_row.avg_sentiment) if analytics_row.avg_sentiment else 0,
                    'total_words': analytics_row.total_words or 0,
                    'first_entry': analytics_row.first_entry.isoformat() if analytics_row.first_entry else None,
                    'last_entry': analytics_row.last_entry.isoformat() if analytics_row.last_entry else None
                }
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting entries by topic: {e}")
            raise RepositoryException(f"Failed to get entries by topic", context={"topic_id": topic_id, "error": str(e)})
    
    @cached(ttl=900, key_prefix="entry_search_tags", monitor_performance=True)
    async def search_by_tags(
        self,
        user_id: str,
        tags: List[str],
        match_all: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Entry]:
        """Search entries by tags using JSONB operations"""
        try:
            if match_all:
                # All tags must be present
                tag_condition = and_(*[Entry.tags.contains([tag]) for tag in tags])
            else:
                # Any tag matches
                tag_condition = or_(*[Entry.tags.contains([tag]) for tag in tags])
            
            query = select(Entry).options(
                selectinload(Entry.topic)
            ).where(
                and_(
                    Entry.user_id == user_id,
                    tag_condition,
                    Entry.deleted_at.is_(None)
                )
            ).order_by(Entry.created_at.desc()).offset(offset).limit(limit)
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Error searching by tags: {e}")
            raise RepositoryException(f"Tag search failed", context={"tags": tags, "error": str(e)})
    
    @cached(ttl=1800, key_prefix="writing_stats", monitor_performance=True)
    async def get_writing_statistics(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get comprehensive writing statistics with caching"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            stats_query = select(
                func.count(Entry.id).label('total_entries'),
                func.sum(Entry.word_count).label('total_words'),
                func.avg(Entry.word_count).label('avg_words_per_entry'),
                func.max(Entry.word_count).label('longest_entry_words'),
                func.min(Entry.word_count).label('shortest_entry_words'),
                func.count(func.distinct(func.date(Entry.created_at))).label('active_days'),
                func.sum(Entry.reading_time_minutes).label('total_reading_time')
            ).where(
                and_(
                    Entry.user_id == user_id,
                    Entry.created_at >= start_date,
                    Entry.deleted_at.is_(None)
                )
            )
            
            result = await self.session.execute(stats_query)
            row = result.first()
            
            # Calculate streak information
            streak_info = await self._calculate_writing_streak(user_id)
            
            return {
                'period_days': days,
                'total_entries': row.total_entries or 0,
                'total_words': row.total_words or 0,
                'avg_words_per_entry': float(row.avg_words_per_entry) if row.avg_words_per_entry else 0,
                'longest_entry_words': row.longest_entry_words or 0,
                'shortest_entry_words': row.shortest_entry_words or 0,
                'active_days': row.active_days or 0,
                'total_reading_time_minutes': row.total_reading_time or 0,
                'consistency_percentage': (row.active_days / days * 100) if row.active_days else 0,
                'avg_entries_per_active_day': (row.total_entries / row.active_days) if row.active_days else 0,
                'streak_info': streak_info,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting writing statistics: {e}")
            raise RepositoryException(f"Writing statistics failed", context={"user_id": user_id, "error": str(e)})
    
    @CachePatterns.INVALIDATE_ENTRIES
    @timed_operation("create_entry_with_analysis", track_errors=True)
    async def create_with_analysis(
        self,
        user_id: str,
        title: str,
        content: str,
        topic_id: Optional[str] = None,
        mood: Optional[str] = None,
        sentiment_score: Optional[float] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> Entry:
        """
        Create entry with automatic content analysis and cache invalidation
        """
        try:
            # Calculate content metrics
            word_count = len(content.split())
            reading_time = max(1, word_count // 200)  # ~200 WPM reading speed
            character_count = len(content)
            
            # Create entry with analysis
            entry_data = {
                'user_id': user_id,
                'title': title,
                'content': content,
                'topic_id': topic_id,
                'mood': mood,
                'sentiment_score': sentiment_score,
                'tags': tags or [],
                'word_count': word_count,
                'reading_time_minutes': reading_time,
                'character_count': character_count,
                'created_at': datetime.utcnow(),
                **kwargs
            }
            
            entry = Entry(**entry_data)
            self.session.add(entry)
            await self.session.flush()
            await self.session.refresh(entry)
            
            # Update search vector for full-text search
            search_vector_query = text("""
                UPDATE entries 
                SET search_vector = to_tsvector('english', title || ' ' || content)
                WHERE id = :entry_id
            """)
            
            await self.session.execute(search_vector_query, {"entry_id": str(entry.id)})
            
            logger.info(f"Created entry {entry.id} with {word_count} words")
            return entry
            
        except Exception as e:
            logger.error(f"Error creating entry with analysis: {e}")
            raise RepositoryException(f"Entry creation failed", context={"title": title, "error": str(e)})
    
    @CachePatterns.INVALIDATE_ENTRIES
    @timed_operation("update_entry", track_errors=True)
    async def update_with_analysis(
        self,
        entry_id: str,
        update_data: Dict[str, Any],
        regenerate_search_vector: bool = True
    ) -> Optional[Entry]:
        """Update entry with cache invalidation and search vector update"""
        try:
            entry = await self.get_by_id(entry_id, use_cache=False)
            if not entry:
                raise NotFoundException(f"Entry not found", context={"entry_id": entry_id})
            
            # Update content metrics if content changed
            if 'content' in update_data:
                content = update_data['content']
                update_data['word_count'] = len(content.split())
                update_data['reading_time_minutes'] = max(1, update_data['word_count'] // 200)
                update_data['character_count'] = len(content)
                
                regenerate_search_vector = True
            
            # Apply updates
            for key, value in update_data.items():
                if hasattr(entry, key):
                    setattr(entry, key, value)
            
            entry.updated_at = datetime.utcnow()
            
            await self.session.flush()
            
            # Regenerate search vector if needed
            if regenerate_search_vector:
                search_vector_query = text("""
                    UPDATE entries 
                    SET search_vector = to_tsvector('english', title || ' ' || content)
                    WHERE id = :entry_id
                """)
                
                await self.session.execute(search_vector_query, {"entry_id": entry_id})
            
            await self.session.refresh(entry)
            
            logger.info(f"Updated entry {entry_id}")
            return entry
            
        except Exception as e:
            logger.error(f"Error updating entry: {e}")
            raise RepositoryException(f"Entry update failed", context={"entry_id": entry_id, "error": str(e)})
    
    @CachePatterns.INVALIDATE_ENTRIES
    async def toggle_favorite(self, entry_id: str) -> Optional[Entry]:
        """Toggle favorite status with cache invalidation"""
        try:
            entry = await self.get_by_id(entry_id, use_cache=False)
            if not entry:
                return None
            
            entry.is_favorite = not entry.is_favorite
            entry.updated_at = datetime.utcnow()
            
            await self.session.flush()
            await self.session.refresh(entry)
            
            logger.info(f"Toggled favorite status for entry {entry_id}: {entry.is_favorite}")
            return entry
            
        except Exception as e:
            logger.error(f"Error toggling favorite: {e}")
            raise RepositoryException(f"Toggle favorite failed", context={"entry_id": entry_id, "error": str(e)})
    
    async def _calculate_writing_streak(self, user_id: str) -> Dict[str, Any]:
        """Calculate writing streak statistics"""
        try:
            # Get dates with entries in the last 100 days
            streak_query = select(
                func.date(Entry.created_at).label('entry_date')
            ).where(
                and_(
                    Entry.user_id == user_id,
                    Entry.created_at >= datetime.utcnow() - timedelta(days=100),
                    Entry.deleted_at.is_(None)
                )
            ).group_by(func.date(Entry.created_at)).order_by(func.date(Entry.created_at).desc())
            
            result = await self.session.execute(streak_query)
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
                'total_active_days': len(entry_dates),
                'last_entry_date': entry_dates[0].isoformat() if entry_dates else None
            }
            
        except Exception as e:
            logger.error(f"Error calculating writing streak: {e}")
            return {'current_streak': 0, 'longest_streak': 0, 'total_active_days': 0}
    
    async def batch_update_search_vectors(self, batch_size: int = 1000) -> int:
        """
        Batch update search vectors for full-text search optimization
        Used for maintenance and migration tasks
        """
        try:
            update_query = text("""
                WITH batch AS (
                    SELECT id 
                    FROM entries 
                    WHERE search_vector IS NULL 
                    AND deleted_at IS NULL
                    LIMIT :batch_size
                )
                UPDATE entries 
                SET search_vector = to_tsvector('english', title || ' ' || content)
                WHERE id IN (SELECT id FROM batch)
            """)
            
            result = await self.session.execute(update_query, {"batch_size": batch_size})
            updated_count = result.rowcount
            
            logger.info(f"Updated search vectors for {updated_count} entries")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error batch updating search vectors: {e}")
            raise RepositoryException(f"Batch search vector update failed", context={"error": str(e)})
    
    @cached(ttl=300, key_prefix="entry_count", monitor_performance=True)
    async def get_entry_count(self, user_id: str, **filters) -> int:
        """Get entry count with caching for pagination"""
        try:
            conditions = [
                Entry.user_id == user_id,
                Entry.deleted_at.is_(None)
            ]
            
            # Apply filters
            for key, value in filters.items():
                if hasattr(Entry, key) and value is not None:
                    conditions.append(getattr(Entry, key) == value)
            
            count_query = select(func.count(Entry.id)).where(and_(*conditions))
            result = await self.session.execute(count_query)
            
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error getting entry count: {e}")
            return 0