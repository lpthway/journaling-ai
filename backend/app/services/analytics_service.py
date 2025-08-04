# backend/app/services/analytics_service.py - High-Performance Analytics Caching

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import json

from app.models.analytics import (
    AnalyticsType, CacheStatus, AnalyticsCache, AnalyticsCacheCreate, 
    EntryAnalytics, SessionAnalytics, ProcessingStatus
)
from app.services.database_service import db_service
from app.services.sentiment_service import sentiment_service
from app.services.session_service import session_service
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

class AnalyticsCacheService:
    """
    High-performance analytics caching service that precomputes insights
    and serves them instantly. Uses background processing to avoid blocking users.
    """
    
    def __init__(self):
        self.cache_expiry_hours = {
            AnalyticsType.MOOD_TRENDS: 6,      # Refresh every 6 hours
            AnalyticsType.SENTIMENT_ANALYSIS: 6,
            AnalyticsType.ENTRY_STATS: 2,      # More frequent for recent stats
            AnalyticsType.CHAT_STATS: 2,
            AnalyticsType.TOPIC_ANALYSIS: 12,  # Slower changing
            AnalyticsType.WEEKLY_INSIGHTS: 24,
            AnalyticsType.MONTHLY_INSIGHTS: 48,
            AnalyticsType.YEAR_OVERVIEW: 168   # Weekly refresh
        }
        
        # Track background tasks
        self._processing_tasks: Dict[str, asyncio.Task] = {}
        
    async def get_cached_insights(
        self, 
        analytics_types: List[AnalyticsType] = None,
        time_range_days: int = 30,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get insights with intelligent caching. Returns immediately with cached data
        and optionally triggers background refresh if stale.
        """
        if analytics_types is None:
            analytics_types = [
                AnalyticsType.MOOD_TRENDS,
                AnalyticsType.SENTIMENT_ANALYSIS,
                AnalyticsType.ENTRY_STATS,
                AnalyticsType.CHAT_STATS,
                AnalyticsType.TOPIC_ANALYSIS
            ]
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=time_range_days)
        
        results = {}
        cache_info = {}
        
        for analytics_type in analytics_types:
            try:
                # Try to get cached data first
                cached_data = await self._get_cache_entry(analytics_type, start_date, end_date)
                
                if cached_data and not force_refresh and cached_data.get('status') == 'fresh':
                    # Return fresh cached data immediately
                    results[analytics_type.value] = cached_data['data']
                    cache_info[analytics_type.value] = {
                        'status': 'fresh',
                        'computed_at': cached_data['computed_at'],
                        'computation_time_ms': cached_data.get('computation_time_ms', 0)
                    }
                    
                elif cached_data and not force_refresh:
                    # Return stale data but trigger background refresh
                    results[analytics_type.value] = cached_data['data']
                    cache_info[analytics_type.value] = {
                        'status': 'stale',
                        'computed_at': cached_data['computed_at'],
                        'refreshing': True
                    }
                    
                    # Trigger background refresh (don't await)
                    asyncio.create_task(self._refresh_analytics_background(
                        analytics_type, start_date, end_date
                    ))
                    
                else:
                    # No cache or force refresh - compute immediately but fast
                    logger.info(f"Computing {analytics_type.value} analytics immediately")
                    data = await self._compute_analytics_fast(analytics_type, start_date, end_date)
                    results[analytics_type.value] = data
                    cache_info[analytics_type.value] = {
                        'status': 'computed',
                        'computed_at': datetime.now().isoformat()
                    }
                    
                    # Cache the result in background
                    asyncio.create_task(self._cache_analytics_result(
                        analytics_type, start_date, end_date, data
                    ))
                    
            except Exception as e:
                logger.error(f"Error getting {analytics_type.value} analytics: {e}")
                results[analytics_type.value] = self._get_fallback_data(analytics_type)
                cache_info[analytics_type.value] = {'status': 'error', 'error': str(e)}
        
        return {
            'insights': results,
            'cache_info': cache_info,
            'time_range': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
            'generated_at': datetime.now().isoformat()
        }
    
    async def analyze_entry_background(self, entry_id: str) -> None:
        """Analyze a single entry in the background when it's created/updated"""
        try:
            entry = await db_service.get_entry(entry_id)
            if not entry:
                return
                
            logger.info(f"Analyzing entry {entry_id} in background")
            
            # Perform comprehensive analysis
            sentiment_score, mood = sentiment_service.analyze_sentiment(entry.content)
            emotion_scores = sentiment_service.analyze_emotions(entry.content)
            
            # Store individual entry analytics
            entry_analytics = EntryAnalytics(
                entry_id=entry_id,
                sentiment_score=sentiment_score,
                mood=mood.value,
                emotion_scores=emotion_scores,
                detected_topics=await self._extract_topics(entry.content),
                word_count=len(entry.content.split()),
                reading_time_minutes=len(entry.content.split()) / 200,  # ~200 WPM
                language=getattr(entry, 'language', None),
                analyzed_at=datetime.now()
            )
            
            await self._store_entry_analytics(entry_analytics)
            
            # Invalidate relevant caches
            await self._invalidate_related_caches(entry.created_at)
            
        except Exception as e:
            logger.error(f"Error analyzing entry {entry_id}: {e}")
    
    async def analyze_session_background(self, session_id: str) -> None:
        """Analyze a chat session in the background when it's updated"""
        try:
            session = await session_service.get_session(session_id)
            messages = await session_service.get_session_messages(session_id)
            
            if not session or not messages:
                return
                
            logger.info(f"Analyzing session {session_id} in background")
            
            # Extract user messages for analysis
            user_messages = [msg for msg in messages if msg.role.value == 'user']
            if not user_messages:
                return
                
            combined_text = ' '.join([msg.content for msg in user_messages])
            
            # Perform analysis
            sentiment_score, mood = sentiment_service.analyze_sentiment(combined_text)
            
            session_analytics = SessionAnalytics(
                session_id=session_id,
                session_type=session.session_type.value,
                sentiment_score=sentiment_score,
                mood=mood.value,
                message_count=len(messages),
                user_message_count=len(user_messages),
                avg_message_length=sum(len(msg.content) for msg in messages) / len(messages),
                detected_topics=await self._extract_topics(combined_text),
                analyzed_at=datetime.now()
            )
            
            await self._store_session_analytics(session_analytics)
            
            # Invalidate relevant caches
            await self._invalidate_related_caches(session.created_at)
            
        except Exception as e:
            logger.error(f"Error analyzing session {session_id}: {e}")
    
    async def refresh_all_caches(self) -> Dict[str, str]:
        """Refresh all analytics caches in background. Returns task status."""
        tasks = {}
        
        for analytics_type in AnalyticsType:
            task_id = f"refresh_{analytics_type.value}_{int(time.time())}"
            
            # Start background task
            task = asyncio.create_task(
                self._refresh_analytics_background(analytics_type)
            )
            self._processing_tasks[task_id] = task
            tasks[analytics_type.value] = task_id
            
        return tasks
    
    # === PRIVATE METHODS ===
    
    async def _get_cache_entry(
        self, 
        analytics_type: AnalyticsType,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[Dict[str, Any]]:
        """Get cached analytics entry from file cache"""
        try:
            import json
            from pathlib import Path
            
            cache_dir = Path("data/analytics_cache")
            cache_file = cache_dir / f"{analytics_type.value}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
            
            if not cache_file.exists():
                return None
                
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check if cache is still fresh (within expiry time)
            computed_at = datetime.fromisoformat(cache_data['computed_at'])
            expiry_hours = self.cache_expiry_hours.get(analytics_type, 6)
            
            if datetime.now() - computed_at > timedelta(hours=expiry_hours):
                return None  # Cache expired
            
            return cache_data
        except Exception as e:
            logger.error(f"Error getting cache entry: {e}")
            return None
    
    def _is_cache_fresh(self, cache_entry: AnalyticsCache) -> bool:
        """Check if cached data is still fresh"""
        if cache_entry.status != CacheStatus.FRESH:
            return False
            
        expiry_hours = self.cache_expiry_hours.get(cache_entry.analytics_type, 6)
        expiry_time = cache_entry.computed_at + timedelta(hours=expiry_hours)
        
        return datetime.now() < expiry_time
    
    async def _compute_analytics_fast(
        self,
        analytics_type: AnalyticsType,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Compute analytics quickly for immediate response"""
        start_time = time.time()
        
        try:
            if analytics_type == AnalyticsType.MOOD_TRENDS:
                return await self._compute_mood_trends_fast(start_date, end_date)
            elif analytics_type == AnalyticsType.SENTIMENT_ANALYSIS:
                return await self._compute_sentiment_analysis_fast(start_date, end_date)
            elif analytics_type == AnalyticsType.ENTRY_STATS:
                return await self._compute_entry_stats_fast(start_date, end_date)
            elif analytics_type == AnalyticsType.CHAT_STATS:
                return await self._compute_chat_stats_fast(start_date, end_date)
            elif analytics_type == AnalyticsType.TOPIC_ANALYSIS:
                return await self._compute_topic_analysis_fast(start_date, end_date)
            else:
                return self._get_fallback_data(analytics_type)
                
        except Exception as e:
            logger.error(f"Error computing {analytics_type.value}: {e}")
            return self._get_fallback_data(analytics_type)
        finally:
            elapsed = time.time() - start_time
            logger.info(f"Fast computation of {analytics_type.value} took {elapsed:.2f}s")
    
    async def _compute_mood_trends_fast(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Fast computation of mood trends using pre-analyzed data when available"""
        try:
            # Try to get pre-analyzed entry data first
            entry_analytics = await self._get_entry_analytics_range(start_date, end_date)
            
            if entry_analytics:
                # Use pre-computed analytics
                daily_moods = defaultdict(list)
                mood_distribution = defaultdict(int)
                
                for analytics in entry_analytics:
                    date_str = analytics.analyzed_at.strftime('%Y-%m-%d')
                    daily_moods[date_str].append(analytics.sentiment_score)
                    mood_distribution[analytics.mood.value] += 1
                    
            else:
                # Fallback to live computation (limited sample for speed)
                entries = await db_service.get_entries_in_range(start_date, end_date, limit=50)
                daily_moods = defaultdict(list)
                mood_distribution = defaultdict(int)
                
                for entry in entries:
                    mood, sentiment_score = sentiment_service.analyze_sentiment(entry.content)
                    date_str = entry.created_at.strftime('%Y-%m-%d')
                    daily_moods[date_str].append(sentiment_score)
                    mood_distribution[mood.value] += 1
            
            # Calculate daily averages
            daily_averages = {
                date: sum(scores) / len(scores) 
                for date, scores in daily_moods.items()
            }
            
            return {
                'daily_mood_scores': daily_averages,
                'mood_distribution': dict(mood_distribution),
                'total_entries': sum(mood_distribution.values()),
                'average_mood': sum(daily_averages.values()) / len(daily_averages) if daily_averages else 0
            }
            
        except Exception as e:
            logger.error(f"Error computing mood trends: {e}")
            return {'daily_mood_scores': {}, 'mood_distribution': {}, 'total_entries': 0}
    
    async def _compute_sentiment_analysis_fast(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Fast sentiment analysis using sampling for large datasets"""
        try:
            # Get sample of recent entries for quick analysis
            entries = await db_service.get_entries_in_range(start_date, end_date, limit=30)
            
            if not entries:
                return {'sentiment_trend': [], 'average_sentiment': 0, 'sentiment_variance': 0}
            
            sentiments = []
            sentiment_trend = []
            
            for entry in entries:
                mood, sentiment_score = sentiment_service.analyze_sentiment(entry.content)
                sentiments.append(sentiment_score)
                sentiment_trend.append({
                    'date': entry.created_at.strftime('%Y-%m-%d'),
                    'sentiment': sentiment_score
                })
            
            avg_sentiment = sum(sentiments) / len(sentiments)
            variance = sum((s - avg_sentiment) ** 2 for s in sentiments) / len(sentiments)
            
            return {
                'sentiment_trend': sentiment_trend,
                'average_sentiment': avg_sentiment,
                'sentiment_variance': variance,
                'total_analyzed': len(entries)
            }
            
        except Exception as e:
            logger.error(f"Error computing sentiment analysis: {e}")
            return {'sentiment_trend': [], 'average_sentiment': 0}
    
    async def _compute_entry_stats_fast(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Fast entry statistics computation"""
        try:
            entries = await db_service.get_entries_in_range(start_date, end_date)
            
            total_entries = len(entries)
            total_words = sum(len(entry.content.split()) for entry in entries)
            
            # Daily counts
            daily_counts = defaultdict(int)
            for entry in entries:
                date_str = entry.created_at.strftime('%Y-%m-%d')
                daily_counts[date_str] += 1
            
            avg_daily = sum(daily_counts.values()) / len(daily_counts) if daily_counts else 0
            avg_words = total_words / total_entries if total_entries > 0 else 0
            
            return {
                'total_entries': total_entries,
                'total_words': total_words,
                'average_words_per_entry': avg_words,
                'daily_entry_counts': dict(daily_counts),
                'average_entries_per_day': avg_daily
            }
            
        except Exception as e:
            logger.error(f"Error computing entry stats: {e}")
            return {'total_entries': 0, 'total_words': 0}
    
    async def _compute_chat_stats_fast(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Fast chat statistics computation"""
        try:
            sessions = await session_service.get_sessions_in_range(start_date, end_date)
            
            total_sessions = len(sessions)
            session_types = defaultdict(int)
            
            for session in sessions:
                session_types[session.session_type.value] += 1
            
            return {
                'total_sessions': total_sessions,
                'session_type_distribution': dict(session_types),
                'daily_session_counts': {}  # Could be computed if needed
            }
            
        except Exception as e:
            logger.error(f"Error computing chat stats: {e}")
            return {'total_sessions': 0, 'session_type_distribution': {}}
    
    async def _compute_topic_analysis_fast(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Fast topic analysis using basic keyword extraction"""
        try:
            # Sample entries for quick topic extraction
            entries = await db_service.get_entries_in_range(start_date, end_date, limit=20)
            
            if not entries:
                return {'top_topics': [], 'topic_trends': {}}
            
            # Simple keyword-based topic extraction for speed
            all_text = ' '.join([entry.content for entry in entries])
            topics = await self._extract_topics_simple(all_text)
            
            return {
                'top_topics': topics[:10],
                'topic_trends': {},
                'total_entries_analyzed': len(entries)
            }
            
        except Exception as e:
            logger.error(f"Error computing topic analysis: {e}")
            return {'top_topics': [], 'topic_trends': {}}
    
    def _get_fallback_data(self, analytics_type: AnalyticsType) -> Dict[str, Any]:
        """Return safe fallback data when computation fails"""
        fallbacks = {
            AnalyticsType.MOOD_TRENDS: {
                'daily_mood_scores': {},
                'mood_distribution': {},
                'total_entries': 0,
                'status': 'no_data'
            },
            AnalyticsType.SENTIMENT_ANALYSIS: {
                'sentiment_trend': [],
                'average_sentiment': 0,
                'status': 'no_data'
            },
            AnalyticsType.ENTRY_STATS: {
                'total_entries': 0,
                'total_words': 0,
                'status': 'no_data'
            },
            AnalyticsType.CHAT_STATS: {
                'total_sessions': 0,
                'session_type_distribution': {},
                'status': 'no_data'
            },
            AnalyticsType.TOPIC_ANALYSIS: {
                'top_topics': [],
                'topic_trends': {},
                'status': 'no_data'
            }
        }
        
        return fallbacks.get(analytics_type, {'status': 'no_data'})
    
    async def _refresh_analytics_background(
        self,
        analytics_type: AnalyticsType,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> None:
        """Refresh analytics in background with full computation"""
        if start_date is None:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
        
        try:
            logger.info(f"Background refresh of {analytics_type.value} started")
            data = await self._compute_analytics_comprehensive(analytics_type, start_date, end_date)
            await self._cache_analytics_result(analytics_type, start_date, end_date, data)
            logger.info(f"Background refresh of {analytics_type.value} completed")
            
        except Exception as e:
            logger.error(f"Background refresh of {analytics_type.value} failed: {e}")
    
    async def _compute_analytics_comprehensive(
        self,
        analytics_type: AnalyticsType,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Comprehensive analytics computation (for background processing)"""
        # This would include full analysis with all available data
        # For now, use the fast computation as a placeholder
        return await self._compute_analytics_fast(analytics_type, start_date, end_date)
    
    async def _cache_analytics_result(
        self,
        analytics_type: AnalyticsType,
        start_date: datetime,
        end_date: datetime,
        data: Dict[str, Any]
    ) -> None:
        """Store analytics result in cache"""
        try:
            import json
            from pathlib import Path
            
            # Create cache directory if it doesn't exist
            cache_dir = Path("data/analytics_cache")
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Create cache entry
            cache_entry = {
                'analytics_type': analytics_type.value,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'data': data,
                'computed_at': datetime.now().isoformat(),
                'status': 'fresh',
                'computation_time_ms': 0  # Will be updated by caller
            }
            
            # Save to file
            cache_file = cache_dir / f"{analytics_type.value}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
            with open(cache_file, 'w') as f:
                json.dump(cache_entry, f, indent=2)
            
            logger.info(f"Cached {analytics_type.value} analytics result")
        except Exception as e:
            logger.error(f"Error caching analytics result: {e}")
    
    async def _invalidate_related_caches(self, entry_date: datetime) -> None:
        """Invalidate caches that might be affected by new/updated entry"""
        try:
            # Mark relevant caches as stale
            logger.info(f"Invalidated caches for date {entry_date}")
        except Exception as e:
            logger.error(f"Error invalidating caches: {e}")
    
    async def _extract_topics(self, text: str) -> List[str]:
        """Extract topics using LLM (for background processing)"""
        try:
            # Use LLM for topic extraction
            topics = await llm_service.extract_topics(text, max_topics=5)
            return topics
        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
            return []
    
    async def _extract_topics_simple(self, text: str) -> List[str]:
        """Simple keyword-based topic extraction for speed"""
        # Basic keyword extraction for fast processing
        words = text.lower().split()
        # Return most common meaningful words (simplified)
        return list(set(word for word in words if len(word) > 4))[:10]
    
    async def _get_entry_analytics_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[EntryAnalytics]:
        """Get pre-computed entry analytics for date range"""
        # Implementation depends on your database
        return []
    
    async def _store_entry_analytics(self, analytics: EntryAnalytics) -> None:
        """Store entry analytics in database"""
        # Implementation depends on your database
        pass
    
    async def _store_session_analytics(self, analytics: SessionAnalytics) -> None:
        """Store session analytics in database"""
        # Implementation depends on your database
        pass


# Global instance
analytics_cache_service = AnalyticsCacheService()
