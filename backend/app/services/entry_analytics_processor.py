# backend/app/services/entry_analytics_processor.py - Lightweight Entry Analytics Processing

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.services.ai_emotion_service import ai_emotion_service, analyze_sentiment
from app.services.redis_service_simple import simple_redis_service
from app.core.cache_patterns import CachePatterns
from app.core.exceptions import AnalyticsException

logger = logging.getLogger(__name__)

class EntryAnalyticsProcessor:
    """
    Lightweight processor for computing analytics at entry creation time.
    Replaces expensive on-demand processing during analytics requests.
    """
    
    async def analyze_new_entry(
        self, 
        entry_id: str, 
        content: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Analyze a new entry and return sentiment/mood data for storage.
        This should be called during entry creation to pre-compute analytics.
        """
        try:
            start_time = datetime.now()
            
            # Perform sentiment analysis
            mood, sentiment_score = analyze_sentiment(content)
            
            # Perform emotion analysis for richer insights
            emotion_analysis = await ai_emotion_service.analyze_emotions(content)
            
            # Build analysis result
            analysis_result = {
                'mood': mood.value if hasattr(mood, 'value') else str(mood),
                'sentiment_score': sentiment_score,
                'primary_emotion': emotion_analysis.primary_emotion.emotion.value,
                'primary_emotion_confidence': emotion_analysis.primary_emotion.confidence,
                'secondary_emotions': [
                    {
                        'emotion': emotion.emotion.value,
                        'confidence': emotion.confidence
                    }
                    for emotion in emotion_analysis.secondary_emotions
                ],
                'word_count': len(content.split()),
                'analyzed_at': datetime.now().isoformat()
            }
            
            # Invalidate relevant analytics caches for this user
            await self.invalidate_analytics_cache(user_id)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Analyzed entry {entry_id} in {processing_time:.2f}s - mood: {mood}, sentiment: {sentiment_score:.2f}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing entry {entry_id}: {e}")
            raise AnalyticsException(
                f"Failed to analyze entry {entry_id}",
                context={"entry_id": entry_id, "user_id": user_id, "error": str(e)}
            )
    
    async def invalidate_analytics_cache(self, user_id: str) -> None:
        """
        Invalidate analytics cache entries for a user after new entry is added.
        This ensures fresh data while maintaining performance.
        """
        try:
            # Get cache keys that need invalidation
            cache_keys_to_invalidate = [
                CachePatterns.analytics_mood_trends(user_id, "30d"),
                CachePatterns.analytics_mood_trends(user_id, "7d"),
                CachePatterns.analytics_writing_stats(user_id, 30),
                CachePatterns.analytics_writing_stats(user_id, 7),
                # Add other relevant cache patterns as needed
            ]
            
            # Invalidate caches
            invalidated_count = 0
            for cache_key in cache_keys_to_invalidate:
                deleted = await simple_redis_service.delete(cache_key)
                if deleted:
                    invalidated_count += 1
            
            logger.debug(f"Invalidated {invalidated_count} analytics cache entries for user {user_id}")
            
        except Exception as e:
            # Don't let cache invalidation errors break entry creation
            logger.warning(f"Failed to invalidate analytics cache for user {user_id}: {e}")
    
    async def update_entry_analysis(
        self, 
        entry_id: str, 
        content: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Re-analyze an updated entry and invalidate caches.
        """
        try:
            # Same analysis as new entry
            analysis_result = await self.analyze_new_entry(entry_id, content, user_id)
            logger.info(f"Re-analyzed updated entry {entry_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error re-analyzing updated entry {entry_id}: {e}")
            raise AnalyticsException(
                f"Failed to re-analyze updated entry {entry_id}",
                context={"entry_id": entry_id, "user_id": user_id, "error": str(e)}
            )

# Global instance
entry_analytics_processor = EntryAnalyticsProcessor()