"""
GPU Memory Management System

Comprehensive GPU memory monitoring, cleanup, and optimization for the hardware-adaptive AI system.
"""

import asyncio
import gc
import logging
import os
import psutil
import subprocess
import torch
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class GPUMemoryExhaustionError(Exception):
    """Raised when GPU memory cannot accommodate model loading"""
    pass

class DuplicateProcessError(Exception):
    """Raised when duplicate AI processes detected"""
    pass

class GPUMemoryRecoveryError(Exception):
    """Raised when GPU memory recovery fails"""
    pass

class ProcessManager:
    """Detect and manage duplicate AI processes"""
    
    def __init__(self):
        self.current_pid = os.getpid()
        self.project_path = "/home/abrasko/Projects/journaling-ai"
    
    def detect_duplicate_processes(self) -> Dict[str, Any]:
        """Detect potentially conflicting GPU processes"""
        try:
            # Get GPU processes using nvidia-smi
            result = subprocess.run([
                "nvidia-smi", "--query-compute-apps=pid,process_name,used_memory",
                "--format=csv,noheader"
            ], capture_output=True, text=True, check=True)
            
            gpu_processes = []
            python_processes = []
            total_gpu_memory = 0
            
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 3:
                        pid = int(parts[0])
                        process_name = parts[1]
                        memory_str = parts[2].replace(' MiB', '')
                        memory_mb = int(memory_str)
                        
                        process_info = {
                            "pid": pid,
                            "process_name": process_name,
                            "memory_mb": memory_mb,
                            "is_current": pid == self.current_pid
                        }
                        
                        gpu_processes.append(process_info)
                        total_gpu_memory += memory_mb
                        
                        # Check if it's a Python process
                        if "python" in process_name.lower():
                            # Try to get more details about the process
                            try:
                                proc = psutil.Process(pid)
                                cmdline = proc.cmdline()
                                process_info.update({
                                    "cmdline": cmdline,
                                    "cwd": proc.cwd(),
                                    "is_journaling_ai": self.project_path in str(cmdline) or self.project_path in proc.cwd()
                                })
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                process_info.update({
                                    "cmdline": [],
                                    "cwd": "",
                                    "is_journaling_ai": False
                                })
                            
                            python_processes.append(process_info)
            
            # Analyze for duplicates
            journaling_ai_processes = [p for p in python_processes if p.get("is_journaling_ai", False)]
            has_conflicts = len(journaling_ai_processes) > 1
            
            return {
                "has_conflicts": has_conflicts,
                "total_gpu_processes": len(gpu_processes),
                "python_processes": len(python_processes),
                "journaling_ai_processes": len(journaling_ai_processes),
                "total_gpu_memory_mb": total_gpu_memory,
                "gpu_processes": gpu_processes,
                "python_processes": python_processes,
                "journaling_ai_processes": journaling_ai_processes,
                "current_pid": self.current_pid,
                "conflicts_detected": [p for p in journaling_ai_processes if p["pid"] != self.current_pid]
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to query GPU processes: {e}")
            return {
                "has_conflicts": False,
                "error": str(e),
                "gpu_processes": [],
                "python_processes": [],
                "journaling_ai_processes": []
            }
    
    async def cleanup_duplicate_processes(self, exclude_current=True) -> Dict[str, Any]:
        """Safely terminate duplicate processes"""
        conflicts = self.detect_duplicate_processes()
        
        if not conflicts["has_conflicts"]:
            return {
                "cleaned_up": 0,
                "memory_freed_mb": 0,
                "message": "No duplicate processes found"
            }
        
        cleanup_results = []
        total_memory_freed = 0
        
        for process in conflicts["conflicts_detected"]:
            if exclude_current and process["pid"] == self.current_pid:
                continue
            
            try:
                pid = process["pid"]
                memory_mb = process["memory_mb"]
                
                logger.info(f"Attempting to terminate duplicate process PID {pid} using {memory_mb}MB GPU memory")
                
                # Try graceful termination first
                proc = psutil.Process(pid)
                proc.terminate()
                
                # Wait up to 10 seconds for graceful termination
                try:
                    proc.wait(timeout=10)
                    cleanup_results.append({
                        "pid": pid,
                        "memory_mb": memory_mb,
                        "method": "graceful_termination",
                        "success": True
                    })
                    total_memory_freed += memory_mb
                    logger.info(f"Successfully terminated process PID {pid}")
                
                except psutil.TimeoutExpired:
                    # Force kill if graceful termination fails
                    logger.warning(f"Graceful termination failed for PID {pid}, forcing kill")
                    proc.kill()
                    proc.wait(timeout=5)
                    cleanup_results.append({
                        "pid": pid,
                        "memory_mb": memory_mb,
                        "method": "force_kill",
                        "success": True
                    })
                    total_memory_freed += memory_mb
                    logger.info(f"Force killed process PID {pid}")
            
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                cleanup_results.append({
                    "pid": process["pid"],
                    "memory_mb": process["memory_mb"],
                    "method": "failed",
                    "success": False,
                    "error": str(e)
                })
                logger.error(f"Failed to terminate process PID {process['pid']}: {e}")
        
        # Wait a moment for GPU memory to be freed
        await asyncio.sleep(2)
        
        return {
            "cleaned_up": len([r for r in cleanup_results if r["success"]]),
            "memory_freed_mb": total_memory_freed,
            "cleanup_results": cleanup_results,
            "message": f"Cleaned up {len([r for r in cleanup_results if r['success']])} duplicate processes, freed ~{total_memory_freed}MB GPU memory"
        }

class GPUMemoryMonitor:
    """Real-time GPU memory monitoring and management"""
    
    def __init__(self):
        self.safety_buffer_mb = 500  # Always keep 500MB free
        self.last_memory_check = None
    
    def get_detailed_gpu_memory(self) -> Dict[str, Any]:
        """Get comprehensive GPU memory information"""
        try:
            # System-level memory info from nvidia-smi
            result = subprocess.run([
                "nvidia-smi", "--query-gpu=memory.total,memory.used,memory.free",
                "--format=csv,noheader,nounits"
            ], capture_output=True, text=True, check=True)
            
            line = result.stdout.strip()
            if line:
                parts = [int(p.strip()) for p in line.split(',')]
                total_mb, used_mb, free_mb = parts
                
                usage_percent = (used_mb / total_mb) * 100
                available_for_models = max(0, free_mb - self.safety_buffer_mb)
                
                # PyTorch-specific memory info (if available)
                pytorch_memory = {}
                if torch.cuda.is_available():
                    try:
                        pytorch_memory = {
                            "allocated_mb": torch.cuda.memory_allocated() // (1024 * 1024),
                            "reserved_mb": torch.cuda.memory_reserved() // (1024 * 1024),
                            "max_allocated_mb": torch.cuda.max_memory_allocated() // (1024 * 1024),
                            "max_reserved_mb": torch.cuda.max_memory_reserved() // (1024 * 1024)
                        }
                    except Exception as e:
                        logger.warning(f"Could not get PyTorch memory info: {e}")
                
                # Determine memory pressure level
                pressure_level = self._assess_memory_pressure(usage_percent, available_for_models)
                
                memory_info = {
                    "total_mb": total_mb,
                    "used_mb": used_mb,
                    "free_mb": free_mb,
                    "usage_percent": round(usage_percent, 1),
                    "available_for_models": available_for_models,
                    "safety_buffer_mb": self.safety_buffer_mb,
                    "pressure_level": pressure_level,
                    "pytorch_memory": pytorch_memory,
                    "timestamp": datetime.now().isoformat()
                }
                
                self.last_memory_check = memory_info
                return memory_info
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get GPU memory info: {e}")
        
        return {
            "error": "Could not retrieve GPU memory information",
            "pressure_level": "UNKNOWN",
            "available_for_models": 0
        }
    
    def _assess_memory_pressure(self, usage_percent: float, available_mb: int) -> str:
        """Assess GPU memory pressure level"""
        if usage_percent > 95 or available_mb < 200:
            return "CRITICAL"  # Cannot load any models
        elif usage_percent > 85 or available_mb < 1000:
            return "HIGH"      # Can only load small models
        elif usage_percent > 70 or available_mb < 2000:
            return "MEDIUM"    # Limited model loading
        else:
            return "LOW"       # Normal operation
    
    def can_load_model(self, estimated_size_mb: int) -> Dict[str, Any]:
        """Check if a model can be loaded safely"""
        memory_info = self.get_detailed_gpu_memory()
        available_mb = memory_info.get("available_for_models", 0)
        pressure_level = memory_info.get("pressure_level", "UNKNOWN")
        
        can_load = available_mb >= estimated_size_mb
        
        recommendation = {
            "can_load": can_load,
            "available_mb": available_mb,
            "requested_mb": estimated_size_mb,
            "pressure_level": pressure_level,
            "safety_margin_mb": available_mb - estimated_size_mb if can_load else 0
        }
        
        if not can_load:
            if pressure_level == "CRITICAL":
                recommendation["recommendation"] = "Emergency cleanup required before any model loading"
            elif available_mb < estimated_size_mb:
                recommendation["recommendation"] = f"Need {estimated_size_mb - available_mb}MB more memory. Try cleanup first."
            else:
                recommendation["recommendation"] = "Memory pressure too high for safe loading"
        else:
            recommendation["recommendation"] = "Safe to load model"
        
        return recommendation

class AggressiveCleanupManager:
    """Force GPU memory cleanup when needed"""
    
    def __init__(self):
        self.model_usage_tracking = {}  # Track when models were last used
        self.loaded_models = {}  # Track currently loaded models
    
    def track_model_usage(self, model_name: str):
        """Track when a model was last used"""
        self.model_usage_tracking[model_name] = datetime.now()
    
    def register_loaded_model(self, model_name: str, model_ref: Any):
        """Register a loaded model for tracking"""
        self.loaded_models[model_name] = {
            "model": model_ref,
            "loaded_at": datetime.now(),
            "last_used": datetime.now()
        }
    
    def unregister_model(self, model_name: str):
        """Unregister a model (when unloaded)"""
        if model_name in self.loaded_models:
            del self.loaded_models[model_name]
        if model_name in self.model_usage_tracking:
            del self.model_usage_tracking[model_name]
    
    async def emergency_gpu_cleanup(self) -> Dict[str, Any]:
        """Complete emergency GPU memory cleanup"""
        cleanup_steps = []
        initial_memory = GPUMemoryMonitor().get_detailed_gpu_memory()
        
        # Step 1: Clear PyTorch CUDA cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            cleanup_steps.append("pytorch_cache_cleared")
        
        # Step 2: Unload all tracked models
        unloaded_models = []
        for model_name in list(self.loaded_models.keys()):
            try:
                del self.loaded_models[model_name]["model"]
                self.unregister_model(model_name)
                unloaded_models.append(model_name)
            except Exception as e:
                logger.error(f"Error unloading model {model_name}: {e}")
        
        if unloaded_models:
            cleanup_steps.append(f"unloaded_models: {unloaded_models}")
        
        # Step 3: Force garbage collection
        gc.collect()
        cleanup_steps.append("garbage_collection")
        
        # Step 4: Clear CUDA cache again
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
            cleanup_steps.append("final_cuda_cleanup")
        
        # Wait for cleanup to take effect
        await asyncio.sleep(1)
        
        final_memory = GPUMemoryMonitor().get_detailed_gpu_memory()
        
        memory_freed = initial_memory.get("used_mb", 0) - final_memory.get("used_mb", 0)
        
        return {
            "success": True,
            "cleanup_steps": cleanup_steps,
            "initial_memory_mb": initial_memory.get("used_mb", 0),
            "final_memory_mb": final_memory.get("used_mb", 0),
            "memory_freed_mb": memory_freed,
            "models_unloaded": unloaded_models,
            "final_pressure": final_memory.get("pressure_level", "UNKNOWN")
        }
    
    async def cleanup_least_used_models(self, max_age_minutes: int = 2) -> Dict[str, Any]:
        """Cleanup models not used recently"""
        cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
        models_to_unload = []
        
        for model_name, model_info in self.loaded_models.items():
            last_used = model_info.get("last_used", model_info["loaded_at"])
            if last_used < cutoff_time:
                models_to_unload.append(model_name)
        
        unloaded_models = []
        for model_name in models_to_unload:
            try:
                del self.loaded_models[model_name]["model"]
                self.unregister_model(model_name)
                unloaded_models.append(model_name)
                
                # Clear cache after each unload
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
            except Exception as e:
                logger.error(f"Error unloading unused model {model_name}: {e}")
        
        return {
            "unloaded_models": unloaded_models,
            "total_unloaded": len(unloaded_models),
            "cutoff_minutes": max_age_minutes
        }
    
    async def unload_non_essential_models(self) -> Dict[str, Any]:
        """Unload all but the most recently used model"""
        if len(self.loaded_models) <= 1:
            return {"message": "Only one or no models loaded, nothing to unload"}
        
        # Find most recently used model
        most_recent_model = None
        most_recent_time = datetime.min
        
        for model_name, model_info in self.loaded_models.items():
            last_used = model_info.get("last_used", model_info["loaded_at"])
            if last_used > most_recent_time:
                most_recent_time = last_used
                most_recent_model = model_name
        
        # Unload all except most recent
        unloaded_models = []
        for model_name in list(self.loaded_models.keys()):
            if model_name != most_recent_model:
                try:
                    del self.loaded_models[model_name]["model"]
                    self.unregister_model(model_name)
                    unloaded_models.append(model_name)
                    
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                
                except Exception as e:
                    logger.error(f"Error unloading non-essential model {model_name}: {e}")
        
        return {
            "kept_model": most_recent_model,
            "unloaded_models": unloaded_models,
            "total_unloaded": len(unloaded_models)
        }

class EmergencyRecoverySystem:
    """Handle catastrophic GPU memory situations"""
    
    def __init__(self):
        self.process_manager = ProcessManager()
        self.gpu_monitor = GPUMemoryMonitor()
        self.cleanup_manager = AggressiveCleanupManager()
    
    async def handle_gpu_memory_exhaustion(self) -> Dict[str, Any]:
        """Complete GPU memory recovery"""
        recovery_steps = []
        initial_memory = self.gpu_monitor.get_detailed_gpu_memory()
        
        logger.warning("Starting emergency GPU memory recovery...")
        
        try:
            # Step 1: Terminate duplicate processes
            logger.info("Step 1: Cleaning up duplicate processes")
            duplicate_cleanup = await self.process_manager.cleanup_duplicate_processes()
            recovery_steps.append(("duplicate_cleanup", duplicate_cleanup))
            
            # Step 2: Emergency model unloading
            logger.info("Step 2: Emergency model cleanup")
            model_cleanup = await self.cleanup_manager.emergency_gpu_cleanup()
            recovery_steps.append(("model_cleanup", model_cleanup))
            
            # Step 3: Clear all GPU caches
            logger.info("Step 3: Clearing GPU caches")
            cache_cleanup = await self._clear_all_gpu_caches()
            recovery_steps.append(("cache_cleanup", cache_cleanup))
            
            # Step 4: Force garbage collection
            logger.info("Step 4: Force garbage collection")
            gc_cleanup = await self._force_garbage_collection()
            recovery_steps.append(("gc_cleanup", gc_cleanup))
            
            # Step 5: Verify recovery
            logger.info("Step 5: Verifying recovery")
            final_memory = self.gpu_monitor.get_detailed_gpu_memory()
            recovery_steps.append(("final_memory", final_memory))
            
            memory_freed = initial_memory.get("used_mb", 0) - final_memory.get("used_mb", 0)
            
            success = final_memory.get("pressure_level", "CRITICAL") != "CRITICAL"
            
            logger.info(f"Emergency recovery {'succeeded' if success else 'failed'}. "
                       f"Freed {memory_freed}MB. Final pressure: {final_memory.get('pressure_level')}")
            
            return {
                "success": success,
                "recovery_steps": recovery_steps,
                "initial_memory_mb": initial_memory.get("used_mb", 0),
                "final_memory_mb": final_memory.get("used_mb", 0),
                "memory_freed_mb": memory_freed,
                "final_pressure": final_memory.get("pressure_level"),
                "final_available_mb": final_memory.get("available_for_models", 0)
            }
        
        except Exception as e:
            logger.error(f"Emergency recovery failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "recovery_steps": recovery_steps
            }
    
    async def _clear_all_gpu_caches(self) -> Dict[str, Any]:
        """Clear all possible GPU caches"""
        cleared_caches = []
        
        if torch.cuda.is_available():
            try:
                torch.cuda.empty_cache()
                cleared_caches.append("pytorch_cache")
            except Exception as e:
                logger.error(f"Error clearing PyTorch cache: {e}")
            
            try:
                torch.cuda.ipc_collect()
                cleared_caches.append("pytorch_ipc")
            except Exception as e:
                logger.error(f"Error clearing PyTorch IPC: {e}")
        
        return {
            "cleared_caches": cleared_caches,
            "success": len(cleared_caches) > 0
        }
    
    async def _force_garbage_collection(self) -> Dict[str, Any]:
        """Force comprehensive garbage collection"""
        try:
            collected_objects = gc.collect()
            return {
                "success": True,
                "collected_objects": collected_objects
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

class GPUMemoryManager:
    """Main GPU memory management orchestrator"""
    
    def __init__(self):
        self.process_manager = ProcessManager()
        self.gpu_monitor = GPUMemoryMonitor()
        self.cleanup_manager = AggressiveCleanupManager()
        self.recovery_system = EmergencyRecoverySystem()
        
        logger.info("GPU Memory Manager initialized")
    
    async def load_model_safely(self, model_name: str, estimated_size_mb: int, 
                               load_function, *args, **kwargs) -> Tuple[Any, Dict[str, Any]]:
        """Load model with comprehensive memory safety checks"""
        load_report = {
            "model_name": model_name,
            "estimated_size_mb": estimated_size_mb,
            "steps_taken": [],
            "success": False
        }
        
        try:
            # Step 1: Check for process conflicts first
            conflicts = self.process_manager.detect_duplicate_processes()
            if conflicts["has_conflicts"]:
                logger.warning(f"Detected {len(conflicts['conflicts_detected'])} duplicate processes")
                cleanup_result = await self.process_manager.cleanup_duplicate_processes()
                load_report["steps_taken"].append(("duplicate_cleanup", cleanup_result))
            
            # Step 2: Assess GPU memory availability
            memory_check = self.gpu_monitor.can_load_model(estimated_size_mb)
            load_report["steps_taken"].append(("initial_memory_check", memory_check))
            
            if not memory_check["can_load"]:
                # Step 3: Try progressive cleanup
                await self._progressive_memory_cleanup(estimated_size_mb, load_report)
                
                # Step 4: Re-check after cleanup
                memory_check = self.gpu_monitor.can_load_model(estimated_size_mb)
                load_report["steps_taken"].append(("post_cleanup_memory_check", memory_check))
                
                if not memory_check["can_load"]:
                    # Step 5: Force emergency cleanup
                    emergency_result = await self.recovery_system.handle_gpu_memory_exhaustion()
                    load_report["steps_taken"].append(("emergency_cleanup", emergency_result))
                    
                    # Step 6: Final check
                    final_check = self.gpu_monitor.can_load_model(estimated_size_mb)
                    load_report["steps_taken"].append(("final_memory_check", final_check))
                    
                    if not final_check["can_load"]:
                        raise GPUMemoryExhaustionError(
                            f"Cannot load {model_name} ({estimated_size_mb}MB). "
                            f"Available: {final_check['available_mb']}MB. "
                            f"Pressure: {final_check['pressure_level']}"
                        )
            
            # Step 7: Load model with optimizations
            logger.info(f"Loading model {model_name} with {estimated_size_mb}MB estimated size")
            model = await self._load_model_gpu_optimized(load_function, *args, **kwargs)
            
            # Step 8: Register and track the model
            self.cleanup_manager.register_loaded_model(model_name, model)
            self.cleanup_manager.track_model_usage(model_name)
            
            # Step 9: Verify memory usage post-load
            post_load_info = self.gpu_monitor.get_detailed_gpu_memory()
            load_report["steps_taken"].append(("post_load_memory", post_load_info))
            
            load_report["success"] = True
            logger.info(f"Successfully loaded {model_name}. GPU pressure: {post_load_info.get('pressure_level')}")
            
            return model, load_report
        
        except Exception as e:
            load_report["error"] = str(e)
            logger.error(f"Failed to load model {model_name}: {e}")
            raise
    
    async def _progressive_memory_cleanup(self, required_mb: int, load_report: Dict[str, Any]):
        """Progressive cleanup strategy when memory needed"""
        
        # Level 1: Clear PyTorch cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            load_report["steps_taken"].append(("level1_cache_clear", "pytorch_cache_cleared"))
            
            if self.gpu_monitor.can_load_model(required_mb)["can_load"]:
                return
        
        # Level 2: Unload models unused for 2+ minutes
        cleanup_result = await self.cleanup_manager.cleanup_least_used_models(max_age_minutes=2)
        load_report["steps_taken"].append(("level2_unused_models", cleanup_result))
        
        if self.gpu_monitor.can_load_model(required_mb)["can_load"]:
            return
        
        # Level 3: Unload all but most essential model
        essential_cleanup = await self.cleanup_manager.unload_non_essential_models()
        load_report["steps_taken"].append(("level3_non_essential", essential_cleanup))
        
        if self.gpu_monitor.can_load_model(required_mb)["can_load"]:
            return
        
        # Level 4: Emergency cleanup (unload everything)
        emergency_cleanup = await self.cleanup_manager.emergency_gpu_cleanup()
        load_report["steps_taken"].append(("level4_emergency", emergency_cleanup))
    
    async def _load_model_gpu_optimized(self, load_function, *args, **kwargs):
        """Load model with maximum GPU memory efficiency"""
        # Add memory optimization parameters if not already specified
        if 'device' not in kwargs:
            kwargs['device'] = 0  # Force GPU usage
        
        if 'torch_dtype' not in kwargs:
            kwargs['torch_dtype'] = torch.float16  # Half precision
        
        # Add model-specific optimizations
        if 'model_kwargs' not in kwargs:
            kwargs['model_kwargs'] = {}
        
        kwargs['model_kwargs'].update({
            "low_cpu_mem_usage": True,
            "torch_dtype": torch.float16,
            "device_map": "auto"
        })
        
        # Call the actual loading function
        if asyncio.iscoroutinefunction(load_function):
            return await load_function(*args, **kwargs)
        else:
            return load_function(*args, **kwargs)
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive GPU memory management status"""
        gpu_memory = self.gpu_monitor.get_detailed_gpu_memory()
        process_info = self.process_manager.detect_duplicate_processes()
        
        return {
            "gpu_memory": gpu_memory,
            "process_info": process_info,
            "loaded_models": len(self.cleanup_manager.loaded_models),
            "model_details": {
                name: {
                    "loaded_at": info["loaded_at"].isoformat(),
                    "last_used": info["last_used"].isoformat()
                }
                for name, info in self.cleanup_manager.loaded_models.items()
            },
            "recommendations": self._generate_recommendations(gpu_memory, process_info)
        }
    
    def _generate_recommendations(self, gpu_memory: Dict[str, Any], 
                                process_info: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        pressure = gpu_memory.get("pressure_level", "UNKNOWN")
        if pressure == "CRITICAL":
            recommendations.append("🚨 CRITICAL: Emergency cleanup required immediately")
        elif pressure == "HIGH":
            recommendations.append("⚠️ HIGH: Consider unloading unused models")
        
        if process_info.get("has_conflicts", False):
            recommendations.append("🔄 Multiple AI processes detected - cleanup recommended")
        
        available_mb = gpu_memory.get("available_for_models", 0)
        if available_mb < 500:
            recommendations.append(f"💾 Low memory available ({available_mb}MB) - cleanup needed")
        
        return recommendations

# Global instance
_gpu_memory_manager: Optional[GPUMemoryManager] = None

def get_gpu_memory_manager() -> GPUMemoryManager:
    """Get global GPU memory manager instance"""
    global _gpu_memory_manager
    if _gpu_memory_manager is None:
        _gpu_memory_manager = GPUMemoryManager()
    return _gpu_memory_manager
