# AI Model Manager Service - Centralized AI Model Management

"""
AI Model Manager Service for Journaling AI
Provides centralized AI model loading, caching, and memory management
Integrates with Phase 2 unified cache patterns and service registry
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
        
        # Hardware detection
        self.has_gpu = torch.cuda.is_available()
        self.gpu_memory = self._get_gpu_memory() if self.has_gpu else 0
        
        # Model configuration
        self.model_configs = self._initialize_model_configs()
        
        logger.info(f"🤖 AI Model Manager initialized")
        logger.info(f"   GPU Available: {self.has_gpu}")
        if self.has_gpu:
            logger.info(f"   GPU Memory: {self.gpu_memory:.1f} GB")
        logger.info(f"   Max Memory Usage: {self.max_memory_usage:.1f} GB")
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

    def _initialize_model_configs(self) -> Dict[str, Dict[str, Any]]:
        """Initialize configuration for available AI models"""
        return {
            # Emotion Analysis Models
            "emotion_classifier": {
                "model_name": "j-hartmann/emotion-english-distilroberta-base",
                "model_type": "text-classification",
                "task": "emotion-analysis",
                "languages": ["en"],
                "memory_estimate": 0.5,  # GB
                "priority": "high",
                "fallback": "sentiment_classifier"
            },
            
            # Sentiment Analysis Models
            "sentiment_classifier": {
                "model_name": "cardiffnlp/twitter-roberta-base-sentiment-latest",
                "model_type": "text-classification", 
                "task": "sentiment-analysis",
                "languages": ["en"],
                "memory_estimate": 0.6,  # GB
                "priority": "high",
                "fallback": "multilingual_sentiment"
            },
            
            "multilingual_sentiment": {
                "model_name": "cardiffnlp/twitter-xlm-roberta-base-sentiment",
                "model_type": "text-classification",
                "task": "sentiment-analysis", 
                "languages": ["en", "de", "es", "fr"],
                "memory_estimate": 1.2,  # GB
                "priority": "medium",
                "fallback": "distilbert_sentiment"
            },
            
            "distilbert_sentiment": {
                "model_name": "distilbert-base-uncased-finetuned-sst-2-english",
                "model_type": "text-classification",
                "task": "sentiment-analysis",
                "languages": ["en"],
                "memory_estimate": 0.3,  # GB
                "priority": "low",
                "fallback": None
            },
            
            # Text Generation Models
            "text_generator": {
                "model_name": "facebook/bart-base",
                "model_type": "text2text-generation",
                "task": "text-generation",
                "languages": ["en"],
                "memory_estimate": 0.8,  # GB
                "priority": "medium",
                "fallback": None
            },
            
            "large_text_generator": {
                "model_name": "facebook/bart-large",
                "model_type": "text2text-generation", 
                "task": "text-generation",
                "languages": ["en"],
                "memory_estimate": 1.6,  # GB
                "priority": "low",
                "fallback": "text_generator"
            },
            
            # Zero-shot Classification
            "zero_shot_classifier": {
                "model_name": "facebook/bart-large-mnli",
                "model_type": "zero-shot-classification",
                "task": "zero-shot-classification",
                "languages": ["en"],
                "memory_estimate": 1.6,  # GB
                "priority": "medium",
                "fallback": None
            },
            
            # Embedding Models
            "sentence_embeddings": {
                "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                "model_type": "sentence-transformers",
                "task": "embeddings",
                "languages": ["en"],
                "memory_estimate": 0.4,  # GB
                "priority": "high",
                "fallback": None
            },
            
            "large_embeddings": {
                "model_name": "sentence-transformers/all-mpnet-base-v2", 
                "model_type": "sentence-transformers",
                "task": "embeddings",
                "languages": ["en"],
                "memory_estimate": 0.8,  # GB
                "priority": "medium",
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
            # Check if model is already loaded
            if model_key in self.loaded_models:
                self._update_model_usage(model_key)
                logger.debug(f"📖 Using cached model: {model_key}")
                return self.loaded_models[model_key]
            
            # Check cache using Phase 2 patterns
            cache_key = CachePatterns.ai_model_instance(model_key, "latest")
            cached_model = await unified_cache_service.get_ai_model_instance(cache_key)
            
            if cached_model:
                logger.debug(f"🗃️ Model retrieved from cache: {model_key}")
                self.loaded_models[model_key] = cached_model
                self._update_model_usage(model_key)
                return cached_model
            
            # Load model with memory management
            model = await self._load_model_with_fallback(model_key, **kwargs)
            
            if model:
                # Cache model using Phase 2 patterns
                await unified_cache_service.set_ai_model_instance(
                    model, cache_key, ttl=21600  # 6 hours
                )
                logger.info(f"✅ Model loaded and cached: {model_key}")
            
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
        
        # Prepare model path
        model_path = self._get_model_path(model_name)
        
        try:
            if model_type == "text-classification":
                return pipeline(
                    "text-classification",
                    model=model_path,
                    tokenizer=model_path,
                    return_all_scores=True,
                    **kwargs
                )
            
            elif model_type == "text2text-generation":
                return pipeline(
                    "text2text-generation",
                    model=model_path,
                    tokenizer=model_path,
                    **kwargs
                )
            
            elif model_type == "zero-shot-classification":
                return pipeline(
                    "zero-shot-classification",
                    model=model_path,
                    tokenizer=model_path,
                    **kwargs
                )
            
            elif model_type == "sentence-transformers":
                # Special handling for sentence transformers
                from sentence_transformers import SentenceTransformer
                return SentenceTransformer(str(model_path))
            
            else:
                logger.error(f"Unsupported model type: {model_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
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
        """Unload a specific model from memory"""
        if model_key in self.loaded_models:
            del self.loaded_models[model_key]
            
            # Clear GPU cache if available
            if self.has_gpu:
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            
            # Force garbage collection
            gc.collect()
            
            logger.debug(f"🗑️ Unloaded model: {model_key}")

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

# ==================== SERVICE INSTANCE ====================

# Global AI Model Manager instance for use across the application
ai_model_manager = AIModelManager()

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
