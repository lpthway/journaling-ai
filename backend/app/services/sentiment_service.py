### app/services/sentiment_service.py

from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
from textblob import TextBlob
from typing import Tuple
import logging
from app.models.entry import MoodType
from app.core.config import settings

logger = logging.getLogger(__name__)

class SentimentService:
    def __init__(self):
        try:
            # Initialize RoBERTa sentiment model for more accurate analysis
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                tokenizer="cardiffnlp/twitter-roberta-base-sentiment-latest"
            )
        except Exception as e:
            logger.warning(f"Could not load RoBERTa model, falling back to TextBlob: {e}")
            self.sentiment_pipeline = None
    
    def analyze_sentiment(self, text: str) -> Tuple[MoodType, float]:
        """Analyze sentiment and return mood type and confidence score"""
        try:
            if self.sentiment_pipeline:
                return self._analyze_with_roberta(text)
            else:
                return self._analyze_with_textblob(text)
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return MoodType.NEUTRAL, 0.5
    
    def _analyze_with_roberta(self, text: str) -> Tuple[MoodType, float]:
        """Analyze sentiment using RoBERTa model"""
        try:
            # Truncate text if too long
            if len(text) > 512:
                text = text[:512]
            
            result = self.sentiment_pipeline(text)[0]
            label = result['label'].lower()
            score = result['score']
            
            # Map RoBERTa labels to mood types
            if label == 'label_2' or 'positive' in label:  # Positive
                if score > 0.8:
                    return MoodType.VERY_POSITIVE, score
                else:
                    return MoodType.POSITIVE, score
            elif label == 'label_0' or 'negative' in label:  # Negative
                if score > 0.8:
                    return MoodType.VERY_NEGATIVE, score
                else:
                    return MoodType.NEGATIVE, score
            else:  # Neutral
                return MoodType.NEUTRAL, score
                
        except Exception as e:
            logger.warning(f"RoBERTa analysis failed, falling back to TextBlob: {e}")
            return self._analyze_with_textblob(text)
    
    def _analyze_with_textblob(self, text: str) -> Tuple[MoodType, float]:
        """Analyze sentiment using TextBlob as fallback"""
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # Range: -1 to 1
        
        # Convert polarity to mood type
        if polarity >= 0.3:
            if polarity >= 0.6:
                return MoodType.VERY_POSITIVE, abs(polarity)
            else:
                return MoodType.POSITIVE, abs(polarity)
        elif polarity <= -0.3:
            if polarity <= -0.6:
                return MoodType.VERY_NEGATIVE, abs(polarity)
            else:
                return MoodType.NEGATIVE, abs(polarity)
        else:
            return MoodType.NEUTRAL, 0.5
    
    def get_mood_color(self, mood: MoodType) -> str:
        """Get color code for mood visualization"""
        color_map = {
            MoodType.VERY_POSITIVE: "#10B981",  # Green
            MoodType.POSITIVE: "#6EE7B7",      # Light Green
            MoodType.NEUTRAL: "#9CA3AF",       # Gray
            MoodType.NEGATIVE: "#F87171",      # Light Red
            MoodType.VERY_NEGATIVE: "#EF4444"  # Red
        }
        return color_map.get(mood, "#9CA3AF")

# Global instance
sentiment_service = SentimentService()