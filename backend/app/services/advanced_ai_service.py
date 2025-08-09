# Advanced AI Service - Comprehensive AI Intelligence Features

"""
Advanced AI Service for Journaling AI
Provides sophisticated AI capabilities including:
- Cross-temporal pattern analysis
- Personalized AI recommendations
- Advanced insights aggregation
- Predictive analytics
- Multi-modal AI processing
"""

import logging
import asyncio
import json
import numpy as np
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
from collections import defaultdict, Counter

# Core imports
from app.core.cache_patterns import CacheDomain, CachePatterns, CacheKeyBuilder
from app.services.cache_service import unified_cache_service
from app.services.ai_model_manager import ai_model_manager
from app.services.ai_emotion_service import ai_emotion_service, EmotionAnalysis
from app.services.ai_prompt_service import ai_prompt_service
from app.services.ai_intervention_service import ai_intervention_service
from app.core.service_interfaces import ServiceRegistry

logger = logging.getLogger(__name__)

class AnalysisTimeframe(Enum):
    """Time frames for AI analysis"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ALL_TIME = "all_time"

class InsightType(Enum):
    """Types of AI insights"""
    EMOTIONAL_PATTERNS = "emotional_patterns"
    BEHAVIORAL_TRENDS = "behavioral_trends"
    GROWTH_OPPORTUNITIES = "growth_opportunities"
    RISK_FACTORS = "risk_factors"
    POSITIVE_INDICATORS = "positive_indicators"
    RECOMMENDATION = "recommendation"
    PREDICTION = "prediction"
    CORRELATION = "correlation"

class PersonalityDimension(Enum):
    """Personality dimensions for analysis"""
    EXTRAVERSION = "extraversion"
    NEUROTICISM = "neuroticism"
    OPENNESS = "openness"
    CONSCIENTIOUSNESS = "conscientiousness"
    AGREEABLENESS = "agreeableness"

@dataclass
class AdvancedInsight:
    """Advanced AI-generated insight"""
    insight_type: InsightType
    title: str
    description: str
    confidence: float
    significance: float
    timeframe: AnalysisTimeframe
    supporting_data: Dict[str, Any]
    recommendations: List[str]
    metadata: Dict[str, Any]
    created_at: datetime

@dataclass
class PersonalityProfile:
    """User personality profile based on journal analysis"""
    dimensions: Dict[PersonalityDimension, float]
    traits: List[str]
    behavioral_patterns: Dict[str, float]
    communication_style: str
    emotional_profile: Dict[str, float]
    growth_areas: List[str]
    strengths: List[str]
    confidence_score: float
    last_updated: datetime

@dataclass
class PredictiveAnalysis:
    """Predictive analysis of user patterns"""
    predicted_mood_trends: Dict[str, float]
    risk_factors: List[Dict[str, Any]]
    opportunity_windows: List[Dict[str, Any]]
    behavioral_predictions: Dict[str, Any]
    confidence_intervals: Dict[str, Tuple[float, float]]
    recommendation_priority: List[str]
    created_at: datetime

class AdvancedAIService:
    """
    Advanced AI Service providing sophisticated intelligence features
    
    Features:
    - Cross-temporal pattern analysis across journal entries
    - Personality profiling from writing patterns
    - Predictive analytics for mood and behavior
    - Personalized recommendation engine
    - Advanced insights aggregation
    - Multi-dimensional emotional analysis
    """
    
    def __init__(self):
        self.analysis_cache = {}
        self.personality_models = self._initialize_personality_models()
        self.pattern_detectors = self._initialize_pattern_detectors()
        self.prediction_models = self._initialize_prediction_models()
        
        # Performance tracking
        self.analytics_stats = {
            "total_analyses": 0,
            "personality_profiles": 0,
            "predictions_generated": 0,
            "insights_created": 0,
            "cache_hits": 0
        }
        
        logger.info("🧠 Advanced AI Service initialized")

    def _initialize_personality_models(self) -> Dict[str, Any]:
        """Initialize personality analysis models"""
        return {
            "big_five": {
                "model_key": "personality_classifier",
                "dimensions": [dim.value for dim in PersonalityDimension],
                "confidence_threshold": 0.6
            },
            "communication_style": {
                "formal_markers": ["however", "furthermore", "consequently"],
                "casual_markers": ["like", "yeah", "kinda", "totally"],
                "emotional_markers": ["feel", "emotion", "heart", "soul"]
            },
            "writing_patterns": {
                "introspective": ["reflect", "think", "consider", "ponder"],
                "action_oriented": ["do", "will", "action", "plan"],
                "social": ["people", "friends", "family", "social"]
            }
        }

    def _initialize_pattern_detectors(self) -> Dict[str, Any]:
        """Initialize pattern detection algorithms"""
        return {
            "temporal_patterns": {
                "daily_cycles": ["morning", "afternoon", "evening", "night"],
                "weekly_cycles": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
                "seasonal_patterns": ["spring", "summer", "autumn", "winter"]
            },
            "emotional_cycles": {
                "mood_swings": {"threshold": 0.6, "window": 7},
                "stability_periods": {"threshold": 0.3, "min_duration": 14},
                "growth_periods": {"trend_threshold": 0.1, "window": 30}
            },
            "behavioral_patterns": {
                "routine_detection": {"similarity_threshold": 0.7},
                "change_detection": {"variance_threshold": 0.4},
                "goal_tracking": {"keyword_patterns": ["goal", "achieve", "accomplish"]}
            }
        }

    def _initialize_prediction_models(self) -> Dict[str, Any]:
        """Initialize predictive models"""
        return {
            "mood_prediction": {
                "model_type": "time_series",
                "lookback_window": 30,
                "prediction_horizon": 7,
                "features": ["emotion_scores", "temporal_features", "external_factors"]
            },
            "behavior_prediction": {
                "model_type": "pattern_matching",
                "similarity_threshold": 0.8,
                "confidence_decay": 0.9
            },
            "risk_assessment": {
                "crisis_indicators": ["hopeless", "worthless", "give up", "end it"],
                "stress_indicators": ["overwhelmed", "anxious", "pressure", "stress"],
                "growth_indicators": ["grateful", "progress", "better", "improvement"]
            }
        }

    # ==================== CROSS-TEMPORAL ANALYSIS ====================

    async def analyze_temporal_patterns(self, user_id: str, entries: List[Dict[str, Any]], 
                                       timeframe: AnalysisTimeframe = AnalysisTimeframe.MONTHLY) -> List[AdvancedInsight]:
        """
        Analyze patterns across different time periods
        
        Args:
            user_id: User identifier
            entries: List of journal entries with timestamps
            timeframe: Analysis timeframe
            
        Returns:
            List of advanced insights about temporal patterns
        """
        try:
            cache_key = self._build_cache_key(f"temporal_{user_id}_{timeframe.value}", entries)
            cached_insights = await unified_cache_service.get_ai_analysis_result(cache_key)
            
            if cached_insights:
                self.analytics_stats["cache_hits"] += 1
                return cached_insights
            
            insights = []
            
            # Emotional pattern analysis
            emotional_patterns = await self._analyze_emotional_temporal_patterns(entries, timeframe)
            if emotional_patterns:
                insights.append(AdvancedInsight(
                    insight_type=InsightType.EMOTIONAL_PATTERNS,
                    title="Emotional Rhythm Analysis",
                    description=f"Discovered {len(emotional_patterns)} significant emotional patterns over {timeframe.value}",
                    confidence=0.85,
                    significance=0.9,
                    timeframe=timeframe,
                    supporting_data={"patterns": emotional_patterns},
                    recommendations=self._generate_emotional_pattern_recommendations(emotional_patterns),
                    metadata={"analysis_type": "temporal", "entries_analyzed": len(entries)},
                    created_at=datetime.utcnow()
                ))

            # Behavioral trend analysis
            behavioral_trends = await self._analyze_behavioral_trends(entries, timeframe)
            if behavioral_trends:
                insights.append(AdvancedInsight(
                    insight_type=InsightType.BEHAVIORAL_TRENDS,
                    title="Behavioral Evolution Tracking",
                    description=f"Identified {len(behavioral_trends)} behavioral trends showing personal development",
                    confidence=0.8,
                    significance=0.85,
                    timeframe=timeframe,
                    supporting_data={"trends": behavioral_trends},
                    recommendations=self._generate_behavioral_recommendations(behavioral_trends),
                    metadata={"trend_analysis": True},
                    created_at=datetime.utcnow()
                ))

            # Growth opportunity identification
            growth_opportunities = await self._identify_growth_opportunities(entries, timeframe)
            if growth_opportunities:
                insights.append(AdvancedInsight(
                    insight_type=InsightType.GROWTH_OPPORTUNITIES,
                    title="Personal Growth Opportunities",
                    description=f"Found {len(growth_opportunities)} areas for potential growth and development",
                    confidence=0.75,
                    significance=0.8,
                    timeframe=timeframe,
                    supporting_data={"opportunities": growth_opportunities},
                    recommendations=self._generate_growth_recommendations(growth_opportunities),
                    metadata={"growth_analysis": True},
                    created_at=datetime.utcnow()
                ))

            # Cache results
            if insights:
                await unified_cache_service.set_ai_analysis_result(insights, cache_key, ttl=7200)  # 2 hours
                self.analytics_stats["insights_created"] += len(insights)
                self.analytics_stats["total_analyses"] += 1

            logger.info(f"🧠 Generated {len(insights)} temporal insights for user {user_id}")
            return insights

        except Exception as e:
            logger.error(f"❌ Error in temporal pattern analysis: {e}")
            return []

    async def _analyze_emotional_temporal_patterns(self, entries: List[Dict[str, Any]], 
                                                  timeframe: AnalysisTimeframe) -> List[Dict[str, Any]]:
        """Analyze emotional patterns over time"""
        patterns = []
        
        try:
            # Group entries by time periods
            time_groups = self._group_entries_by_time(entries, timeframe)
            
            # Analyze each time group
            for period, period_entries in time_groups.items():
                if len(period_entries) < 2:
                    continue
                    
                # Extract emotions for this period
                emotions = []
                for entry in period_entries:
                    if 'content' in entry:
                        emotion_analysis = await ai_emotion_service.analyze_emotions(entry['content'])
                        emotions.append({
                            'primary': emotion_analysis.primary_emotion.emotion,
                            'score': emotion_analysis.primary_emotion.score,
                            'timestamp': entry.get('created_at', datetime.utcnow())
                        })
                
                if emotions:
                    # Calculate emotional statistics for this period
                    emotion_scores = [e['score'] for e in emotions]
                    emotional_variance = statistics.variance(emotion_scores) if len(emotion_scores) > 1 else 0
                    dominant_emotion = Counter([e['primary'] for e in emotions]).most_common(1)[0]
                    
                    patterns.append({
                        'period': str(period),
                        'dominant_emotion': dominant_emotion[0],
                        'emotional_stability': 1.0 - emotional_variance,
                        'emotion_diversity': len(set(e['primary'] for e in emotions)),
                        'average_intensity': statistics.mean(emotion_scores),
                        'entries_count': len(period_entries)
                    })
            
            return patterns
            
        except Exception as e:
            logger.error(f"❌ Error in emotional temporal analysis: {e}")
            return []

    async def _analyze_behavioral_trends(self, entries: List[Dict[str, Any]], 
                                        timeframe: AnalysisTimeframe) -> List[Dict[str, Any]]:
        """Analyze behavioral trends over time"""
        trends = []
        
        try:
            # Define behavioral indicators
            behavioral_indicators = {
                'social_activity': ['friends', 'social', 'people', 'party', 'meeting'],
                'self_care': ['exercise', 'sleep', 'healthy', 'relax', 'meditation'],
                'productivity': ['work', 'accomplish', 'productive', 'goal', 'task'],
                'creativity': ['creative', 'art', 'music', 'write', 'design'],
                'learning': ['learn', 'study', 'read', 'course', 'skill']
            }
            
            # Group entries by time periods
            time_groups = self._group_entries_by_time(entries, timeframe)
            
            # Calculate trends for each behavioral dimension
            for behavior_name, keywords in behavioral_indicators.items():
                period_scores = {}
                
                for period, period_entries in time_groups.items():
                    score = 0
                    total_words = 0
                    
                    for entry in period_entries:
                        if 'content' in entry:
                            content = entry['content'].lower()
                            words = content.split()
                            total_words += len(words)
                            
                            # Count keyword matches
                            matches = sum(1 for word in words if any(kw in word for kw in keywords))
                            score += matches
                    
                    # Normalize by entry count and content length
                    if total_words > 0:
                        period_scores[period] = (score / total_words) * 100  # Percentage
                
                # Calculate trend direction
                if len(period_scores) > 1:
                    periods = sorted(period_scores.keys())
                    scores = [period_scores[p] for p in periods]
                    
                    # Simple linear trend
                    if len(scores) >= 2:
                        trend_slope = (scores[-1] - scores[0]) / len(scores)
                        trend_direction = "increasing" if trend_slope > 0.1 else "decreasing" if trend_slope < -0.1 else "stable"
                        
                        trends.append({
                            'behavior': behavior_name,
                            'trend_direction': trend_direction,
                            'trend_strength': abs(trend_slope),
                            'current_level': scores[-1] if scores else 0,
                            'change_magnitude': abs(scores[-1] - scores[0]) if len(scores) > 1 else 0,
                            'periods_analyzed': len(periods)
                        })
            
            return trends
            
        except Exception as e:
            logger.error(f"❌ Error in behavioral trend analysis: {e}")
            return []

    async def _identify_growth_opportunities(self, entries: List[Dict[str, Any]], 
                                           timeframe: AnalysisTimeframe) -> List[Dict[str, Any]]:
        """Identify growth opportunities from journal analysis"""
        opportunities = []
        
        try:
            # Analyze content for growth-related themes
            growth_themes = {
                'emotional_intelligence': ['understand', 'emotion', 'feeling', 'empathy'],
                'relationships': ['relationship', 'communication', 'connect', 'love'],
                'career_development': ['career', 'job', 'professional', 'skills'],
                'health_wellness': ['health', 'fitness', 'wellness', 'balance'],
                'creativity': ['creative', 'art', 'express', 'imagine'],
                'learning': ['learn', 'knowledge', 'grow', 'develop']
            }
            
            # Analyze mentions and sentiment for each theme
            for theme_name, keywords in growth_themes.items():
                theme_analysis = {
                    'mentions': 0,
                    'positive_context': 0,
                    'challenges_mentioned': 0,
                    'goals_set': 0
                }
                
                for entry in entries:
                    if 'content' in entry:
                        content = entry['content'].lower()
                        
                        # Count mentions
                        mentions = sum(1 for keyword in keywords if keyword in content)
                        theme_analysis['mentions'] += mentions
                        
                        if mentions > 0:
                            # Analyze sentiment context
                            emotion_analysis = await ai_emotion_service.analyze_emotions(entry['content'])
                            if emotion_analysis.sentiment_polarity > 0.3:
                                theme_analysis['positive_context'] += 1
                            
                            # Look for challenge indicators
                            challenge_words = ['difficult', 'struggle', 'hard', 'challenge', 'problem']
                            if any(word in content for word in challenge_words):
                                theme_analysis['challenges_mentioned'] += 1
                            
                            # Look for goal-setting language
                            goal_words = ['want to', 'will', 'plan to', 'goal', 'aim to']
                            if any(word in content for word in goal_words):
                                theme_analysis['goals_set'] += 1
                
                # Determine if this represents a growth opportunity
                if theme_analysis['mentions'] > 0:
                    opportunity_score = (
                        theme_analysis['challenges_mentioned'] * 0.4 +
                        theme_analysis['goals_set'] * 0.4 +
                        (theme_analysis['mentions'] - theme_analysis['positive_context']) * 0.2
                    )
                    
                    if opportunity_score > 0.5:
                        opportunities.append({
                            'theme': theme_name,
                            'opportunity_score': opportunity_score,
                            'mentions': theme_analysis['mentions'],
                            'challenges_identified': theme_analysis['challenges_mentioned'],
                            'goals_mentioned': theme_analysis['goals_set'],
                            'positive_associations': theme_analysis['positive_context'],
                            'recommendation_priority': 'high' if opportunity_score > 1.0 else 'medium'
                        })
            
            # Sort by opportunity score
            opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)
            return opportunities
            
        except Exception as e:
            logger.error(f"❌ Error in growth opportunity identification: {e}")
            return []

    # ==================== PERSONALITY PROFILING ====================

    async def generate_personality_profile(self, user_id: str, entries: List[Dict[str, Any]]) -> PersonalityProfile:
        """
        Generate comprehensive personality profile from journal entries
        
        Args:
            user_id: User identifier
            entries: List of journal entries
            
        Returns:
            Detailed personality profile
        """
        try:
            cache_key = self._build_cache_key(f"personality_{user_id}", entries)
            cached_profile = await unified_cache_service.get_ai_analysis_result(cache_key)
            
            if cached_profile:
                self.analytics_stats["cache_hits"] += 1
                return cached_profile
            
            # Analyze Big Five personality dimensions
            dimensions = await self._analyze_big_five_dimensions(entries)
            
            # Extract behavioral patterns
            behavioral_patterns = await self._analyze_behavioral_patterns(entries)
            
            # Determine communication style
            communication_style = await self._analyze_communication_style(entries)
            
            # Generate emotional profile
            emotional_profile = await self._generate_emotional_profile(entries)
            
            # Identify traits, strengths, and growth areas
            traits = self._extract_personality_traits(dimensions, behavioral_patterns)
            strengths = self._identify_strengths(dimensions, behavioral_patterns, emotional_profile)
            growth_areas = self._identify_growth_areas(dimensions, behavioral_patterns)
            
            # Calculate overall confidence
            confidence_score = self._calculate_profile_confidence(entries, dimensions)
            
            profile = PersonalityProfile(
                dimensions=dimensions,
                traits=traits,
                behavioral_patterns=behavioral_patterns,
                communication_style=communication_style,
                emotional_profile=emotional_profile,
                growth_areas=growth_areas,
                strengths=strengths,
                confidence_score=confidence_score,
                last_updated=datetime.utcnow()
            )
            
            # Cache the profile
            await unified_cache_service.set_ai_analysis_result(profile, cache_key, ttl=86400)  # 24 hours
            self.analytics_stats["personality_profiles"] += 1
            
            logger.info(f"🧠 Generated personality profile for user {user_id} (confidence: {confidence_score:.2f})")
            return profile
            
        except Exception as e:
            logger.error(f"❌ Error generating personality profile: {e}")
            return self._generate_fallback_profile()

    async def _analyze_big_five_dimensions(self, entries: List[Dict[str, Any]]) -> Dict[PersonalityDimension, float]:
        """Analyze Big Five personality dimensions from text"""
        dimensions = {}
        
        try:
            # Define dimension indicators
            dimension_indicators = {
                PersonalityDimension.EXTRAVERSION: {
                    'high': ['social', 'party', 'people', 'outgoing', 'energy'],
                    'low': ['quiet', 'alone', 'solitude', 'introverted', 'peaceful']
                },
                PersonalityDimension.NEUROTICISM: {
                    'high': ['anxious', 'worry', 'stress', 'nervous', 'overwhelmed'],
                    'low': ['calm', 'stable', 'relaxed', 'confident', 'secure']
                },
                PersonalityDimension.OPENNESS: {
                    'high': ['creative', 'art', 'new', 'explore', 'imagine'],
                    'low': ['routine', 'practical', 'traditional', 'conventional']
                },
                PersonalityDimension.CONSCIENTIOUSNESS: {
                    'high': ['organized', 'plan', 'responsible', 'goal', 'discipline'],
                    'low': ['spontaneous', 'flexible', 'casual', 'free']
                },
                PersonalityDimension.AGREEABLENESS: {
                    'high': ['kind', 'helpful', 'cooperative', 'caring', 'trust'],
                    'low': ['competitive', 'critical', 'independent', 'assertive']
                }
            }
            
            for dimension, indicators in dimension_indicators.items():
                high_score = 0
                low_score = 0
                total_words = 0
                
                for entry in entries:
                    if 'content' in entry:
                        content = entry['content'].lower()
                        words = content.split()
                        total_words += len(words)
                        
                        # Count high and low indicators
                        high_score += sum(1 for word in words if any(ind in word for ind in indicators['high']))
                        low_score += sum(1 for word in words if any(ind in word for ind in indicators['low']))
                
                # Calculate dimension score (0-1 scale)
                if total_words > 0:
                    high_ratio = high_score / total_words
                    low_ratio = low_score / total_words
                    
                    # Score represents tendency toward high end of dimension
                    if high_ratio + low_ratio > 0:
                        dimension_score = high_ratio / (high_ratio + low_ratio)
                    else:
                        dimension_score = 0.5  # Neutral if no indicators
                    
                    dimensions[dimension] = min(max(dimension_score, 0.0), 1.0)
                else:
                    dimensions[dimension] = 0.5
            
            return dimensions
            
        except Exception as e:
            logger.error(f"❌ Error in Big Five analysis: {e}")
            return {dim: 0.5 for dim in PersonalityDimension}

    async def _analyze_behavioral_patterns(self, entries: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze behavioral patterns from journal entries"""
        patterns = {}
        
        try:
            # Define behavioral pattern indicators
            pattern_indicators = {
                'routine_oriented': ['routine', 'schedule', 'plan', 'organize', 'structure'],
                'spontaneous': ['spontaneous', 'sudden', 'unexpected', 'impulse', 'random'],
                'reflective': ['think', 'reflect', 'consider', 'ponder', 'contemplate'],
                'action_oriented': ['do', 'action', 'execute', 'implement', 'achieve'],
                'social_seeking': ['friends', 'social', 'together', 'group', 'community'],
                'independence': ['alone', 'independent', 'self', 'own', 'individual'],
                'growth_minded': ['learn', 'grow', 'improve', 'develop', 'better'],
                'risk_taking': ['risk', 'adventure', 'challenge', 'bold', 'daring']
            }
            
            total_words = sum(len(entry.get('content', '').split()) for entry in entries)
            
            for pattern_name, keywords in pattern_indicators.items():
                keyword_count = 0
                
                for entry in entries:
                    if 'content' in entry:
                        content = entry['content'].lower()
                        words = content.split()
                        keyword_count += sum(1 for word in words if any(kw in word for kw in keywords))
                
                # Normalize by total word count
                if total_words > 0:
                    patterns[pattern_name] = (keyword_count / total_words) * 100  # Percentage
                else:
                    patterns[pattern_name] = 0.0
            
            return patterns
            
        except Exception as e:
            logger.error(f"❌ Error in behavioral pattern analysis: {e}")
            return {}

    async def _analyze_communication_style(self, entries: List[Dict[str, Any]]) -> str:
        """Analyze communication style from writing patterns"""
        try:
            style_scores = {
                'formal': 0,
                'casual': 0,
                'emotional': 0,
                'analytical': 0
            }
            
            for entry in entries:
                if 'content' in entry:
                    content = entry['content']
                    
                    # Formal indicators
                    formal_markers = ['however', 'furthermore', 'consequently', 'therefore']
                    style_scores['formal'] += sum(1 for marker in formal_markers if marker in content.lower())
                    
                    # Casual indicators
                    casual_markers = ['like', 'yeah', 'kinda', 'totally', 'awesome']
                    style_scores['casual'] += sum(1 for marker in casual_markers if marker in content.lower())
                    
                    # Emotional indicators
                    emotional_markers = ['feel', 'emotion', 'heart', 'soul', '!']
                    style_scores['emotional'] += sum(1 for marker in emotional_markers if marker in content.lower())
                    
                    # Analytical indicators
                    analytical_markers = ['analyze', 'consider', 'evaluate', 'assess', 'examine']
                    style_scores['analytical'] += sum(1 for marker in analytical_markers if marker in content.lower())
            
            # Determine dominant style
            if style_scores:
                dominant_style = max(style_scores.items(), key=lambda x: x[1])[0]
                return dominant_style
            else:
                return 'balanced'
                
        except Exception as e:
            logger.error(f"❌ Error in communication style analysis: {e}")
            return 'unknown'

    # ==================== PREDICTIVE ANALYTICS ====================

    async def generate_predictive_analysis(self, user_id: str, entries: List[Dict[str, Any]], 
                                          prediction_horizon: int = 7) -> PredictiveAnalysis:
        """
        Generate predictive analysis for user patterns
        
        Args:
            user_id: User identifier
            entries: Historical journal entries
            prediction_horizon: Days to predict ahead
            
        Returns:
            Predictive analysis with forecasts and recommendations
        """
        try:
            cache_key = self._build_cache_key(f"prediction_{user_id}_{prediction_horizon}", entries)
            cached_analysis = await unified_cache_service.get_ai_analysis_result(cache_key)
            
            if cached_analysis:
                self.analytics_stats["cache_hits"] += 1
                return cached_analysis
            
            # Predict mood trends
            predicted_moods = await self._predict_mood_trends(entries, prediction_horizon)
            
            # Identify risk factors
            risk_factors = await self._identify_risk_factors(entries)
            
            # Find opportunity windows
            opportunities = await self._identify_opportunity_windows(entries, prediction_horizon)
            
            # Generate behavioral predictions
            behavior_predictions = await self._predict_behavioral_patterns(entries, prediction_horizon)
            
            # Calculate confidence intervals
            confidence_intervals = self._calculate_prediction_confidence(entries, predicted_moods)
            
            # Generate priority recommendations
            recommendations = self._generate_predictive_recommendations(
                predicted_moods, risk_factors, opportunities
            )
            
            analysis = PredictiveAnalysis(
                predicted_mood_trends=predicted_moods,
                risk_factors=risk_factors,
                opportunity_windows=opportunities,
                behavioral_predictions=behavior_predictions,
                confidence_intervals=confidence_intervals,
                recommendation_priority=recommendations,
                created_at=datetime.utcnow()
            )
            
            # Cache results
            await unified_cache_service.set_ai_analysis_result(analysis, cache_key, ttl=14400)  # 4 hours
            self.analytics_stats["predictions_generated"] += 1
            
            logger.info(f"🔮 Generated predictive analysis for user {user_id} ({prediction_horizon} day horizon)")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error in predictive analysis: {e}")
            return self._generate_fallback_prediction()

    async def _predict_mood_trends(self, entries: List[Dict[str, Any]], 
                                  horizon: int) -> Dict[str, float]:
        """Predict mood trends for future periods"""
        try:
            # Get historical mood scores
            mood_history = []
            for entry in sorted(entries, key=lambda x: x.get('created_at', datetime.now())):
                if 'content' in entry:
                    emotion_analysis = await ai_emotion_service.analyze_emotions(entry['content'])
                    mood_history.append({
                        'date': entry.get('created_at', datetime.now()),
                        'sentiment': emotion_analysis.sentiment_polarity,
                        'primary_emotion': emotion_analysis.primary_emotion.emotion,
                        'intensity': emotion_analysis.primary_emotion.score
                    })
            
            if len(mood_history) < 3:
                return {'sentiment_trend': 0.0, 'confidence': 0.3}
            
            # Simple trend analysis (in a real implementation, this would use more sophisticated ML)
            recent_sentiments = [m['sentiment'] for m in mood_history[-7:]]  # Last 7 entries
            older_sentiments = [m['sentiment'] for m in mood_history[-14:-7] if len(mood_history) > 7]
            
            if older_sentiments:
                trend = statistics.mean(recent_sentiments) - statistics.mean(older_sentiments)
                predicted_sentiment = statistics.mean(recent_sentiments) + (trend * 0.5)
            else:
                predicted_sentiment = statistics.mean(recent_sentiments)
            
            # Predict dominant emotions
            recent_emotions = [m['primary_emotion'] for m in mood_history[-7:]]
            emotion_counts = Counter(recent_emotions)
            likely_emotions = dict(emotion_counts.most_common(3))
            
            predictions = {
                'sentiment_trend': predicted_sentiment,
                'likely_emotions': likely_emotions,
                'trend_direction': 'improving' if trend > 0.1 else 'declining' if trend < -0.1 else 'stable',
                'confidence': min(len(mood_history) / 30.0, 1.0)  # Higher confidence with more data
            }
            
            return predictions
            
        except Exception as e:
            logger.error(f"❌ Error in mood trend prediction: {e}")
            return {'sentiment_trend': 0.0, 'confidence': 0.1}

    # ==================== UTILITY METHODS ====================

    def _group_entries_by_time(self, entries: List[Dict[str, Any]], 
                              timeframe: AnalysisTimeframe) -> Dict[Any, List[Dict[str, Any]]]:
        """Group entries by time periods"""
        groups = defaultdict(list)
        
        for entry in entries:
            created_at = entry.get('created_at', datetime.now())
            
            if timeframe == AnalysisTimeframe.DAILY:
                key = created_at.date()
            elif timeframe == AnalysisTimeframe.WEEKLY:
                key = created_at.isocalendar()[1]  # Week number
            elif timeframe == AnalysisTimeframe.MONTHLY:
                key = (created_at.year, created_at.month)
            elif timeframe == AnalysisTimeframe.QUARTERLY:
                key = (created_at.year, (created_at.month - 1) // 3 + 1)
            elif timeframe == AnalysisTimeframe.YEARLY:
                key = created_at.year
            else:
                key = 'all_time'
            
            groups[key].append(entry)
        
        return dict(groups)

    def _build_cache_key(self, base_key: str, entries: List[Dict[str, Any]]) -> str:
        """Build cache key for analysis results"""
        entry_hash = hash(str(sorted([e.get('id', str(hash(str(e)))) for e in entries])))
        return CachePatterns.ai_model_instance(f"{base_key}_{entry_hash}", "latest")

    def _generate_emotional_pattern_recommendations(self, patterns: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on emotional patterns"""
        recommendations = []
        
        for pattern in patterns:
            stability = pattern.get('emotional_stability', 0.5)
            if stability < 0.3:
                recommendations.append("Consider implementing daily mindfulness practices to improve emotional stability")
            
            diversity = pattern.get('emotion_diversity', 1)
            if diversity < 2:
                recommendations.append("Try exploring new activities to expand your emotional experiences")
        
        return recommendations or ["Continue monitoring your emotional patterns for insights"]

    def _generate_behavioral_recommendations(self, trends: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on behavioral trends"""
        recommendations = []
        
        for trend in trends:
            if trend['behavior'] == 'self_care' and trend['trend_direction'] == 'decreasing':
                recommendations.append("Consider prioritizing self-care activities in your routine")
            elif trend['behavior'] == 'social_activity' and trend['current_level'] < 1.0:
                recommendations.append("Explore opportunities for meaningful social connections")
        
        return recommendations or ["Your behavioral patterns show positive development"]

    def _generate_growth_recommendations(self, opportunities: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on growth opportunities"""
        recommendations = []
        
        for opportunity in opportunities[:3]:  # Top 3 opportunities
            theme = opportunity['theme']
            if theme == 'emotional_intelligence':
                recommendations.append("Consider exploring emotional awareness exercises and reflection techniques")
            elif theme == 'relationships':
                recommendations.append("Focus on developing communication skills and empathy practices")
            elif theme == 'health_wellness':
                recommendations.append("Create a balanced approach to physical and mental wellness")
        
        return recommendations or ["Continue your current growth trajectory"]

    def _extract_personality_traits(self, dimensions: Dict[PersonalityDimension, float], 
                                   patterns: Dict[str, float]) -> List[str]:
        """Extract personality traits from analysis"""
        traits = []
        
        for dimension, score in dimensions.items():
            if score > 0.7:
                if dimension == PersonalityDimension.EXTRAVERSION:
                    traits.append("outgoing")
                elif dimension == PersonalityDimension.OPENNESS:
                    traits.append("creative")
                elif dimension == PersonalityDimension.CONSCIENTIOUSNESS:
                    traits.append("organized")
            elif score < 0.3:
                if dimension == PersonalityDimension.EXTRAVERSION:
                    traits.append("introspective")
                elif dimension == PersonalityDimension.NEUROTICISM:
                    traits.append("emotionally_stable")
        
        # Add pattern-based traits
        if patterns.get('reflective', 0) > 2.0:
            traits.append("thoughtful")
        if patterns.get('growth_minded', 0) > 1.5:
            traits.append("growth_oriented")
        
        return traits[:5]  # Limit to top 5 traits

    def _identify_strengths(self, dimensions: Dict[PersonalityDimension, float], 
                           patterns: Dict[str, float], 
                           emotional_profile: Dict[str, float]) -> List[str]:
        """Identify user strengths"""
        strengths = []
        
        if dimensions.get(PersonalityDimension.CONSCIENTIOUSNESS, 0.5) > 0.7:
            strengths.append("Strong organizational skills")
        if patterns.get('reflective', 0) > 2.0:
            strengths.append("Deep self-awareness")
        if patterns.get('growth_minded', 0) > 1.5:
            strengths.append("Commitment to personal development")
        
        return strengths[:3]

    def _identify_growth_areas(self, dimensions: Dict[PersonalityDimension, float], 
                              patterns: Dict[str, float]) -> List[str]:
        """Identify areas for growth"""
        growth_areas = []
        
        if dimensions.get(PersonalityDimension.NEUROTICISM, 0.5) > 0.7:
            growth_areas.append("Emotional regulation and stress management")
        if patterns.get('social_seeking', 0) < 0.5:
            growth_areas.append("Building social connections")
        
        return growth_areas[:3]

    def _calculate_profile_confidence(self, entries: List[Dict[str, Any]], 
                                     dimensions: Dict[PersonalityDimension, float]) -> float:
        """Calculate confidence score for personality profile"""
        # Base confidence on amount of data
        data_confidence = min(len(entries) / 50.0, 1.0)  # More confident with more entries
        
        # Adjust based on dimension clarity
        dimension_clarity = statistics.mean([
            abs(score - 0.5) * 2 for score in dimensions.values()
        ]) if dimensions else 0
        
        return (data_confidence * 0.7) + (dimension_clarity * 0.3)

    async def _generate_emotional_profile(self, entries: List[Dict[str, Any]]) -> Dict[str, float]:
        """Generate emotional profile from entries"""
        emotion_counts = defaultdict(int)
        total_entries = 0
        
        for entry in entries:
            if 'content' in entry:
                emotion_analysis = await ai_emotion_service.analyze_emotions(entry['content'])
                emotion_counts[emotion_analysis.primary_emotion.emotion] += 1
                total_entries += 1
        
        # Convert to percentages
        if total_entries > 0:
            return {emotion: (count / total_entries) * 100 
                   for emotion, count in emotion_counts.items()}
        return {}

    def _generate_fallback_profile(self) -> PersonalityProfile:
        """Generate fallback personality profile"""
        return PersonalityProfile(
            dimensions={dim: 0.5 for dim in PersonalityDimension},
            traits=["developing"],
            behavioral_patterns={},
            communication_style="unknown",
            emotional_profile={},
            growth_areas=["Need more data for analysis"],
            strengths=["Commitment to self-reflection through journaling"],
            confidence_score=0.1,
            last_updated=datetime.utcnow()
        )

    async def _identify_risk_factors(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify potential risk factors from entries"""
        risk_factors = []
        
        risk_indicators = {
            'crisis_risk': ['hopeless', 'worthless', 'give up', 'end it all', 'no point'],
            'depression_risk': ['depressed', 'sad', 'empty', 'numb', 'meaningless'],
            'anxiety_risk': ['anxious', 'panic', 'overwhelmed', 'worry', 'fear'],
            'isolation_risk': ['alone', 'lonely', 'isolated', 'no friends', 'nobody']
        }
        
        for risk_type, indicators in risk_indicators.items():
            risk_score = 0
            mentions = 0
            
            for entry in entries:
                if 'content' in entry:
                    content = entry['content'].lower()
                    for indicator in indicators:
                        if indicator in content:
                            mentions += 1
                            risk_score += 1
            
            if mentions > 0:
                risk_factors.append({
                    'type': risk_type,
                    'mentions': mentions,
                    'risk_score': min(risk_score / len(entries), 1.0),
                    'severity': 'high' if risk_score > len(entries) * 0.3 else 'medium' if risk_score > len(entries) * 0.1 else 'low'
                })
        
        return risk_factors

    async def _identify_opportunity_windows(self, entries: List[Dict[str, Any]], 
                                          horizon: int) -> List[Dict[str, Any]]:
        """Identify windows of opportunity for growth"""
        # This is a simplified implementation
        opportunities = []
        
        # Look for patterns of motivation or goal-setting
        motivation_keywords = ['motivated', 'goal', 'want to', 'will', 'determined']
        
        recent_entries = entries[-7:]  # Last week
        motivation_mentions = 0
        
        for entry in recent_entries:
            if 'content' in entry:
                content = entry['content'].lower()
                motivation_mentions += sum(1 for keyword in motivation_keywords if keyword in content)
        
        if motivation_mentions > 0:
            opportunities.append({
                'type': 'motivation_window',
                'description': 'Current high motivation period detected',
                'strength': motivation_mentions / len(recent_entries),
                'recommended_actions': ['Set specific goals', 'Create action plans', 'Track progress']
            })
        
        return opportunities

    async def _predict_behavioral_patterns(self, entries: List[Dict[str, Any]], 
                                         horizon: int) -> Dict[str, Any]:
        """Predict future behavioral patterns"""
        # Simplified behavioral prediction
        behavioral_trends = await self._analyze_behavioral_trends(entries, AnalysisTimeframe.WEEKLY)
        
        predictions = {}
        for trend in behavioral_trends:
            behavior = trend['behavior']
            current_level = trend['current_level']
            trend_direction = trend['trend_direction']
            
            if trend_direction == 'increasing':
                predicted_level = min(current_level * 1.1, 100.0)
            elif trend_direction == 'decreasing':
                predicted_level = max(current_level * 0.9, 0.0)
            else:
                predicted_level = current_level
            
            predictions[behavior] = {
                'current': current_level,
                'predicted': predicted_level,
                'confidence': 0.6 if len(entries) > 10 else 0.3
            }
        
        return predictions

    def _calculate_prediction_confidence(self, entries: List[Dict[str, Any]], 
                                       predictions: Dict[str, float]) -> Dict[str, Tuple[float, float]]:
        """Calculate confidence intervals for predictions"""
        confidence_intervals = {}
        
        # Base confidence on data amount
        base_confidence = min(len(entries) / 30.0, 0.9)
        
        for key, prediction in predictions.items():
            if isinstance(prediction, (int, float)):
                margin = (1.0 - base_confidence) * prediction
                confidence_intervals[key] = (
                    max(prediction - margin, 0.0),
                    min(prediction + margin, 1.0)
                )
        
        return confidence_intervals

    def _generate_predictive_recommendations(self, mood_predictions: Dict[str, float], 
                                           risk_factors: List[Dict[str, Any]], 
                                           opportunities: List[Dict[str, Any]]) -> List[str]:
        """Generate priority recommendations based on predictions"""
        recommendations = []
        
        # High priority: Address risk factors
        high_risk_factors = [rf for rf in risk_factors if rf.get('severity') == 'high']
        if high_risk_factors:
            recommendations.append("Prioritize addressing identified risk factors - consider professional support")
        
        # Medium priority: Capitalize on opportunities
        if opportunities:
            recommendations.append("Take advantage of current motivation windows for goal setting")
        
        # Mood-based recommendations
        sentiment_trend = mood_predictions.get('sentiment_trend', 0)
        if sentiment_trend < -0.3:
            recommendations.append("Focus on mood-boosting activities and self-care")
        elif sentiment_trend > 0.3:
            recommendations.append("Maintain current positive trajectory with continued healthy habits")
        
        return recommendations[:5]  # Limit to top 5 recommendations

    def _generate_fallback_prediction(self) -> PredictiveAnalysis:
        """Generate fallback prediction when analysis fails"""
        return PredictiveAnalysis(
            predicted_mood_trends={'sentiment_trend': 0.0, 'confidence': 0.1},
            risk_factors=[],
            opportunity_windows=[],
            behavioral_predictions={},
            confidence_intervals={},
            recommendation_priority=["Continue journaling to build analysis foundation"],
            created_at=datetime.utcnow()
        )

    # ==================== MONITORING AND STATISTICS ====================

    def get_service_stats(self) -> Dict[str, Any]:
        """Get advanced AI service statistics"""
        total = max(self.analytics_stats["total_analyses"], 1)
        return {
            "total_analyses": self.analytics_stats["total_analyses"],
            "cache_hit_rate": (self.analytics_stats["cache_hits"] / total) * 100,
            "personality_profiles_generated": self.analytics_stats["personality_profiles"],
            "predictions_generated": self.analytics_stats["predictions_generated"],
            "insights_created": self.analytics_stats["insights_created"],
            "service_status": "operational"
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on advanced AI service"""
        health = {
            "status": "healthy",
            "dependencies_available": True,
            "cache_operational": False,
            "service_stats": self.get_service_stats()
        }
        
        try:
            # Check dependencies
            emotion_service_health = await ai_emotion_service.health_check()
            health["emotion_service_healthy"] = emotion_service_health.get("status") == "healthy"
            
            # Check cache
            test_key = "health_check_advanced_ai"
            test_data = {"test": "data"}
            await unified_cache_service.set_ai_analysis_result(test_data, test_key, ttl=60)
            cached_data = await unified_cache_service.get_ai_analysis_result(test_key)
            health["cache_operational"] = cached_data is not None
            
            # Overall status
            if not health["emotion_service_healthy"] or not health["cache_operational"]:
                health["status"] = "degraded"
            
        except Exception as e:
            health["status"] = "error"
            health["error"] = str(e)
        
        return health

# ==================== SERVICE INSTANCE ====================

# Global Advanced AI Service instance
advanced_ai_service = AdvancedAIService()

# Integration with service registry
def register_advanced_ai_service():
    """Register Advanced AI Service in service registry"""
    try:
        from app.core.service_interfaces import service_registry
        service_registry.register_service("advanced_ai_service", advanced_ai_service)
        logger.info("✅ Advanced AI Service registered in service registry")
    except Exception as e:
        logger.error(f"❌ Failed to register Advanced AI Service: {e}")

# Auto-register when module is imported
register_advanced_ai_service()

# Export key classes and functions
__all__ = [
    'AdvancedAIService',
    'advanced_ai_service',
    'AdvancedInsight',
    'PersonalityProfile',
    'PredictiveAnalysis',
    'AnalysisTimeframe',
    'InsightType',
    'PersonalityDimension'
]