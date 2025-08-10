# AI Model Manager Service - Centralized AI Model Management

"""
AI Model Manager Service for Journaling AI
Provides centralized AI model loading, caching, and memory management
Integrates with Phase 2 unified cache patterns and service registry
Hardware-adaptive model selection for optimal performance
"""

import logging
import asyncio
import hashlib
import torch
import gc
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from pathlib import Path
from transformers import pipeline, AutoTokenizer, AutoModel, AutoModelForSequenceClassification
import psutil

# Phase 2 integration imports
from app.core.cache_patterns import CacheDomain, CachePatterns, CacheKeyBuilder
from app.services.cache_service import unified_cache_service
from app.core.service_interfaces import ServiceRegistry
from app.core.config import settings

# Hardware-adaptive model selection
from app.services.hardware_service import hardware_service

logger = logging.getLogger(__name__)

class ModelInfo:
    """Information about an AI model"""
    def __init__(self, name: str, model_type: str, memory_usage: int = 0, 
                 loaded_at: datetime = None, last_used: datetime = None):
        self.name = name
        self.model_type = model_type
        self.memory_usage = memory_usage
        self.loaded_at = loaded_at or datetime.utcnow()
        self.last_used = last_used or datetime.utcnow()
        self.usage_count = 0

class AIModelManager:
    """
    Centralized AI Model Manager
    
    Provides enterprise-grade model management with:
    - Phase 2 cache integration
    - Hardware-aware model selection
    - Memory usage optimization
    - Automatic model lifecycle management
    """
    
    def __init__(self):
        self.loaded_models: Dict[str, Any] = {}
        self.model_info: Dict[str, ModelInfo] = {}
        self.max_memory_usage = self._get_max_memory_usage()
        self.models_directory = Path(__file__).parent.parent.parent / "models"
        
        # Get configuration settings
        self.settings = settings
        
        # Set CUDA memory management environment variables for better fragmentation handling
        import os
        if not os.environ.get('PYTORCH_CUDA_ALLOC_CONF'):
            os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
        
        # Check for CPU fallback configuration
        self.force_cpu = self.settings.AI_FORCE_CPU
        if self.force_cpu:
            logger.warning("🔄 AI_FORCE_CPU is enabled - forcing CPU mode for all models")
            os.environ['CUDA_VISIBLE_DEVICES'] = ""
        
        # Hardware detection with fallback handling
        self.has_gpu = torch.cuda.is_available() and not self.force_cpu
        self.gpu_memory = self._get_gpu_memory() if self.has_gpu else 0
        
        # Model configuration will be initialized async
        self.model_configs: Dict[str, Dict[str, Any]] = {}
        self._initialized = False
        
        logger.info(f"🤖 AI Model Manager initializing...")
        logger.info(f"   GPU Available: {torch.cuda.is_available()}")
        logger.info(f"   Force CPU Mode: {self.force_cpu}")
        logger.info(f"   Using GPU: {self.has_gpu}")
        if self.has_gpu:
            logger.info(f"   GPU Memory: {self.gpu_memory:.1f} GB")
        logger.info(f"   Max Memory Usage: {self.max_memory_usage:.1f} GB")
        
    async def initialize(self):
        """Initialize hardware-adaptive model configurations"""
        if not self._initialized:
            self.model_configs = await self._initialize_model_configs()
            self._initialized = True
            logger.info(f"✅ AI Model Manager fully initialized")
        logger.info(f"   Models Directory: {self.models_directory}")

    def _get_max_memory_usage(self) -> float:
        """Calculate maximum memory usage for AI models"""
        total_memory = psutil.virtual_memory().total / (1024**3)  # GB
        # Use 30% of system memory for AI models, with minimum 2GB
        return max(total_memory * 0.3, 2.0)

    def _get_gpu_memory(self) -> float:
        """Get GPU memory in GB"""
        if torch.cuda.is_available():
            return torch.cuda.get_device_properties(0).total_memory / (1024**3)
        return 0.0

    async def _initialize_model_configs(self) -> Dict[str, Dict[str, Any]]:
        """Initialize configuration for available AI models with hardware adaptation"""
        
        # Detect hardware first
        await hardware_service.detect_hardware()
        hardware_summary = hardware_service.get_hardware_summary()
        optimal_models = hardware_service.get_all_optimal_models()
        
        logger.info(f"🔧 Hardware-adaptive model selection enabled")
        logger.info(f"   Performance tier: {hardware_summary['performance_tier']}")
        logger.info(f"   GPU: {hardware_summary['gpu']['name']} ({hardware_summary['gpu']['memory_gb']:.1f}GB)")
        
        # Get optimal models for each task
        emotion_model, emotion_gpu = optimal_models["emotion"]
        sentiment_model, sentiment_gpu = optimal_models["sentiment"]
        embedding_model, embedding_gpu = optimal_models["embeddings"]
        classification_model, classification_gpu = optimal_models["classification"]
        
        logger.info(f"🎯 Selected models:")
        logger.info(f"   Emotion: {emotion_model} (GPU: {emotion_gpu})")
        logger.info(f"   Sentiment: {sentiment_model} (GPU: {sentiment_gpu})")
        logger.info(f"   Embeddings: {embedding_model} (GPU: {embedding_gpu})")
        logger.info(f"   Classification: {classification_model} (GPU: {classification_gpu})")
        
        return {
            # Hardware-optimized Emotion Analysis
            "emotion_classifier": {
                "model_name": "j-hartmann/emotion-english-distilroberta-base",  # Use proper emotion model
                "model_type": "text-classification",
                "task": "emotion-analysis",
                "languages": ["en"],
                "memory_estimate": 1.2 if emotion_gpu else 0.5,  # GB
                "priority": "high",
                "use_gpu": emotion_gpu,
                "fallback": "cardiffnlp/twitter-roberta-base-emotion-latest"
            },
            
            # Hardware-optimized Sentiment Analysis
            "sentiment_classifier": {
                "model_name": sentiment_model,
                "model_type": "text-classification", 
                "task": "sentiment-analysis",
                "languages": ["en"],
                "memory_estimate": 1.5 if sentiment_gpu else 0.6,  # GB
                "priority": "high",
                "use_gpu": sentiment_gpu,
                "fallback": "cardiffnlp/twitter-roberta-base-sentiment-latest"
            },
            
            # Multilingual sentiment (always available)
            "multilingual_sentiment": {
                "model_name": "cardiffnlp/twitter-xlm-roberta-base-sentiment",
                "model_type": "text-classification",
                "task": "sentiment-analysis", 
                "languages": ["en", "de", "es", "fr"],
                "memory_estimate": 1.2,  # GB
                "priority": "medium",
                "use_gpu": sentiment_gpu,
                "fallback": "distilbert-base-uncased-finetuned-sst-2-english"
            },
            
            # Lightweight fallback
            "distilbert_sentiment": {
                "model_name": "distilbert-base-uncased-finetuned-sst-2-english",
                "model_type": "text-classification",
                "task": "sentiment-analysis",
                "languages": ["en"],
                "memory_estimate": 0.3,  # GB
                "priority": "low",
                "use_gpu": False,
                "fallback": None
            },
            
            # Hardware-optimized Text Generation
            "text_generator": {
                "model_name": "facebook/bart-base",
                "model_type": "text2text-generation",
                "task": "text-generation",
                "languages": ["en"],
                "memory_estimate": 0.8,  # GB
                "priority": "medium",
                "use_gpu": classification_gpu,
                "fallback": None
            },
            
            "large_text_generator": {
                "model_name": "facebook/bart-large",
                "model_type": "text2text-generation", 
                "task": "text-generation",
                "languages": ["en"],
                "memory_estimate": 1.6,  # GB
                "priority": "low",
                "use_gpu": classification_gpu,
                "fallback": "text_generator"
            },
            
            # Hardware-optimized Zero-shot Classification
            "zero_shot_classifier": {
                "model_name": "facebook/bart-large-mnli",  # Proper zero-shot model
                "model_type": "zero-shot-classification",
                "task": "zero-shot-classification",
                "languages": ["en"],
                "memory_estimate": 6.0 if classification_gpu else 1.6,  # GB
                "priority": "medium",
                "use_gpu": classification_gpu,
                "fallback": "microsoft/DialoGPT-medium"
            },
            
            # Hardware-optimized Embeddings
            "sentence_embeddings": {
                "model_name": embedding_model,
                "model_type": "sentence-transformers",
                "task": "embeddings",
                "languages": ["en", "multilingual"],
                "memory_estimate": 4.0 if embedding_gpu else 0.4,  # GB
                "priority": "high",
                "use_gpu": embedding_gpu,
                "fallback": "sentence-transformers/all-MiniLM-L6-v2"
            },
            
            "large_embeddings": {
                "model_name": "sentence-transformers/all-mpnet-base-v2", 
                "model_type": "sentence-transformers",
                "task": "embeddings",
                "languages": ["en"],
                "memory_estimate": 0.8,  # GB
                "priority": "medium",
                "use_gpu": embedding_gpu,
                "fallback": "sentence_embeddings"
            }
        }

    # ==================== MODEL LOADING AND CACHING ====================

    async def get_model(self, model_key: str, **kwargs) -> Optional[Any]:
        """
        Get AI model with intelligent caching and memory management
        
        Args:
            model_key: Model identifier from model_configs
            **kwargs: Additional model loading parameters
            
        Returns:
            Loaded model pipeline or None if unavailable
        """
        try:
            # Ensure we're initialized
            if not self._initialized:
                await self.initialize()
            
            # Check if model is already loaded
            if model_key in self.loaded_models:
                self._update_model_usage(model_key)
                logger.debug(f"📖 Using cached model: {model_key}")
                return self.loaded_models[model_key]
            
            # NOTE: AI model objects (transformers pipelines) cannot be properly serialized
            # for Redis cache due to their complexity. They should only be cached in memory.
            # Redis cache is only suitable for serializable data objects, not model instances.
            
            # Load model with memory management
            model = await self._load_model_with_fallback(model_key, **kwargs)
            
            if model:
                # Store in memory only (AI models can't be serialized for Redis)
                self.loaded_models[model_key] = model
                logger.info(f"✅ Model loaded and stored in memory: {model_key}")
            
            return model
            
        except Exception as e:
            logger.error(f"❌ Error loading model {model_key}: {e}")
            return None

    async def _load_model_with_fallback(self, model_key: str, **kwargs) -> Optional[Any]:
        """Load model with automatic fallback to alternative models"""
        config = self.model_configs.get(model_key)
        if not config:
            logger.error(f"Unknown model key: {model_key}")
            return None
        
        # Check memory availability
        if not self._check_memory_availability(config["memory_estimate"]):
            await self._free_memory_for_model(config["memory_estimate"])
        
        try:
            # Attempt to load primary model
            model = await self._load_single_model(model_key, config, **kwargs)
            if model:
                self._register_loaded_model(model_key, config, model)
                return model
                
        except Exception as e:
            logger.warning(f"Failed to load primary model {model_key}: {e}")
            
            # Clear GPU cache if CUDA out of memory error
            if "CUDA out of memory" in str(e) and self.has_gpu:
                logger.warning("🧹 Clearing GPU cache due to CUDA memory error")
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        torch.cuda.synchronize()
                        torch.cuda.ipc_collect()
                except Exception as cleanup_error:
                    logger.error(f"Failed to clear GPU cache: {cleanup_error}")
            
            # Try fallback model if available
            fallback_key = config.get("fallback")
            if fallback_key and fallback_key != model_key:
                logger.info(f"🔄 Attempting fallback model: {fallback_key}")
                return await self._load_model_with_fallback(fallback_key, **kwargs)
        
        return None

    async def _load_single_model(self, model_key: str, config: Dict[str, Any], 
                                **kwargs) -> Optional[Any]:
        """Load a single AI model based on configuration"""
        model_name = config["model_name"]
        model_type = config["model_type"]
        use_gpu = config.get("use_gpu", False) and self.has_gpu
        
        # Determine device
        device = 0 if use_gpu else -1  # 0 for GPU, -1 for CPU
        
        # Prepare model path
        model_path = self._get_model_path(model_name)
        
        logger.info(f"🔄 Loading {model_key} on {'GPU' if use_gpu else 'CPU'}")
        
        try:
            if model_type == "text-classification":
                return pipeline(
                    "text-classification",
                    model=model_path,
                    tokenizer=model_path,
                    top_k=None,  # Updated from return_all_scores=True
                    device=device,
                    **kwargs
                )
            
            elif model_type == "text2text-generation":
                return pipeline(
                    "text2text-generation",
                    model=model_path,
                    tokenizer=model_path,
                    device=device,
                    **kwargs
                )
            
            elif model_type == "zero-shot-classification":
                return pipeline(
                    "zero-shot-classification",
                    model=model_path,
                    tokenizer=model_path,
                    device=device,
                    **kwargs
                )
            
            elif model_type == "sentence-transformers":
                # Special handling for sentence transformers
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer(str(model_path))
                if use_gpu:
                    model = model.to('cuda')
                return model
            
            else:
                logger.error(f"Unsupported model type: {model_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            
            # Handle CUDA errors with CPU fallback
            if ("CUDA" in str(e) or "device-side assert" in str(e)) and use_gpu:
                logger.warning(f"🔄 CUDA error detected, retrying {model_key} on CPU: {e}")
                
                # Clear GPU cache
                try:
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        torch.cuda.synchronize()
                        torch.cuda.ipc_collect()
                except Exception as cleanup_error:
                    logger.error(f"Failed to clear GPU cache: {cleanup_error}")
                
                # Retry on CPU
                try:
                    logger.info(f"🔄 Retrying {model_key} on CPU due to CUDA error")
                    device = -1  # Force CPU
                    
                    if model_type == "text-classification":
                        return pipeline(
                            "text-classification",
                            model=model_path,
                            tokenizer=model_path,
                            top_k=None,  # Updated from return_all_scores=True
                            device=device,
                            **kwargs
                        )
                    elif model_type == "zero-shot-classification":
                        return pipeline(
                            "zero-shot-classification",
                            model=model_path,
                            tokenizer=model_path,
                            device=device,
                            **kwargs
                        )
                    elif model_type == "sentence-transformers":
                        from sentence_transformers import SentenceTransformer
                        model = SentenceTransformer(str(model_path))
                        # Keep on CPU for sentence transformers fallback
                        return model
                    else:
                        return pipeline(
                            model_type,
                            model=model_path,
                            tokenizer=model_path,
                            device=device,
                            **kwargs
                        )
                        
                except Exception as cpu_error:
                    logger.error(f"❌ CPU fallback also failed for {model_key}: {cpu_error}")
                    return None
            
            # Clear GPU cache if CUDA out of memory error
            elif "CUDA out of memory" in str(e) and self.has_gpu:
                logger.warning("🧹 Clearing GPU cache due to CUDA memory error in single model load")
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        torch.cuda.synchronize()
                        torch.cuda.ipc_collect()
                except Exception as cleanup_error:
                    logger.error(f"Failed to clear GPU cache: {cleanup_error}")
            
            return None

    def _get_model_path(self, model_name: str) -> str:
        """Get local path for model, falling back to Hugging Face if not found locally"""
        local_path = self.models_directory / model_name.replace("/", "--")
        
        if local_path.exists():
            logger.debug(f"📁 Using local model: {local_path}")
            return str(local_path)
        else:
            logger.debug(f"🌐 Using Hugging Face model: {model_name}")
            return model_name

    # ==================== MEMORY MANAGEMENT ====================

    def _check_memory_availability(self, required_memory: float) -> bool:
        """Check if sufficient memory is available for model loading"""
        current_usage = self._calculate_current_memory_usage()
        available = self.max_memory_usage - current_usage
        
        logger.debug(f"💾 Memory check: {available:.1f}GB available, {required_memory:.1f}GB required")
        return available >= required_memory

    def _calculate_current_memory_usage(self) -> float:
        """Calculate current memory usage by loaded models"""
        total_usage = 0.0
        for model_key, info in self.model_info.items():
            if model_key in self.loaded_models:
                total_usage += info.memory_usage
        return total_usage

    async def _free_memory_for_model(self, required_memory: float) -> None:
        """Free memory by unloading least recently used models"""
        logger.info(f"🧹 Freeing memory for new model ({required_memory:.1f}GB required)")
        
        # Sort models by last used time (oldest first)
        sorted_models = sorted(
            self.model_info.items(),
            key=lambda x: x[1].last_used
        )
        
        freed_memory = 0.0
        for model_key, info in sorted_models:
            if freed_memory >= required_memory:
                break
                
            if model_key in self.loaded_models:
                await self._unload_model(model_key)
                freed_memory += info.memory_usage
                logger.info(f"   Unloaded {model_key} ({info.memory_usage:.1f}GB)")

    async def _unload_model(self, model_key: str) -> None:
        """Unload a specific model from memory with proper cleanup"""
        if model_key in self.loaded_models:
            model = self.loaded_models[model_key]
            
            try:
                # Proper cleanup for different model types
                if hasattr(model, 'model') and hasattr(model.model, 'cpu'):
                    # Move model to CPU first to free GPU memory
                    model.model.cpu()
                elif hasattr(model, 'cpu'):
                    model.cpu()
                
                # Clear model references
                if hasattr(model, '__del__'):
                    try:
                        model.__del__()
                    except:
                        pass  # Ignore deletion errors
                
                # Remove from our tracking
                del self.loaded_models[model_key]
                
                # Also remove from model_info to prevent memory leaks in metadata
                if model_key in self.model_info:
                    del self.model_info[model_key]
                
                # Clear from unified cache to prevent cache memory leaks
                try:
                    cache_key = CachePatterns.ai_model_instance(model_key, "latest")
                    await unified_cache_service.delete_ai_model_instance(cache_key)
                except Exception as e:
                    logger.debug(f"Cache cleanup error for {model_key}: {e}")
                
            except Exception as e:
                logger.warning(f"Error during model cleanup for {model_key}: {e}")
            
            finally:
                # Ensure GPU cache is cleared
                if self.has_gpu and torch.cuda.is_available():
                    try:
                        torch.cuda.empty_cache()
                        torch.cuda.synchronize()
                        # Force clear GPU memory for the specific device
                        torch.cuda.ipc_collect()
                    except Exception as e:
                        logger.debug(f"GPU cleanup error: {e}")
                
                # Aggressive garbage collection
                import gc
                gc.collect()
                gc.collect()  # Call twice for better cleanup
                
                logger.debug(f"🗑️ Fully unloaded model with cleanup: {model_key}")

    # ==================== MODEL LIFECYCLE MANAGEMENT ====================

    def _register_loaded_model(self, model_key: str, config: Dict[str, Any], model: Any) -> None:
        """Register a newly loaded model"""
        self.loaded_models[model_key] = model
        self.model_info[model_key] = ModelInfo(
            name=config["model_name"],
            model_type=config["model_type"],
            memory_usage=config["memory_estimate"],
            loaded_at=datetime.utcnow(),
            last_used=datetime.utcnow()
        )

    def _update_model_usage(self, model_key: str) -> None:
        """Update model usage statistics"""
        if model_key in self.model_info:
            info = self.model_info[model_key]
            info.last_used = datetime.utcnow()
            info.usage_count += 1

    # ==================== HARDWARE-AWARE MODEL SELECTION ====================

    def get_optimal_model_for_task(self, task: str, language: str = "en", 
                                  performance_priority: bool = False) -> Optional[str]:
        """
        Get optimal model for a task based on hardware and requirements
        
        Args:
            task: AI task type (emotion-analysis, sentiment-analysis, etc.)
            language: Target language
            performance_priority: Whether to prioritize performance over accuracy
            
        Returns:
            Optimal model key or None
        """
        candidates = []
        
        # Find suitable models for task and language
        for model_key, config in self.model_configs.items():
            if config["task"] == task and language in config["languages"]:
                candidates.append((model_key, config))
        
        if not candidates:
            return None
        
        # Select best model based on criteria
        if performance_priority:
            # Prioritize speed: smallest memory footprint
            return min(candidates, key=lambda x: x[1]["memory_estimate"])[0]
        else:
            # Prioritize accuracy: highest priority models that fit in memory
            suitable = [
                (key, config) for key, config in candidates
                if config["memory_estimate"] <= self.max_memory_usage
            ]
            
            if suitable:
                priority_map = {"high": 3, "medium": 2, "low": 1}
                return max(suitable, key=lambda x: priority_map.get(x[1]["priority"], 0))[0]
            else:
                # Fallback to smallest model that fits
                return min(candidates, key=lambda x: x[1]["memory_estimate"])[0]

    # ==================== MONITORING AND DIAGNOSTICS ====================

    def get_model_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all AI models"""
        status = {
            "loaded_models": len(self.loaded_models),
            "total_memory_usage": self._calculate_current_memory_usage(),
            "max_memory_usage": self.max_memory_usage,
            "gpu_available": self.has_gpu,
            "gpu_memory": self.gpu_memory,
            "models": {}
        }
        
        for model_key, info in self.model_info.items():
            status["models"][model_key] = {
                "loaded": model_key in self.loaded_models,
                "memory_usage": info.memory_usage,
                "usage_count": info.usage_count,
                "last_used": info.last_used.isoformat(),
                "loaded_at": info.loaded_at.isoformat()
            }
        
        return status

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on AI model system"""
        health = {
            "status": "healthy",
            "issues": [],
            "recommendations": []
        }
        
        # Check memory usage
        memory_usage_pct = (self._calculate_current_memory_usage() / self.max_memory_usage) * 100
        if memory_usage_pct > 80:
            health["issues"].append(f"High memory usage: {memory_usage_pct:.1f}%")
            health["recommendations"].append("Consider unloading unused models")
        
        # Check GPU availability
        if self.has_gpu:
            try:
                gpu_memory_used = torch.cuda.memory_allocated() / (1024**3)
                gpu_memory_pct = (gpu_memory_used / self.gpu_memory) * 100
                if gpu_memory_pct > 80:
                    health["issues"].append(f"High GPU memory usage: {gpu_memory_pct:.1f}%")
                    health["recommendations"].append("Clear GPU cache or reduce model size")
            except Exception as e:
                health["issues"].append(f"GPU monitoring error: {e}")
        
        # Set overall status
        if health["issues"]:
            health["status"] = "warning" if len(health["issues"]) < 3 else "critical"
        
        return health

    # ==================== CACHE INTEGRATION ====================

    async def preload_common_models(self) -> None:
        """Preload commonly used models for faster response times"""
        common_models = [
            "emotion_classifier",
            "sentiment_classifier", 
            "sentence_embeddings"
        ]
        
        logger.info("🚀 Preloading common AI models...")
        
        for model_key in common_models:
            try:
                model = await self.get_model(model_key)
                if model:
                    logger.info(f"   ✅ Preloaded: {model_key}")
                else:
                    logger.warning(f"   ❌ Failed to preload: {model_key}")
            except Exception as e:
                logger.error(f"   ❌ Error preloading {model_key}: {e}")

    async def cleanup_old_models(self, max_age_hours: int = 6) -> None:
        """Clean up models that haven't been used recently"""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        models_to_remove = []
        
        for model_key, info in self.model_info.items():
            if info.last_used < cutoff and model_key in self.loaded_models:
                models_to_remove.append(model_key)
        
        if models_to_remove:
            logger.info(f"🧹 Cleaning up {len(models_to_remove)} old models")
            for model_key in models_to_remove:
                await self._unload_model(model_key)
                
    async def cleanup_all_models(self) -> None:
        """Clean up all loaded models (for shutdown or emergency cleanup)"""
        logger.info(f"🧹 Emergency cleanup: unloading all {len(self.loaded_models)} models")
        
        # Get all model keys to avoid modifying dict during iteration
        model_keys = list(self.loaded_models.keys())
        
        for model_key in model_keys:
            try:
                await self._unload_model(model_key)
            except Exception as e:
                logger.error(f"Error unloading model {model_key} during cleanup: {e}")
        
        # Final cleanup
        self.loaded_models.clear()
        self.model_info.clear()
        
        # Force final garbage collection
        import gc
        gc.collect()
        gc.collect()
        
        if self.has_gpu and torch.cuda.is_available():
            try:
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                torch.cuda.ipc_collect()
            except Exception as e:
                logger.debug(f"Final GPU cleanup error: {e}")
        
        logger.info("✅ All models cleaned up successfully")
                
    def __del__(self):
        """Destructor to ensure cleanup on garbage collection"""
        try:
            # Attempt synchronous cleanup as destructor can't be async
            if hasattr(self, 'loaded_models') and self.loaded_models:
                logger.warning("🚨 AIModelManager destroyed with models still loaded - forcing cleanup")
                
                for model_key, model in list(self.loaded_models.items()):
                    try:
                        if hasattr(model, 'cpu'):
                            model.cpu()
                        del model
                    except:
                        pass
                
                self.loaded_models.clear()
                
                if hasattr(self, 'model_info'):
                    self.model_info.clear()
                
                # Force garbage collection
                import gc
                gc.collect()
                
                if self.has_gpu and torch.cuda.is_available():
                    try:
                        torch.cuda.empty_cache()
                    except:
                        pass
        except Exception as e:
            # Ensure destructor doesn't raise exceptions
            pass

# ==================== SERVICE INSTANCE ====================

# Global AI Model Manager instance for use across the application
ai_model_manager = AIModelManager()

# Automatic cleanup scheduler
import asyncio
from typing import Optional

class ModelCleanupScheduler:
    """Automatic model cleanup scheduler to prevent memory leaks"""
    
    def __init__(self, model_manager: AIModelManager, cleanup_interval_minutes: int = 30):
        self.model_manager = model_manager
        self.cleanup_interval = cleanup_interval_minutes * 60  # Convert to seconds
        self._cleanup_task: Optional[asyncio.Task] = None
        self._stop_cleanup = False
        
    async def start_scheduled_cleanup(self):
        """Start the automatic cleanup scheduler"""
        if self._cleanup_task and not self._cleanup_task.done():
            logger.warning("Cleanup scheduler already running")
            return
            
        self._stop_cleanup = False
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"🔄 Started AI model cleanup scheduler (every {self.cleanup_interval//60} minutes)")
    
    async def stop_scheduled_cleanup(self):
        """Stop the automatic cleanup scheduler"""
        self._stop_cleanup = True
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("⏹️ Stopped AI model cleanup scheduler")
    
    async def _cleanup_loop(self):
        """Main cleanup loop"""
        try:
            while not self._stop_cleanup:
                await asyncio.sleep(self.cleanup_interval)
                
                if self._stop_cleanup:
                    break
                    
                try:
                    await self.model_manager.cleanup_old_models(max_age_hours=2)
                    logger.debug("🧹 Scheduled AI model cleanup completed")
                except Exception as e:
                    logger.error(f"❌ Scheduled cleanup error: {e}")
                    
        except asyncio.CancelledError:
            logger.debug("Cleanup scheduler cancelled")
            
# Global cleanup scheduler instance
model_cleanup_scheduler = ModelCleanupScheduler(ai_model_manager)

# Integration with Phase 2 Service Registry
def register_ai_model_manager():
    """Register AI Model Manager in Phase 2 service registry"""
    try:
        from app.core.service_interfaces import service_registry
        service_registry.register_service("ai_model_manager", ai_model_manager)
        logger.info("✅ AI Model Manager registered in service registry")
    except Exception as e:
        logger.error(f"❌ Failed to register AI Model Manager: {e}")

# Auto-register when module is imported
register_ai_model_manager()
