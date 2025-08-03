#!/usr/bin/env python3
"""
Test Hardware-Adaptive AI Integration with Enhanced AI Service

This script tests the integration of the GPU memory management system
with the existing enhanced AI service to ensure seamless operation.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.enhanced_ai_service import enhanced_ai_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_enhanced_ai_integration():
    """Test hardware-adaptive AI integration with enhanced AI service"""
    print("🚀 Testing Enhanced AI Service with Hardware-Adaptive AI Integration")
    print("=" * 80)
    
    # Test 1: Initialize the enhanced AI service
    print("\n🧠 STEP 1: Enhanced AI Service Initialization")
    print("-" * 50)
    
    try:
        await enhanced_ai_service.initialize()
        print("✅ Enhanced AI Service initialized successfully")
        
        # Check if adaptive AI is available
        if enhanced_ai_service.adaptive_ai:
            print("🤖 Hardware-Adaptive AI: ✅ Available")
            status = enhanced_ai_service.adaptive_ai.get_system_status()
            print(f"🏆 Hardware Tier: {status.get('current_tier', 'Unknown')}")
        else:
            print("⚠️ Hardware-Adaptive AI: ❌ Not available (fallback mode)")
        
        # Check GPU memory manager
        if enhanced_ai_service.gpu_memory_manager:
            gpu_status = enhanced_ai_service.gpu_memory_manager.get_comprehensive_status()
            print(f"💾 GPU Memory: {gpu_status['gpu_memory']['usage_percent']}%")
            print(f"📊 Memory Pressure: {gpu_status['gpu_memory']['pressure_level']}")
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return
    
    # Test 2: Mood Prediction with Hardware-Adaptive AI
    print("\n😊 STEP 2: Mood Prediction Test")
    print("-" * 50)
    
    test_entries = [
        {
            "title": "Amazing Day",
            "content": "I'm feeling absolutely wonderful today! The weather is perfect and I accomplished everything I set out to do."
        },
        {
            "title": "Challenging Times",
            "content": "Today was really difficult. Work was stressful and I'm feeling overwhelmed with everything."
        },
        {
            "title": "Quiet Reflection",
            "content": "Just sitting here thinking about life. Not particularly happy or sad, just contemplating."
        }
    ]
    
    for i, entry in enumerate(test_entries, 1):
        print(f"\n📄 Test {i}: {entry['title']}")
        try:
            result = await enhanced_ai_service.predict_mood(entry["content"], entry["title"])
            
            print(f"   🎯 Predicted Mood: {result['predicted_mood']}")
            print(f"   📊 Confidence: {result['confidence']:.2f}")
            print(f"   🔧 Method: {result.get('method', 'traditional')}")
            
            if 'hardware_tier' in result:
                print(f"   🏆 Hardware Tier: {result['hardware_tier']}")
            if 'fallback_used' in result:
                print(f"   🔄 Fallback Used: {result['fallback_used']}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test 3: Tag Suggestions with Hardware-Adaptive AI
    print("\n🏷️ STEP 3: Tag Suggestions Test")
    print("-" * 50)
    
    test_content = "Today I went for a long hike in the mountains. The fresh air and beautiful scenery really helped clear my mind after a stressful week at work."
    test_title = "Mountain Hike"
    
    try:
        tags = await enhanced_ai_service.suggest_tags(test_content, test_title)
        
        print(f"📝 Content: {test_content[:60]}...")
        print(f"📋 Generated {len(tags)} tag suggestions:")
        
        for tag in tags[:5]:  # Show top 5
            print(f"   🏷️ {tag['tag']} (confidence: {tag['confidence']:.2f}, source: {tag.get('source', 'traditional')})")
            
    except Exception as e:
        print(f"❌ Tag generation error: {e}")
    
    # Test 4: Smart Prompts with Hardware-Adaptive AI
    print("\n💡 STEP 4: Smart Prompts Test")
    print("-" * 50)
    
    current_content = "I've been thinking a lot about my career lately. There are some exciting opportunities on the horizon, but I'm also feeling uncertain about making big changes."
    current_title = "Career Thoughts"
    
    try:
        prompts = await enhanced_ai_service.generate_smart_prompts(
            user_history_days=30,
            current_content=current_content,
            current_title=current_title
        )
        
        print(f"📝 Current Content: {current_content[:60]}...")
        print(f"🔮 Generated {len(prompts)} smart prompts:")
        
        for i, prompt in enumerate(prompts[:3], 1):  # Show top 3
            print(f"   {i}. {prompt['prompt']}")
            print(f"      📁 Category: {prompt.get('category', 'general')}")
            if 'reasoning' in prompt:
                print(f"      🤖 Reasoning: {prompt['reasoning']}")
            print()
            
    except Exception as e:
        print(f"❌ Smart prompts error: {e}")
    
    # Test 5: System Performance and Memory Status
    print("\n📊 STEP 5: System Performance Status")
    print("-" * 50)
    
    try:
        if enhanced_ai_service.adaptive_ai:
            system_status = enhanced_ai_service.adaptive_ai.get_system_status()
            
            print("🖥️ System Status:")
            print(f"   Status: {system_status['status']}")
            print(f"   Tier: {system_status['current_tier']}")
            print(f"   Uptime: {system_status.get('uptime_seconds', 0):.1f}s")
            
            if 'hardware_info' in system_status:
                hw_info = system_status['hardware_info']
                gpu_info = hw_info.get('gpu', {})
                print(f"   GPU Memory: {gpu_info.get('usage_percent', 0):.1f}%")
                print(f"   Memory Pressure: {gpu_info.get('memory_pressure', 'Unknown')}")
        
        if enhanced_ai_service.gpu_memory_manager:
            gpu_status = enhanced_ai_service.gpu_memory_manager.get_comprehensive_status()
            recommendations = gpu_status.get('recommendations', [])
            
            if recommendations:
                print("\n📋 GPU Memory Recommendations:")
                for rec in recommendations:
                    print(f"   {rec}")
            else:
                print("✅ No GPU memory recommendations - system healthy")
        
    except Exception as e:
        print(f"❌ Status check error: {e}")
    
    # Test 6: Resource Cleanup
    print("\n🧹 STEP 6: Resource Cleanup Test")
    print("-" * 50)
    
    try:
        # Test GPU memory cleanup
        if enhanced_ai_service.gpu_memory_manager:
            cleanup_result = await enhanced_ai_service.gpu_memory_manager.cleanup_manager.emergency_gpu_cleanup()
            print(f"🧹 GPU Cleanup: {cleanup_result['success']}")
            print(f"💾 Memory Freed: {cleanup_result['memory_freed_mb']}MB")
            print(f"📊 Final Pressure: {cleanup_result['final_pressure']}")
        
        # Test service shutdown
        if enhanced_ai_service.adaptive_ai:
            await enhanced_ai_service.adaptive_ai.shutdown()
            print("🔒 Hardware-Adaptive AI shutdown: ✅")
        
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
    
    print("\n" + "=" * 80)
    print("🎯 Enhanced AI Service Integration Test Complete!")
    print("=" * 80)

def main():
    """Main test function"""
    try:
        asyncio.run(test_enhanced_ai_integration())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
