#!/usr/bin/env python3
"""
Emergency GPU Memory Recovery Script

This script immediately detects and cleans up duplicate processes using GPU memory
and provides real-time GPU memory monitoring.
"""

import asyncio
import sys
import os
sys.path.append('/home/abrasko/Projects/journaling-ai/backend')

from app.core.gpu_memory_manager import GPUMemoryManager, get_gpu_memory_manager

async def emergency_gpu_recovery():
    """Perform emergency GPU memory recovery"""
    print("🚨 Emergency GPU Memory Recovery Starting...")
    print("=" * 60)
    
    gpu_manager = get_gpu_memory_manager()
    
    # Get initial GPU status
    print("📊 Initial GPU Memory Status:")
    initial_status = gpu_manager.get_comprehensive_status()
    gpu_memory = initial_status["gpu_memory"]
    
    print(f"  Total GPU Memory: {gpu_memory.get('total_mb', 0)}MB")
    print(f"  Used GPU Memory: {gpu_memory.get('used_mb', 0)}MB")
    print(f"  Free GPU Memory: {gpu_memory.get('free_mb', 0)}MB")
    print(f"  Usage Percentage: {gpu_memory.get('usage_percent', 0)}%")
    print(f"  Memory Pressure: {gpu_memory.get('pressure_level', 'UNKNOWN')}")
    print(f"  Available for Models: {gpu_memory.get('available_for_models', 0)}MB")
    
    # Check for process conflicts
    process_info = initial_status["process_info"]
    print(f"\n🔍 Process Analysis:")
    print(f"  Total GPU Processes: {process_info.get('total_gpu_processes', 0)}")
    print(f"  Python Processes: {process_info.get('python_processes', 0)}")
    print(f"  Journaling AI Processes: {process_info.get('journaling_ai_processes', 0)}")
    print(f"  Has Conflicts: {process_info.get('has_conflicts', False)}")
    
    if process_info.get("has_conflicts", False):
        print(f"\n⚠️  Detected {len(process_info.get('conflicts_detected', []))} duplicate processes:")
        for conflict in process_info.get("conflicts_detected", []):
            print(f"    PID {conflict['pid']}: {conflict['process_name']} using {conflict['memory_mb']}MB")
    
    # Display recommendations
    recommendations = initial_status.get("recommendations", [])
    if recommendations:
        print(f"\n💡 Recommendations:")
        for rec in recommendations:
            print(f"    {rec}")
    
    # Perform emergency recovery if needed
    pressure = gpu_memory.get("pressure_level", "LOW")
    if pressure in ["CRITICAL", "HIGH"] or process_info.get("has_conflicts", False):
        print(f"\n🚑 Starting Emergency Recovery (Pressure: {pressure})...")
        
        recovery_result = await gpu_manager.recovery_system.handle_gpu_memory_exhaustion()
        
        print(f"\n📈 Recovery Results:")
        print(f"  Success: {recovery_result.get('success', False)}")
        print(f"  Initial Memory: {recovery_result.get('initial_memory_mb', 0)}MB")
        print(f"  Final Memory: {recovery_result.get('final_memory_mb', 0)}MB")
        print(f"  Memory Freed: {recovery_result.get('memory_freed_mb', 0)}MB")
        print(f"  Final Pressure: {recovery_result.get('final_pressure', 'UNKNOWN')}")
        print(f"  Available for Models: {recovery_result.get('final_available_mb', 0)}MB")
        
        # Show recovery steps taken
        if "recovery_steps" in recovery_result:
            print(f"\n🔧 Recovery Steps Taken:")
            for step_name, step_result in recovery_result["recovery_steps"]:
                if isinstance(step_result, dict):
                    if "cleaned_up" in step_result:
                        print(f"    {step_name}: Cleaned {step_result['cleaned_up']} processes, freed {step_result.get('memory_freed_mb', 0)}MB")
                    elif "success" in step_result:
                        print(f"    {step_name}: {'Success' if step_result['success'] else 'Failed'}")
                    else:
                        print(f"    {step_name}: Completed")
                else:
                    print(f"    {step_name}: {step_result}")
    
    else:
        print(f"\n✅ GPU Memory Status: {pressure} - No emergency recovery needed")
    
    # Final status check
    print(f"\n📊 Final GPU Memory Status:")
    final_status = gpu_manager.get_comprehensive_status()
    final_gpu_memory = final_status["gpu_memory"]
    
    print(f"  Used GPU Memory: {final_gpu_memory.get('used_mb', 0)}MB")
    print(f"  Free GPU Memory: {final_gpu_memory.get('free_mb', 0)}MB")
    print(f"  Usage Percentage: {final_gpu_memory.get('usage_percent', 0)}%")
    print(f"  Memory Pressure: {final_gpu_memory.get('pressure_level', 'UNKNOWN')}")
    print(f"  Available for Models: {final_gpu_memory.get('available_for_models', 0)}MB")
    
    print("\n" + "=" * 60)
    print("🎯 Emergency GPU Memory Recovery Complete!")

if __name__ == "__main__":
    asyncio.run(emergency_gpu_recovery())
