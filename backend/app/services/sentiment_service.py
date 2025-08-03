# backend/app/services/sentiment_service.py - Enhanced for German/English

from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
from textblob import TextBlob
from typing import Tuple, Dict
import logging
from app.models.entry import MoodType
from app.core.config import settings
import langdetect

logger = logging.getLogger(__name__)

class MultilingualSentimentService:
    def __init__(self):
        # TEMPORARILY DISABLED: Load models on-demand to prevent VRAM usage at startup
        self.emotion_pipeline = None
        self.multilingual_pipeline = None
        self.primary_pipeline = None
        self.models_loaded = False
        
        # Local model cache directory
        from pathlib import Path
        self._cache_dir = Path(__file__).parent.parent.parent / "models"
        self._cache_dir.mkdir(exist_ok=True)
        
        logger.info("🔧 Sentiment service initialized (models will load on demand with local caching)")
        
    def _ensure_model_cached(self, model_name: str) -> str:
        """Ensure model is downloaded and cached locally"""
        from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification
        
        # Create model-specific cache directory
        model_cache_dir = self._cache_dir / model_name.replace("/", "--")
        
        if model_cache_dir.exists() and any(model_cache_dir.iterdir()):
            logger.info(f"📦 Using cached model: {model_name}")
            return str(model_cache_dir)
        
        logger.info(f"⬇️ Downloading and caching model: {model_name}")
        
        try:
            # Download tokenizer and model to cache
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=str(model_cache_dir)
            )
            
            # Try sequence classification model first, then fall back to base model
            try:
                model = AutoModelForSequenceClassification.from_pretrained(
                    model_name,
                    cache_dir=str(model_cache_dir)
                )
            except:
                model = AutoModel.from_pretrained(
                    model_name,
                    cache_dir=str(model_cache_dir)
                )
            
            logger.info(f"✅ Model cached successfully: {model_name}")
            return str(model_cache_dir)
            
        except Exception as e:
            logger.error(f"❌ Failed to cache model {model_name}: {e}")
            # If caching fails, return original model name for online loading
            return model_name
        
    def _load_single_model(self, model_type: str):
        """Load only one model at a time to conserve VRAM"""
        # Clear any existing models first
        self._clear_models()
        
        import time
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # Add exponential backoff for rate limiting
                    delay = min(5 * (2 ** attempt), 30)
                    logger.info(f"⏳ Rate limiting: waiting {delay}s before retry {attempt}")
                    time.sleep(delay)
                
                if model_type == "emotion" and not self.emotion_pipeline:
                    # Primary: Enhanced emotion detection (English)
                    model_name = "j-hartmann/emotion-english-distilroberta-base"
                    cached_path = self._ensure_model_cached(model_name)
                    
                    self.emotion_pipeline = pipeline(
                        "text-classification",
                        model=cached_path,
                        return_all_scores=True
                    )
                    logger.info("✅ Loaded emotion detection model")
                    return
                    
                elif model_type == "multilingual" and not self.multilingual_pipeline:
                    # Fallback: Multilingual sentiment (German/English)
                    model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
                    logger.info("🌐 Loading multilingual sentiment model...")
                    cached_path = self._ensure_model_cached(model_name)
                    
                    self.multilingual_pipeline = pipeline(
                        "sentiment-analysis",
                        model=cached_path
                    )
                    logger.info("✅ Loaded multilingual sentiment model")
                    return
                    
                elif model_type == "backup" and not self.primary_pipeline:
                    # Backup: Original RoBERTa (English only)
                    model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
                    cached_path = self._ensure_model_cached(model_name)
                    
                    self.primary_pipeline = pipeline(
                        "sentiment-analysis",
                        model=cached_path
                    )
                    logger.info("✅ Loaded backup sentiment model")
                    return
                    
            except Exception as e:
                error_msg = str(e)
                # Handle Hugging Face rate limiting
                if "429" in error_msg or "rate limit" in error_msg.lower() or "too many requests" in error_msg.lower():
                    if attempt < max_retries - 1:
                        logger.warning(f"🚫 Rate limited by Hugging Face, retrying in next attempt...")
                        continue
                    else:
                        logger.error(f"❌ Rate limited by Hugging Face, max retries exceeded for {model_type}")
                        return
                elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                    if attempt < max_retries - 1:
                        logger.warning(f"🌐 Network error loading {model_type}, retrying...")
                        continue
                    else:
                        logger.error(f"❌ Network error loading {model_type}: {e}")
                        return
                else:
                    logger.warning(f"Could not load {model_type} model: {e}")
                    return
            
    def _clear_models(self):
        """Clear all models to free VRAM"""
        import gc
        import torch
        
        self.emotion_pipeline = None
        self.multilingual_pipeline = None
        self.primary_pipeline = None
        
        # Force garbage collection and clear GPU cache
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
    
    def detect_language(self, text: str) -> str:
        """Detect if text is German or English"""
        try:
            if len(text.strip()) < 10:
                return "en"  # Default to English for short text
            return langdetect.detect(text)
        except:
            return "en"  # Default fallback
    
    def analyze_sentiment(self, text: str) -> Tuple[MoodType, float]:
        """Analyze sentiment with language detection and sequential model loading"""
        try:
            language = self.detect_language(text)
            
            # For English: Try advanced emotion detection
            if language == "en":
                try:
                    self._load_single_model("emotion")
                    if self.emotion_pipeline:
                        return self._analyze_with_emotions(text)
                except Exception as e:
                    logger.warning(f"Emotion model failed, falling back: {e}")
            
            # For German or if emotion detection fails: Try multilingual (often rate limited)
            if language == "de":
                try:
                    self._load_single_model("multilingual")
                    if self.multilingual_pipeline:
                        return self._analyze_multilingual(text)
                except Exception as e:
                    logger.warning(f"Multilingual model failed (likely rate limited), falling back: {e}")
            
            # Try backup model
            try:
                self._load_single_model("backup")
                if self.primary_pipeline:
                    return self._analyze_with_roberta(text)
            except Exception as e:
                logger.warning(f"Backup model failed, using TextBlob fallback: {e}")
            
            # Ultimate fallback (no GPU required, no external API calls)
            logger.info("🔄 Using TextBlob fallback (no external dependencies)")
            return self._analyze_with_textblob(text)
                
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return MoodType.NEUTRAL, 0.5
    
    def _analyze_with_emotions(self, text: str) -> Tuple[MoodType, float]:
        """Enhanced emotion analysis (English) - 6 emotions"""
        try:
            if len(text) > 512:
                text = text[:512]
            
            results = self.emotion_pipeline(text)[0]
            emotion_scores = {result['label'].lower(): result['score'] for result in results}
            
            # Advanced emotion mapping
            joy = emotion_scores.get('joy', 0)
            surprise = emotion_scores.get('surprise', 0) * 0.7  # Moderate positive
            sadness = emotion_scores.get('sadness', 0)
            anger = emotion_scores.get('anger', 0)
            fear = emotion_scores.get('fear', 0)
            disgust = emotion_scores.get('disgust', 0)
            
            # Calculate composite scores
            positive_score = joy + surprise
            negative_score = sadness + anger + fear + disgust
            
            # Get dominant emotion and confidence
            max_emotion = max(emotion_scores.items(), key=lambda x: x[1])
            confidence = max_emotion[1]
            dominant = max_emotion[0]
            
            # Enhanced mood classification
            if positive_score > negative_score:
                if joy > 0.6 or confidence > 0.8:
                    return MoodType.VERY_POSITIVE, confidence
                else:
                    return MoodType.POSITIVE, confidence
            elif negative_score > positive_score:
                if (sadness > 0.6 or anger > 0.6 or fear > 0.6) or confidence > 0.8:
                    return MoodType.VERY_NEGATIVE, confidence
                else:
                    return MoodType.NEGATIVE, confidence
            else:
                return MoodType.NEUTRAL, confidence
                
        except Exception as e:
            logger.warning(f"Emotion analysis failed: {e}")
            return self._analyze_multilingual(text)
    
    def _analyze_multilingual(self, text: str) -> Tuple[MoodType, float]:
        """Multilingual sentiment analysis (German/English)"""
        try:
            if len(text) > 512:
                text = text[:512]
            
            result = self.multilingual_pipeline(text)[0]
            label = result['label'].lower()
            score = result['score']
            
            # Map multilingual model outputs
            if 'positive' in label or label == 'pos':
                if score > 0.8:
                    return MoodType.VERY_POSITIVE, score
                else:
                    return MoodType.POSITIVE, score
            elif 'negative' in label or label == 'neg':
                if score > 0.8:
                    return MoodType.VERY_NEGATIVE, score
                else:
                    return MoodType.NEGATIVE, score
            else:
                return MoodType.NEUTRAL, score
                
        except Exception as e:
            logger.warning(f"Multilingual analysis failed: {e}")
            return self._analyze_with_textblob(text)
    
    def _analyze_with_roberta(self, text: str) -> Tuple[MoodType, float]:
        """Original RoBERTa analysis (English backup)"""
        try:
            if len(text) > 512:
                text = text[:512]
            
            result = self.primary_pipeline(text)[0]
            label = result['label'].lower()
            score = result['score']
            
            if label == 'label_2' or 'positive' in label:
                if score > 0.8:
                    return MoodType.VERY_POSITIVE, score
                else:
                    return MoodType.POSITIVE, score
            elif label == 'label_0' or 'negative' in label:
                if score > 0.8:
                    return MoodType.VERY_NEGATIVE, score
                else:
                    return MoodType.NEGATIVE, score
            else:
                return MoodType.NEUTRAL, score
                
        except Exception as e:
            logger.warning(f"RoBERTa analysis failed: {e}")
            return self._analyze_with_textblob(text)
    
    def _analyze_with_textblob(self, text: str) -> Tuple[MoodType, float]:
        """TextBlob fallback (works with German too)"""
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        
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
    
    def get_detailed_emotions(self, text: str) -> Dict[str, float]:
        """Get detailed emotion breakdown (English only)"""
        if not self.emotion_pipeline:
            return {}
            
        try:
            language = self.detect_language(text)
            if language != "en":
                return {"note": "Detailed emotions only available for English text"}
                
            if len(text) > 512:
                text = text[:512]
                
            results = self.emotion_pipeline(text)[0]
            emotions = {}
            
            for result in results:
                emotion = result['label'].lower()
                score = result['score']
                emotions[emotion] = round(score, 3)
                
            return emotions
        except Exception as e:
            logger.error(f"Error getting detailed emotions: {e}")
            return {}
    
    def get_mood_insights(self, text: str) -> Dict[str, any]:
        """Comprehensive mood analysis"""
        language = self.detect_language(text)
        mood, confidence = self.analyze_sentiment(text)
        emotions = self.get_detailed_emotions(text) if language == "en" else {}
        
        return {
            'mood': mood.value,
            'confidence': round(confidence, 3),
            'language': language,
            'emotions': emotions,
            'analysis_method': (
                'advanced_emotions' if language == "en" and emotions else
                'multilingual_sentiment' if language == "de" else
                'basic_sentiment'
            )
        }
    
    def get_mood_color(self, mood: MoodType) -> str:
        """Get color code for mood visualization"""
        color_map = {
            MoodType.VERY_POSITIVE: "#10B981",
            MoodType.POSITIVE: "#6EE7B7",
            MoodType.NEUTRAL: "#9CA3AF", 
            MoodType.NEGATIVE: "#F87171",
            MoodType.VERY_NEGATIVE: "#EF4444"
        }
        return color_map.get(mood, "#9CA3AF")

# Global instance
sentiment_service = MultilingualSentimentService()