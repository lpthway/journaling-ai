# AI Emotion Service - Intelligent Emotion Analysis

"""
AI Emotion Service for Journaling AI
Replaces hardcoded emotion keywords with advanced AI-powered emotion detection
Integrates with Phase 2 cache patterns and AI Model Manager
"""

import logging
import asyncio
import json
import numpy as np
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

# Phase 2 integration imports
from app.core.cache_patterns import CacheDomain, CachePatterns, CacheKeyBuilder
from app.services.cache_service import unified_cache_service
from app.services.ai_model_manager import ai_model_manager
from app.core.service_interfaces import ServiceRegistry

logger = logging.getLogger(__name__)

class EmotionCategory(Enum):
    """Primary emotion categories"""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    TRUST = "trust"
    ANTICIPATION = "anticipation"

class EmotionIntensity(Enum):
    """Emotion intensity levels"""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"

@dataclass
class EmotionScore:
    """Individual emotion score with confidence"""
    emotion: str
    score: float
    confidence: float
    category: EmotionCategory
    intensity: EmotionIntensity

@dataclass
class EmotionAnalysis:
    """Complete emotion analysis result"""
    text: str
    primary_emotion: EmotionScore
    secondary_emotions: List[EmotionScore]
    emotional_complexity: float
    sentiment_polarity: float
    emotional_stability: float
    detected_patterns: List[str]
    analysis_metadata: Dict[str, Any]
    created_at: datetime

class AIEmotionService:
    """
    Advanced AI-powered Emotion Analysis Service
    
    Provides intelligent emotion detection that:
    - Uses state-of-the-art emotion recognition models
    - Detects complex emotional states and patterns
    - Provides confidence scores and intensity levels
    - Integrates with Phase 2 cache patterns for performance
    - Supports multilingual emotion analysis
    """
    
    def __init__(self):
        # In-memory cache for AI results (avoiding Redis recursion issues)
        self._memory_cache = {}
        self._cache_max_size = 1000  # Limit memory usage
        self.emotion_models = self._initialize_emotion_models()
        self.emotion_patterns = self._initialize_emotion_patterns()
        self.cultural_emotion_mappings = self._initialize_cultural_mappings()
        
        # Performance tracking
        self.analysis_stats = {
            "total_analyses": 0,
            "cache_hits": 0,
            "ai_analyses": 0,
            "pattern_detections": 0,
            "multilingual_analyses": 0
        }
        
        logger.info("🎭 AI Emotion Service initialized")

    def _initialize_emotion_models(self) -> Dict[str, Dict[str, Any]]:
        """Initialize emotion detection model configurations"""
        return {
            "primary_emotion": {
                "model_key": "emotion_classifier",
                "confidence_threshold": 0.6,
                "fallback_model": "sentiment_classifier"
            },
            "sentiment_analysis": {
                "model_key": "sentiment_classifier",
                "confidence_threshold": 0.7,
                "fallback_model": "multilingual_sentiment"
            },
            "multilingual_emotion": {
                "model_key": "multilingual_sentiment",
                "confidence_threshold": 0.6,
                "supported_languages": ["en", "de", "es", "fr"]
            }
        }

    def _initialize_emotion_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize emotion pattern detection rules"""
        return {
            # Complex emotional states
            "ambivalence": {
                "description": "Mixed positive and negative emotions",
                "detection_criteria": {
                    "mixed_sentiment": True,
                    "emotion_variance": "high",
                    "conflicting_emotions": True
                },
                "therapeutic_significance": "May indicate internal conflict or complex processing"
            },
            
            "emotional_numbness": {
                "description": "Absence or suppression of emotional expression",
                "detection_criteria": {
                    "low_emotional_intensity": True,
                    "neutral_sentiment": True,
                    "factual_language": True
                },
                "therapeutic_significance": "Could indicate dissociation or emotional suppression"
            },
            
            "emotional_escalation": {
                "description": "Increasing emotional intensity throughout text",
                "detection_criteria": {
                    "intensity_progression": "increasing",
                    "strong_language": True,
                    "exclamation_patterns": True
                },
                "therapeutic_significance": "May indicate building distress or excitement"
            },
            
            "rumination": {
                "description": "Repetitive negative thought patterns",
                "detection_criteria": {
                    "repetitive_themes": True,
                    "negative_sentiment": True,
                    "circular_thinking": True
                },
                "therapeutic_significance": "Common in depression and anxiety"
            },
            
            "gratitude_expression": {
                "description": "Expressions of thankfulness and appreciation",
                "detection_criteria": {
                    "grateful_language": True,
                    "positive_reflection": True,
                    "appreciation_markers": True
                },
                "therapeutic_significance": "Positive indicator for mental health"
            },
            
            "self_criticism": {
                "description": "Harsh self-evaluation and judgment",
                "detection_criteria": {
                    "negative_self_talk": True,
                    "perfectionism_markers": True,
                    "self_blame": True
                },
                "therapeutic_significance": "May indicate low self-esteem or perfectionism"
            }
        }

    def _initialize_cultural_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Initialize cultural emotion expression mappings"""
        return {
            "en": {
                "directness": "high",
                "emotional_expressiveness": "moderate",
                "cultural_specific_emotions": ["guilt", "pride", "embarrassment"],
                "expression_patterns": ["I feel", "I am", "This makes me"]
            },
            "es": {
                "directness": "moderate",
                "emotional_expressiveness": "high",
                "cultural_specific_emotions": ["orgullo", "verguenza", "alegria"],
                "expression_patterns": ["me siento", "estoy", "me da"]
            },
            "de": {
                "directness": "high",
                "emotional_expressiveness": "moderate",
                "cultural_specific_emotions": ["Schadenfreude", "Fernweh", "Weltschmerz"],
                "expression_patterns": ["ich fühle", "ich bin", "das macht mich"]
            },
            "fr": {
                "directness": "moderate",
                "emotional_expressiveness": "high",
                "cultural_specific_emotions": ["ennui", "joie de vivre", "mélancolie"],
                "expression_patterns": ["je me sens", "je suis", "cela me rend"]
            }
        }

    def _intelligently_process_text(self, text: str, max_chars: int, purpose: str = "analysis") -> str:
        """
        Intelligently process text to preserve important content while staying within limits
        
        Uses smart truncation strategies:
        1. For short texts: return as-is
        2. For medium texts: preserve beginning and end
        3. For long texts: extract key sentences/paragraphs
        """
        if len(text) <= max_chars:
            return text
        
        # For sentiment analysis, preserve emotional content better
        if purpose == "sentiment":
            # Try to preserve beginning (context) and recent content (current state)
            quarter = max_chars // 4
            if len(text) > max_chars:
                # Take first quarter + last three quarters, with ellipsis
                beginning = text[:quarter]
                remaining_space = max_chars - quarter - 5  # 5 for " ... "
                end_portion = text[-remaining_space:] if remaining_space > 0 else ""
                return f"{beginning} ... {end_portion}" if end_portion else beginning
        
        # For crisis detection, focus on recent and emotionally charged content
        elif purpose == "crisis":
            # Split into sentences and prioritize recent + emotional keywords
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            if not sentences:
                return text[:max_chars]
            
            # Look for crisis-related keywords
            crisis_keywords = ['suicide', 'kill', 'die', 'hurt', 'pain', 'hopeless', 'worthless', 
                             'end it', 'give up', 'can\'t go on', 'no point', 'better off dead']
            
            important_sentences = []
            current_length = 0
            
            # First pass: prioritize sentences with crisis keywords
            for sentence in sentences:
                sentence_text = sentence + '. '
                if any(keyword in sentence.lower() for keyword in crisis_keywords):
                    if current_length + len(sentence_text) <= max_chars:
                        important_sentences.append(sentence)
                        current_length += len(sentence_text)
            
            # Second pass: add recent sentences if space remains
            for sentence in reversed(sentences[-10:]):  # Last 10 sentences
                sentence_text = sentence + '. '
                if sentence not in important_sentences and current_length + len(sentence_text) <= max_chars:
                    important_sentences.insert(0, sentence)
                    current_length += len(sentence_text)
            
            if important_sentences:
                return '. '.join(important_sentences) + '.'
        
        # Default: smart truncation with sentence boundaries
        if max_chars > 100:
            # Try to end at sentence boundary
            truncated = text[:max_chars-3]
            last_period = truncated.rfind('.')
            last_exclamation = truncated.rfind('!')
            last_question = truncated.rfind('?')
            
            sentence_end = max(last_period, last_exclamation, last_question)
            if sentence_end > max_chars * 0.7:  # If we can preserve 70% and end cleanly
                return text[:sentence_end + 1]
        
        # Fallback: simple truncation
        return text[:max_chars-3] + "..."

    # ==================== MAIN EMOTION ANALYSIS ====================

    async def analyze_emotions(self, text: str, language: str = "en", 
                              include_patterns: bool = True,
                              user_context: Optional[Dict[str, Any]] = None) -> EmotionAnalysis:
        """
        Perform comprehensive emotion analysis on text
        
        Args:
            text: Text to analyze for emotions
            language: Language of the text
            include_patterns: Whether to detect emotion patterns
            user_context: Additional user context for personalized analysis
            
        Returns:
            EmotionAnalysis with comprehensive results
        """
        try:
            # Use in-memory cache instead of Redis for AI results
            cache_key = self._build_emotion_cache_key(text, language, include_patterns)
            if hasattr(self, '_memory_cache') and cache_key in self._memory_cache:
                self.analysis_stats["cache_hits"] += 1
                logger.debug(f"🗃️ Using memory-cached emotion analysis")
                return self._memory_cache[cache_key]
            
            # Perform new analysis
            analysis = await self._perform_emotion_analysis(
                text, language, include_patterns, user_context
            )
            
            if analysis:
                # Store in memory cache (avoiding Redis recursion issues)
                if len(self._memory_cache) >= self._cache_max_size:
                    # Simple LRU: remove oldest entry
                    oldest_key = next(iter(self._memory_cache))
                    del self._memory_cache[oldest_key]
                self._memory_cache[cache_key] = analysis
                
                self.analysis_stats["total_analyses"] += 1
                if language != "en":
                    self.analysis_stats["multilingual_analyses"] += 1
                
                logger.info(f"🎭 Completed emotion analysis: primary={analysis.primary_emotion.emotion}")
                
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error in emotion analysis: {e}")
            return await self._fallback_emotion_analysis(text, language)

    async def _perform_emotion_analysis(self, text: str, language: str, 
                                       include_patterns: bool,
                                       user_context: Optional[Dict[str, Any]]) -> EmotionAnalysis:
        """Perform comprehensive emotion analysis"""
        
        # Step 1: Primary emotion detection
        primary_emotions = await self._detect_primary_emotions(text, language)
        
        # Step 2: Sentiment analysis
        sentiment_score = await self._analyze_sentiment(text, language)
        
        # Step 3: Pattern detection (if requested)
        detected_patterns = []
        if include_patterns:
            detected_patterns = await self._detect_emotion_patterns(text, primary_emotions)
            if detected_patterns:
                self.analysis_stats["pattern_detections"] += 1
        
        # Step 4: Calculate emotional metrics
        emotional_complexity = self._calculate_emotional_complexity(primary_emotions)
        emotional_stability = self._calculate_emotional_stability(primary_emotions, sentiment_score)
        
        # Step 5: Identify primary and secondary emotions
        if primary_emotions:
            primary_emotion = primary_emotions[0]
            secondary_emotions = primary_emotions[1:3]  # Top 2 secondary emotions
        else:
            # Fallback emotion
            primary_emotion = EmotionScore(
                emotion="neutral",
                score=0.5,
                confidence=0.3,
                category=EmotionCategory.TRUST,
                intensity=EmotionIntensity.LOW
            )
            secondary_emotions = []
        
        # Step 6: Build analysis metadata
        metadata = {
            "language": language,
            "text_length": len(text),
            "word_count": len(text.split()),
            "analysis_method": "ai_powered",
            "models_used": ["emotion_classifier", "sentiment_classifier"],
            "pattern_detection": include_patterns,
            "user_context_available": user_context is not None
        }
        
        self.analysis_stats["ai_analyses"] += 1
        
        return EmotionAnalysis(
            text=text,
            primary_emotion=primary_emotion,
            secondary_emotions=secondary_emotions,
            emotional_complexity=emotional_complexity,
            sentiment_polarity=sentiment_score,
            emotional_stability=emotional_stability,
            detected_patterns=detected_patterns,
            analysis_metadata=metadata,
            created_at=datetime.utcnow()
        )

    # ==================== EMOTION DETECTION ====================

    async def _detect_primary_emotions(self, text: str, language: str) -> List[EmotionScore]:
        """Detect primary emotions using AI models"""
        try:
            # Get appropriate emotion model
            model = await ai_model_manager.get_model("emotion_classifier")
            
            if not model:
                logger.warning("🤖 Primary emotion model unavailable, using sentiment fallback")
                return await self._sentiment_to_emotion_fallback(text, language)
            
            # Analyze emotions
            results = model(text)
            
            if not results or not isinstance(results, list):
                return []
            
            # Convert results to EmotionScore objects
            emotion_scores = []
            for result in results[0]:  # First result set
                emotion_name = result['label'].lower()
                score = result['score']
                confidence = score  # Use score as confidence for now
                
                # Map to emotion category and intensity
                category = self._map_emotion_to_category(emotion_name)
                intensity = self._calculate_emotion_intensity(score)
                
                emotion_score = EmotionScore(
                    emotion=emotion_name,
                    score=score,
                    confidence=confidence,
                    category=category,
                    intensity=intensity
                )
                emotion_scores.append(emotion_score)
            
            # Sort by score (highest first)
            emotion_scores.sort(key=lambda x: x.score, reverse=True)
            
            return emotion_scores[:5]  # Return top 5 emotions
            
        except Exception as e:
            logger.error(f"❌ Error in primary emotion detection: {e}")
            return await self._sentiment_to_emotion_fallback(text, language)

    async def _analyze_sentiment(self, text: str, language: str) -> float:
        """Analyze sentiment polarity"""
        try:
            # Validate input
            if not text or not text.strip():
                return 0.0
            
            # Smart text processing for long content
            processed_text = self._intelligently_process_text(text, max_chars=2000, purpose="sentiment")
            if processed_text != text:
                logger.debug(f"Processed text for sentiment analysis: {len(processed_text)} chars (original: {len(text)})")
            
            # Select appropriate sentiment model based on language
            model_key = "multilingual_sentiment" if language != "en" else "sentiment_classifier"
            model = await ai_model_manager.get_model(model_key)
            
            if not model:
                logger.warning("🤖 Sentiment model unavailable, using neutral fallback")
                return 0.0
            
            # Analyze sentiment with comprehensive error handling
            try:
                results = model(processed_text)
            except Exception as model_error:
                if "tensor" in str(model_error).lower() or "size" in str(model_error).lower():
                    logger.warning(f"🤖 Tensor dimension error in sentiment analysis, trying shorter text: {model_error}")
                    # Try with even shorter text as fallback
                    short_text = processed_text[:500]
                    try:
                        results = model(short_text)
                    except Exception:
                        logger.warning("🤖 Sentiment analysis failed completely, using neutral fallback")
                        return 0.0
                else:
                    raise
            
            if not results or not isinstance(results, list):
                return 0.0
            
            # Convert sentiment labels to polarity score
            sentiment_mapping = {
                "positive": 1.0,
                "negative": -1.0,
                "neutral": 0.0,
                "label_0": -1.0,  # Negative in some models
                "label_1": 0.0,   # Neutral in some models
                "label_2": 1.0    # Positive in some models
            }
            
            # Calculate weighted sentiment score
            total_score = 0.0
            total_weight = 0.0
            
            for result in results[0]:
                label = result['label'].lower()
                score = result['score']
                
                if label in sentiment_mapping:
                    polarity = sentiment_mapping[label]
                    total_score += polarity * score
                    total_weight += score
            
            return total_score / max(total_weight, 0.01)
            
        except Exception as e:
            logger.error(f"❌ Error in sentiment analysis: {e}")
            return 0.0

    async def _sentiment_to_emotion_fallback(self, text: str, language: str) -> List[EmotionScore]:
        """Fallback emotion detection using sentiment analysis"""
        sentiment_score = await self._analyze_sentiment(text, language)
        
        # Map sentiment to basic emotions
        if sentiment_score > 0.3:
            emotion = "joy"
            category = EmotionCategory.JOY
        elif sentiment_score < -0.3:
            emotion = "sadness"
            category = EmotionCategory.SADNESS
        else:
            emotion = "neutral"
            category = EmotionCategory.TRUST
        
        intensity = self._calculate_emotion_intensity(abs(sentiment_score))
        
        return [EmotionScore(
            emotion=emotion,
            score=abs(sentiment_score),
            confidence=0.6,
            category=category,
            intensity=intensity
        )]

    # ==================== PATTERN DETECTION ====================

    async def _detect_emotion_patterns(self, text: str, emotions: List[EmotionScore]) -> List[str]:
        """Detect complex emotion patterns in text"""
        detected_patterns = []
        
        try:
            # Pattern 1: Ambivalence (mixed emotions)
            if self._detect_ambivalence(emotions):
                detected_patterns.append("ambivalence")
            
            # Pattern 2: Emotional numbness
            if self._detect_emotional_numbness(text, emotions):
                detected_patterns.append("emotional_numbness")
            
            # Pattern 3: Emotional escalation
            if self._detect_emotional_escalation(text):
                detected_patterns.append("emotional_escalation")
            
            # Pattern 4: Rumination
            if self._detect_rumination(text):
                detected_patterns.append("rumination")
            
            # Pattern 5: Gratitude expression
            if self._detect_gratitude(text):
                detected_patterns.append("gratitude_expression")
            
            # Pattern 6: Self-criticism
            if self._detect_self_criticism(text):
                detected_patterns.append("self_criticism")
            
            return detected_patterns
            
        except Exception as e:
            logger.error(f"❌ Error in pattern detection: {e}")
            return []

    def _detect_ambivalence(self, emotions: List[EmotionScore]) -> bool:
        """Detect mixed/conflicting emotions"""
        if len(emotions) < 2:
            return False
        
        # Check for high scores in conflicting emotions
        positive_emotions = {"joy", "trust", "anticipation", "surprise"}
        negative_emotions = {"sadness", "anger", "fear", "disgust"}
        
        has_positive = any(e.emotion in positive_emotions and e.score > 0.6 for e in emotions)
        has_negative = any(e.emotion in negative_emotions and e.score > 0.6 for e in emotions)
        
        return has_positive and has_negative

    def _detect_emotional_numbness(self, text: str, emotions: List[EmotionScore]) -> bool:
        """Detect absence of emotional expression"""
        # Low emotional intensity across all emotions
        max_score = max([e.score for e in emotions]) if emotions else 0
        
        # Factual language indicators
        factual_indicators = ["today i", "i went", "i did", "happened", "occurred"]
        factual_count = sum(1 for indicator in factual_indicators if indicator in text.lower())
        
        return max_score < 0.4 and factual_count > 2

    def _detect_emotional_escalation(self, text: str) -> bool:
        """Detect increasing emotional intensity"""
        # Simple heuristic: multiple exclamation marks or caps
        exclamation_count = text.count('!')
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        
        return exclamation_count > 2 or caps_ratio > 0.3

    def _detect_rumination(self, text: str) -> bool:
        """Detect repetitive negative thinking patterns"""
        # Look for repetitive phrases and negative cycles
        rumination_markers = ["keep thinking", "can't stop", "over and over", "again and again", "keep worrying"]
        
        marker_count = sum(1 for marker in rumination_markers if marker in text.lower())
        
        # Check for repetitive sentence patterns
        sentences = text.split('.')
        if len(sentences) > 3:
            similar_starts = len(set(s.strip()[:10] for s in sentences if s.strip()))
            repetition_ratio = similar_starts / len(sentences)
            return marker_count > 0 or repetition_ratio < 0.7
        
        return marker_count > 0

    def _detect_gratitude(self, text: str) -> bool:
        """Detect gratitude expressions"""
        gratitude_markers = [
            "grateful", "thankful", "appreciate", "blessed", "lucky",
            "glad", "grateful for", "thank you", "appreciate that"
        ]
        
        return any(marker in text.lower() for marker in gratitude_markers)

    def _detect_self_criticism(self, text: str) -> bool:
        """Detect self-critical language"""
        self_criticism_markers = [
            "i'm stupid", "i'm worthless", "i'm terrible", "i can't do anything",
            "i'm not good", "i always", "i never", "i should have", "i'm such"
        ]
        
        return any(marker in text.lower() for marker in self_criticism_markers)

    # ==================== UTILITY METHODS ====================

    def _map_emotion_to_category(self, emotion_name: str) -> EmotionCategory:
        """Map emotion name to primary emotion category"""
        emotion_mapping = {
            "joy": EmotionCategory.JOY,
            "happiness": EmotionCategory.JOY,
            "sadness": EmotionCategory.SADNESS,
            "grief": EmotionCategory.SADNESS,
            "anger": EmotionCategory.ANGER,
            "rage": EmotionCategory.ANGER,
            "fear": EmotionCategory.FEAR,
            "anxiety": EmotionCategory.FEAR,
            "surprise": EmotionCategory.SURPRISE,
            "disgust": EmotionCategory.DISGUST,
            "trust": EmotionCategory.TRUST,
            "anticipation": EmotionCategory.ANTICIPATION,
            "excitement": EmotionCategory.ANTICIPATION
        }
        
        return emotion_mapping.get(emotion_name.lower(), EmotionCategory.TRUST)

    def _calculate_emotion_intensity(self, score: float) -> EmotionIntensity:
        """Calculate emotion intensity based on score"""
        if score >= 0.8:
            return EmotionIntensity.VERY_HIGH
        elif score >= 0.6:
            return EmotionIntensity.HIGH
        elif score >= 0.4:
            return EmotionIntensity.MODERATE
        elif score >= 0.2:
            return EmotionIntensity.LOW
        else:
            return EmotionIntensity.VERY_LOW

    def _calculate_emotional_complexity(self, emotions: List[EmotionScore]) -> float:
        """Calculate emotional complexity score"""
        if not emotions:
            return 0.0
        
        # Complexity based on number of significant emotions and their distribution
        significant_emotions = [e for e in emotions if e.score > 0.3]
        num_significant = len(significant_emotions)
        
        # Distribution variance
        scores = [e.score for e in emotions]
        variance = np.var(scores) if len(scores) > 1 else 0
        
        # Combine factors
        complexity = (num_significant / 5.0) + variance
        return min(complexity, 1.0)

    def _calculate_emotional_stability(self, emotions: List[EmotionScore], sentiment: float) -> float:
        """Calculate emotional stability score"""
        if not emotions:
            return 0.5
        
        # Stability based on consistency of emotions and sentiment alignment
        primary_score = emotions[0].score if emotions else 0.5
        sentiment_alignment = abs(sentiment) * primary_score
        
        # More stable if primary emotion is strong and aligns with sentiment
        stability = (primary_score + sentiment_alignment) / 2.0
        return min(stability, 1.0)

    def _build_emotion_cache_key(self, text: str, language: str, include_patterns: bool) -> str:
        """Build cache key for emotion analysis"""
        text_hash = hash(text)
        params = f"{language}_{include_patterns}_{text_hash}"
        return CachePatterns.ai_model_instance(f"emotion_{params}", "latest")

    # ==================== FALLBACK AND ERROR HANDLING ====================

    async def _fallback_emotion_analysis(self, text: str, language: str) -> EmotionAnalysis:
        """Provide fallback emotion analysis when AI methods fail"""
        # Simple keyword-based fallback
        emotion_keywords = {
            "joy": ["happy", "joy", "excited", "wonderful", "great", "amazing"],
            "sadness": ["sad", "depressed", "down", "terrible", "awful", "cry"],
            "anger": ["angry", "mad", "furious", "annoyed", "frustrated"],
            "fear": ["afraid", "scared", "worried", "anxious", "nervous"],
            "surprise": ["surprised", "shocked", "unexpected", "wow"],
            "disgust": ["disgusted", "sick", "revolted", "nasty"],
            "trust": ["trust", "confident", "sure", "believe"],
            "anticipation": ["excited", "looking forward", "anticipate", "expect"]
        }
        
        text_lower = text.lower()
        emotion_scores = []
        
        for emotion, keywords in emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower) / len(keywords)
            if score > 0:
                emotion_scores.append(EmotionScore(
                    emotion=emotion,
                    score=score,
                    confidence=0.3,
                    category=self._map_emotion_to_category(emotion),
                    intensity=self._calculate_emotion_intensity(score)
                ))
        
        # Sort by score
        emotion_scores.sort(key=lambda x: x.score, reverse=True)
        
        if not emotion_scores:
            # Default neutral emotion
            emotion_scores = [EmotionScore(
                emotion="neutral",
                score=0.5,
                confidence=0.2,
                category=EmotionCategory.TRUST,
                intensity=EmotionIntensity.LOW
            )]
        
        return EmotionAnalysis(
            text=text,
            primary_emotion=emotion_scores[0],
            secondary_emotions=emotion_scores[1:3],
            emotional_complexity=0.3,
            sentiment_polarity=0.0,
            emotional_stability=0.5,
            detected_patterns=[],
            analysis_metadata={
                "language": language,
                "analysis_method": "keyword_fallback",
                "fallback": True
            },
            created_at=datetime.utcnow()
        )

    # ==================== BATCH OPERATIONS ====================

    async def analyze_emotions_batch(self, texts: List[str], language: str = "en") -> List[EmotionAnalysis]:
        """Analyze emotions for multiple texts efficiently"""
        logger.info(f"🔄 Analyzing emotions for batch of {len(texts)} texts")
        
        # Process in parallel for better performance
        tasks = [self.analyze_emotions(text, language) for text in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        successful_analyses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Batch emotion analysis failed for text {i}: {result}")
                # Generate fallback
                fallback = await self._fallback_emotion_analysis(texts[i], language)
                successful_analyses.append(fallback)
            else:
                successful_analyses.append(result)
        
        return successful_analyses

    # ==================== MONITORING AND STATISTICS ====================

    def get_analysis_stats(self) -> Dict[str, Any]:
        """Get emotion analysis statistics"""
        total = max(self.analysis_stats["total_analyses"], 1)
        return {
            "total_analyses": self.analysis_stats["total_analyses"],
            "cache_hit_rate": (self.analysis_stats["cache_hits"] / total) * 100,
            "ai_analysis_rate": (self.analysis_stats["ai_analyses"] / total) * 100,
            "pattern_detection_rate": (self.analysis_stats["pattern_detections"] / total) * 100,
            "multilingual_rate": (self.analysis_stats["multilingual_analyses"] / total) * 100
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on emotion analysis system"""
        health = {
            "status": "healthy",
            "emotion_model_available": False,
            "sentiment_model_available": False,
            "cache_operational": False,
            "analysis_stats": self.get_analysis_stats()
        }
        
        try:
            # Check emotion model
            emotion_model = await ai_model_manager.get_model("emotion_classifier")
            health["emotion_model_available"] = emotion_model is not None
            
            # Check sentiment model
            sentiment_model = await ai_model_manager.get_model("sentiment_classifier")
            health["sentiment_model_available"] = sentiment_model is not None
            
            # Check cache system
            test_key = "health_check_emotion"
            test_analysis = EmotionAnalysis(
                text="test", primary_emotion=None, secondary_emotions=[],
                emotional_complexity=0.0, sentiment_polarity=0.0,
                emotional_stability=0.0, detected_patterns=[],
                analysis_metadata={}, created_at=datetime.utcnow()
            )
            await unified_cache_service.set_ai_analysis_result(test_analysis, test_key, ttl=60)
            cached_value = await unified_cache_service.get_ai_analysis_result(test_key)
            health["cache_operational"] = cached_value is not None
            
            # Overall status
            if not health["emotion_model_available"] and not health["sentiment_model_available"]:
                health["status"] = "degraded"
            
        except Exception as e:
            health["status"] = "error"
            health["error"] = str(e)
        
        return health

# ==================== SERVICE INSTANCE ====================

# Global AI Emotion Service instance
ai_emotion_service = AIEmotionService()

# Integration with Phase 2 Service Registry
def register_ai_emotion_service():
    """Register AI Emotion Service in Phase 2 service registry"""
    try:
        from app.core.service_interfaces import service_registry
        service_registry.register_service("ai_emotion_service", ai_emotion_service)
        logger.info("✅ AI Emotion Service registered in service registry")
    except Exception as e:
        logger.error(f"❌ Failed to register AI Emotion Service: {e}")

# Auto-register when module is imported
register_ai_emotion_service()

# ==================== LEGACY COMPATIBILITY ====================

def analyze_sentiment(text: str) -> Tuple:
    """
    Legacy compatibility function for sentiment_service.analyze_sentiment()
    Maps to modern AI emotion analysis
    
    Returns:
        Tuple of (mood, confidence_score) for backward compatibility
    """
    try:
        import asyncio
        # Run async emotion analysis in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            emotion_analysis = loop.run_until_complete(
                ai_emotion_service.analyze_emotions(text)
            )
            # Convert EmotionCategory to MoodType for backward compatibility
            from app.models.entry import MoodType
            emotion_to_mood_map = {
                "joy": MoodType.HAPPY,
                "sadness": MoodType.SAD,
                "anger": MoodType.ANGRY,
                "fear": MoodType.ANXIOUS,
                "surprise": MoodType.EXCITED,
                "trust": MoodType.CALM,
                "anticipation": MoodType.EXCITED,
                "disgust": MoodType.FRUSTRATED
            }
            
            primary_emotion = emotion_analysis.primary_emotion.emotion.value
            mood = emotion_to_mood_map.get(primary_emotion, MoodType.NEUTRAL)
            confidence = emotion_analysis.primary_emotion.confidence
            
            return mood, confidence
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Legacy sentiment analysis failed: {e}")
        from app.models.entry import MoodType
        return MoodType.NEUTRAL, 0.5
