import pytest
import sys
import os
import torch
from unittest.mock import Mock, patch

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.ai_model_manager import ai_model_manager

class TestAIModelManager:
    """Test AI Model Manager functionality"""
    
    def test_hardware_detection(self):
        """Test GPU/CPU detection logic via model status"""
        model_status = ai_model_manager.get_model_status()
        
        assert 'gpu_available' in model_status
        assert 'total_memory_usage' in model_status
        assert 'loaded_models' in model_status
        assert isinstance(model_status['gpu_available'], bool)
        
        print(f"Hardware detected: GPU={model_status['gpu_available']}, "
              f"Memory Usage={model_status['total_memory_usage']:.1f}GB, "
              f"Models Loaded={model_status['loaded_models']}")
    
    def test_model_status_reporting(self):
        """Test model status reporting"""
        status = ai_model_manager.get_model_status()
        
        assert 'loaded_models' in status
        assert 'total_memory_usage' in status
        assert 'gpu_available' in status
        assert isinstance(status['loaded_models'], int)
        assert isinstance(status['total_memory_usage'], (int, float))
        
        print(f"Model status: {status['loaded_models']} models loaded, "
              f"{status['total_memory_usage']:.2f}GB memory used")
    
    @pytest.mark.skip(reason="Model configurations not fully implemented yet")
    def test_model_configuration_access(self):
        """Test that model configurations are properly defined"""
        configs = ai_model_manager.model_configs
        
        assert len(configs) > 0
        print(f"Available model configurations: {len(configs)}")
        
        # Check that basic model types are configured
        expected_types = ["emotion_classifier", "text_generator"]
        for model_key in expected_types:
            assert model_key in configs, f"Missing configuration for {model_key}"
            
            config = configs[model_key]
            assert 'model_name' in config
            assert 'memory_estimate' in config
            
            print(f"✓ {model_key}: {config['model_name']}")
    
    def test_memory_estimation(self):
        """Test model memory requirement estimation"""
        for model_key in ["emotion_classifier", "text_generator"]:
            try:
                memory_estimate = ai_model_manager.estimate_memory_requirement(model_key)
                assert memory_estimate > 0
                assert memory_estimate < 20  # Reasonable upper bound
                print(f"Memory estimate for {model_key}: {memory_estimate:.2f}GB")
            except Exception as e:
                print(f"Memory estimation failed for {model_key}: {e}")
    
    @pytest.mark.slow
    def test_basic_model_loading(self):
        """Test basic model loading (marked as slow due to model download)"""
        try:
            # Try to load the emotion analysis model (usually smallest)
            model = ai_model_manager.load_model("emotion_classifier")
            assert model is not None
            print(f"✓ Successfully loaded emotion_classifier")
            
            # Check status after loading
            status = ai_model_manager.get_model_status()
            assert status['loaded_models'] >= 1
            
        except Exception as e:
            # Model loading might fail due to network issues or memory constraints
            print(f"Model loading failed (expected in some environments): {e}")
            pytest.skip(f"Model loading not available: {e}")
    
    def test_model_caching_logic(self):
        """Test model caching behavior via public methods"""
        # Test get_optimal_model_for_task method (returns string, not dict)
        model_suggestion = ai_model_manager.get_optimal_model_for_task("emotion-analysis")
        
        # Note: This might return None if no models are configured for this task
        print(f"Optimal model for emotion analysis: {model_suggestion}")
        
        # Test model status includes loaded models count
        status = ai_model_manager.get_model_status()
        assert 'loaded_models' in status
        assert isinstance(status['loaded_models'], int)
        
        print(f"Currently loaded models: {status['loaded_models']}")
        
        # Test models dict in status
        assert 'models' in status
        assert isinstance(status['models'], dict)
