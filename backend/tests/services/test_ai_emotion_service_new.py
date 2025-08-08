import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.services.ai_emotion_service import (
    AIEmotionService, 
    EmotionCategory, 
    EmotionIntensity, 
    EmotionScore, 
    EmotionAnalysis
)

class TestAIEmotionService:
    """Test AI emotion analysis service functionality"""

    @pytest.fixture
    def emotion_service(self):
        """Create emotion service instance for testing"""
        with patch('app.services.ai_model_manager.ai_model_manager'), \
             patch('app.services.cache_service.unified_cache_service'), \
             patch('app.core.service_interfaces.ServiceRegistry'):
            return AIEmotionService()

    @pytest.fixture
    def sample_emotional_texts(self):
        """Sample emotional text for testing"""
        return {
            "positive": "I feel absolutely wonderful today! Life is amazing and I'm so grateful.",
            "negative": "I'm feeling really down and disappointed. Everything seems hopeless.",
            "mixed": "I'm excited about the opportunity but also nervous about the challenges.",
            "neutral": "Today I went to the store and bought some groceries. It was a normal day.",
            "complex": "While I'm heartbroken about the loss, I also feel grateful for the memories we shared."
        }

    def test_emotion_category_enum(self):
        """Test EmotionCategory enum values"""
        assert EmotionCategory.JOY.value == "joy"
        assert EmotionCategory.SADNESS.value == "sadness"
        assert EmotionCategory.ANGER.value == "anger"
        assert EmotionCategory.FEAR.value == "fear"
        assert EmotionCategory.SURPRISE.value == "surprise"
        assert EmotionCategory.DISGUST.value == "disgust"
        assert EmotionCategory.TRUST.value == "trust"
        assert EmotionCategory.ANTICIPATION.value == "anticipation"
        print("✓ EmotionCategory enum test passed")

    def test_emotion_intensity_enum(self):
        """Test EmotionIntensity enum values"""
        assert EmotionIntensity.VERY_LOW.value == "very_low"
        assert EmotionIntensity.LOW.value == "low"
        assert EmotionIntensity.MODERATE.value == "moderate"
        assert EmotionIntensity.HIGH.value == "high"
        assert EmotionIntensity.VERY_HIGH.value == "very_high"
        print("✓ EmotionIntensity enum test passed")

    def test_emotion_score_creation(self):
        """Test EmotionScore dataclass creation"""
        score = EmotionScore(
            emotion="happiness",
            score=0.85,
            confidence=0.92,
            category=EmotionCategory.JOY,
            intensity=EmotionIntensity.HIGH
        )
        
        assert score.emotion == "happiness"
        assert score.score == 0.85
        assert score.confidence == 0.92
        assert score.category == EmotionCategory.JOY
        assert score.intensity == EmotionIntensity.HIGH
        print("✓ EmotionScore dataclass test passed")

    def test_emotion_analysis_creation(self):
        """Test EmotionAnalysis dataclass creation"""
        primary_emotion = EmotionScore(
            emotion="joy",
            score=0.9,
            confidence=0.95,
            category=EmotionCategory.JOY,
            intensity=EmotionIntensity.HIGH
        )
        
        secondary_emotions = [
            EmotionScore("gratitude", 0.7, 0.8, EmotionCategory.JOY, EmotionIntensity.MODERATE)
        ]
        
        analysis = EmotionAnalysis(
            text="I feel amazing!",
            primary_emotion=primary_emotion,
            secondary_emotions=secondary_emotions,
            emotional_complexity=0.6,
            sentiment_polarity=0.9,
            emotional_stability=0.8,
            detected_patterns=["gratitude", "enthusiasm"],
            analysis_metadata={"model_version": "v1.0", "processing_time": 0.15},
            created_at=datetime.now()
        )
        
        assert analysis.text == "I feel amazing!"
        assert analysis.primary_emotion.emotion == "joy"
        assert len(analysis.secondary_emotions) == 1
        assert analysis.emotional_complexity == 0.6
        print("✓ EmotionAnalysis dataclass test passed")

    def test_service_initialization(self, emotion_service):
        """Test emotion service initialization"""
        assert emotion_service is not None
        assert hasattr(emotion_service, 'emotion_models')
        assert hasattr(emotion_service, 'emotion_patterns')
        assert hasattr(emotion_service, 'analysis_stats')
        
        # Check initial stats
        assert emotion_service.analysis_stats['total_analyses'] == 0
        assert emotion_service.analysis_stats['cache_hits'] == 0
        print("✓ Service initialization test passed")

    @pytest.mark.asyncio
    async def test_analyze_emotions_positive_text(self, emotion_service, sample_emotional_texts):
        """Test emotion analysis for positive text"""
        with patch.object(emotion_service, '_perform_ai_analysis') as mock_analysis:
            # Mock positive emotion analysis
            mock_primary = EmotionScore(
                emotion="joy",
                score=0.9,
                confidence=0.95,
                category=EmotionCategory.JOY,
                intensity=EmotionIntensity.HIGH
            )
            
            mock_result = EmotionAnalysis(
                text=sample_emotional_texts["positive"],
                primary_emotion=mock_primary,
                secondary_emotions=[],
                emotional_complexity=0.3,
                sentiment_polarity=0.9,
                emotional_stability=0.8,
                detected_patterns=["gratitude", "enthusiasm"],
                analysis_metadata={},
                created_at=datetime.now()
            )
            
            mock_analysis.return_value = mock_result
            
            result = await emotion_service.analyze_emotions(sample_emotional_texts["positive"])
            
            assert result is not None
            assert result.primary_emotion.category == EmotionCategory.JOY
            assert result.sentiment_polarity > 0.5
            mock_analysis.assert_called_once()
        
        print("✓ Positive emotion analysis test passed")

    @pytest.mark.asyncio
    async def test_analyze_emotions_negative_text(self, emotion_service, sample_emotional_texts):
        """Test emotion analysis for negative text"""
        with patch.object(emotion_service, '_perform_ai_analysis') as mock_analysis:
            # Mock negative emotion analysis
            mock_primary = EmotionScore(
                emotion="sadness",
                score=0.85,
                confidence=0.9,
                category=EmotionCategory.SADNESS,
                intensity=EmotionIntensity.HIGH
            )
            
            mock_result = EmotionAnalysis(
                text=sample_emotional_texts["negative"],
                primary_emotion=mock_primary,
                secondary_emotions=[],
                emotional_complexity=0.4,
                sentiment_polarity=-0.8,
                emotional_stability=0.3,
                detected_patterns=["hopelessness", "disappointment"],
                analysis_metadata={},
                created_at=datetime.now()
            )
            
            mock_analysis.return_value = mock_result
            
            result = await emotion_service.analyze_emotions(sample_emotional_texts["negative"])
            
            assert result is not None
            assert result.primary_emotion.category == EmotionCategory.SADNESS
            assert result.sentiment_polarity < -0.5
            mock_analysis.assert_called_once()
        
        print("✓ Negative emotion analysis test passed")

    @pytest.mark.asyncio
    async def test_analyze_emotions_mixed_emotions(self, emotion_service, sample_emotional_texts):
        """Test emotion analysis for mixed emotional content"""
        with patch.object(emotion_service, '_perform_ai_analysis') as mock_analysis:
            # Mock mixed emotion analysis
            mock_primary = EmotionScore(
                emotion="excitement",
                score=0.7,
                confidence=0.8,
                category=EmotionCategory.ANTICIPATION,
                intensity=EmotionIntensity.MODERATE
            )
            
            mock_secondary = [
                EmotionScore(
                    emotion="anxiety",
                    score=0.6,
                    confidence=0.75,
                    category=EmotionCategory.FEAR,
                    intensity=EmotionIntensity.MODERATE
                )
            ]
            
            mock_result = EmotionAnalysis(
                text=sample_emotional_texts["mixed"],
                primary_emotion=mock_primary,
                secondary_emotions=mock_secondary,
                emotional_complexity=0.8,
                sentiment_polarity=0.1,
                emotional_stability=0.5,
                detected_patterns=["ambivalence", "mixed_feelings"],
                analysis_metadata={},
                created_at=datetime.now()
            )
            
            mock_analysis.return_value = mock_result
            
            result = await emotion_service.analyze_emotions(sample_emotional_texts["mixed"])
            
            assert result is not None
            assert len(result.secondary_emotions) > 0
            assert result.emotional_complexity > 0.7
            mock_analysis.assert_called_once()
        
        print("✓ Mixed emotion analysis test passed")

    @pytest.mark.asyncio
    async def test_caching_behavior(self, emotion_service):
        """Test emotion analysis caching functionality"""
        test_text = "I feel happy and excited about the future!"
        
        with patch('app.services.cache_service.unified_cache_service') as mock_cache:
            # First call - cache miss
            mock_cache.get.return_value = None
            
            with patch.object(emotion_service, '_perform_ai_analysis') as mock_analysis:
                mock_result = Mock()
                mock_analysis.return_value = mock_result
                
                result1 = await emotion_service.analyze_emotions(test_text)
                
                # Should call AI analysis and cache result
                mock_analysis.assert_called_once()
                mock_cache.set.assert_called_once()
            
            # Second call - cache hit
            mock_cache.get.return_value = mock_result
            
            with patch.object(emotion_service, '_perform_ai_analysis') as mock_analysis2:
                result2 = await emotion_service.analyze_emotions(test_text)
                
                # Should not call AI analysis
                mock_analysis2.assert_not_called()
        
        print("✓ Emotion analysis caching test passed")

    @pytest.mark.asyncio
    async def test_error_handling(self, emotion_service):
        """Test error handling in emotion analysis"""
        with patch.object(emotion_service, '_perform_ai_analysis') as mock_analysis:
            # Mock AI analysis failure
            mock_analysis.side_effect = Exception("AI service unavailable")
            
            # Should handle error gracefully
            with pytest.raises(Exception):
                await emotion_service.analyze_emotions("Test text")
        
        print("✓ Error handling test passed")

    @pytest.mark.asyncio
    async def test_performance_stats_tracking(self, emotion_service):
        """Test performance statistics tracking"""
        initial_count = emotion_service.analysis_stats['total_analyses']
        
        with patch.object(emotion_service, '_perform_ai_analysis') as mock_analysis:
            mock_result = Mock()
            mock_analysis.return_value = mock_result
            
            await emotion_service.analyze_emotions("Test text")
            
            # Should increment analysis counter
            assert emotion_service.analysis_stats['total_analyses'] == initial_count + 1
        
        print("✓ Performance stats tracking test passed")

    def test_emotion_intensity_classification(self, emotion_service):
        """Test emotion intensity classification logic"""
        # Test score to intensity mapping
        test_cases = [
            (0.1, EmotionIntensity.VERY_LOW),
            (0.3, EmotionIntensity.LOW),
            (0.5, EmotionIntensity.MODERATE),
            (0.7, EmotionIntensity.HIGH),
            (0.9, EmotionIntensity.VERY_HIGH)
        ]
        
        for score, expected_intensity in test_cases:
            intensity = emotion_service._classify_intensity(score)
            assert intensity == expected_intensity
        
        print("✓ Emotion intensity classification test passed")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])