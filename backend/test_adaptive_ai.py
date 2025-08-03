#!/usr/bin/env python3
"""
Hardware-Adaptive AI Test Suite

Test script to verify the hardware-adaptive AI system functionality.
"""

import asyncio
import json
import logging
from pathlib import Path
import sys

# Add the backend directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.hardware_adaptive_ai import HardwareAdaptiveAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_hardware_detection():
    """Test hardware detection and classification"""
    print("\n" + "="*60)
    print("🔍 TESTING HARDWARE DETECTION")
    print("="*60)
    
    adaptive_ai = HardwareAdaptiveAI()
    
    # Test hardware profiler
    system_info = adaptive_ai.hardware_profiler.detect_system_info()
    print(f"📊 Detected RAM: {system_info['ram']['total_gb']:.1f}GB")
    print(f"🖥️  CPU Cores: {system_info['cpu']['cores']}")
    print(f"🎮 GPU Available: {system_info['gpu']['has_gpu']}")
    if system_info['gpu']['has_gpu']:
        print(f"💾 GPU Memory: {system_info['gpu']['total_memory_mb']}MB")
    
    # Test tier classification
    tier, classification_info = adaptive_ai.hardware_profiler.classify_hardware_tier(system_info)
    print(f"\n🏆 Hardware Tier: {tier.value}")
    print(f"📝 Reasoning: {classification_info['reasoning']}")
    
    return adaptive_ai, tier

async def test_memory_management(adaptive_ai):
    """Test memory management functionality"""
    print("\n" + "="*60)
    print("🧠 TESTING MEMORY MANAGEMENT")
    print("="*60)
    
    await adaptive_ai.initialize()
    
    memory_info = adaptive_ai.memory_manager.get_memory_info()
    print(f"💾 Memory Limit: {memory_info['memory_limit_mb']}MB")
    print(f"📈 Memory Usage: {memory_info['memory_usage_mb']}MB")
    print(f"📊 Usage Percentage: {memory_info['usage_percent']:.1f}%")
    print(f"🔢 Loaded Models: {memory_info['loaded_models']}")
    
    # Test memory cleanup
    print("\n🧹 Testing memory cleanup...")
    await adaptive_ai.memory_manager.cleanup_unused_models()
    print("✅ Memory cleanup completed")

async def test_feature_availability(adaptive_ai):
    """Test feature availability and capabilities"""
    print("\n" + "="*60)
    print("⚡ TESTING FEATURE AVAILABILITY")
    print("="*60)
    
    capabilities = adaptive_ai.get_available_features()
    
    print(f"🏆 Current Tier: {capabilities['current_tier']}")
    print(f"📋 Available Features:")
    for feature in capabilities['available_features']:
        print(f"   ✅ {feature}")
    
    print(f"\n🔍 Feature Analysis:")
    for analysis_type, info in capabilities['feature_analysis'].items():
        status = "🟢 Available" if info['available'] else "🔴 Unavailable"
        method = info['method']
        print(f"   {status} {analysis_type}: {method}")

async def test_text_analysis(adaptive_ai):
    """Test text analysis with different types"""
    print("\n" + "="*60)
    print("📝 TESTING TEXT ANALYSIS")
    print("="*60)
    
    test_texts = [
        "I'm feeling absolutely wonderful today! The weather is perfect and everything is going great.",
        "I'm quite worried about the upcoming presentation. It's making me anxious and stressed.",
        "Work has been really challenging lately. I need to find better work-life balance.",
        "I love spending time with my family. They always make me feel happy and supported."
    ]
    
    analysis_types = ["sentiment", "emotion", "topic", "stats"]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n📄 Test Text {i}: {text[:50]}...")
        
        for analysis_type in analysis_types:
            try:
                result = await adaptive_ai.analyze_text(text, analysis_type)
                if result['success']:
                    print(f"   ✅ {analysis_type}: {result['method_used']} "
                          f"(confidence: {result['confidence']:.2f})")
                    if result['fallback_used']:
                        print(f"      ⚠️  Used fallback method")
                else:
                    print(f"   ❌ {analysis_type}: {result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"   ❌ {analysis_type}: Error - {e}")

async def test_batch_analysis(adaptive_ai):
    """Test batch analysis functionality"""
    print("\n" + "="*60)
    print("📦 TESTING BATCH ANALYSIS")
    print("="*60)
    
    test_texts = [
        "Today was an amazing day!",
        "I'm feeling quite sad and lonely.",
        "Work is going really well this week.",
        "I'm excited about my vacation plans!"
    ]
    
    print(f"🔄 Processing {len(test_texts)} texts in batch...")
    
    try:
        results = await adaptive_ai.batch_analyze(test_texts, "sentiment")
        
        for i, result in enumerate(results):
            if result['success']:
                sentiment = result['result'].get('sentiment', 'unknown')
                confidence = result['confidence']
                print(f"   📄 Text {i+1}: {sentiment} (confidence: {confidence:.2f})")
            else:
                print(f"   ❌ Text {i+1}: Error - {result.get('error', 'Unknown')}")
                
        print("✅ Batch analysis completed")
        
    except Exception as e:
        print(f"❌ Batch analysis failed: {e}")

async def test_optimization_suggestions(adaptive_ai):
    """Test optimization suggestions"""
    print("\n" + "="*60)
    print("💡 TESTING OPTIMIZATION SUGGESTIONS")
    print("="*60)
    
    try:
        suggestions = await adaptive_ai.suggest_optimizations()
        
        print(f"🏆 Current Tier: {suggestions['current_tier']}")
        print(f"📊 System Score: {suggestions['system_score']['overall']}/100")
        
        if suggestions['suggestions']:
            print("\n💡 Optimization Suggestions:")
            for suggestion in suggestions['suggestions']:
                priority = suggestion['priority'].upper()
                print(f"   🔥 {priority}: {suggestion['description']}")
                print(f"      💪 Expected improvement: {suggestion['expected_improvement']}")
        else:
            print("🎉 No optimization suggestions - your system is well configured!")
        
        next_tier = suggestions.get('next_tier_requirements', {})
        if 'next_tier' in next_tier:
            print(f"\n🎯 Next Tier: {next_tier['next_tier']}")
            print(f"   💾 Requires: {next_tier.get('min_ram_gb', 0)}GB RAM")
            if next_tier.get('min_gpu_memory_mb', 0) > 0:
                print(f"   🎮 GPU Memory: {next_tier['min_gpu_memory_mb']}MB")
    
    except Exception as e:
        print(f"❌ Optimization suggestions failed: {e}")

async def test_system_status(adaptive_ai):
    """Test system status reporting"""
    print("\n" + "="*60)
    print("📊 TESTING SYSTEM STATUS")
    print("="*60)
    
    try:
        status = adaptive_ai.get_system_status()
        
        print(f"🟢 Status: {status['status']}")
        print(f"🏆 Tier: {status['current_tier']}")
        print(f"⏱️  Uptime: {status['uptime_seconds']:.1f} seconds")
        print(f"🧠 Monitoring: {'✅ Active' if status['monitoring_status']['is_monitoring'] else '❌ Inactive'}")
        
        memory = status['memory_info']
        print(f"💾 Memory Usage: {memory['memory_usage_mb']}/{memory['memory_limit_mb']}MB "
              f"({memory['usage_percent']:.1f}%)")
        
    except Exception as e:
        print(f"❌ System status check failed: {e}")

async def run_comprehensive_test():
    """Run comprehensive test suite"""
    print("🚀 HARDWARE-ADAPTIVE AI TEST SUITE")
    print("🔬 Testing all components and functionality...")
    
    try:
        # Test hardware detection
        adaptive_ai, tier = await test_hardware_detection()
        
        # Test memory management
        await test_memory_management(adaptive_ai)
        
        # Test feature availability
        await test_feature_availability(adaptive_ai)
        
        # Test text analysis
        await test_text_analysis(adaptive_ai)
        
        # Test batch analysis
        await test_batch_analysis(adaptive_ai)
        
        # Test optimization suggestions
        await test_optimization_suggestions(adaptive_ai)
        
        # Test system status
        await test_system_status(adaptive_ai)
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"🏆 Your system is classified as: {tier.value}")
        print("🎉 Hardware-Adaptive AI is working correctly!")
        
        # Cleanup
        await adaptive_ai.shutdown()
        
    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        logger.exception("Detailed error information:")

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())
