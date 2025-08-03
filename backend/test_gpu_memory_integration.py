#!/usr/bin/env python3
"""
Test GPU Memory Management Integration

This script tests the integration of the GPU memory management system
with the hardware-adaptive AI service to ensure models load safely.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.hardware_adaptive_ai import HardwareAdaptiveAI
from app.core.gpu_memory_manager import get_gpu_memory_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_gpu_memory_integration():
    """Test GPU memory management integration"""
    print("🚀 Testing GPU Memory Management Integration")
    print("=" * 60)
    
    # Test 1: Get GPU memory manager status
    print("\n📊 STEP 1: GPU Memory Manager Status")
    print("-" * 40)
    
    gpu_manager = get_gpu_memory_manager()
    status = gpu_manager.get_comprehensive_status()
    
    print(f"GPU Memory Usage: {status['gpu_memory']['usage_percent']}%")
    print(f"Available for Models: {status['gpu_memory']['available_for_models']}MB")
    print(f"Memory Pressure: {status['gpu_memory']['pressure_level']}")
    print(f"Process Conflicts: {len(status['process_info']['conflicts_detected'])}")
    
    if status['recommendations']:
        print("📋 Recommendations:")
        for rec in status['recommendations']:
            print(f"  {rec}")
    else:
        print("✅ No recommendations - system is healthy")
    
    # Test 2: Initialize Hardware-Adaptive AI
    print("\n🧠 STEP 2: Hardware-Adaptive AI Initialization")
    print("-" * 40)
    
    ai_system = HardwareAdaptiveAI()
    init_result = await ai_system.initialize()
    
    if init_result["status"] == "success":
        print(f"✅ Initialization successful")
        print(f"🏆 Hardware Tier: {init_result['tier']}")
        print(f"💾 Memory Limit: {init_result['memory_limit_mb']}MB")
        print(f"⚡ Available Features: {len(init_result['available_features'])}")
    else:
        print(f"❌ Initialization failed: {init_result.get('error')}")
        return
    
    # Test 3: Test text analysis with GPU memory monitoring
    print("\n📝 STEP 3: Text Analysis with GPU Memory Monitoring")
    print("-" * 40)
    
    test_texts = [
        "I'm feeling really excited about this new project!",
        "Today was a difficult day with many challenges.",
        "Working with the team has been incredibly rewarding.",
        "I'm worried about the upcoming deadline."
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n📄 Test {i}: {text[:50]}...")
        
        # Monitor GPU memory before analysis
        pre_analysis = gpu_manager.gpu_monitor.get_detailed_gpu_memory()
        
        # Perform analysis
        result = await ai_system.analyze_text(text, analysis_type="sentiment")
        
        # Monitor GPU memory after analysis
        post_analysis = gpu_manager.gpu_monitor.get_detailed_gpu_memory()
        
        memory_change = post_analysis['used_mb'] - pre_analysis['used_mb']
        
        if result["success"]:
            print(f"   ✅ Analysis: {result['result']} (confidence: {result['confidence']:.2f})")
            print(f"   🔧 Method: {result['method_used']}")
            print(f"   💾 Memory Change: {memory_change:+d}MB")
            print(f"   ⏱️  Processing Time: {result['processing_time']:.3f}s")
        else:
            print(f"   ❌ Analysis failed: {result.get('error')}")
    
    # Test 4: Test memory cleanup
    print("\n🧹 STEP 4: Memory Cleanup Test")
    print("-" * 40)
    
    # Force memory cleanup
    cleanup_result = await gpu_manager.cleanup_manager.emergency_gpu_cleanup()
    
    print(f"Memory Cleanup Results:")
    print(f"  ✅ Success: {cleanup_result['success']}")
    print(f"  📦 Models Unloaded: {len(cleanup_result['models_unloaded'])}")
    print(f"  💾 Memory Freed: {cleanup_result['memory_freed_mb']}MB")
    print(f"  📊 Final Pressure: {cleanup_result['final_pressure']}")
    
    # Test 5: System recommendations
    print("\n💡 STEP 5: System Optimization Recommendations")
    print("-" * 40)
    
    recommendations = await ai_system.suggest_optimizations()
    
    print(f"🏆 Current Tier: {recommendations['current_tier']}")
    print(f"📊 System Score: {recommendations['system_score']['overall']}/100")
    
    if recommendations['suggestions']:
        print("📋 Optimization Suggestions:")
        for suggestion in recommendations['suggestions']:
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(suggestion['priority'], "⚪")
            print(f"  {priority_emoji} {suggestion['type']}: {suggestion['description']}")
    else:
        print("🎉 No optimization suggestions - system is well configured!")
    
    # Test 6: Shutdown with GPU cleanup
    print("\n🔒 STEP 6: Clean Shutdown")
    print("-" * 40)
    
    await ai_system.shutdown()
    print("✅ Hardware-Adaptive AI shutdown complete")
    
    # Final GPU memory check
    final_status = gpu_manager.get_comprehensive_status()
    print(f"📊 Final GPU Memory: {final_status['gpu_memory']['usage_percent']}%")
    print(f"💾 Available for Models: {final_status['gpu_memory']['available_for_models']}MB")
    
    print("\n" + "=" * 60)
    print("🎯 GPU Memory Management Integration Test Complete!")
    print("=" * 60)

def main():
    """Main test function"""
    try:
        asyncio.run(test_gpu_memory_integration())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
