#!/usr/bin/env python3
"""
Quick test for GPU Memory Management System
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, '/home/abrasko/Projects/journaling-ai/backend')

async def test_gpu_memory_manager():
    """Test the GPU memory management system"""
    print("🧪 Testing GPU Memory Management System")
    print("=" * 50)
    
    try:
        from app.core.gpu_memory_manager import get_gpu_memory_manager
        
        # Get the GPU memory manager
        manager = get_gpu_memory_manager()
        print("✅ GPU Memory Manager initialized")
        
        # Get comprehensive status
        status = manager.get_comprehensive_status()
        print("\n📊 Current System Status:")
        
        gpu_memory = status.get("gpu_memory", {})
        print(f"   GPU Memory Usage: {gpu_memory.get('usage_percent', 0):.1f}%")
        print(f"   Available for Models: {gpu_memory.get('available_for_models', 0)}MB")
        print(f"   Memory Pressure: {gpu_memory.get('pressure_level', 'UNKNOWN')}")
        
        process_info = status.get("process_info", {})
        print(f"   GPU Processes: {process_info.get('total_gpu_processes', 0)}")
        print(f"   Conflicts: {'Yes' if process_info.get('has_conflicts', False) else 'No'}")
        
        recommendations = status.get("recommendations", [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations:
                print(f"   {rec}")
        
        print("\n✅ GPU Memory Management System is operational!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing GPU memory manager: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_hardware_profiler():
    """Test the enhanced hardware profiler"""
    print("\n🔍 Testing Enhanced Hardware Profiler")
    print("=" * 50)
    
    try:
        from app.core.hardware_profiler import HardwareProfiler
        
        profiler = HardwareProfiler()
        print("✅ Hardware Profiler initialized")
        
        # Test system detection
        system_info = profiler.detect_system_info()
        
        print("\n💻 System Information:")
        print(f"   RAM: {system_info['ram']['total_gb']:.1f}GB")
        print(f"   CPU Cores: {system_info['cpu']['cores']}")
        
        gpu_info = system_info.get('gpu', {})
        print(f"   GPU: {'Yes' if gpu_info.get('has_gpu', False) else 'No'}")
        if gpu_info.get('has_gpu', False):
            print(f"   GPU Memory: {gpu_info.get('total_memory_mb', 0)}MB")
            print(f"   Memory Pressure: {gpu_info.get('memory_pressure', 'UNKNOWN')}")
            print(f"   Available for Models: {gpu_info.get('available_memory_mb', 0)}MB")
        
        # Test tier classification
        tier, classification_info = profiler.classify_hardware_tier(system_info)
        print(f"\n🏆 Hardware Tier: {tier.value}")
        print(f"   Reasoning: {classification_info.get('reasoning', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing hardware profiler: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_hardware_adaptive_ai():
    """Test the main hardware-adaptive AI system"""
    print("\n🤖 Testing Hardware-Adaptive AI System")
    print("=" * 50)
    
    try:
        from app.services.hardware_adaptive_ai import HardwareAdaptiveAI
        
        # Initialize the system
        ai_system = HardwareAdaptiveAI()
        print("✅ Hardware-Adaptive AI created")
        
        # Initialize
        init_result = await ai_system.initialize()
        
        if init_result.get("status") == "success":
            print("✅ Hardware-Adaptive AI initialized successfully")
            print(f"   Tier: {init_result.get('tier', 'UNKNOWN')}")
            print(f"   Memory Limit: {init_result.get('memory_limit_mb', 0)}MB")
            
            # Test system status
            status = ai_system.get_system_status()
            print(f"   Status: {status.get('status', 'UNKNOWN')}")
            
            # Test features
            features = ai_system.get_available_features()
            available_features = features.get('available_features', [])
            print(f"   Available Features: {len(available_features)}")
            
            return True
        else:
            print(f"❌ Initialization failed: {init_result.get('error', 'Unknown error')}")
            return False
        
    except Exception as e:
        print(f"❌ Error testing hardware-adaptive AI: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🚀 GPU Memory Management Integration Test")
    print("=" * 60)
    
    results = []
    
    # Test GPU Memory Manager
    results.append(await test_gpu_memory_manager())
    
    # Test Hardware Profiler
    results.append(await test_hardware_profiler())
    
    # Test Hardware-Adaptive AI
    results.append(await test_hardware_adaptive_ai())
    
    # Summary
    print("\n🎯 Test Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! GPU Memory Management is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
