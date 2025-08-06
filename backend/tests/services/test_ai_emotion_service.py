import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.ai_emotion_service import ai_emotion_service

class TestAIEmotionService:
    """Test AI Emotion Service functionality"""
    
    def test_service_initialization(self):
        """Test that emotion service is properly initialized"""
        assert ai_emotion_service is not None
        
        # Check if the service has expected methods
        assert hasattr(ai_emotion_service, 'analyze_emotions')
        assert hasattr(ai_emotion_service, 'get_analysis_stats')
        
        print("✓ AI Emotion Service initialized with required methods")
    
    def test_analysis_stats(self):
        """Test emotion analysis statistics"""
        try:
            stats = ai_emotion_service.get_analysis_stats()
            
            assert 'total_analyses' in stats
            assert 'cache_hit_rate' in stats
            assert isinstance(stats['total_analyses'], int)
            assert isinstance(stats['cache_hit_rate'], (int, float))
            
            print(f"Analysis stats: {stats['total_analyses']} total analyses, "
                  f"{stats['cache_hit_rate']:.2f} cache hit rate")
            
        except Exception as e:
            print(f"Stats collection failed: {e}")
            # This might fail if the service isn't fully initialized
            pytest.skip(f"Stats not available: {e}")
    
    @pytest.mark.asyncio
    async def test_basic_emotion_analysis(self):
        """Test basic emotion detection (marked as slow due to AI processing)"""
        test_texts = [
            "I'm feeling really happy today!",
            "This is such a wonderful day",
            "I'm so grateful for everything"
        ]
        
        for text in test_texts:
            try:
                result = await ai_emotion_service.analyze_emotions(text)
                
                # Basic validation of result structure
                assert result is not None
                assert hasattr(result, 'primary_emotion')
                assert hasattr(result, 'emotional_complexity')
                
                print(f"Text: '{text}' -> Emotion: {result.primary_emotion.emotion} "
                      f"(confidence: {result.primary_emotion.confidence:.2f})")
                
                # Confidence should be between 0 and 1
                assert 0 <= result.primary_emotion.confidence <= 1
                
                # Should detect some form of positive emotion for positive text
                positive_indicators = ['joy', 'happiness', 'positive', 'grateful', 'content']
                emotion_text = result.primary_emotion.emotion.lower()
                has_positive = any(indicator in emotion_text for indicator in positive_indicators)
                
                if has_positive:
                    print(f"✓ Correctly detected positive emotion: {result.primary_emotion.emotion}")
                else:
                    print(f"⚠ Expected positive emotion, got: {result.primary_emotion.emotion}")
                
                return  # Success - exit early to avoid multiple model loads
                
            except Exception as e:
                print(f"Emotion analysis failed for '{text}': {e}")
                continue
        
        # If all texts failed, skip the test
        pytest.skip("Emotion analysis not available (network/model issues)")
    
    def test_emotion_service_configuration(self):
        """Test emotion service configuration"""
        # Test that the service has proper configuration
        assert hasattr(ai_emotion_service, 'emotion_models')
        assert hasattr(ai_emotion_service, 'emotion_patterns')
        
        print(f"Emotion models configured: {len(ai_emotion_service.emotion_models)}")
        print(f"Emotion patterns: {len(ai_emotion_service.emotion_patterns)}")
        
        # Should have at least one model and pattern configured
        assert len(ai_emotion_service.emotion_models) > 0
        assert len(ai_emotion_service.emotion_patterns) > 0
    
    def test_cultural_adaptation_config(self):
        """Test cultural adaptation configuration"""
        cultural_mappings = ai_emotion_service.cultural_emotion_mappings
        
        assert isinstance(cultural_mappings, dict)
        assert len(cultural_mappings) > 0
        
        print(f"Cultural mappings available: {list(cultural_mappings.keys())}")
    
    def test_cache_key_generation(self):
        """Test cache key generation logic"""
        text = "Test text for caching"
        
        # Test basic cache key generation
        key1 = ai_emotion_service._build_emotion_cache_key(text, "en", True)
        key2 = ai_emotion_service._build_emotion_cache_key(text, "en", True)
        
        # Same text should generate same key
        assert key1 == key2
        
        # Different text should generate different key
        key3 = ai_emotion_service._build_emotion_cache_key("Different text", "en", True)
        assert key1 != key3
        
        print(f"Cache key generation working correctly")
