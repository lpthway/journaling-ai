#!/usr/bin/env python3
"""
Test Hardware-Adaptive Model Configuration System

This script tests the dynamic model selection based on hardware tiers.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.enhanced_ai_service import EnhancedAIService
from app.services.hardware_adaptive_ai import get_adaptive_ai

async def test_hardware_adaptive_models():
    """Test hardware-adaptive model configurations"""
    
    print("🚀 Testing Hardware-Adaptive Model Configuration System")
    print("=" * 80)
    
    # Initialize Enhanced AI Service
    ai_service = EnhancedAIService()
    await ai_service.initialize()
    
    print("\n🔧 STEP 1: Current Hardware Configuration")
    print("-" * 50)
    
    current_tier = ai_service._get_current_hardware_tier()
    print(f"Current Hardware Tier: {current_tier}")
    
    available_models = ai_service.get_available_models_for_tier()
    print(f"\n📊 Available Models for {current_tier} tier:")
    
    for model_key, model_info in available_models.items():
        print(f"   🤖 {model_key}:")
        print(f"      Model: {model_info['model_name']}")
        print(f"      Accuracy: {model_info['accuracy_tier']}")
        print(f"      Memory: {model_info['memory_estimate_mb']}MB")
        print(f"      CPU Optimized: {model_info['cpu_optimized']}")
        print()
    
    print("\n🧠 STEP 2: Model Loading Test")
    print("-" * 50)
    
    # Test loading models based on current hardware tier
    test_content = "I feel really excited about this new project at work!"
    
    print(f"Testing with content: '{test_content}'")
    print()
    
    # Test mood prediction with adaptive models
    mood_result = await ai_service.predict_mood(test_content, "Exciting Day")
    print("🎯 Mood Prediction Result:")
    print(f"   Predicted Mood: {mood_result.get('predicted_mood')}")
    print(f"   Confidence: {mood_result.get('confidence', 0):.2f}")
    print(f"   Method: {mood_result.get('analysis', 'Unknown')}")
    print()
    
    # Test tag suggestions with adaptive models
    tag_results = await ai_service.suggest_tags(test_content, "Exciting Day")
    print("🏷️ Tag Suggestions:")
    for i, tag in enumerate(tag_results[:5], 1):
        print(f"   {i}. {tag.get('tag')} (confidence: {tag.get('confidence', 0):.2f})")
    print()
    
    print("\n📈 STEP 3: Hardware Tier Simulation")
    print("-" * 50)
    
    # Simulate different hardware tiers
    tiers_to_test = ["HIGH_END", "INTERMEDIATE", "BASIC", "MINIMAL"]
    
    for test_tier in tiers_to_test:
        print(f"\n🔄 Simulating {test_tier} hardware tier:")
        
        # Temporarily override the tier detection
        original_method = ai_service._get_current_hardware_tier
        ai_service._get_current_hardware_tier = lambda: test_tier
        
        # Refresh configurations
        ai_service.refresh_hardware_adaptive_models()
        
        # Get models for this tier
        tier_models = ai_service.get_available_models_for_tier()
        print(f"   Available models: {list(tier_models.keys())}")
        
        total_memory = sum(model['memory_estimate_mb'] for model in tier_models.values())
        print(f"   Total estimated memory: {total_memory}MB")
        
        # Restore original method
        ai_service._get_current_hardware_tier = original_method
    
    print("\n🧹 STEP 4: Cleanup Test")
    print("-" * 50)
    
    await ai_service.cleanup()
    print("✅ Enhanced AI Service cleaned up")
    
    print("\n" + "=" * 80)
    print("🎯 Hardware-Adaptive Model Configuration Test Complete!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_hardware_adaptive_models())
