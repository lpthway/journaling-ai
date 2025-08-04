# backend/app/repositories/analytics.py - Analytics Repository

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, desc, asc, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgresql import UserAnalytics, JournalEntry, Conversation, ChatSession
from app.repositories.base import BaseRepository

class AnalyticsRepository(BaseRepository[UserAnalytics]):
    """Repository for analytics operations with pre-computed metrics"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserAnalytics)
    
    async def get_user_analytics(
        self, 
        user_id: str, 
        period_type: str = "monthly",
        limit: int = 12
    ) -> List[UserAnalytics]:
        """Get analytics for a user by period type"""
        query = select(UserAnalytics).where(
            and_(
                UserAnalytics.user_id == user_id,
                UserAnalytics.period_type == period_type
            )
        ).order_by(desc(UserAnalytics.period_start)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_latest_analytics(
        self, 
        user_id: str
    ) -> Dict[str, Optional[UserAnalytics]]:
        """Get the latest analytics for each period type"""
        period_types = ["daily", "weekly", "monthly", "yearly"]
        results = {}
        
        for period_type in period_types:
            query = select(UserAnalytics).where(
                and_(
                    UserAnalytics.user_id == user_id,
                    UserAnalytics.period_type == period_type
                )
            ).order_by(desc(UserAnalytics.period_start)).limit(1)
            
            result = await self.session.execute(query)
            results[period_type] = result.scalar_one_or_none()
        
        return results
    
    async def compute_daily_analytics(
        self, 
        user_id: str, 
        target_date: date
    ) -> Optional[UserAnalytics]:
        """Compute and store daily analytics"""
        start_time = datetime.now()
        
        # Get entries for the day
        entries_query = select(JournalEntry).where(
            and_(
                JournalEntry.user_id == user_id,
                JournalEntry.entry_date == target_date,
                JournalEntry.is_archived == False
            )
        )
        
        entries_result = await self.session.execute(entries_query)
        entries = entries_result.scalars().all()
        
        if not entries:
            return None
        
        # Calculate basic stats
        total_entries = len(entries)
        total_words = sum(entry.word_count for entry in entries)
        mood_scores = [entry.mood_score for entry in entries if entry.mood_score is not None]
        avg_mood = sum(mood_scores) / len(mood_scores) if mood_scores else None
        
        # Aggregate sentiment analysis
        sentiment_trends = self._aggregate_sentiment_data(entries)
        emotion_patterns = self._aggregate_emotion_data(entries)
        topic_distribution = self._aggregate_topic_data(entries)
        
        # Create or update analytics record
        existing = await self.session.execute(
            select(UserAnalytics).where(
                and_(
                    UserAnalytics.user_id == user_id,
                    UserAnalytics.period_type == "daily",
                    UserAnalytics.period_start == target_date
                )
            )
        )
        
        analytics_record = existing.scalar_one_or_none()
        computation_time = (datetime.now() - start_time).total_seconds() * 1000
        
        if analytics_record:
            # Update existing
            analytics_record.total_entries = total_entries
            analytics_record.total_words = total_words
            analytics_record.avg_mood = avg_mood
            analytics_record.sentiment_trends = sentiment_trends
            analytics_record.emotion_patterns = emotion_patterns
            analytics_record.topic_distribution = topic_distribution
            analytics_record.computation_time_ms = computation_time
            analytics_record.data_freshness = datetime.now()
            analytics_record.updated_at = datetime.now()
        else:
            # Create new
            analytics_record = UserAnalytics(
                user_id=user_id,
                period_type="daily",
                period_start=target_date,
                period_end=target_date,
                total_entries=total_entries,
                total_words=total_words,
                avg_mood=avg_mood,
                sentiment_trends=sentiment_trends,
                emotion_patterns=emotion_patterns,
                topic_distribution=topic_distribution,
                computation_time_ms=computation_time,
                data_freshness=datetime.now()
            )
            self.session.add(analytics_record)
        
        await self.session.commit()
        await self.session.refresh(analytics_record)
        return analytics_record
    
    async def compute_weekly_analytics(
        self, 
        user_id: str, 
        week_start: date
    ) -> Optional[UserAnalytics]:
        """Compute and store weekly analytics"""
        week_end = week_start + timedelta(days=6)
        start_time = datetime.now()
        
        # Get entries for the week
        entries_query = select(JournalEntry).where(
            and_(
                JournalEntry.user_id == user_id,
                JournalEntry.entry_date >= week_start,
                JournalEntry.entry_date <= week_end,
                JournalEntry.is_archived == False
            )
        )
        
        entries_result = await self.session.execute(entries_query)
        entries = entries_result.scalars().all()
        
        if not entries:
            return None
        
        # Calculate weekly metrics
        total_entries = len(entries)
        total_words = sum(entry.word_count for entry in entries)
        mood_scores = [entry.mood_score for entry in entries if entry.mood_score is not None]
        avg_mood = sum(mood_scores) / len(mood_scores) if mood_scores else None
        
        # Calculate writing consistency (days with entries / 7)
        unique_dates = set(entry.entry_date for entry in entries)
        writing_consistency = len(unique_dates) / 7.0
        
        # Calculate most active days
        day_counts = {}
        for entry in entries:
            day_name = entry.entry_date.strftime('%A')
            day_counts[day_name] = day_counts.get(day_name, 0) + 1
        
        most_active_days = sorted(day_counts.keys(), key=lambda x: day_counts[x], reverse=True)[:3]
        
        # Aggregate analysis data
        sentiment_trends = self._aggregate_sentiment_data(entries)
        emotion_patterns = self._aggregate_emotion_data(entries)
        topic_distribution = self._aggregate_topic_data(entries)
        
        computation_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Create or update record
        existing = await self.session.execute(
            select(UserAnalytics).where(
                and_(
                    UserAnalytics.user_id == user_id,
                    UserAnalytics.period_type == "weekly",
                    UserAnalytics.period_start == week_start
                )
            )
        )
        
        analytics_record = existing.scalar_one_or_none()
        
        if analytics_record:
            # Update existing
            analytics_record.total_entries = total_entries
            analytics_record.total_words = total_words
            analytics_record.avg_mood = avg_mood
            analytics_record.writing_consistency = writing_consistency
            analytics_record.most_active_days = most_active_days
            analytics_record.sentiment_trends = sentiment_trends
            analytics_record.emotion_patterns = emotion_patterns
            analytics_record.topic_distribution = topic_distribution
            analytics_record.computation_time_ms = computation_time
            analytics_record.data_freshness = datetime.now()
            analytics_record.updated_at = datetime.now()
        else:
            # Create new
            analytics_record = UserAnalytics(
                user_id=user_id,
                period_type="weekly",
                period_start=week_start,
                period_end=week_end,
                total_entries=total_entries,
                total_words=total_words,
                avg_mood=avg_mood,
                writing_consistency=writing_consistency,
                most_active_days=most_active_days,
                sentiment_trends=sentiment_trends,
                emotion_patterns=emotion_patterns,
                topic_distribution=topic_distribution,
                computation_time_ms=computation_time,
                data_freshness=datetime.now()
            )
            self.session.add(analytics_record)
        
        await self.session.commit()
        await self.session.refresh(analytics_record)
        return analytics_record
    
    async def get_performance_summary(self, user_id: str) -> Dict[str, Any]:
        """Get analytics computation performance summary"""
        # Average computation times by period type
        avg_times_query = select(
            UserAnalytics.period_type,
            func.avg(UserAnalytics.computation_time_ms).label('avg_time'),
            func.count(UserAnalytics.id).label('count')
        ).where(
            UserAnalytics.user_id == user_id
        ).group_by(UserAnalytics.period_type)
        
        result = await self.session.execute(avg_times_query)
        performance_data = {
            row.period_type: {
                "average_computation_ms": round(row.avg_time, 2),
                "total_computations": row.count
            }
            for row in result
        }
        
        # Data freshness
        freshness_query = select(
            UserAnalytics.period_type,
            func.max(UserAnalytics.data_freshness).label('latest_update')
        ).where(
            UserAnalytics.user_id == user_id
        ).group_by(UserAnalytics.period_type)
        
        freshness_result = await self.session.execute(freshness_query)
        freshness_data = {
            row.period_type: row.latest_update.isoformat() if row.latest_update else None
            for row in freshness_result
        }
        
        return {
            "performance_metrics": performance_data,
            "data_freshness": freshness_data,
            "target_performance_ms": 50  # Our target from config
        }
    
    def _aggregate_sentiment_data(self, entries: List[JournalEntry]) -> Dict[str, Any]:
        """Aggregate sentiment analysis data from entries"""
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        sentiment_scores = []
        
        for entry in entries:
            if entry.sentiment_analysis:
                sentiment = entry.sentiment_analysis.get("sentiment", "neutral")
                sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
                
                score = entry.sentiment_analysis.get("score", 0.5)
                sentiment_scores.append(score)
        
        return {
            "distribution": sentiment_counts,
            "average_score": sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0,
            "total_analyzed": len([e for e in entries if e.sentiment_analysis])
        }
    
    def _aggregate_emotion_data(self, entries: List[JournalEntry]) -> Dict[str, Any]:
        """Aggregate emotion analysis data from entries"""
        emotion_counts = {}
        
        for entry in entries:
            if entry.emotion_analysis and "emotions" in entry.emotion_analysis:
                emotions = entry.emotion_analysis["emotions"]
                for emotion, score in emotions.items():
                    if emotion not in emotion_counts:
                        emotion_counts[emotion] = []
                    emotion_counts[emotion].append(score)
        
        # Calculate averages
        emotion_averages = {
            emotion: sum(scores) / len(scores)
            for emotion, scores in emotion_counts.items()
            if scores
        }
        
        return {
            "average_emotions": emotion_averages,
            "total_analyzed": len([e for e in entries if e.emotion_analysis])
        }
    
    def _aggregate_topic_data(self, entries: List[JournalEntry]) -> Dict[str, Any]:
        """Aggregate topic analysis data from entries"""
        topic_counts = {}
        
        for entry in entries:
            if entry.topic_analysis and "topics" in entry.topic_analysis:
                topics = entry.topic_analysis["topics"]
                for topic in topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # Sort by frequency
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "topic_frequency": dict(sorted_topics[:10]),  # Top 10 topics
            "total_topics": len(topic_counts),
            "total_analyzed": len([e for e in entries if e.topic_analysis])
        }
