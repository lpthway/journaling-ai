# backend/app/services/personality_analytics_processor.py - Personality Analytics Processing

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.services.redis_service_simple import simple_redis_service
from app.core.cache_patterns import CachePatterns
from app.core.exceptions import AnalyticsException

logger = logging.getLogger(__name__)

class PersonalityAnalyticsProcessor:
    """
    Lightweight processor for managing personality analysis caches.
    Ensures personality profiles are invalidated when entries are added/updated.
    """
    
    async def invalidate_personality_cache(self, user_id: str) -> None:
        """
        Invalidate personality analysis cache for a user after new entry is added.
        This ensures personality profiles reflect the latest entries.
        """
        try:
            # Get cache keys that need invalidation for personality analysis
            cache_keys_to_invalidate = [
                f"personality_{user_id}*",  # All personality cache keys for user
                f"ai_analysis:personality*{user_id}*",  # AI analysis cache patterns
                f"advanced_ai:personality:{user_id}*",  # Advanced AI cache patterns
            ]
            
            # Invalidate caches using pattern matching
            invalidated_count = 0
            for pattern in cache_keys_to_invalidate:
                deleted = await simple_redis_service.invalidate_pattern(pattern)
                invalidated_count += deleted
            
            logger.debug(f"Invalidated {invalidated_count} personality cache entries for user {user_id}")
            
        except Exception as e:
            # Don't let cache invalidation errors break entry creation
            logger.warning(f"Failed to invalidate personality cache for user {user_id}: {e}")
    
    async def get_stored_emotion_data(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract stored emotion analysis data from entries to avoid recomputation.
        
        Args:
            entries: List of entry dictionaries with emotion_analysis field
            
        Returns:
            List of emotion data extracted from stored analysis
        """
        try:
            emotion_data = []
            
            for entry in entries:
                # Check if entry already has emotion analysis stored
                emotion_analysis = entry.get('emotion_analysis')
                if emotion_analysis and isinstance(emotion_analysis, dict):
                    # Extract emotion data from stored analysis
                    emotion_data.append({
                        'entry_id': entry.get('id'),
                        'primary_emotion': emotion_analysis.get('primary_emotion'),
                        'confidence': emotion_analysis.get('confidence', 0.5),
                        'secondary_emotions': emotion_analysis.get('secondary_emotions', []),
                        'sentiment_polarity': emotion_analysis.get('sentiment_polarity', 0.0),
                        'emotional_complexity': emotion_analysis.get('emotional_complexity', 0.0),
                        'created_at': entry.get('created_at'),
                        'content_length': len(entry.get('content', ''))
                    })
                else:
                    # Entry doesn't have emotion analysis stored - this shouldn't happen
                    # with our analytics optimization, but handle gracefully
                    logger.warning(f"Entry {entry.get('id', 'unknown')} missing emotion analysis data")
                    
            logger.debug(f"Retrieved stored emotion data for {len(emotion_data)} entries (avoided recomputation)")
            return emotion_data
            
        except Exception as e:
            logger.error(f"Error retrieving stored emotion data: {e}")
            raise AnalyticsException(
                "Failed to retrieve stored emotion data",
                context={"error": str(e), "entry_count": len(entries)}
            )

    async def calculate_personality_dimensions_from_stored_data(
        self, 
        emotion_data: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate Big Five personality dimensions from stored emotion data.
        This replaces the expensive individual entry emotion analysis.
        
        Args:
            emotion_data: Pre-computed emotion analysis data
            
        Returns:
            Dictionary of personality dimension scores
        """
        try:
            # Initialize dimension scores
            dimensions = {
                'extraversion': 0.0,
                'neuroticism': 0.0,
                'openness': 0.0,
                'conscientiousness': 0.0,
                'agreeableness': 0.0
            }
            
            if not emotion_data:
                logger.warning("No emotion data available for personality calculation")
                return dimensions
                
            # Calculate dimensions based on emotion patterns
            total_entries = len(emotion_data)
            
            # Emotion to dimension mapping (simplified but effective)
            emotion_weights = {
                'joy': {'extraversion': 0.3, 'agreeableness': 0.2},
                'sadness': {'neuroticism': 0.4, 'extraversion': -0.2},
                'fear': {'neuroticism': 0.5, 'openness': -0.1},
                'anger': {'neuroticism': 0.3, 'agreeableness': -0.3},
                'surprise': {'openness': 0.3, 'extraversion': 0.1},
                'disgust': {'agreeableness': -0.2, 'neuroticism': 0.2},
                'neutral': {'conscientiousness': 0.1}
            }
            
            # Process each emotion entry
            for entry in emotion_data:
                primary_emotion = entry.get('primary_emotion', 'neutral')
                confidence = entry.get('confidence', 0.5)
                sentiment = entry.get('sentiment_polarity', 0.0)
                
                # Apply emotion weights
                if primary_emotion in emotion_weights:
                    for dimension, weight in emotion_weights[primary_emotion].items():
                        dimensions[dimension] += weight * confidence
                
                # Factor in sentiment polarity
                if sentiment > 0.2:  # Positive sentiment
                    dimensions['extraversion'] += 0.1
                    dimensions['agreeableness'] += 0.1
                elif sentiment < -0.2:  # Negative sentiment
                    dimensions['neuroticism'] += 0.1
                
                # Content length suggests conscientiousness
                content_length = entry.get('content_length', 0)
                if content_length > 500:  # Longer entries suggest conscientiousness
                    dimensions['conscientiousness'] += 0.05
            
            # Normalize dimensions to 0-1 range
            for dimension in dimensions:
                # Convert to percentage and normalize
                raw_score = dimensions[dimension] / total_entries
                dimensions[dimension] = max(0.0, min(1.0, 0.5 + raw_score))
            
            logger.debug(f"Calculated personality dimensions from {total_entries} stored emotion analyses")
            return dimensions
            
        except Exception as e:
            logger.error(f"Error calculating personality dimensions: {e}")
            raise AnalyticsException(
                "Failed to calculate personality dimensions",
                context={"error": str(e), "data_count": len(emotion_data)}
            )

# Global instance
personality_analytics_processor = PersonalityAnalyticsProcessor()