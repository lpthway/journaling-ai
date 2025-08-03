"""
Adaptive Memory Management System

This module manages AI model memory allocation and cleanup based on available
hardware resources to prevent OOM errors and optimize performance.
"""

import asyncio
import gc
import logging
import time
import threading
from typing import Dict, Any, Optional, Set, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import weakref

# Import the GPU memory management system
from .gpu_memory_manager import GPUMemoryManager, get_gpu_memory_manager

logger = logging.getLogger(__name__)

class ModelState(Enum):
    """States of model lifecycle"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVE = "active"
    CLEANUP_SCHEDULED = "cleanup_scheduled"

@dataclass
class ModelInfo:
    """Information about a loaded model"""
    model_type: str
    model_name: str
    memory_mb: int
    last_accessed: datetime = field(default_factory=datetime.now)
    load_time: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    state: ModelState = ModelState.UNLOADED
    model_ref: Optional[weakref.ref] = None
    loading_task: Optional[asyncio.Task] = None

class AdaptiveMemoryManager:
    """Manage AI model memory based on available resources"""
    
    def __init__(self, hardware_tier: str, memory_limit_mb: int):
        self.hardware_tier = hardware_tier
        self.memory_limit_mb = memory_limit_mb
        self.loaded_models: Dict[str, ModelInfo] = {}
        self.memory_usage_mb = 0
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # Integrate GPU memory management
        self.gpu_memory_manager = get_gpu_memory_manager()
        self.monitor_task: Optional[asyncio.Task] = None
        self.cleanup_interval = 300  # 5 minutes
        self.model_timeout = 600  # 10 minutes
        self.memory_pressure_threshold = 0.85
        self.emergency_cleanup_threshold = 0.95
        self.max_concurrent_models = 3
        self._lock = asyncio.Lock()
        self._memory_pressure = False
        self._emergency_mode = False
        
        # Start background tasks
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background monitoring and cleanup tasks"""
        try:
            loop = asyncio.get_running_loop()
            self.cleanup_task = loop.create_task(self._periodic_cleanup())
            self.monitor_task = loop.create_task(self._memory_monitor())
        except RuntimeError:
            # No event loop running, tasks will be started later
            pass
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of unused models"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_unused_models()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    async def _memory_monitor(self):
        """Monitor memory usage and trigger emergency cleanup if needed"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._check_memory_pressure()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in memory monitor: {e}")
    
    async def _check_memory_pressure(self):
        """Check for memory pressure and take action"""
        usage_ratio = self.memory_usage_mb / self.memory_limit_mb
        
        if usage_ratio >= self.emergency_cleanup_threshold:
            if not self._emergency_mode:
                logger.warning(f"Emergency memory cleanup triggered! Usage: {usage_ratio:.1%}")
                self._emergency_mode = True
                await self._emergency_cleanup()
        elif usage_ratio >= self.memory_pressure_threshold:
            if not self._memory_pressure:
                logger.info(f"Memory pressure detected. Usage: {usage_ratio:.1%}")
                self._memory_pressure = True
                await self._aggressive_cleanup()
        else:
            self._memory_pressure = False
            self._emergency_mode = False
    
    async def load_model_safely(self, model_type: str, model_config: Dict[str, Any]) -> Optional[Any]:
        """Load a model safely with comprehensive GPU memory management"""
        model_key = f"{model_type}_{model_config['name']}"
        estimated_memory_mb = model_config.get('memory_mb', 500)
        
        async with self._lock:
            # Check if model is already loaded
            if model_key in self.loaded_models:
                model_info = self.loaded_models[model_key]
                if model_info.state == ModelState.LOADED and model_info.model_ref:
                    model = model_info.model_ref()
                    if model is not None:
                        model_info.last_accessed = datetime.now()
                        model_info.access_count += 1
                        model_info.state = ModelState.ACTIVE
                        logger.debug(f"Reusing loaded model: {model_key}")
                        return model
                
                # Model exists but not loaded properly, remove it
                await self._unload_model(model_key)
            
            # Use GPU memory manager for comprehensive safety checks
            try:
                def load_function():
                    return self._load_optimized_model_sync(model_config)
                
                model, load_report = await self.gpu_memory_manager.load_model_safely(
                    model_name=model_key,
                    estimated_size_mb=estimated_memory_mb,
                    load_function=load_function
                )
                
                # Track the successfully loaded model
                model_info = ModelInfo(
                    model_type=model_type,
                    model_name=model_config['name'],
                    memory_mb=estimated_memory_mb,
                    state=ModelState.LOADED
                )
                
                model_info.model_ref = weakref.ref(model, 
                                                 lambda ref: asyncio.create_task(self._on_model_deleted(model_key)))
                model_info.last_accessed = datetime.now()
                model_info.access_count = 1
                self.memory_usage_mb += estimated_memory_mb
                
                self.loaded_models[model_key] = model_info
                
                logger.info(f"Successfully loaded model with GPU management: {model_key} ({estimated_memory_mb}MB)")
                logger.debug(f"Load report: {load_report}")
                
                return model
                
            except Exception as e:
                logger.error(f"GPU memory management failed for {model_key}: {e}")
                
                # Fallback to traditional memory management
                logger.info("Attempting traditional memory management as fallback")
                return await self._fallback_load_model(model_type, model_config)
    
    async def _fallback_load_model(self, model_type: str, model_config: Dict[str, Any]) -> Optional[Any]:
        """Fallback model loading when GPU memory management fails"""
        model_key = f"{model_type}_{model_config['name']}"
        required_memory = model_config.get('memory_mb', 500)
        
        # Check memory availability
        if not await self._ensure_memory_available(required_memory):
            logger.warning(f"Cannot load {model_key}: insufficient memory")
            return None
        
        # Check concurrent model limit
        active_models = sum(1 for info in self.loaded_models.values() 
                          if info.state in [ModelState.LOADED, ModelState.ACTIVE])
        
        if active_models >= self.max_concurrent_models:
            logger.info(f"Max concurrent models reached, cleaning up least used")
            await self._cleanup_least_used_model()
        
        # Start loading
        model_info = ModelInfo(
            model_type=model_type,
            model_name=model_config['name'],
            memory_mb=required_memory,
            state=ModelState.LOADING
        )
        
        self.loaded_models[model_key] = model_info
        
        try:
            # Load model with optimization
            model = await self._load_optimized_model(model_config)
            
            if model is not None:
                model_info.model_ref = weakref.ref(model, 
                                                 lambda ref: asyncio.create_task(self._on_model_deleted(model_key)))
                model_info.state = ModelState.LOADED
                model_info.last_accessed = datetime.now()
                model_info.access_count = 1
                self.memory_usage_mb += required_memory
                
                logger.info(f"Successfully loaded model (fallback): {model_key} ({required_memory}MB)")
                return model
            else:
                # Loading failed
                del self.loaded_models[model_key]
                return None
                
        except Exception as e:
            logger.error(f"Failed to load model {model_key} (fallback): {e}")
            if model_key in self.loaded_models:
                del self.loaded_models[model_key]
            await self._force_cleanup()
            return None
    
    def _load_optimized_model_sync(self, model_config: Dict[str, Any]) -> Any:
        """Synchronous optimized model loading for GPU memory manager"""
        try:
            # Import here to avoid startup issues if transformers not available
            from transformers import pipeline
            import torch
            
            model_name = model_config['name']
            task = model_config['task']
            
            # GPU optimization parameters
            optimization_kwargs = {}
            if torch.cuda.is_available():
                optimization_kwargs.update({
                    'device': 0,  # Force GPU usage
                    'torch_dtype': torch.float16,  # Half precision
                    'model_kwargs': {
                        "low_cpu_mem_usage": True,
                        "torch_dtype": torch.float16,
                        "device_map": "auto"
                    }
                })
            
            # Load the model
            model = pipeline(
                task=task,
                model=model_name,
                **optimization_kwargs
            )
            
            return model
            
        except Exception as e:
            logger.error(f"Failed to load optimized model: {e}")
            raise
    
    async def _load_optimized_model(self, model_config: Dict[str, Any]) -> Optional[Any]:
        """Load model with memory optimizations"""
        try:
            # Import here to avoid startup issues if transformers not available
            from transformers import pipeline
            import torch
            
            model_name = model_config['name']
            task = model_config['task']
            
            # Optimization parameters based on hardware tier
            optimization_params = {
                'model': model_name,
                'task': task,
                'device_map': 'auto',
                'trust_remote_code': True,
                'model_kwargs': {
                    'cache_dir': './models',
                    'low_cpu_mem_usage': True,
                }
            }
            
            # Add hardware-specific optimizations
            if self.hardware_tier in ['STANDARD', 'HIGH_END']:
                # Use half precision for better memory efficiency
                optimization_params['torch_dtype'] = torch.float16
                
                # Try to use GPU if available
                if torch.cuda.is_available():
                    optimization_params['device'] = 0
                    # Reserve some GPU memory
                    torch.cuda.empty_cache()
            
            logger.info(f"Loading model {model_name} with optimizations for {self.hardware_tier}")
            
            # Load model in executor to avoid blocking
            loop = asyncio.get_running_loop()
            model = await loop.run_in_executor(
                None, 
                lambda: pipeline(**optimization_params)
            )
            
            return model
            
        except ImportError:
            logger.error("transformers library not available for model loading")
            return None
        except Exception as e:
            logger.error(f"Error loading optimized model: {e}")
            await self._cleanup_gpu_memory()
            return None
    
    async def _ensure_memory_available(self, required_mb: int) -> bool:
        """Ensure sufficient memory is available"""
        available_mb = self.memory_limit_mb - self.memory_usage_mb
        
        if available_mb >= required_mb:
            return True
        
        # Try to free up memory
        cleanup_target = required_mb - available_mb + 100  # Extra buffer
        freed_mb = await self._free_memory(cleanup_target)
        
        available_after_cleanup = self.memory_limit_mb - self.memory_usage_mb
        return available_after_cleanup >= required_mb
    
    async def _free_memory(self, target_mb: int) -> int:
        """Free up specified amount of memory"""
        freed_mb = 0
        
        # Sort models by priority (least recently used, least accessed)
        cleanup_candidates = [
            (key, info) for key, info in self.loaded_models.items()
            if info.state in [ModelState.LOADED, ModelState.ACTIVE]
        ]
        
        cleanup_candidates.sort(key=lambda x: (
            x[1].last_accessed,  # Least recently used first
            x[1].access_count    # Least accessed first
        ))
        
        for model_key, model_info in cleanup_candidates:
            if freed_mb >= target_mb:
                break
                
            logger.info(f"Freeing memory by unloading {model_key}")
            await self._unload_model(model_key)
            freed_mb += model_info.memory_mb
        
        # Force garbage collection
        gc.collect()
        await self._cleanup_gpu_memory()
        
        return freed_mb
    
    async def cleanup_unused_models(self):
        """Clean up models that haven't been used recently"""
        cutoff_time = datetime.now() - timedelta(seconds=self.model_timeout)
        
        models_to_cleanup = [
            key for key, info in self.loaded_models.items()
            if (info.last_accessed < cutoff_time and 
                info.state in [ModelState.LOADED, ModelState.ACTIVE])
        ]
        
        for model_key in models_to_cleanup:
            logger.info(f"Cleaning up unused model: {model_key}")
            await self._unload_model(model_key)
    
    async def _aggressive_cleanup(self):
        """More aggressive cleanup during memory pressure"""
        # Reduce timeout for cleanup
        cutoff_time = datetime.now() - timedelta(seconds=self.model_timeout // 2)
        
        models_to_cleanup = [
            key for key, info in self.loaded_models.items()
            if info.last_accessed < cutoff_time
        ]
        
        for model_key in models_to_cleanup:
            await self._unload_model(model_key)
        
        gc.collect()
        await self._cleanup_gpu_memory()
    
    async def _emergency_cleanup(self):
        """Emergency cleanup - unload all but most recently used model"""
        if not self.loaded_models:
            return
        
        # Keep only the most recently accessed model
        most_recent = max(self.loaded_models.items(), 
                         key=lambda x: x[1].last_accessed)
        
        models_to_cleanup = [
            key for key in self.loaded_models.keys() 
            if key != most_recent[0]
        ]
        
        logger.warning(f"Emergency cleanup: unloading {len(models_to_cleanup)} models")
        
        for model_key in models_to_cleanup:
            await self._unload_model(model_key)
        
        # Force aggressive garbage collection
        for _ in range(3):
            gc.collect()
        
        await self._cleanup_gpu_memory()
    
    async def _cleanup_least_used_model(self):
        """Clean up the least used model"""
        if not self.loaded_models:
            return
        
        # Find least used model
        least_used = min(self.loaded_models.items(),
                        key=lambda x: (x[1].access_count, x[1].last_accessed))
        
        await self._unload_model(least_used[0])
    
    async def _unload_model(self, model_key: str):
        """Unload a specific model"""
        if model_key not in self.loaded_models:
            return
        
        model_info = self.loaded_models[model_key]
        
        # Clear model reference
        if model_info.model_ref:
            model = model_info.model_ref()
            if model is not None:
                del model
        
        # Update memory tracking
        self.memory_usage_mb -= model_info.memory_mb
        
        # Remove from tracking
        del self.loaded_models[model_key]
        
        logger.debug(f"Unloaded model: {model_key}")
    
    async def _on_model_deleted(self, model_key: str):
        """Callback when model is garbage collected"""
        if model_key in self.loaded_models:
            model_info = self.loaded_models[model_key]
            self.memory_usage_mb -= model_info.memory_mb
            del self.loaded_models[model_key]
            logger.debug(f"Model garbage collected: {model_key}")
    
    async def _cleanup_gpu_memory(self):
        """Clean up GPU memory if available"""
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"GPU cleanup error: {e}")
    
    async def _force_cleanup(self):
        """Force cleanup of all resources"""
        logger.warning("Forcing cleanup of all loaded models")
        
        models_to_cleanup = list(self.loaded_models.keys())
        for model_key in models_to_cleanup:
            await self._unload_model(model_key)
        
        # Aggressive garbage collection
        for _ in range(3):
            gc.collect()
        
        await self._cleanup_gpu_memory()
        
        self.memory_usage_mb = 0
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get current memory usage information"""
        return {
            "memory_limit_mb": self.memory_limit_mb,
            "memory_usage_mb": self.memory_usage_mb,
            "memory_free_mb": self.memory_limit_mb - self.memory_usage_mb,
            "usage_percent": (self.memory_usage_mb / self.memory_limit_mb) * 100,
            "loaded_models": len(self.loaded_models),
            "memory_pressure": self._memory_pressure,
            "emergency_mode": self._emergency_mode,
            "model_details": {
                key: {
                    "memory_mb": info.memory_mb,
                    "last_accessed": info.last_accessed.isoformat(),
                    "access_count": info.access_count,
                    "state": info.state.value
                }
                for key, info in self.loaded_models.items()
            }
        }
    
    async def shutdown(self):
        """Clean shutdown of memory manager with GPU memory management"""
        logger.info("Shutting down adaptive memory manager")
        
        # Cancel background tasks
        if self.cleanup_task:
            self.cleanup_task.cancel()
        if self.monitor_task:
            self.monitor_task.cancel()
        
        # Use GPU memory manager for comprehensive cleanup
        try:
            cleanup_result = await self.gpu_memory_manager.recovery_system.handle_gpu_memory_exhaustion()
            logger.info(f"GPU memory cleanup during shutdown: {cleanup_result}")
        except Exception as e:
            logger.warning(f"GPU memory cleanup failed during shutdown: {e}")
        
        # Clean up all models
        await self._force_cleanup()
        
        logger.info("Memory manager shutdown complete")
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive status including GPU memory management"""
        basic_info = self.get_memory_info()
        
        # Add GPU memory management status
        try:
            gpu_status = self.gpu_memory_manager.get_comprehensive_status()
            basic_info["gpu_memory_management"] = gpu_status
        except Exception as e:
            logger.warning(f"Could not get GPU memory status: {e}")
            basic_info["gpu_memory_management"] = {"error": str(e)}
        
        return basic_info
