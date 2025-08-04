# backend/app/repositories/journal.py - Journal Entry Repository

from datetime import date, datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.postgresql import JournalEntry, User
from app.repositories.base import BaseRepository

class JournalEntryRepository(BaseRepository[JournalEntry]):
    """Repository for journal entry operations with advanced querying"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, JournalEntry)
    
    async def get_by_user_id(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        include_archived: bool = False
    ) -> List[JournalEntry]:
        """Get journal entries for a specific user with filtering"""
        query = select(JournalEntry).where(JournalEntry.user_id == user_id)
        
        # Date filtering
        if start_date:
            query = query.where(JournalEntry.entry_date >= start_date)
        if end_date:
            query = query.where(JournalEntry.entry_date <= end_date)
        
        # Archive filtering
        if not include_archived:
            query = query.where(JournalEntry.is_archived == False)
        
        # Order by entry date (newest first)
        query = query.order_by(desc(JournalEntry.entry_date), desc(JournalEntry.created_at))
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_date_range(
        self, 
        user_id: str, 
        start_date: date, 
        end_date: date
    ) -> List[JournalEntry]:
        """Get entries within a specific date range"""
        query = select(JournalEntry).where(
            and_(
                JournalEntry.user_id == user_id,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date,
                JournalEntry.is_archived == False
            )
        ).order_by(asc(JournalEntry.entry_date))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def search_by_content(
        self, 
        user_id: str, 
        search_term: str, 
        limit: int = 20
    ) -> List[JournalEntry]:
        """Search entries by content using PostgreSQL full-text search"""
        query = select(JournalEntry).where(
            and_(
                JournalEntry.user_id == user_id,
                JournalEntry.content.contains(search_term),  # Simple contains for now
                JournalEntry.is_archived == False
            )
        ).order_by(desc(JournalEntry.created_at)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_mood_range(
        self, 
        user_id: str, 
        min_mood: float, 
        max_mood: float,
        limit: int = 50
    ) -> List[JournalEntry]:
        """Get entries within a mood score range"""
        query = select(JournalEntry).where(
            and_(
                JournalEntry.user_id == user_id,
                JournalEntry.mood_score >= min_mood,
                JournalEntry.mood_score <= max_mood,
                JournalEntry.is_archived == False
            )
        ).order_by(desc(JournalEntry.entry_date)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_tags(
        self, 
        user_id: str, 
        tags: List[str], 
        limit: int = 50
    ) -> List[JournalEntry]:
        """Get entries containing any of the specified tags"""
        query = select(JournalEntry).where(
            and_(
                JournalEntry.user_id == user_id,
                JournalEntry.tags.overlap(tags),  # PostgreSQL array overlap
                JournalEntry.is_archived == False
            )
        ).order_by(desc(JournalEntry.entry_date)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_analytics_summary(
        self, 
        user_id: str, 
        start_date: date, 
        end_date: date
    ) -> Dict[str, Any]:
        """Get analytics summary for date range"""
        # Count entries
        count_query = select(func.count(JournalEntry.id)).where(
            and_(
                JournalEntry.user_id == user_id,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date,
                JournalEntry.is_archived == False
            )
        )
        
        # Average mood
        mood_query = select(func.avg(JournalEntry.mood_score)).where(
            and_(
                JournalEntry.user_id == user_id,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date,
                JournalEntry.mood_score.isnot(None),
                JournalEntry.is_archived == False
            )
        )
        
        # Total words
        words_query = select(func.sum(JournalEntry.word_count)).where(
            and_(
                JournalEntry.user_id == user_id,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date,
                JournalEntry.is_archived == False
            )
        )
        
        # Execute queries
        count_result = await self.session.execute(count_query)
        mood_result = await self.session.execute(mood_query)
        words_result = await self.session.execute(words_query)
        
        return {
            "total_entries": count_result.scalar() or 0,
            "average_mood": round(mood_result.scalar() or 0, 2),
            "total_words": words_result.scalar() or 0,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat()
        }
    
    async def get_mood_trends(
        self, 
        user_id: str, 
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get daily mood trends for the last N days"""
        query = select(
            JournalEntry.entry_date,
            func.avg(JournalEntry.mood_score).label('avg_mood'),
            func.count(JournalEntry.id).label('entry_count')
        ).where(
            and_(
                JournalEntry.user_id == user_id,
                JournalEntry.entry_date >= date.today() - datetime.timedelta(days=days),
                JournalEntry.mood_score.isnot(None),
                JournalEntry.is_archived == False
            )
        ).group_by(JournalEntry.entry_date).order_by(JournalEntry.entry_date)
        
        result = await self.session.execute(query)
        return [
            {
                "date": row.entry_date.isoformat(),
                "average_mood": round(row.avg_mood, 2),
                "entry_count": row.entry_count
            }
            for row in result
        ]
    
    async def get_recent_entries(
        self, 
        user_id: str, 
        limit: int = 10
    ) -> List[JournalEntry]:
        """Get most recent entries for a user"""
        query = select(JournalEntry).where(
            and_(
                JournalEntry.user_id == user_id,
                JournalEntry.is_archived == False
            )
        ).order_by(desc(JournalEntry.created_at)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def archive_entry(self, entry_id: str) -> bool:
        """Archive an entry (soft delete)"""
        return await self.update(entry_id, is_archived=True, updated_at=datetime.now())
    
    async def unarchive_entry(self, entry_id: str) -> bool:
        """Unarchive an entry"""
        return await self.update(entry_id, is_archived=False, updated_at=datetime.now())
    
    async def update_analysis(
        self, 
        entry_id: str, 
        sentiment_analysis: Optional[Dict[str, Any]] = None,
        emotion_analysis: Optional[Dict[str, Any]] = None,
        topic_analysis: Optional[Dict[str, Any]] = None,
        psychology_insights: Optional[Dict[str, Any]] = None
    ) -> Optional[JournalEntry]:
        """Update AI analysis results for an entry"""
        update_data = {"updated_at": datetime.now()}
        
        if sentiment_analysis is not None:
            update_data["sentiment_analysis"] = sentiment_analysis
        if emotion_analysis is not None:
            update_data["emotion_analysis"] = emotion_analysis
        if topic_analysis is not None:
            update_data["topic_analysis"] = topic_analysis
        if psychology_insights is not None:
            update_data["psychology_insights"] = psychology_insights
        
        return await self.update(entry_id, **update_data)
