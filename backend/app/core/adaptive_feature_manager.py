"""
Adaptive Feature Management System

This module manages which AI features are available based on hardware capabilities
and provides graceful fallbacks when advanced features are not available.
"""

import asyncio
import logging
import re
from typing import Dict, Any, List, Optional, Union, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import json

from .hardware_profiler import HardwareTier, HardwareProfiler
from .adaptive_memory_manager import AdaptiveMemoryManager

logger = logging.getLogger(__name__)

class AnalysisType(Enum):
    """Types of text analysis available"""
    SENTIMENT = "sentiment"
    EMOTION = "emotion"
    TOPIC = "topic"
    SUMMARY = "summary"
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    STATS = "stats"

@dataclass
class AnalysisResult:
    """Result of text analysis"""
    analysis_type: AnalysisType
    result: Any
    confidence: float
    method_used: str
    processing_time: float
    hardware_tier: str
    fallback_used: bool = False

class AdaptiveFeatureManager:
    """Manage which features are available based on hardware"""
    
    def __init__(self, hardware_profiler: HardwareProfiler, memory_manager: AdaptiveMemoryManager):
        self.hardware_profiler = hardware_profiler
        self.memory_manager = memory_manager
        self.current_tier = None
        self.tier_config = {}
        self.fallback_methods = {}
        self._initialize_fallbacks()
        
        # Initialize with current hardware
        self._update_hardware_tier()
    
    def _initialize_fallbacks(self):
        """Initialize fallback analysis methods"""
        self.fallback_methods = {
            AnalysisType.SENTIMENT: self._keyword_sentiment_analysis,
            AnalysisType.EMOTION: self._pattern_emotion_analysis,
            AnalysisType.TOPIC: self._keyword_topic_analysis,
            AnalysisType.SUMMARY: self._extractive_summary,
            AnalysisType.SEMANTIC: self._tfidf_similarity,
            AnalysisType.KEYWORD: self._simple_keyword_extraction,
            AnalysisType.STATS: self._text_statistics
        }
    
    def _update_hardware_tier(self):
        """Update current hardware tier and configuration"""
        self.current_tier, classification_info = self.hardware_profiler.classify_hardware_tier()
        self.tier_config = classification_info.get('tier_config', {})
        logger.info(f"Feature manager initialized with tier: {self.current_tier.value}")
    
    def get_available_features(self) -> List[str]:
        """Return list of features available for current hardware tier"""
        return self.tier_config.get('features', ['basic_stats'])
    
    def can_perform_analysis(self, analysis_type: Union[AnalysisType, str]) -> bool:
        """Check if specific analysis is possible with current hardware"""
        if isinstance(analysis_type, str):
            try:
                analysis_type = AnalysisType(analysis_type)
            except ValueError:
                return False
        
        # Basic analyses are always available through fallbacks
        if analysis_type in [AnalysisType.KEYWORD, AnalysisType.STATS]:
            return True
        
        # Check tier-specific features
        available_features = self.get_available_features()
        
        feature_mapping = {
            AnalysisType.SENTIMENT: ['sentiment_analysis', 'advanced_sentiment_analysis', 'premium_sentiment_analysis'],
            AnalysisType.EMOTION: ['basic_emotion_detection', 'detailed_emotion_detection', 'comprehensive_emotion_analysis'],
            AnalysisType.TOPIC: ['topic_modeling', 'advanced_topic_modeling'],
            AnalysisType.SUMMARY: ['auto_summary_generation'],
            AnalysisType.SEMANTIC: ['semantic_search']
        }
        
        required_features = feature_mapping.get(analysis_type, [])
        return any(feature in available_features for feature in required_features)
    
    async def analyze_text(self, text: str, analysis_type: Union[AnalysisType, str] = 'auto',
                          context: Optional[Dict[str, Any]] = None) -> AnalysisResult:
        """Perform best available analysis for current hardware"""
        start_time = datetime.now()
        
        if isinstance(analysis_type, str):
            if analysis_type == 'auto':
                # Determine best analysis type for current tier
                analysis_type = self._select_optimal_analysis_type()
            else:
                try:
                    analysis_type = AnalysisType(analysis_type)
                except ValueError:
                    analysis_type = AnalysisType.STATS
        
        # Try AI-powered analysis first if available
        if self.can_perform_analysis(analysis_type):
            try:
                result = await self._ai_analysis(text, analysis_type, context)
                if result is not None:
                    processing_time = (datetime.now() - start_time).total_seconds()
                    return AnalysisResult(
                        analysis_type=analysis_type,
                        result=result,
                        confidence=0.8,  # AI analysis generally has higher confidence
                        method_used="ai_model",
                        processing_time=processing_time,
                        hardware_tier=self.current_tier.value,
                        fallback_used=False
                    )
            except Exception as e:
                logger.warning(f"AI analysis failed for {analysis_type.value}: {e}")
        
        # Fall back to algorithmic analysis
        logger.info(f"Using fallback method for {analysis_type.value}")
        result = await self._fallback_analysis(text, analysis_type, context)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return AnalysisResult(
            analysis_type=analysis_type,
            result=result,
            confidence=0.6,  # Fallback methods have lower confidence
            method_used="algorithmic",
            processing_time=processing_time,
            hardware_tier=self.current_tier.value,
            fallback_used=True
        )
    
    def _select_optimal_analysis_type(self) -> AnalysisType:
        """Select the best analysis type for current hardware tier"""
        if self.current_tier == HardwareTier.HIGH_END:
            return AnalysisType.SEMANTIC
        elif self.current_tier == HardwareTier.STANDARD:
            return AnalysisType.SENTIMENT
        elif self.current_tier == HardwareTier.BASIC:
            return AnalysisType.EMOTION
        else:
            return AnalysisType.STATS
    
    async def _ai_analysis(self, text: str, analysis_type: AnalysisType, 
                          context: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """Perform AI-powered analysis using loaded models"""
        models_config = self.tier_config.get('models', {})
        
        # Map analysis types to model types
        model_mapping = {
            AnalysisType.SENTIMENT: 'sentiment',
            AnalysisType.EMOTION: 'emotion',
            AnalysisType.TOPIC: 'topic',
            AnalysisType.SUMMARY: 'summary',
            AnalysisType.SEMANTIC: 'semantic'
        }
        
        model_type = model_mapping.get(analysis_type)
        if not model_type or model_type not in models_config:
            return None
        
        model_config = models_config[model_type]
        
        # Load model safely
        model = await self.memory_manager.load_model_safely(model_type, model_config)
        if model is None:
            return None
        
        try:
            # Perform analysis based on type
            if analysis_type == AnalysisType.SENTIMENT:
                return await self._ai_sentiment_analysis(model, text)
            elif analysis_type == AnalysisType.EMOTION:
                return await self._ai_emotion_analysis(model, text)
            elif analysis_type == AnalysisType.TOPIC:
                return await self._ai_topic_analysis(model, text, context)
            elif analysis_type == AnalysisType.SUMMARY:
                return await self._ai_summary_analysis(model, text)
            elif analysis_type == AnalysisType.SEMANTIC:
                return await self._ai_semantic_analysis(model, text)
            else:
                return None
                
        except Exception as e:
            logger.error(f"AI analysis error for {analysis_type.value}: {e}")
            return None
    
    async def _ai_sentiment_analysis(self, model, text: str) -> Dict[str, Any]:
        """Perform AI sentiment analysis"""
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, lambda: model(text))
        
        if isinstance(result, list) and len(result) > 0:
            result = result[0]
        
        return {
            "sentiment": result.get('label', 'neutral').lower(),
            "confidence": result.get('score', 0.5),
            "raw_result": result
        }
    
    async def _ai_emotion_analysis(self, model, text: str) -> Dict[str, Any]:
        """Perform AI emotion analysis"""
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, lambda: model(text))
        
        if isinstance(result, list) and len(result) > 0:
            result = result[0]
        
        return {
            "emotion": result.get('label', 'neutral').lower(),
            "confidence": result.get('score', 0.5),
            "raw_result": result
        }
    
    async def _ai_topic_analysis(self, model, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform AI topic analysis"""
        # Default topic candidates
        topic_candidates = [
            "work and career", "personal relationships", "health and wellness",
            "travel and adventure", "learning and education", "finance and money",
            "family and home", "hobbies and interests", "emotions and feelings",
            "goals and aspirations"
        ]
        
        if context and 'topics' in context:
            topic_candidates = context['topics']
        
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, 
            lambda: model(text, topic_candidates)
        )
        
        if isinstance(result, dict):
            return {
                "topic": result.get('labels', ['unknown'])[0] if result.get('labels') else 'unknown',
                "confidence": result.get('scores', [0.5])[0] if result.get('scores') else 0.5,
                "all_topics": list(zip(result.get('labels', []), result.get('scores', [])))
            }
        
        return {"topic": "unknown", "confidence": 0.0, "all_topics": []}
    
    async def _ai_summary_analysis(self, model, text: str) -> Dict[str, Any]:
        """Perform AI summary generation"""
        # Only summarize if text is long enough
        if len(text.split()) < 50:
            return {"summary": text, "compression_ratio": 1.0}
        
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: model(text, max_length=100, min_length=20, do_sample=False)
        )
        
        if isinstance(result, list) and len(result) > 0:
            summary = result[0].get('summary_text', text)
        else:
            summary = text
        
        compression_ratio = len(summary.split()) / len(text.split())
        
        return {
            "summary": summary,
            "compression_ratio": compression_ratio,
            "original_length": len(text.split()),
            "summary_length": len(summary.split())
        }
    
    async def _ai_semantic_analysis(self, model, text: str) -> Dict[str, Any]:
        """Perform AI semantic analysis"""
        loop = asyncio.get_running_loop()
        embeddings = await loop.run_in_executor(None, lambda: model(text))
        
        # Convert to list if numpy array
        if hasattr(embeddings, 'tolist'):
            embeddings = embeddings.tolist()
        elif isinstance(embeddings, list) and len(embeddings) > 0:
            if hasattr(embeddings[0], 'tolist'):
                embeddings = embeddings[0].tolist()
        
        return {
            "embeddings": embeddings,
            "dimension": len(embeddings) if isinstance(embeddings, list) else 0
        }
    
    async def _fallback_analysis(self, text: str, analysis_type: AnalysisType,
                                context: Optional[Dict[str, Any]] = None) -> Any:
        """Perform fallback algorithmic analysis"""
        fallback_method = self.fallback_methods.get(analysis_type)
        if fallback_method:
            return await fallback_method(text, context)
        else:
            return await self._text_statistics(text, context)
    
    async def _keyword_sentiment_analysis(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Keyword-based sentiment analysis fallback"""
        positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'happy',
            'joy', 'excited', 'pleased', 'satisfied', 'delighted', 'thrilled', 'perfect',
            'awesome', 'brilliant', 'success', 'achievement', 'accomplishment'
        }
        
        negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'hate', 'sad', 'angry', 'frustrated',
            'disappointed', 'worried', 'stressed', 'anxious', 'depressed', 'upset',
            'annoyed', 'irritated', 'failure', 'problem', 'issue', 'difficulty'
        }
        
        words = re.findall(r'\b\w+\b', text.lower())
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        if positive_count > negative_count:
            sentiment = 'positive'
            confidence = min(0.8, 0.5 + (positive_count - negative_count) / len(words))
        elif negative_count > positive_count:
            sentiment = 'negative'
            confidence = min(0.8, 0.5 + (negative_count - positive_count) / len(words))
        else:
            sentiment = 'neutral'
            confidence = 0.5
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "positive_indicators": positive_count,
            "negative_indicators": negative_count
        }
    
    async def _pattern_emotion_analysis(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Pattern-based emotion analysis fallback"""
        emotion_patterns = {
            'joy': [r'\b(happy|joy|excited|thrilled|delighted|amazing|wonderful)\b'],
            'sadness': [r'\b(sad|depressed|down|unhappy|miserable|crying)\b'],
            'anger': [r'\b(angry|mad|furious|irritated|annoyed|frustrated)\b'],
            'fear': [r'\b(scared|afraid|worried|anxious|nervous|terrified)\b'],
            'surprise': [r'\b(surprised|shocked|amazed|astonished|unexpected)\b'],
            'disgust': [r'\b(disgusted|revolted|appalled|sickened)\b']
        }
        
        text_lower = text.lower()
        emotion_scores = {}
        
        for emotion, patterns in emotion_patterns.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                score += len(matches)
            emotion_scores[emotion] = score
        
        if not any(emotion_scores.values()):
            return {"emotion": "neutral", "confidence": 0.5}
        
        dominant_emotion = max(emotion_scores, key=emotion_scores.get)
        max_score = emotion_scores[dominant_emotion]
        confidence = min(0.8, 0.3 + max_score / len(text.split()))
        
        return {
            "emotion": dominant_emotion,
            "confidence": confidence,
            "all_emotions": emotion_scores
        }
    
    async def _keyword_topic_analysis(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Keyword-based topic analysis fallback"""
        topic_keywords = {
            "work": ["work", "job", "career", "office", "meeting", "project", "boss", "colleague"],
            "family": ["family", "parent", "child", "spouse", "brother", "sister", "home"],
            "health": ["health", "exercise", "diet", "doctor", "medicine", "fitness", "wellness"],
            "travel": ["travel", "trip", "vacation", "journey", "flight", "hotel", "destination"],
            "learning": ["learn", "study", "book", "course", "education", "knowledge", "skill"],
            "finance": ["money", "budget", "investment", "savings", "expense", "financial"]
        }
        
        text_lower = text.lower()
        topic_scores = {}
        
        for topic, keywords in topic_keywords.items():
            score = sum(text_lower.count(keyword) for keyword in keywords)
            topic_scores[topic] = score
        
        if not any(topic_scores.values()):
            return {"topic": "personal", "confidence": 0.3}
        
        dominant_topic = max(topic_scores, key=topic_scores.get)
        max_score = topic_scores[dominant_topic]
        confidence = min(0.7, 0.3 + max_score / len(text.split()))
        
        return {
            "topic": dominant_topic,
            "confidence": confidence,
            "all_topics": [(topic, score) for topic, score in topic_scores.items()]
        }
    
    async def _extractive_summary(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extractive summary fallback"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 2:
            return {"summary": text, "compression_ratio": 1.0}
        
        # Score sentences by length and position
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            words = len(sentence.split())
            position_score = 1.0 if i < len(sentences) * 0.3 else 0.5  # Favor early sentences
            length_score = min(1.0, words / 20)  # Favor medium-length sentences
            score = position_score * length_score
            scored_sentences.append((score, sentence))
        
        # Select top sentences
        scored_sentences.sort(reverse=True)
        summary_length = max(1, len(sentences) // 3)
        selected_sentences = [sent for _, sent in scored_sentences[:summary_length]]
        
        summary = '. '.join(selected_sentences) + '.'
        compression_ratio = len(summary.split()) / len(text.split())
        
        return {
            "summary": summary,
            "compression_ratio": compression_ratio,
            "original_length": len(text.split()),
            "summary_length": len(summary.split())
        }
    
    async def _tfidf_similarity(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """TF-IDF based similarity fallback"""
        words = re.findall(r'\b\w+\b', text.lower())
        word_freq = {}
        
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Simple TF calculation
        total_words = len(words)
        tf_scores = {word: freq / total_words for word, freq in word_freq.items()}
        
        # Use top words as "embedding"
        top_words = sorted(tf_scores.items(), key=lambda x: x[1], reverse=True)[:50]
        
        return {
            "embeddings": [score for _, score in top_words],
            "dimension": len(top_words),
            "top_terms": top_words
        }
    
    async def _simple_keyword_extraction(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Simple keyword extraction"""
        # Common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'was', 'are', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her'
        }
        
        words = re.findall(r'\b\w+\b', text.lower())
        words = [word for word in words if word not in stop_words and len(word) > 2]
        
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top keywords
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "keywords": [word for word, freq in keywords],
            "keyword_scores": dict(keywords),
            "total_unique_words": len(word_freq)
        }
    
    async def _text_statistics(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Basic text statistics"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        words = re.findall(r'\b\w+\b', text)
        chars = len(text)
        chars_no_spaces = len(text.replace(' ', ''))
        
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        
        return {
            "character_count": chars,
            "character_count_no_spaces": chars_no_spaces,
            "word_count": len(words),
            "sentence_count": len(sentences),
            "average_word_length": round(avg_word_length, 2),
            "average_sentence_length": round(avg_sentence_length, 2),
            "reading_time_minutes": round(len(words) / 200, 1)  # Assume 200 WPM
        }
    
    async def batch_analyze(self, texts: List[str], analysis_type: Union[AnalysisType, str] = 'auto') -> List[AnalysisResult]:
        """Analyze multiple texts efficiently"""
        results = []
        
        # For AI models, batch processing can be more efficient
        if len(texts) > 1 and self.can_perform_analysis(analysis_type):
            try:
                # Try batch processing
                batch_results = await self._batch_ai_analysis(texts, analysis_type)
                if batch_results:
                    return batch_results
            except Exception as e:
                logger.warning(f"Batch processing failed: {e}")
        
        # Fall back to individual processing
        for text in texts:
            result = await self.analyze_text(text, analysis_type)
            results.append(result)
        
        return results
    
    async def _batch_ai_analysis(self, texts: List[str], analysis_type: AnalysisType) -> Optional[List[AnalysisResult]]:
        """Perform batch AI analysis for efficiency"""
        # This would be implemented for specific models that support batch processing
        # For now, fall back to individual processing
        return None
    
    def get_feature_status(self) -> Dict[str, Any]:
        """Get current feature availability status"""
        available_features = self.get_available_features()
        
        feature_status = {}
        for analysis_type in AnalysisType:
            feature_status[analysis_type.value] = {
                "available": self.can_perform_analysis(analysis_type),
                "method": "ai_model" if self.can_perform_analysis(analysis_type) else "algorithmic",
                "tier_required": self._get_minimum_tier_for_analysis(analysis_type)
            }
        
        return {
            "current_tier": self.current_tier.value,
            "available_features": available_features,
            "feature_analysis": feature_status,
            "memory_info": self.memory_manager.get_memory_info()
        }
    
    def _get_minimum_tier_for_analysis(self, analysis_type: AnalysisType) -> str:
        """Get minimum tier required for AI-powered analysis"""
        tier_requirements = {
            AnalysisType.SENTIMENT: "BASIC",
            AnalysisType.EMOTION: "BASIC",
            AnalysisType.TOPIC: "STANDARD",
            AnalysisType.SUMMARY: "HIGH_END",
            AnalysisType.SEMANTIC: "HIGH_END",
            AnalysisType.KEYWORD: "MINIMAL",
            AnalysisType.STATS: "MINIMAL"
        }
        return tier_requirements.get(analysis_type, "MINIMAL")
    
    async def upgrade_features(self, new_tier: HardwareTier) -> Dict[str, Any]:
        """Handle feature upgrades when hardware improves"""
        old_tier = self.current_tier
        old_features = set(self.get_available_features())
        
        # Update to new tier
        self.current_tier = new_tier
        self.tier_config = self.hardware_profiler.get_tier_capabilities(new_tier)
        
        new_features = set(self.get_available_features())
        added_features = new_features - old_features
        
        logger.info(f"Hardware tier upgraded from {old_tier.value} to {new_tier.value}")
        logger.info(f"New features available: {list(added_features)}")
        
        return {
            "old_tier": old_tier.value,
            "new_tier": new_tier.value,
            "added_features": list(added_features),
            "all_features": list(new_features)
        }
