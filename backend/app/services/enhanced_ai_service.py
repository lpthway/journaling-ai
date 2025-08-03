"""
Enhanced AI Service for Journaling AI
Provides intelligent features like smart prompts, auto-tagging, style analysis, and mood prediction
"""

import logging
import re
import gc
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import statistics
import asyncio
from pathlib import Path

# NLP and ML libraries
import spacy
from transformers import pipeline, AutoTokenizer, AutoModel
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Text processing
from textstat import flesch_reading_ease, flesch_kincaid_grade, lexicon_count
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Internal imports
from app.models.entry import Entry, MoodType
from app.services.sentiment_service import MultilingualSentimentService
from app.services.database_service import db_service

# Import hardware-adaptive AI system (temporarily disabled)
# from app.services.hardware_adaptive_ai import get_adaptive_ai, HardwareAdaptiveAI
# from app.core.gpu_memory_manager import get_gpu_memory_manager

logger = logging.getLogger(__name__)

class EnhancedAIService:
    """
    Enhanced AI service providing intelligent features for journaling with GPU memory management
    """
    
    def __init__(self):
        self.sentiment_service = MultilingualSentimentService()
        self.nlp = None
        self.tag_classifier = None
        self.embeddings_model = None
        self.emotion_classifier = None
        self.multilingual_classifier = None
        self.backup_classifier = None
        
        # Initialize hardware-adaptive AI system (temporarily disabled)
        # self.adaptive_ai: Optional[HardwareAdaptiveAI] = None
        # self.gpu_memory_manager = get_gpu_memory_manager()
        self.adaptive_ai = None
        self.gpu_memory_manager = None
        
        # Initialize TfidfVectorizer with memory-safe settings
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000, 
            stop_words='english',
            # Disable parallel processing to prevent memory leaks
            dtype=np.float32  # Use float32 instead of float64 to save memory
        )
        self.lemmatizer = WordNetLemmatizer()
        
        # Model loading state
        self._models_initialized = False
        self._use_gpu = torch.cuda.is_available()
        
        # Cached data for performance
        self._user_patterns_cache = {}
        self._cache_timestamp = None
        
        # Model loading throttle to prevent Hugging Face rate limiting
        self._last_model_load_time = 0
        self._model_load_delay = 2.0  # Minimum seconds between model loads
        
        # Local model cache directory
        self._cache_dir = Path(__file__).parent.parent.parent / "models"
        self._cache_dir.mkdir(exist_ok=True)
        
    def _ensure_model_cached(self, model_name: str) -> str:
        """Ensure model is downloaded and cached locally"""
        import os
        from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification
        
        # Create model-specific cache directory
        model_cache_dir = self._cache_dir / model_name.replace("/", "--")
        
        if model_cache_dir.exists() and any(model_cache_dir.iterdir()):
            logger.info(f"📦 Using cached model: {model_name}")
            return str(model_cache_dir)
        
        logger.info(f"⬇️ Downloading and caching model: {model_name}")
        
        try:
            # Download tokenizer and model to cache
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=str(model_cache_dir)
            )
            
            # Try sequence classification model first, then fall back to base model
            try:
                model = AutoModelForSequenceClassification.from_pretrained(
                    model_name,
                    cache_dir=str(model_cache_dir)
                )
            except:
                model = AutoModel.from_pretrained(
                    model_name,
                    cache_dir=str(model_cache_dir)
                )
            
            logger.info(f"✅ Model cached successfully: {model_name}")
            return str(model_cache_dir)
            
        except Exception as e:
            logger.error(f"❌ Failed to cache model {model_name}: {e}")
            # If caching fails, return original model name for online loading
            return model_name
        
    async def initialize(self):
        """Initialize the AI service and load models with hardware-adaptive AI"""
        if self._models_initialized:
            return
            
        logger.info("🚀 Initializing Enhanced AI Service with Hardware-Adaptive AI...")
        
        # Initialize hardware-adaptive AI system (temporarily disabled)
        try:
            # self.adaptive_ai = await get_adaptive_ai()
            # logger.info("✅ Hardware-Adaptive AI initialized successfully")
            logger.info("⚠️ Hardware-Adaptive AI temporarily disabled")
            self.adaptive_ai = None
        except Exception as e:
            logger.warning(f"Hardware-Adaptive AI initialization failed: {e}")
            self.adaptive_ai = None
        
        # Initialize traditional models as fallback
        self._initialize_models()
        self._models_initialized = True
        logger.info("✅ Enhanced AI Service initialized")
        
    async def cleanup(self):
        """Clean up resources and clear GPU memory"""
        logger.info("🧹 Cleaning up Enhanced AI Service...")
        
        # Clear all model references
        self.tag_classifier = None
        self.embeddings_model = None
        self.emotion_classifier = None
        self.multilingual_classifier = None
        self.backup_classifier = None
        
        # Force garbage collection
        import gc
        gc.collect()
        
        # Clear GPU memory aggressively
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            # Force clear all cached memory
            torch.cuda.reset_peak_memory_stats()
        
        # GPU memory cleanup (temporarily disabled)
        # # await self.gpu_memory_manager.cleanup_manager.emergency_gpu_cleanup()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        
        # Log memory status
        if torch.cuda.is_available():
            free_memory = torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)
            free_mb = free_memory / 1024 / 1024
            logger.info(f"💾 GPU Memory freed: {free_mb:.1f}MB available")
        
        logger.info("✅ Enhanced AI Service cleaned up")
        
    def _safe_load_model(self, model_name: str, task: str, max_retries: int = 2, config: Dict[str, Any] = None) -> Optional[Any]:
        """Safely load a model with GPU memory management and hardware-adaptive optimizations"""
        
        if config is None:
            config = {}
        
        cpu_optimized = config.get('cpu_optimized', False)
        memory_estimate = config.get('memory_estimate_mb', 500)
        
        for attempt in range(max_retries + 1):
            try:
                # Clear memory before attempting to load
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()
                
                # Add delay for rate limiting (especially on retries)
                if attempt > 0:
                    import time
                    delay = min(2 ** attempt, 30)  # Exponential backoff, max 30s
                    logger.info(f"⏳ Rate limiting: waiting {delay}s before retry {attempt}")
                    time.sleep(delay)
                
                # Determine device based on hardware tier and memory pressure
                if cpu_optimized or not self._use_gpu:
                    device = -1  # CPU
                    device_name = "cpu"
                    logger.info(f"🖥️ Loading {model_name} on CPU (optimized: {cpu_optimized})")
                elif self._use_gpu and torch.cuda.is_available():
                    total_memory = torch.cuda.get_device_properties(0).total_memory
                    allocated_memory = torch.cuda.memory_allocated(0)
                    available_mb = (total_memory - allocated_memory) / 1024 / 1024
                    
                    if available_mb < memory_estimate * 1.2:  # Need 20% buffer
                        logger.warning(f"⚠️ Low GPU memory: {available_mb:.1f}MB available, need {memory_estimate}MB, using CPU")
                        device = -1
                        device_name = "cpu"
                    else:
                        device = 0
                        device_name = "cuda:0"
                else:
                    device = -1
                    device_name = "cpu"
                
                logger.info(f"Device set to use {device_name}")
                
                # Ensure model is cached locally to avoid rate limiting
                cached_model_path = self._ensure_model_cached(model_name)
                
                # Configure model loading parameters to avoid conflicts
                model_kwargs = {
                    'model': cached_model_path,
                    'device': device,
                    'local_files_only': cached_model_path != model_name,  # Use local files if cached
                }
                
                # Add appropriate dtype based on device
                if device >= 0:  # GPU
                    model_kwargs['torch_dtype'] = torch.float16
                else:  # CPU
                    model_kwargs['torch_dtype'] = torch.float32
                
                # Load model with specific device setting (avoid device_map conflicts)
                model = pipeline(task, **model_kwargs)
                
                logger.info(f"✅ Loaded {model_name} on {device_name}")
                return model
                
            except RuntimeError as e:
                if "out of memory" in str(e).lower() and attempt < max_retries:
                    logger.warning(f"GPU memory error loading {model_name}, clearing cache and retrying...")
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        torch.cuda.synchronize()
                    self._use_gpu = False  # Disable GPU for subsequent attempts
                    continue
                else:
                    logger.error(f"Could not load {model_name}: {e}")
                    return None
                    
            except Exception as e:
                error_msg = str(e)
                # Handle Hugging Face rate limiting
                if "429" in error_msg or "rate limit" in error_msg.lower() or "too many requests" in error_msg.lower():
                    if attempt < max_retries:
                        delay = min(10 * (2 ** attempt), 60)  # Longer delays for rate limits
                        logger.warning(f"🚫 Rate limited by Hugging Face, waiting {delay}s before retry {attempt + 1}")
                        import time
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"❌ Rate limited by Hugging Face, max retries exceeded for {model_name}")
                        return None
                elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                    if attempt < max_retries:
                        logger.warning(f"🌐 Network error loading {model_name}, retrying...")
                        continue
                    else:
                        logger.error(f"❌ Network error loading {model_name}: {e}")
                        return None
                else:
                    logger.error(f"❌ Unexpected error loading {model_name}: {e}")
                    return None
                
        return None

    def _initialize_models(self):
        """Initialize lightweight components only - models loaded on demand"""
        try:
            logger.info("🔧 Initializing Enhanced AI Service...")
            
            # Check if models are cached locally
            cached_models = list(self._cache_dir.glob("*"))
            if cached_models:
                logger.info(f"📦 Found {len(cached_models)} cached models, will use offline mode")
            else:
                logger.info("⚠️ No cached models found, will download on first use")
                logger.info("💡 Run 'python download_models.py' to pre-download all models")
            
            # Load spaCy model for advanced NLP (CPU only, lightweight)
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("✅ Loaded spaCy English model")
            except OSError:
                logger.warning("❌ spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
                
            # Download required NLTK data (do this first, lightweight)
            try:
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
                nltk.download('wordnet', quiet=True)
                logger.info("✅ NLTK data ready")
            except Exception as e:
                logger.warning(f"NLTK setup issue: {e}")
            
            # Initialize hardware-adaptive model configurations
            self.model_configs = self._get_hardware_adaptive_model_configs()
            
            logger.info(f"📊 Model configs initialized for hardware tier: {self._get_current_hardware_tier()}")
            
            # Clear any existing models
            self.tag_classifier = None
            self.embeddings_model = None
            self.emotion_classifier = None
            self.multilingual_classifier = None
            self.backup_classifier = None
            
            # Clear memory 
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            
            logger.info("✅ Enhanced AI Service ready (models will load on demand)")
            
        except Exception as e:
            logger.error(f"Error initializing AI service: {e}")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            
    def _load_model_on_demand(self, model_key: str, max_retries: int = 2) -> Optional[Any]:
        """Load a specific model on demand with hardware-adaptive selection"""
        
        # Throttle model loading to prevent Hugging Face rate limiting
        import time
        current_time = time.time()
        time_since_last_load = current_time - self._last_model_load_time
        
        if time_since_last_load < self._model_load_delay:
            wait_time = self._model_load_delay - time_since_last_load
            logger.info(f"⏳ Throttling model load: waiting {wait_time:.1f}s to prevent rate limiting")
            time.sleep(wait_time)
        
        self._last_model_load_time = time.time()
        
        # Ensure service is initialized
        if not hasattr(self, 'model_configs') or not self.model_configs:
            logger.warning("Model configs not initialized, refreshing hardware-adaptive configs")
            self.model_configs = self._get_hardware_adaptive_model_configs()
            
        if model_key not in self.model_configs:
            logger.warning(f"Model {model_key} not available in current hardware tier: {self._get_current_hardware_tier()}")
            return None
            
        # Check if model is already loaded
        current_model = getattr(self, model_key, None)
        if current_model is not None:
            logger.info(f"♻️ Reusing already loaded model: {model_key}")
            return current_model
            
        config = self.model_configs[model_key]
        model_name = config['model_name']
        task = config['task']
        memory_estimate = config.get('memory_estimate_mb', 500)
        
        logger.info(f"🔄 Loading {model_key}: {model_name} (estimated: {memory_estimate}MB)")
        
        # Check memory availability before loading (temporarily disabled)
        # if self.gpu_memory_manager:
        #     try:
        #         memory_check = self.gpu_memory_manager.gpu_monitor.can_load_model(memory_estimate)
        #         if not memory_check.get('can_load', False):
        #             logger.warning(f"⚠️ Insufficient memory for {model_key}, trying CPU fallback")
        #             self._use_gpu = False
        #     except Exception as e:
        #         logger.warning(f"Memory check failed: {e}")
        
        # Simple fallback memory check
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated(0) / 1024 / 1024
            total = torch.cuda.get_device_properties(0).total_memory / 1024 / 1024
            available = total - allocated
            if available < memory_estimate * 1.2:
                logger.warning(f"⚠️ Low GPU memory: {available:.1f}MB available, need {memory_estimate}MB, using CPU")
                self._use_gpu = False
        
        # Free up space by unloading other models first
        self._unload_all_models_except(model_key)
        
        # Load the requested model with hardware optimization
        model = self._safe_load_model(model_name, task, max_retries, config)
        
        if model is not None:
            setattr(self, model_key, model)
            logger.info(f"✅ Loaded {model_key} on demand (tier: {config.get('accuracy_tier', 'unknown')})")
            
            # Log current memory usage
            if torch.cuda.is_available():
                allocated = torch.cuda.memory_allocated(0) / 1024 / 1024
                logger.info(f"💾 GPU Memory in use: {allocated:.1f}MB")
        else:
            logger.error(f"❌ Failed to load {model_key}")
            
        return model
        
    def _unload_all_models_except(self, keep_model: str = None):
        """Unload all models except the specified one to free memory"""
        models_to_clear = ['tag_classifier', 'emotion_classifier', 'multilingual_classifier', 
                          'backup_classifier', 'embeddings_model']
        
        for model_name in models_to_clear:
            if model_name != keep_model:
                if hasattr(self, model_name):
                    setattr(self, model_name, None)
                    
        # Aggressive memory cleanup
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        
        if keep_model:
            logger.info(f"🗑️ Cleared all models except {keep_model}")
        else:
            logger.info("🗑️ Cleared all models")
    
    def _get_current_hardware_tier(self) -> str:
        """Get current hardware tier based on available hardware"""
        try:
            # If adaptive AI is available, use it
            if self.adaptive_ai and hasattr(self.adaptive_ai, 'feature_manager'):
                return self.adaptive_ai.feature_manager.current_tier
            
            # Otherwise, detect tier based on GPU memory
            if torch.cuda.is_available():
                total_vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                
                if total_vram_gb >= 10:  # 10GB+ VRAM = HIGH_END
                    return "HIGH_END"
                elif total_vram_gb >= 6:  # 6-10GB VRAM = INTERMEDIATE  
                    return "INTERMEDIATE"
                elif total_vram_gb >= 4:  # 4-6GB VRAM = BASIC
                    return "BASIC"
                else:  # <4GB VRAM = MINIMAL
                    return "MINIMAL"
            else:
                return "MINIMAL"  # CPU-only fallback
                
        except Exception as e:
            logger.warning(f"Hardware tier detection failed: {e}")
            return "BASIC"
    
    def _get_hardware_adaptive_model_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get model configurations based on current hardware tier and memory pressure"""
        tier = self._get_current_hardware_tier()
        
        # Get current GPU memory status (temporarily disabled)
        gpu_memory_info = {}
        # if self.gpu_memory_manager:
        #     try:
        #         gpu_memory_info = self.gpu_memory_manager.gpu_monitor.get_detailed_gpu_memory()
        #     except Exception:
        #         pass
        
        # Simple fallback memory info
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated(0) / 1024 / 1024
            total = torch.cuda.get_device_properties(0).total_memory / 1024 / 1024
            gpu_memory_info = {
                'available_for_models': total - allocated,
                'pressure_level': 'LOW' if (total - allocated) > 2000 else 'HIGH'
            }
        
        available_memory_mb = gpu_memory_info.get('available_for_models', 0)
        memory_pressure = gpu_memory_info.get('pressure_level', 'UNKNOWN')
        
        logger.info(f"🔧 Selecting models for tier: {tier}, available memory: {available_memory_mb}MB, pressure: {memory_pressure}")
        
        # Define model configurations by tier
        configs = {
            "HIGH_END": self._get_high_end_model_configs(),
            "INTERMEDIATE": self._get_intermediate_model_configs(), 
            "BASIC": self._get_basic_model_configs(),
            "MINIMAL": self._get_minimal_model_configs()
        }
        
        selected_config = configs.get(tier, configs["BASIC"])
        
        # Apply memory pressure adjustments
        if memory_pressure in ["CRITICAL", "HIGH"] or available_memory_mb < 1000:
            logger.warning(f"⚠️ Memory pressure {memory_pressure}, falling back to minimal models")
            selected_config = self._apply_memory_pressure_fallback(selected_config, available_memory_mb)
        
        return selected_config
    
    def _get_high_end_model_configs(self) -> Dict[str, Dict[str, Any]]:
        """High-end models for powerful hardware (8GB+ GPU memory)"""
        return {
            'emotion_classifier': {
                'model_name': "j-hartmann/emotion-english-distilroberta-base",
                'task': "text-classification", 
                'priority': 1,
                'memory_estimate_mb': 800,
                'accuracy_tier': "high"
            },
            'tag_classifier': {
                'model_name': "facebook/bart-large-mnli",
                'task': "zero-shot-classification",
                'priority': 2,
                'memory_estimate_mb': 1600,
                'accuracy_tier': "high"
            },
            'backup_classifier': {
                'model_name': "cardiffnlp/twitter-roberta-base-sentiment-latest",
                'task': "sentiment-analysis",
                'priority': 3, 
                'memory_estimate_mb': 500,
                'accuracy_tier': "high"
            },
            'embeddings_model': {
                'model_name': "sentence-transformers/all-mpnet-base-v2",
                'task': "feature-extraction",
                'priority': 4,
                'memory_estimate_mb': 400,
                'accuracy_tier': "high"
            },
            'multilingual_classifier': {
                'model_name': "cardiffnlp/twitter-xlm-roberta-base-sentiment",
                'task': "sentiment-analysis",
                'priority': 5,
                'memory_estimate_mb': 700,
                'accuracy_tier': "high"
            }
        }
    
    def _get_intermediate_model_configs(self) -> Dict[str, Dict[str, Any]]:
        """Intermediate models for moderate hardware (4-8GB GPU memory)"""
        return {
            'emotion_classifier': {
                'model_name': "j-hartmann/emotion-english-distilroberta-base", 
                'task': "text-classification",
                'priority': 1,
                'memory_estimate_mb': 800,
                'accuracy_tier': "medium"
            },
            'backup_classifier': {
                'model_name': "cardiffnlp/twitter-roberta-base-sentiment-latest",
                'task': "sentiment-analysis", 
                'priority': 2,
                'memory_estimate_mb': 500,
                'accuracy_tier': "medium"
            },
            'embeddings_model': {
                'model_name': "sentence-transformers/all-MiniLM-L6-v2",
                'task': "feature-extraction",
                'priority': 3,
                'memory_estimate_mb': 200,
                'accuracy_tier': "medium"
            },
            'tag_classifier': {
                'model_name': "facebook/bart-base",
                'task': "zero-shot-classification",
                'priority': 4,
                'memory_estimate_mb': 800,
                'accuracy_tier': "medium"
            }
        }
    
    def _get_basic_model_configs(self) -> Dict[str, Dict[str, Any]]:
        """Basic models for limited hardware (2-4GB GPU memory)"""
        return {
            'emotion_classifier': {
                'model_name': "j-hartmann/emotion-english-distilroberta-base",
                'task': "text-classification",
                'priority': 1,
                'memory_estimate_mb': 800,
                'accuracy_tier': "basic"
            },
            'backup_classifier': {
                'model_name': "cardiffnlp/twitter-roberta-base-sentiment-latest", 
                'task': "sentiment-analysis",
                'priority': 2,
                'memory_estimate_mb': 500,
                'accuracy_tier': "basic"
            },
            'embeddings_model': {
                'model_name': "sentence-transformers/all-MiniLM-L6-v2",
                'task': "feature-extraction", 
                'priority': 3,
                'memory_estimate_mb': 200,
                'accuracy_tier': "basic"
            },
            'tag_classifier': {
                'model_name': "facebook/bart-base",
                'task': "zero-shot-classification",
                'priority': 4,
                'memory_estimate_mb': 400,
                'accuracy_tier': "basic"
            }
        }
    
    def _get_minimal_model_configs(self) -> Dict[str, Dict[str, Any]]:
        """Minimal models for very limited hardware (<2GB GPU memory) or CPU-only"""
        return {
            'backup_classifier': {
                'model_name': "distilbert-base-uncased-finetuned-sst-2-english",
                'task': "sentiment-analysis",
                'priority': 1,
                'memory_estimate_mb': 250,
                'accuracy_tier': "minimal",
                'cpu_optimized': True
            },
            'embeddings_model': {
                'model_name': "sentence-transformers/all-MiniLM-L6-v2",
                'task': "feature-extraction",
                'priority': 2, 
                'memory_estimate_mb': 200,
                'accuracy_tier': "minimal",
                'cpu_optimized': True
            }
        }
    
    def _apply_memory_pressure_fallback(self, config: Dict[str, Dict[str, Any]], available_mb: int) -> Dict[str, Dict[str, Any]]:
        """Apply memory pressure fallbacks to model configuration"""
        if available_mb < 500:
            # Critical memory - only keep most essential model
            essential_models = ['backup_classifier']
            return {k: v for k, v in config.items() if k in essential_models}
        elif available_mb < 1500:
            # High pressure - remove heavy models
            lightweight_models = ['backup_classifier', 'embeddings_model']
            return {k: v for k, v in config.items() if k in lightweight_models and v.get('memory_estimate_mb', 0) < 600}
        else:
            # Moderate pressure - prefer lighter alternatives
            optimized_config = {}
            for model_key, model_config in config.items():
                if model_config.get('memory_estimate_mb', 0) > 1000:
                    # Replace heavy models with lighter alternatives
                    if model_key == 'tag_classifier':
                        optimized_config[model_key] = {
                            'model_name': "microsoft/DialoGPT-small",
                            'task': "text-generation",
                            'priority': model_config['priority'],
                            'memory_estimate_mb': 300,
                            'accuracy_tier': "fallback"
                        }
                    else:
                        optimized_config[model_key] = model_config
                else:
                    optimized_config[model_key] = model_config
            return optimized_config
    
    def refresh_hardware_adaptive_models(self):
        """Refresh model configurations when hardware tier changes"""
        old_tier = getattr(self, '_last_hardware_tier', None)
        current_tier = self._get_current_hardware_tier()
        
        if old_tier != current_tier:
            logger.info(f"🔄 Hardware tier changed: {old_tier} → {current_tier}, refreshing model configs")
            
            # Clear existing models
            self._unload_all_models_except()
            
            # Update model configurations
            self.model_configs = self._get_hardware_adaptive_model_configs()
            
            # Reset GPU usage flag for new tier
            self._use_gpu = torch.cuda.is_available() and current_tier not in ['MINIMAL']
            
            self._last_hardware_tier = current_tier
            logger.info(f"✅ Model configurations updated for tier: {current_tier}")
    
    def get_available_models_for_tier(self) -> Dict[str, str]:
        """Get list of available models for current hardware tier"""
        tier = self._get_current_hardware_tier()
        configs = self._get_hardware_adaptive_model_configs()
        
        return {
            model_key: {
                'model_name': config['model_name'],
                'accuracy_tier': config.get('accuracy_tier', 'unknown'),
                'memory_estimate_mb': config.get('memory_estimate_mb', 0),
                'cpu_optimized': config.get('cpu_optimized', False)
            }
            for model_key, config in configs.items()
        }
    
    # ==================== AUTOMATIC TAGGING SUGGESTIONS ====================
    
    async def suggest_tags(self, content: str, title: str, existing_tags: List[str] = None) -> List[Dict[str, Any]]:
        """
        Generate intelligent tag suggestions based on content analysis with hardware-adaptive AI
        
        Args:
            content: Entry content
            title: Entry title
            existing_tags: Currently applied tags
            
        Returns:
            List of suggested tags with confidence scores
        """
        try:
            # Ensure service is initialized
            if not self._models_initialized:
                await self.initialize()
                
            suggestions = []
            text = f"{title} {content}".strip()
            
            logger.info(f"🏷️ Generating tags for text: {text[:100]}...")
            
            # Try hardware-adaptive AI first
            if self.adaptive_ai:
                try:
                    result = await self.adaptive_ai.analyze_text(text, "topic")
                    if result["success"]:
                        # Convert topic result to tag format
                        topic_result = result["result"]
                        if isinstance(topic_result, dict) and 'topics' in topic_result:
                            adaptive_tags = []
                            for topic in topic_result['topics'][:5]:  # Top 5 topics
                                adaptive_tags.append({
                                    'tag': topic.lower().replace(' ', '_'),
                                    'confidence': result["confidence"],
                                    'source': f"adaptive_ai_{result['method_used']}",
                                    'reasoning': f"Hardware-adaptive AI topic analysis"
                                })
                            suggestions.extend(adaptive_tags)
                            logger.info(f"🤖 Adaptive AI tags: {len(adaptive_tags)} found")
                except Exception as e:
                    logger.warning(f"Hardware-adaptive AI tag suggestion failed: {e}")
            
            # Method 1: NLP-based entity and keyword extraction (fallback)
            nlp_tags = await self._extract_nlp_tags(text)
            suggestions.extend(nlp_tags)
            logger.info(f"🔤 NLP tags: {len(nlp_tags)} found")
            
            # Method 2: Zero-shot classification with predefined categories
            category_tags = await self._classify_content_categories(text)
            suggestions.extend(category_tags)
            logger.info(f"📂 Category tags: {len(category_tags)} found - {[t.get('tag') for t in category_tags]}")
            
            # Method 3: Historical pattern matching
            pattern_tags = await self._suggest_from_patterns(text, existing_tags or [])
            suggestions.extend(pattern_tags)
            logger.info(f"📊 Pattern tags: {len(pattern_tags)} found")
            
            # Method 4: Emotion and sentiment-based tags
            emotion_tags = await self._extract_emotion_tags(text)
            suggestions.extend(emotion_tags)
            logger.info(f"😊 Emotion tags: {len(emotion_tags)} found")
            
            logger.info(f"🔍 Total suggestions before ranking: {len(suggestions)}")
            
            # Deduplicate and rank suggestions
            ranked_suggestions = self._rank_and_deduplicate_tags(suggestions, existing_tags or [])
            
            logger.info(f"✅ Final ranked suggestions: {len(ranked_suggestions)} tags")
            
            return ranked_suggestions[:10]  # Return top 10 suggestions
            
        except Exception as e:
            logger.error(f"Error in tag suggestion: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
        finally:
            # Always cleanup after tag suggestions to prevent memory leaks
            self._unload_all_models_except()
            # await self.gpu_memory_manager.cleanup_manager.emergency_gpu_cleanup()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
    
    async def _extract_nlp_tags(self, text: str) -> List[Dict[str, Any]]:
        """Extract tags using NLP techniques"""
        tags = []
        
        if not self.nlp:
            return tags
            
        try:
            doc = self.nlp(text)
            
            # Extract named entities
            for ent in doc.ents:
                if ent.label_ in ['PERSON', 'ORG', 'WORK_OF_ART', 'EVENT', 'PRODUCT']:
                    tags.append({
                        'tag': ent.text.lower(),
                        'confidence': 0.8,
                        'source': 'nlp_entity',
                        'category': ent.label_
                    })
            
            # Extract key noun phrases
            for chunk in doc.noun_chunks:
                if len(chunk.text.split()) <= 2 and len(chunk.text) > 2:
                    tags.append({
                        'tag': chunk.text.lower(),
                        'confidence': 0.6,
                        'source': 'nlp_phrase',
                        'category': 'concept'
                    })
                    
        except Exception as e:
            logger.error(f"NLP tag extraction error: {e}")
            
        return tags
    
    async def _classify_content_categories(self, text: str) -> List[Dict[str, Any]]:
        """Classify content into predefined categories using on-demand model loading"""
        tags = []
        
        # Try zero-shot classification with on-demand loading first
        tag_classifier = self._load_model_on_demand('tag_classifier')
        if tag_classifier:
            try:
                # Define predefined categories for classification
                candidate_labels = [
                    'work and career', 'health and fitness', 'relationships and family',
                    'stress and anxiety', 'happiness and joy', 'achievement and success',
                    'learning and education', 'travel and adventure', 'creativity and hobbies',
                    'food and cooking', 'technology', 'nature and outdoors'
                ]
                
                logger.info(f"🎯 Using zero-shot classification for: {text[:50]}...")
                result = tag_classifier(text, candidate_labels, multi_label=True)
                
                # Process results
                if isinstance(result, dict):
                    labels = result.get('labels', [])
                    scores = result.get('scores', [])
                    
                    for label, score in zip(labels[:5], scores[:5]):  # Top 5 predictions
                        if score > 0.3:  # Confidence threshold
                            # Convert label to tag format
                            tag_name = label.lower().replace(' and ', '_').replace(' ', '_')
                            tags.append({
                                'tag': tag_name,
                                'confidence': score,
                                'source': 'zero_shot_classification',
                                'category': 'topic'
                            })
                
                logger.info(f"✅ Zero-shot classification found {len(tags)} tags")
                
            except Exception as e:
                logger.warning(f"Zero-shot classification failed: {e}")
                # Clear the model if it failed
                self.tag_classifier = None
        
        # Fallback to keyword matching if zero-shot fails or unavailable
        if not tags:
            logger.info("🔄 Falling back to keyword-based classification")
            fallback_categories = {
                'work': ['work', 'job', 'career', 'office', 'meeting', 'project', 'report', 'productive', 'schedule', 'deadline'],
                'health': ['health', 'doctor', 'exercise', 'fitness', 'wellness', 'workout', 'gym', 'training'],
                'relationships': ['relationship', 'friend', 'family', 'love', 'partner'],
                'stress': ['stress', 'stressed', 'pressure', 'overwhelmed', 'busy'],
                'happiness': ['happy', 'joy', 'excited', 'great', 'amazing', 'wonderful'],
                'achievement': ['accomplished', 'achievement', 'success', 'finished', 'completed', 'proud', 'strong'],
                'fitness': ['workout', 'exercise', 'gym', 'training', 'fitness', 'strong', 'physical']
            }
            
            text_lower = text.lower()
            for category, keywords in fallback_categories.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        tags.append({
                            'tag': category,
                            'confidence': 0.6,
                            'source': 'keyword_fallback',
                            'category': 'topic'
                        })
                        break
                        
        return tags
    
    async def _suggest_from_patterns(self, text: str, existing_tags: List[str]) -> List[Dict[str, Any]]:
        """Suggest tags based on historical patterns"""
        tags = []
        
        try:
            # Get user's historical entries
            entries = await db_service.get_entries(limit=100)
            
            if not entries:
                return tags
                
            # Find similar entries and their tags
            similar_entries = self._find_similar_entries(text, entries)
            
            # Collect tags from similar entries
            similar_tags = []
            for entry, similarity in similar_entries[:5]:  # Top 5 similar entries
                for tag in entry.tags:
                    if tag not in existing_tags:
                        similar_tags.append((tag, similarity))
            
            # Count and rank tags
            tag_counts = Counter([tag for tag, _ in similar_tags])
            
            for tag, count in tag_counts.most_common(5):
                avg_similarity = statistics.mean([sim for t, sim in similar_tags if t == tag])
                tags.append({
                    'tag': tag,
                    'confidence': min(avg_similarity * count / 5, 0.9),
                    'source': 'pattern_matching',
                    'category': 'historical'
                })
                
        except Exception as e:
            logger.error(f"Pattern matching error: {e}")
            
        return tags
    
    async def _extract_emotion_tags(self, text: str) -> List[Dict[str, Any]]:
        """Extract emotion-based tags from content"""
        tags = []
        
        try:
            # Get sentiment and mood analysis
            mood, sentiment_score = self.sentiment_service.analyze_sentiment(text)
            
            # Add mood-based tags
            if mood:
                mood_tag = mood.value.replace('_', ' ')
                tags.append({
                    'tag': mood_tag,
                    'confidence': abs(sentiment_score),
                    'source': 'emotion_analysis',
                    'category': 'mood'
                })
            
            # Detect specific emotions in text
            emotion_keywords = {
                'grateful': ['grateful', 'thankful', 'blessed', 'appreciate'],
                'excited': ['excited', 'thrilled', 'enthusiastic', 'eager'],
                'worried': ['worried', 'concerned', 'anxious', 'nervous'],
                'proud': ['proud', 'accomplished', 'achieved', 'success'],
                'frustrated': ['frustrated', 'annoyed', 'irritated', 'upset'],
                'peaceful': ['peaceful', 'calm', 'serene', 'relaxed'],
                'motivated': ['motivated', 'inspired', 'determined', 'driven']
            }
            
            text_lower = text.lower()
            for emotion, keywords in emotion_keywords.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        tags.append({
                            'tag': emotion,
                            'confidence': 0.7,
                            'source': 'emotion_keywords',
                            'category': 'emotion'
                        })
                        break
                        
        except Exception as e:
            logger.error(f"Emotion tag extraction error: {e}")
            
        return tags
    
    def _rank_and_deduplicate_tags(self, suggestions: List[Dict[str, Any]], existing_tags: List[str]) -> List[Dict[str, Any]]:
        """Rank and deduplicate tag suggestions"""
        # Group by tag name and combine scores
        tag_groups = defaultdict(list)
        for suggestion in suggestions:
            tag_name = suggestion.get('tag', '').lower().strip()
            if tag_name and tag_name not in [t.lower() for t in existing_tags]:
                tag_groups[tag_name].append(suggestion)
        
        # Combine and rank
        final_suggestions = []
        for tag_name, group in tag_groups.items():
            # Calculate combined confidence
            combined_confidence = max([s.get('confidence', 0.0) for s in group])
            # Boost confidence if suggested by multiple sources
            if len(group) > 1:
                combined_confidence = min(combined_confidence * 1.2, 1.0)
            
            # Collect all sources for this tag
            sources = [s.get('source', 'unknown') for s in group]
            
            final_suggestions.append({
                'tag': tag_name,
                'confidence': combined_confidence,
                'source': sources[0],  # Keep single source for backward compatibility
                'sources': sources,    # Multiple sources for enhanced info
                'category': group[0].get('category', 'general')
            })
        
        # Sort by confidence
        return sorted(final_suggestions, key=lambda x: x['confidence'], reverse=True)
    
    def _find_similar_entries(self, text: str, entries: List[Entry]) -> List[Tuple[Entry, float]]:
        """Find entries similar to the given text"""
        try:
            if not entries:
                return []
                
            # Prepare texts for comparison
            texts = [text] + [f"{entry.title} {entry.content}" for entry in entries]
            
            # Calculate TF-IDF similarities
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
            
            # Pair entries with similarities and sort
            entry_similarities = list(zip(entries, similarities))
            return sorted(entry_similarities, key=lambda x: x[1], reverse=True)
            
        except Exception as e:
            logger.error(f"Similarity calculation error: {e}")
            return []
    
    # ==================== MOOD PREDICTION ====================
    
    async def predict_mood(self, content: str, title: str = "") -> Dict[str, Any]:
        """
        Main mood prediction method - analyzes entry content and predicts emotional state with hardware-adaptive AI
        
        Args:
            content: Full entry content
            title: Entry title if available
            
        Returns:
            Mood prediction with confidence and analysis
        """
        try:
            # Refresh hardware-adaptive configurations if needed
            self.refresh_hardware_adaptive_models()
            
            text = f"{title} {content}".strip()
            
            if len(text) < 5:  # Need minimum content for prediction
                return {
                    'predicted_mood': 'neutral',
                    'confidence': 0.0,
                    'analysis': 'Insufficient content for mood analysis',
                    'method': 'insufficient_content'
                }
            
            # Try hardware-adaptive AI first
            if self.adaptive_ai:
                try:
                    result = await self.adaptive_ai.analyze_text(text, "sentiment")
                    if result["success"]:
                        # Convert sentiment result to mood format
                        sentiment_result = result["result"]
                        mood_mapping = {
                            'positive': 'happy',
                            'negative': 'sad', 
                            'neutral': 'neutral'
                        }
                        
                        predicted_mood = mood_mapping.get(sentiment_result.get('sentiment', 'neutral'), 'neutral')
                        
                        return {
                            'predicted_mood': predicted_mood,
                            'confidence': result["confidence"],
                            'analysis': f"Hardware-adaptive AI analysis using {result['method_used']}",
                            'method': f"adaptive_ai_{result['method_used']}",
                            'hardware_tier': result.get('hardware_tier', 'unknown'),
                            'processing_time': result.get('processing_time', 0),
                            'fallback_used': result.get('fallback_used', False)
                        }
                except Exception as e:
                    logger.warning(f"Hardware-adaptive AI mood prediction failed: {e}")
            
            # Fallback to traditional models for robust prediction
            predictions = []
            
            # Method 1: Use emotion classifier if available
            if self.emotion_classifier:
                try:
                    # Clear memory before inference
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        torch.cuda.synchronize()
                    
                    emotion_result = self.emotion_classifier(text)
                    if emotion_result:
                        emotion_label = emotion_result[0]['label'].lower()
                        emotion_score = emotion_result[0]['score']
                        
                        # Map emotion to mood
                        mood_mapping = {
                            'joy': 'very_positive',
                            'happiness': 'positive', 
                            'optimism': 'positive',
                            'love': 'positive',
                            'surprise': 'neutral',
                            'neutral': 'neutral',
                            'sadness': 'negative',
                            'disappointment': 'negative',
                            'pessimism': 'negative',
                            'anger': 'very_negative',
                            'disgust': 'very_negative',
                            'fear': 'very_negative'
                        }
                        
                        predicted_mood = mood_mapping.get(emotion_label, 'neutral')
                        predictions.append((predicted_mood, emotion_score))
                        
                except Exception as e:
                    logger.warning(f"Emotion classifier failed: {e}")
            
            # Method 2: Use sentiment service
            try:
                mood, sentiment_score = self.sentiment_service.analyze_sentiment(text)
                if mood:
                    predictions.append((mood.value, abs(sentiment_score)))
            except Exception as e:
                logger.warning(f"Sentiment service failed: {e}")
            
            # Method 3: Backup sentiment classifier
            if self.backup_classifier and not predictions:
                try:
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        torch.cuda.synchronize()
                    
                    sentiment_result = self.backup_classifier(text)
                    if sentiment_result:
                        label = sentiment_result[0]['label'].lower()
                        score = sentiment_result[0]['score']
                        
                        # Map sentiment to mood
                        if 'positive' in label:
                            predicted_mood = 'positive' if score > 0.7 else 'neutral'
                        elif 'negative' in label:
                            predicted_mood = 'negative' if score > 0.7 else 'neutral'
                        else:
                            predicted_mood = 'neutral'
                            
                        predictions.append((predicted_mood, score))
                        
                except Exception as e:
                    logger.warning(f"Backup classifier failed: {e}")
            
            # Combine predictions or use fallback
            if predictions:
                # Weight by confidence and take most confident
                best_prediction = max(predictions, key=lambda x: x[1])
                predicted_mood, confidence = best_prediction
            else:
                # Fallback: simple keyword analysis
                positive_words = ['happy', 'good', 'great', 'wonderful', 'amazing', 'love', 'excited']
                negative_words = ['sad', 'bad', 'terrible', 'awful', 'hate', 'angry', 'frustrated']
                
                text_lower = text.lower()
                positive_count = sum(1 for word in positive_words if word in text_lower)
                negative_count = sum(1 for word in negative_words if word in text_lower)
                
                if positive_count > negative_count:
                    predicted_mood = 'positive'
                    confidence = min(positive_count / 10, 0.8)
                elif negative_count > positive_count:
                    predicted_mood = 'negative'
                    confidence = min(negative_count / 10, 0.8)
                else:
                    predicted_mood = 'neutral'
                    confidence = 0.5
                    
            # Final cleanup
            # await self.gpu_memory_manager.cleanup_manager.emergency_gpu_cleanup()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            
            return {
                'predicted_mood': predicted_mood,
                'confidence': float(confidence),
                'analysis': f'Analyzed {len(text)} characters using {len(predictions)} prediction methods'
            }
            
        except Exception as e:
            logger.error(f"Mood prediction error: {e}")
            return {
                'predicted_mood': 'neutral',
                'confidence': 0.0,
                'analysis': f'Error in mood prediction: {str(e)}'
            }
    
    # ==================== MOOD PREDICTION ====================
    
    async def predict_mood(self, content: str, title: str = "") -> Dict[str, Any]:
        """
        Predict mood using multiple AI models with on-demand loading
        
        Args:
            content: Entry content
            title: Entry title
            
        Returns:
            Mood prediction with confidence and analysis details
        """
        try:
            text = f"{title} {content}".strip()
            
            if len(text) < 5:
                return {
                    'predicted_mood': 'neutral',
                    'confidence': 0.0,
                    'analysis': 'Text too short for analysis'
                }
            
            predictions = []
            analysis_methods = []
            
            # Method 1: Use emotion classifier (load on demand)
            emotion_model = self._load_model_on_demand('emotion_classifier')
            if emotion_model:
                try:
                    emotion_result = emotion_model(text, top_k=1)
                    if emotion_result and len(emotion_result) > 0:
                        emotion = emotion_result[0]
                        emotion_to_mood = {
                            'joy': 'very_positive',
                            'optimism': 'positive', 
                            'love': 'positive',
                            'neutral': 'neutral',
                            'surprise': 'neutral',
                            'sadness': 'negative',
                            'fear': 'negative',
                            'anger': 'very_negative',
                            'disgust': 'very_negative',
                            'pessimism': 'negative'
                        }
                        mood = emotion_to_mood.get(emotion['label'].lower(), 'neutral')
                        predictions.append((mood, emotion['score']))
                        analysis_methods.append('emotion_classifier')
                except Exception as e:
                    logger.warning(f"Emotion classifier failed: {e}")
            
            # Method 2: Use backup sentiment classifier  
            backup_model = self._load_model_on_demand('backup_classifier')
            if backup_model:
                try:
                    sentiment_result = backup_model(text, top_k=1)
                    if sentiment_result and len(sentiment_result) > 0:
                        sentiment = sentiment_result[0]
                        # Map sentiment to mood
                        if sentiment['label'].upper() == 'NEGATIVE':
                            if sentiment['score'] > 0.8:
                                mood = 'very_negative'
                            else:
                                mood = 'negative'
                        elif sentiment['label'].upper() == 'POSITIVE':
                            if sentiment['score'] > 0.8:
                                mood = 'very_positive'
                            else:
                                mood = 'positive'
                        else:
                            mood = 'neutral'
                        predictions.append((mood, sentiment['score']))
                        analysis_methods.append('sentiment_classifier')
                except Exception as e:
                    logger.warning(f"Backup classifier failed: {e}")
            
            # Aggregate predictions
            if predictions:
                # Weight by confidence and take majority
                mood_votes = {}
                total_confidence = 0
                
                for mood, confidence in predictions:
                    if mood not in mood_votes:
                        mood_votes[mood] = 0
                    mood_votes[mood] += confidence
                    total_confidence += confidence
                
                # Get mood with highest weighted vote
                predicted_mood = max(mood_votes.keys(), key=lambda k: mood_votes[k])
                confidence = mood_votes[predicted_mood] / total_confidence if total_confidence > 0 else 0
                
                return {
                    'predicted_mood': predicted_mood,
                    'confidence': confidence,
                    'analysis': f'Analyzed {len(text)} characters using {len(analysis_methods)} prediction methods'
                }
            else:
                # Fallback to simple keyword analysis
                positive_words = ['good', 'great', 'happy', 'wonderful', 'amazing', 'excited', 'love', 'joy']
                negative_words = ['bad', 'terrible', 'sad', 'awful', 'hate', 'angry', 'frustrated', 'depressed']
                
                text_lower = text.lower()
                positive_count = sum(1 for word in positive_words if word in text_lower)
                negative_count = sum(1 for word in negative_words if word in text_lower)
                
                if positive_count > negative_count:
                    mood = 'positive'
                    confidence = min(positive_count / 10.0, 1.0)
                elif negative_count > positive_count:
                    mood = 'negative' 
                    confidence = min(negative_count / 10.0, 1.0)
                else:
                    mood = 'neutral'
                    confidence = 0.5
                
                return {
                    'predicted_mood': mood,
                    'confidence': confidence,
                    'analysis': 'Fallback keyword-based analysis'
                }
                
        except Exception as e:
            logger.error(f"Mood prediction error: {e}")
            return {
                'predicted_mood': 'neutral',
                'confidence': 0.0,
                'analysis': f'Error in mood prediction: {str(e)}'
            }
        finally:
            # Always cleanup after prediction to prevent memory leaks
            self._unload_all_models_except()
            # await self.gpu_memory_manager.cleanup_manager.emergency_gpu_cleanup()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()

    async def predict_mood_early(self, partial_content: str, title: str = "") -> Dict[str, Any]:
        """
        Predict mood based on early entry content to provide timely support
        
        Args:
            partial_content: Partial entry content
            title: Entry title if available
            
        Returns:
            Mood prediction with confidence and suggested interventions
        """
        try:
            text = f"{title} {partial_content}".strip()
            
            if len(text) < 10:  # Need minimum content for prediction
                return {
                    'predicted_mood': None,
                    'confidence': 0.0,
                    'interventions': [],
                    'message': 'Need more content for mood prediction'
                }
            
            # Get sentiment analysis
            mood, sentiment_score = self.sentiment_service.analyze_sentiment(text)
            
            # Analyze emotional indicators
            emotional_analysis = self._analyze_emotional_indicators(text)
            
            # Check for crisis keywords
            crisis_indicators = self._detect_crisis_indicators(text)
            
            # Generate interventions based on mood
            interventions = self._generate_mood_interventions(mood, emotional_analysis, crisis_indicators)
            
            # Calculate confidence based on text length and clarity
            confidence = min(len(text) / 100, 1.0) * abs(sentiment_score)
            
            return {
                'predicted_mood': mood.value if mood else None,
                'confidence': confidence,
                'sentiment_score': sentiment_score,
                'emotional_indicators': emotional_analysis,
                'crisis_indicators': crisis_indicators,
                'interventions': interventions,
                'message': self._generate_supportive_message(mood, emotional_analysis)
            }
            
        except Exception as e:
            logger.error(f"Mood prediction error: {e}")
            return {
                'predicted_mood': None,
                'confidence': 0.0,
                'interventions': [],
                'message': 'Unable to predict mood at this time'
            }
    
    def _analyze_emotional_indicators(self, text: str) -> Dict[str, float]:
        """Analyze specific emotional indicators in text"""
        indicators = {
            'stress': 0.0,
            'anxiety': 0.0,
            'joy': 0.0,
            'sadness': 0.0,
            'anger': 0.0,
            'hope': 0.0
        }
        
        # Define keyword patterns for each emotion
        emotion_patterns = {
            'stress': [
                'stressed', 'overwhelmed', 'pressure', 'burden', 'exhausted',
                'too much', 'can\'t handle', 'breaking point'
            ],
            'anxiety': [
                'anxious', 'worried', 'nervous', 'panic', 'fear', 'scared',
                'what if', 'can\'t stop thinking', 'overthinking'
            ],
            'joy': [
                'happy', 'excited', 'thrilled', 'amazing', 'wonderful',
                'love', 'grateful', 'blessed', 'fantastic'
            ],
            'sadness': [
                'sad', 'depressed', 'down', 'empty', 'lonely', 'disappointed',
                'crying', 'tears', 'hurt'
            ],
            'anger': [
                'angry', 'furious', 'frustrated', 'annoyed', 'hate',
                'mad', 'irritated', 'fed up'
            ],
            'hope': [
                'hope', 'optimistic', 'looking forward', 'better', 'improve',
                'positive', 'bright', 'opportunity'
            ]
        }
        
        text_lower = text.lower()
        word_count = len(text.split())
        
        for emotion, keywords in emotion_patterns.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            indicators[emotion] = min(matches / max(word_count / 50, 1), 1.0)
        
        return indicators
    
    def _detect_crisis_indicators(self, text: str) -> List[str]:
        """Detect crisis or urgent support indicators"""
        crisis_keywords = [
            'suicide', 'kill myself', 'end it all', 'not worth living',
            'give up', 'can\'t go on', 'hopeless', 'no point',
            'self harm', 'hurt myself', 'cut myself'
        ]
        
        text_lower = text.lower()
        detected = []
        
        for keyword in crisis_keywords:
            if keyword in text_lower:
                detected.append(keyword)
        
        return detected
    
    def _generate_mood_interventions(self, mood: MoodType, emotional_analysis: Dict[str, float], crisis_indicators: List[str]) -> List[Dict[str, str]]:
        """Generate appropriate interventions based on mood and emotional state"""
        interventions = []
        
        # Crisis intervention
        if crisis_indicators:
            interventions.append({
                'type': 'crisis_support',
                'title': 'Immediate Support Available',
                'description': 'If you\'re having thoughts of self-harm, please reach out for immediate help.',
                'action': 'Contact crisis hotline or emergency services',
                'priority': 'urgent'
            })
        
        # Mood-specific interventions
        if mood == MoodType.VERY_NEGATIVE or emotional_analysis.get('sadness', 0) > 0.5:
            interventions.extend([
                {
                    'type': 'breathing_exercise',
                    'title': 'Deep Breathing Exercise',
                    'description': 'Take 5 deep breaths to help regulate your emotions',
                    'action': 'Practice 4-7-8 breathing technique',
                    'priority': 'medium'
                },
                {
                    'type': 'gratitude_prompt',
                    'title': 'Find Something Small to Appreciate',
                    'description': 'Even in difficult times, small moments of gratitude can help',
                    'action': 'Write down one thing you\'re grateful for today',
                    'priority': 'low'
                }
            ])
        
        elif emotional_analysis.get('stress', 0) > 0.5 or emotional_analysis.get('anxiety', 0) > 0.5:
            interventions.extend([
                {
                    'type': 'grounding_exercise',
                    'title': '5-4-3-2-1 Grounding Technique',
                    'description': 'Ground yourself in the present moment',
                    'action': 'Name 5 things you see, 4 you hear, 3 you touch, 2 you smell, 1 you taste',
                    'priority': 'medium'
                },
                {
                    'type': 'task_breakdown',
                    'title': 'Break Down Your Tasks',
                    'description': 'Large tasks can feel overwhelming. Break them into smaller steps.',
                    'action': 'List 3 small actions you can take today',
                    'priority': 'medium'
                }
            ])
        
        elif mood == MoodType.POSITIVE or mood == MoodType.VERY_POSITIVE:
            interventions.append({
                'type': 'celebrate',
                'title': 'Celebrate This Moment',
                'description': 'You\'re feeling good! Take time to appreciate this positive state.',
                'action': 'Write about what\'s contributing to your positive mood',
                'priority': 'low'
            })
        
        return interventions
    
    def _generate_supportive_message(self, mood: MoodType, emotional_analysis: Dict[str, float]) -> str:
        """Generate a supportive message based on current emotional state"""
        if not mood:
            return "Thank you for sharing your thoughts. Keep writing when you're ready."
        
        if mood == MoodType.VERY_NEGATIVE:
            return "I notice you might be going through a difficult time. Remember that your feelings are valid, and it's okay to seek support when you need it."
        
        elif mood == MoodType.NEGATIVE:
            return "It sounds like you're facing some challenges. Writing about your experiences can be a helpful way to process these feelings."
        
        elif emotional_analysis.get('stress', 0) > 0.5:
            return "I can sense some stress in your writing. Take a moment to breathe deeply and be gentle with yourself."
        
        elif emotional_analysis.get('anxiety', 0) > 0.5:
            return "Your anxiety is showing through your words. Remember that anxious thoughts aren't facts, and this feeling will pass."
        
        elif mood == MoodType.POSITIVE or mood == MoodType.VERY_POSITIVE:
            return "It's wonderful to see you in a positive space! These good moments are worth celebrating and remembering."
        
        else:
            return "Thank you for sharing your thoughts and feelings. Continue writing whenever you feel moved to do so."
    
    # ==================== SMART PROMPTS ====================
    
    async def get_smart_prompts(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get smart prompts for the user with memory-efficient loading
        
        Args:
            user_id: User identifier
            limit: Maximum number of prompts to return
            
        Returns:
            List of smart prompt dictionaries
        """
        try:
            # Generate smart prompts using existing method
            all_prompts = await self.generate_smart_prompts()
            
            # Return requested number of prompts
            return all_prompts[:limit] if all_prompts else self._get_default_prompts()[:limit]
            
        except Exception as e:
            logger.error(f"Error getting smart prompts: {e}")
            return self._get_default_prompts()[:limit]

    async def generate_smart_prompts(self, user_history_days: int = 30, current_content: Optional[str] = None, current_title: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate context-aware writing prompts based on user history and patterns with hardware-adaptive AI
        
        Args:
            user_history_days: Number of days to look back for pattern analysis
            current_content: Current entry content for contextual suggestions
            current_title: Current entry title for contextual suggestions
            
        Returns:
            List of personalized writing prompts
        """
        try:
            # Get user's recent entries
            end_date = datetime.now()
            start_date = end_date - timedelta(days=user_history_days)
            entries = await db_service.get_entries(date_from=start_date, limit=100)
            
            if not entries:
                return self._get_default_prompts()
            
            # Try hardware-adaptive AI for smart prompt generation
            if self.adaptive_ai and current_content:
                try:
                    context = {
                        'user_history_days': user_history_days,
                        'recent_entries_count': len(entries),
                        'current_title': current_title,
                        'analysis_type': 'smart_prompts'
                    }
                    
                    result = await self.adaptive_ai.analyze_text(current_content, "auto", context)
                    if result["success"]:
                        # Generate contextual prompts based on AI analysis
                        adaptive_prompts = self._generate_contextual_prompts_from_ai(result, current_content)
                        if adaptive_prompts:
                            logger.info(f"🤖 Generated {len(adaptive_prompts)} adaptive AI prompts")
                            return adaptive_prompts
                except Exception as e:
                    logger.warning(f"Hardware-adaptive AI prompt generation failed: {e}")
            
            # Analyze user patterns (fallback)
            patterns = await self._analyze_user_patterns(entries)
            
            # Add current content context if provided
            if current_content:
                patterns['current_context'] = {
                    'content': current_content,
                    'title': current_title,
                    'topics': self._extract_topics_from_text(current_content),
                    'mood_indicators': self._extract_mood_indicators(current_content)
                }
            
            # Generate personalized prompts
            prompts = []
            
            # Context-aware prompts (if current content is provided)
            if current_content:
                context_prompts = self._generate_context_aware_prompts(patterns)
                prompts.extend(context_prompts)
            
            # Mood-based prompts
            mood_prompts = self._generate_mood_based_prompts(patterns)
            prompts.extend(mood_prompts)
            
            # Topic-based prompts
            topic_prompts = self._generate_topic_based_prompts(patterns)
            prompts.extend(topic_prompts)
            
            # Growth and reflection prompts
            growth_prompts = self._generate_growth_prompts(patterns)
            prompts.extend(growth_prompts)
            
            # Time-based prompts
            time_prompts = self._generate_time_based_prompts()
            prompts.extend(time_prompts)
            
            # Rank and return top prompts
            ranked_prompts = self._rank_prompts(prompts, patterns)
            
            return ranked_prompts[:10]  # Return top 10 prompts
            
        except Exception as e:
            logger.error(f"Smart prompts generation error: {e}")
            return self._get_default_prompts()
    
    async def _analyze_user_patterns(self, entries: List[Entry]) -> Dict[str, Any]:
        """Analyze user writing patterns and preferences"""
        patterns = {
            'dominant_moods': [],
            'common_topics': [],
            'writing_frequency': 0,
            'avg_word_count': 0,
            'time_patterns': [],
            'emotional_trends': {},
            'recurring_themes': []
        }
        
        try:
            if not entries:
                return patterns
            
            # Mood analysis
            moods = [entry.mood.value for entry in entries if entry.mood]
            patterns['dominant_moods'] = [mood for mood, count in Counter(moods).most_common(3)]
            
            # Topic analysis
            all_tags = []
            for entry in entries:
                all_tags.extend(entry.tags)
            patterns['common_topics'] = [tag for tag, count in Counter(all_tags).most_common(5)]
            
            # Writing frequency and length
            patterns['writing_frequency'] = len(entries) / 30  # entries per day
            word_counts = [entry.word_count for entry in entries if entry.word_count]
            patterns['avg_word_count'] = statistics.mean(word_counts) if word_counts else 0
            
            # Time patterns
            hours = [entry.created_at.hour for entry in entries]
            patterns['time_patterns'] = [hour for hour, count in Counter(hours).most_common(3)]
            
            # Emotional trends (last 7 days vs previous)
            recent_entries = [e for e in entries if e.created_at >= datetime.now() - timedelta(days=7)]
            older_entries = [e for e in entries if e.created_at < datetime.now() - timedelta(days=7)]
            
            if recent_entries and older_entries:
                recent_scores = [e.sentiment_score for e in recent_entries if e.sentiment_score]
                older_scores = [e.sentiment_score for e in older_entries if e.sentiment_score]
                
                if recent_scores and older_scores:
                    recent_avg = statistics.mean(recent_scores)
                    older_avg = statistics.mean(older_scores)
                    patterns['emotional_trends'] = {
                        'recent_sentiment': recent_avg,
                        'previous_sentiment': older_avg,
                        'trend': 'improving' if recent_avg > older_avg else 'declining' if recent_avg < older_avg else 'stable'
                    }
            
            return patterns
            
        except Exception as e:
            logger.error(f"Pattern analysis error: {e}")
            return patterns
    
    def _generate_mood_based_prompts(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate prompts based on user's mood patterns"""
        prompts = []
        dominant_moods = patterns.get('dominant_moods', [])
        emotional_trends = patterns.get('emotional_trends', {})
        
        # Prompts for common negative moods
        if 'very_negative' in dominant_moods or 'negative' in dominant_moods:
            prompts.extend([
                {
                    'id': 'mood_coping',
                    'title': 'Coping Strategies Reflection',
                    'prompt': 'What coping strategies have helped you during difficult times? Which ones would you like to try or improve?',
                    'category': 'emotional_support',
                    'relevance_score': 0.9
                },
                {
                    'id': 'mood_silver_lining',
                    'title': 'Finding Light in Darkness',
                    'prompt': 'Even during tough times, there can be small moments of relief or learning. What small positive thing can you notice today?',
                    'category': 'resilience',
                    'relevance_score': 0.8
                }
            ])
        
        # Prompts for positive moods
        if 'very_positive' in dominant_moods or 'positive' in dominant_moods:
            prompts.extend([
                {
                    'id': 'mood_gratitude',
                    'title': 'Amplifying Gratitude',
                    'prompt': 'You seem to be in a good space lately. What specific things, people, or experiences are contributing to your positive feelings?',
                    'category': 'gratitude',
                    'relevance_score': 0.8
                },
                {
                    'id': 'mood_sharing_joy',
                    'title': 'Spreading Positivity',
                    'prompt': 'How might you share your current positive energy with others or use it to tackle something you have been putting off?',
                    'category': 'action',
                    'relevance_score': 0.7
                }
            ])
        
        # Trend-based prompts
        trend = emotional_trends.get('trend')
        if trend == 'improving':
            prompts.append({
                'id': 'trend_improving',
                'title': 'Recognizing Progress',
                'prompt': 'Your emotional tone seems to be improving lately. What changes in your life or mindset might be contributing to this positive shift?',
                'category': 'self_awareness',
                'relevance_score': 0.9
            })
        elif trend == 'declining':
            prompts.append({
                'id': 'trend_declining',
                'title': 'Gentle Self-Check',
                'prompt': 'You might be going through a challenging period. What support systems or self-care practices could help you right now?',
                'category': 'self_care',
                'relevance_score': 0.9
            })
        
        return prompts
    
    def _generate_context_aware_prompts(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate prompts based on current content context"""
        prompts = []
        context = patterns.get('current_context', {})
        
        if not context:
            return prompts
            
        content = context.get('content', '')
        topics = context.get('topics', [])
        mood_indicators = context.get('mood_indicators', [])
        
        # Generate prompts based on detected topics in current content
        if 'stress' in content.lower() or 'anxious' in content.lower():
            prompts.append({
                'id': 'stress_coping',
                'title': 'Stress Management',
                'prompt': 'What specific strategies help you manage stress? How could you apply one of them right now?',
                'category': 'self_care',
                'relevance_score': 0.95
            })
        
        if 'work' in content.lower() or 'job' in content.lower():
            prompts.append({
                'id': 'work_reflection',
                'title': 'Work Perspective',
                'prompt': 'What aspects of your work situation do you have control over? What small change could improve your experience?',
                'category': 'career',
                'relevance_score': 0.9
            })
        
        if 'relationship' in content.lower() or 'friend' in content.lower() or 'family' in content.lower():
            prompts.append({
                'id': 'relationship_insight',
                'title': 'Connection Reflection',
                'prompt': 'What do you value most in this relationship? How can you nurture that quality?',
                'category': 'relationships',
                'relevance_score': 0.9
            })
        
        if 'goal' in content.lower() or 'future' in content.lower() or 'plan' in content.lower():
            prompts.append({
                'id': 'goal_clarity',
                'title': 'Next Steps',
                'prompt': 'What is one small, concrete step you could take this week toward this goal?',
                'category': 'growth',
                'relevance_score': 0.85
            })
        
        # Add prompts based on mood indicators
        positive_words = ['happy', 'excited', 'grateful', 'joy', 'good', 'great']
        negative_words = ['sad', 'frustrated', 'angry', 'worried', 'difficult', 'hard']
        
        if any(word in content.lower() for word in positive_words):
            prompts.append({
                'id': 'positive_amplify',
                'title': 'Amplifying Positivity',
                'prompt': 'How can you build on or share this positive energy with others in your life?',
                'category': 'gratitude',
                'relevance_score': 0.8
            })
        
        if any(word in content.lower() for word in negative_words):
            prompts.append({
                'id': 'challenge_growth',
                'title': 'Learning from Challenges',
                'prompt': 'What is this situation teaching you about yourself? How might you approach something similar in the future?',
                'category': 'reflection',
                'relevance_score': 0.85
            })
        
        return prompts
    
    def _extract_topics_from_text(self, text: str) -> List[str]:
        """Extract main topics from text content"""
        topics = []
        text_lower = text.lower()
        
        # Simple keyword-based topic detection
        topic_keywords = {
            'work': ['work', 'job', 'career', 'office', 'boss', 'colleague', 'project'],
            'relationships': ['relationship', 'friend', 'family', 'partner', 'love', 'social'],
            'health': ['health', 'exercise', 'diet', 'sleep', 'tired', 'energy'],
            'personal_growth': ['goal', 'learn', 'grow', 'improve', 'develop', 'progress'],
            'emotions': ['feel', 'emotion', 'mood', 'happy', 'sad', 'angry', 'anxious']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _extract_mood_indicators(self, text: str) -> List[str]:
        """Extract mood indicators from text"""
        indicators = []
        text_lower = text.lower()
        
        # Positive indicators
        positive = ['happy', 'joy', 'excited', 'grateful', 'good', 'great', 'amazing', 'wonderful']
        negative = ['sad', 'angry', 'frustrated', 'worried', 'anxious', 'depressed', 'upset']
        neutral = ['okay', 'fine', 'normal', 'usual', 'average']
        
        for word in positive:
            if word in text_lower:
                indicators.append(f'positive:{word}')
        
        for word in negative:
            if word in text_lower:
                indicators.append(f'negative:{word}')
        
        for word in neutral:
            if word in text_lower:
                indicators.append(f'neutral:{word}')
        
        return indicators
    
    def _generate_topic_based_prompts(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate prompts based on user's common topics"""
        prompts = []
        common_topics = patterns.get('common_topics', [])
        
        topic_prompt_map = {
            'work': [
                {
                    'id': 'work_satisfaction',
                    'title': 'Work-Life Reflection',
                    'prompt': 'How has your relationship with work evolved recently? What aspects bring you energy vs. drain you?',
                    'category': 'career'
                },
                {
                    'id': 'work_growth',
                    'title': 'Professional Development',
                    'prompt': 'What new skills or opportunities at work are you most curious about exploring?',
                    'category': 'growth'
                }
            ],
            'relationships': [
                {
                    'id': 'relationship_appreciation',
                    'title': 'Connection Appreciation',
                    'prompt': 'Think about the relationships in your life. Which connections feel most nourishing right now, and why?',
                    'category': 'relationships'
                },
                {
                    'id': 'relationship_boundaries',
                    'title': 'Healthy Boundaries',
                    'prompt': 'How are you doing with setting and maintaining boundaries in your relationships?',
                    'category': 'self_care'
                }
            ],
            'health': [
                {
                    'id': 'health_habits',
                    'title': 'Wellness Check-in',
                    'prompt': 'How are you feeling physically and mentally today? What small step could you take to care for yourself?',
                    'category': 'health'
                },
                {
                    'id': 'health_energy',
                    'title': 'Energy Patterns',
                    'prompt': 'When do you feel most energized during the day? What activities or habits contribute to your vitality?',
                    'category': 'self_awareness'
                }
            ],
            'goals': [
                {
                    'id': 'goals_progress',
                    'title': 'Goal Progress Review',
                    'prompt': 'What progress have you made on your personal goals recently? What obstacles have you overcome?',
                    'category': 'achievement'
                },
                {
                    'id': 'goals_adjustment',
                    'title': 'Goal Refinement',
                    'prompt': 'Are your current goals still aligned with what matters most to you? What might need adjusting?',
                    'category': 'planning'
                }
            ]
        }
        
        for topic in common_topics:
            if topic in topic_prompt_map:
                for prompt_data in topic_prompt_map[topic]:
                    prompt_data['relevance_score'] = 0.8  # High relevance for user's topics
                    prompts.append(prompt_data)
        
        return prompts
    
    def _generate_growth_prompts(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate prompts focused on personal growth and reflection"""
        prompts = [
            {
                'id': 'growth_lessons',
                'title': 'Recent Life Lessons',
                'prompt': 'What important lesson have you learned about yourself in the past month?',
                'category': 'self_awareness',
                'relevance_score': 0.7
            },
            {
                'id': 'growth_challenges',
                'title': 'Embracing Challenges',
                'prompt': 'What challenge are you currently facing that might actually be an opportunity for growth?',
                'category': 'resilience',
                'relevance_score': 0.7
            },
            {
                'id': 'growth_values',
                'title': 'Values Alignment',
                'prompt': 'How well are your current actions and decisions aligned with your core values?',
                'category': 'values',
                'relevance_score': 0.6
            },
            {
                'id': 'growth_future_self',
                'title': 'Future Self Wisdom',
                'prompt': 'If you could give advice to yourself from one year ago, what would you say?',
                'category': 'reflection',
                'relevance_score': 0.6
            }
        ]
        
        return prompts
    
    def _generate_time_based_prompts(self) -> List[Dict[str, Any]]:
        """Generate prompts based on current time/season"""
        now = datetime.now()
        prompts = []
        
        # Day of week prompts
        if now.weekday() == 0:  # Monday
            prompts.append({
                'id': 'monday_intention',
                'title': 'Monday Intention Setting',
                'prompt': 'As you start a new week, what intention do you want to set for yourself?',
                'category': 'planning',
                'relevance_score': 0.6
            })
        elif now.weekday() == 4:  # Friday
            prompts.append({
                'id': 'friday_reflection',
                'title': 'Week in Review',
                'prompt': 'As the week comes to an end, what moments stand out to you? What are you proud of?',
                'category': 'reflection',
                'relevance_score': 0.6
            })
        elif now.weekday() == 6:  # Sunday
            prompts.append({
                'id': 'sunday_preparation',
                'title': 'Sunday Reset',
                'prompt': 'How do you want to prepare yourself mentally and emotionally for the week ahead?',
                'category': 'planning',
                'relevance_score': 0.6
            })
        
        # Month-based prompts
        if now.day <= 3:  # Beginning of month
            prompts.append({
                'id': 'month_fresh_start',
                'title': 'Fresh Start Reflection',
                'prompt': 'A new month is beginning. What would you like to focus on or change this month?',
                'category': 'planning',
                'relevance_score': 0.5
            })
        elif now.day >= 28:  # End of month
            prompts.append({
                'id': 'month_review',
                'title': 'Monthly Review',
                'prompt': 'As this month comes to a close, what are your biggest takeaways and accomplishments?',
                'category': 'reflection',
                'relevance_score': 0.5
            })
        
        return prompts
    
    def _rank_prompts(self, prompts: List[Dict[str, Any]], patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank prompts based on relevance and user patterns"""
        # Add randomization factor to prevent repetition
        import random
        
        for prompt in prompts:
            base_score = prompt.get('relevance_score', 0.5)
            randomization = random.uniform(0.8, 1.2)  # ±20% randomization
            prompt['final_score'] = base_score * randomization
        
        return sorted(prompts, key=lambda x: x['final_score'], reverse=True)
    
    def _get_default_prompts(self) -> List[Dict[str, Any]]:
        """Get default prompts for new users or when pattern analysis fails"""
        return [
            {
                'id': 'default_mood',
                'title': 'How Are You Feeling?',
                'prompt': 'Take a moment to check in with yourself. How are you feeling right now, and what might be influencing your mood?',
                'category': 'mood_check',
                'relevance_score': 0.8
            },
            {
                'id': 'default_gratitude',
                'title': 'Daily Gratitude',
                'prompt': 'What are three things you are grateful for today, no matter how small they might seem?',
                'category': 'gratitude',
                'relevance_score': 0.7
            },
            {
                'id': 'default_reflection',
                'title': 'Daily Reflection',
                'prompt': 'What was the most meaningful part of your day, and why did it stand out to you?',
                'category': 'reflection',
                'relevance_score': 0.7
            },
            {
                'id': 'default_goals',
                'title': 'Personal Growth',
                'prompt': 'What\'s one small step you could take today toward becoming the person you want to be?',
                'category': 'growth',
                'relevance_score': 0.6
            },
            {
                'id': 'default_creativity',
                'title': 'Creative Expression',
                'prompt': 'If you could express your current thoughts and feelings through art, music, or movement, what would that look like?',
                'category': 'creativity',
                'relevance_score': 0.5
            }
        ]
    
    # ==================== WRITING STYLE ANALYSIS ====================
    
    async def analyze_writing_style(self, entries: List[Entry], time_period_days: int = 90) -> Dict[str, Any]:
        """
        Analyze user's writing style and track changes over time
        
        Args:
            entries: List of entries to analyze
            time_period_days: Period to analyze for trends
            
        Returns:
            Comprehensive writing style analysis
        """
        try:
            if not entries:
                return {'error': 'No entries to analyze'}
            
            # Split entries into time periods for trend analysis
            now = datetime.now()
            recent_cutoff = now - timedelta(days=time_period_days // 2)
            
            recent_entries = [e for e in entries if e.created_at >= recent_cutoff]
            older_entries = [e for e in entries if e.created_at < recent_cutoff]
            
            # Analyze both periods
            recent_analysis = self._analyze_style_metrics(recent_entries) if recent_entries else {}
            older_analysis = self._analyze_style_metrics(older_entries) if older_entries else {}
            
            # Calculate trends
            trends = self._calculate_style_trends(recent_analysis, older_analysis)
            
            # Overall style profile
            all_analysis = self._analyze_style_metrics(entries)
            
            return {
                'overall_profile': all_analysis,
                'recent_period': recent_analysis,
                'previous_period': older_analysis,
                'trends': trends,
                'analysis_date': now.isoformat(),
                'total_entries': len(entries),
                'time_period_days': time_period_days
            }
            
        except Exception as e:
            logger.error(f"Writing style analysis error: {e}")
            return {'error': f'Analysis failed: {str(e)}'}
        finally:
            # Always cleanup after style analysis to prevent memory leaks
            self._unload_all_models_except()
            # await self.gpu_memory_manager.cleanup_manager.emergency_gpu_cleanup()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
    
    def _analyze_style_metrics(self, entries: List[Entry]) -> Dict[str, Any]:
        """Analyze various writing style metrics for a set of entries"""
        if not entries:
            return {}
        
        try:
            # Combine all text
            all_text = ' '.join([f"{entry.title} {entry.content}" for entry in entries])
            
            # Basic metrics
            total_words = sum(entry.word_count or 0 for entry in entries)
            avg_entry_length = total_words / len(entries) if entries else 0
            
            # Readability metrics
            readability = self._calculate_readability_metrics(all_text)
            
            # Vocabulary analysis
            vocabulary = self._analyze_vocabulary(all_text)
            
            # Sentiment patterns
            sentiment_scores = [e.sentiment_score for e in entries if e.sentiment_score is not None]
            sentiment_analysis = {
                'avg_sentiment': statistics.mean(sentiment_scores) if sentiment_scores else 0,
                'sentiment_variance': statistics.variance(sentiment_scores) if len(sentiment_scores) > 1 else 0,
                'sentiment_range': max(sentiment_scores) - min(sentiment_scores) if sentiment_scores else 0
            }
            
            # Temporal patterns
            temporal = self._analyze_temporal_patterns(entries)
            
            return {
                'basic_metrics': {
                    'total_entries': len(entries),
                    'total_words': total_words,
                    'avg_entry_length': round(avg_entry_length, 1),
                    'avg_words_per_sentence': self._avg_words_per_sentence(all_text)
                },
                'readability': readability,
                'vocabulary': vocabulary,
                'sentiment': sentiment_analysis,
                'temporal': temporal
            }
            
        except Exception as e:
            logger.error(f"Style metrics calculation error: {e}")
            return {}
    
    def _calculate_readability_metrics(self, text: str) -> Dict[str, float]:
        """Calculate readability metrics for text"""
        try:
            metrics = {
                'flesch_reading_ease': flesch_reading_ease(text),
                'flesch_kincaid_grade': flesch_kincaid_grade(text),
                'avg_sentence_length': self._avg_sentence_length(text),
                'complexity_score': self._calculate_complexity_score(text)
            }
            
            # Interpret readability
            ease_score = metrics['flesch_reading_ease']
            if ease_score >= 90:
                metrics['readability_level'] = 'Very Easy'
            elif ease_score >= 80:
                metrics['readability_level'] = 'Easy'
            elif ease_score >= 70:
                metrics['readability_level'] = 'Fairly Easy'
            elif ease_score >= 60:
                metrics['readability_level'] = 'Standard'
            elif ease_score >= 50:
                metrics['readability_level'] = 'Fairly Difficult'
            elif ease_score >= 30:
                metrics['readability_level'] = 'Difficult'
            else:
                metrics['readability_level'] = 'Very Difficult'
            
            return metrics
            
        except Exception as e:
            logger.error(f"Readability calculation error: {e}")
            return {}
    
    def _analyze_vocabulary(self, text: str) -> Dict[str, Any]:
        """Analyze vocabulary richness and patterns"""
        try:
            words = word_tokenize(text.lower())
            words = [word for word in words if word.isalpha()]
            
            if not words:
                return {}
            
            # Basic vocabulary metrics
            unique_words = set(words)
            vocabulary_richness = len(unique_words) / len(words) if words else 0
            
            # Most common words (excluding stopwords)
            stop_words = set(stopwords.words('english'))
            content_words = [word for word in words if word not in stop_words]
            common_words = Counter(content_words).most_common(10)
            
            # Average word length
            avg_word_length = statistics.mean([len(word) for word in words])
            
            return {
                'total_words': len(words),
                'unique_words': len(unique_words),
                'vocabulary_richness': round(vocabulary_richness, 3),
                'avg_word_length': round(avg_word_length, 2),
                'most_common_words': common_words
            }
            
        except Exception as e:
            logger.error(f"Vocabulary analysis error: {e}")
            return {}
    
    def _analyze_temporal_patterns(self, entries: List[Entry]) -> Dict[str, Any]:
        """Analyze temporal writing patterns"""
        try:
            # Writing times
            hours = [entry.created_at.hour for entry in entries]
            days_of_week = [entry.created_at.weekday() for entry in entries]
            
            # Most common writing times
            common_hours = Counter(hours).most_common(3)
            common_days = Counter(days_of_week).most_common(3)
            
            # Day names for readability
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            common_day_names = [(day_names[day], count) for day, count in common_days]
            
            # Writing frequency
            if len(entries) > 1:
                date_range = (entries[0].created_at - entries[-1].created_at).days
                entries_per_week = (len(entries) / date_range) * 7 if date_range > 0 else 0
            else:
                entries_per_week = 0
            
            return {
                'preferred_hours': common_hours,
                'preferred_days': common_day_names,
                'entries_per_week': round(entries_per_week, 1),
                'total_timespan_days': (entries[0].created_at - entries[-1].created_at).days if len(entries) > 1 else 0
            }
            
        except Exception as e:
            logger.error(f"Temporal analysis error: {e}")
            return {}
    
    def _calculate_style_trends(self, recent: Dict[str, Any], older: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate trends between two time periods"""
        trends = {}
        
        if not recent or not older:
            return trends
        
        try:
            # Compare basic metrics
            recent_basic = recent.get('basic_metrics', {})
            older_basic = older.get('basic_metrics', {})
            
            if recent_basic and older_basic:
                trends['entry_length_change'] = recent_basic.get('avg_entry_length', 0) - older_basic.get('avg_entry_length', 0)
                trends['writing_frequency_change'] = recent_basic.get('total_entries', 0) - older_basic.get('total_entries', 0)
            
            # Compare readability
            recent_read = recent.get('readability', {})
            older_read = older.get('readability', {})
            
            if recent_read and older_read:
                trends['readability_change'] = recent_read.get('flesch_reading_ease', 0) - older_read.get('flesch_reading_ease', 0)
                trends['complexity_change'] = recent_read.get('complexity_score', 0) - older_read.get('complexity_score', 0)
            
            # Compare vocabulary
            recent_vocab = recent.get('vocabulary', {})
            older_vocab = older.get('vocabulary', {})
            
            if recent_vocab and older_vocab:
                trends['vocabulary_richness_change'] = recent_vocab.get('vocabulary_richness', 0) - older_vocab.get('vocabulary_richness', 0)
                trends['word_length_change'] = recent_vocab.get('avg_word_length', 0) - older_vocab.get('avg_word_length', 0)
            
            # Compare sentiment
            recent_sentiment = recent.get('sentiment', {})
            older_sentiment = older.get('sentiment', {})
            
            if recent_sentiment and older_sentiment:
                trends['sentiment_change'] = recent_sentiment.get('avg_sentiment', 0) - older_sentiment.get('avg_sentiment', 0)
                trends['emotional_stability_change'] = older_sentiment.get('sentiment_variance', 0) - recent_sentiment.get('sentiment_variance', 0)  # Lower variance = more stable
            
            return trends
            
        except Exception as e:
            logger.error(f"Trend calculation error: {e}")
            return trends
    
    def _avg_sentence_length(self, text: str) -> float:
        """Calculate average sentence length"""
        try:
            sentences = sent_tokenize(text)
            if not sentences:
                return 0
            words_per_sentence = [len(word_tokenize(sentence)) for sentence in sentences]
            return statistics.mean(words_per_sentence)
        except:
            return 0
    
    def _avg_words_per_sentence(self, text: str) -> float:
        """Calculate average words per sentence"""
        return self._avg_sentence_length(text)
    
    def _calculate_complexity_score(self, text: str) -> float:
        """Calculate a custom complexity score based on various factors"""
        try:
            # Factors contributing to complexity
            avg_word_length = statistics.mean([len(word) for word in word_tokenize(text) if word.isalpha()])
            sentence_length_variance = statistics.variance([len(word_tokenize(sent)) for sent in sent_tokenize(text)])
            
            # Combine factors (normalized)
            complexity = (avg_word_length / 10) + (sentence_length_variance / 100)
            return min(complexity, 1.0)  # Cap at 1.0
            
        except:
            return 0
    
    def _generate_contextual_prompts_from_ai(self, ai_result: Dict[str, Any], current_content: str) -> List[Dict[str, Any]]:
        """Generate contextual prompts based on hardware-adaptive AI analysis"""
        try:
            prompts = []
            analysis = ai_result.get("result", {})
            method_used = ai_result.get("method_used", "unknown")
            
            # Base contextual prompts based on current content themes
            content_words = current_content.lower().split()
            
            # Generate prompts based on detected themes
            if "work" in content_words or "job" in content_words:
                prompts.extend([
                    {
                        "prompt": "What specific accomplishment at work made you feel most proud today?",
                        "category": "work_reflection",
                        "reasoning": f"Detected work-related content using {method_used}",
                        "confidence": ai_result.get("confidence", 0.7)
                    },
                    {
                        "prompt": "How did your interactions with colleagues shape your day?",
                        "category": "workplace_relationships",
                        "reasoning": f"Work context analysis via {method_used}",
                        "confidence": ai_result.get("confidence", 0.7)
                    }
                ])
            
            if "family" in content_words or "friend" in content_words:
                prompts.extend([
                    {
                        "prompt": "What moment with loved ones brought you the most joy recently?",
                        "category": "relationships",
                        "reasoning": f"Detected relationship themes using {method_used}",
                        "confidence": ai_result.get("confidence", 0.7)
                    },
                    {
                        "prompt": "How have your relationships been evolving lately?",
                        "category": "relationship_growth",
                        "reasoning": f"Social context analysis via {method_used}",
                        "confidence": ai_result.get("confidence", 0.7)
                    }
                ])
            
            if "feel" in content_words or "emotion" in content_words:
                prompts.extend([
                    {
                        "prompt": "What physical sensations accompany your current emotional state?",
                        "category": "emotional_awareness",
                        "reasoning": f"Detected emotional content using {method_used}",
                        "confidence": ai_result.get("confidence", 0.7)
                    },
                    {
                        "prompt": "If your emotions had a color today, what would it be and why?",
                        "category": "creative_reflection",
                        "reasoning": f"Emotional analysis via {method_used}",
                        "confidence": ai_result.get("confidence", 0.7)
                    }
                ])
            
            # Add sentiment-based prompts
            if isinstance(analysis, dict) and 'sentiment' in analysis:
                sentiment = analysis['sentiment']
                if sentiment == 'positive':
                    prompts.append({
                        "prompt": "What factors contributed most to your positive mindset today?",
                        "category": "gratitude",
                        "reasoning": f"Positive sentiment detected via {method_used}",
                        "confidence": ai_result.get("confidence", 0.7)
                    })
                elif sentiment == 'negative':
                    prompts.append({
                        "prompt": "What small step could you take tomorrow to improve how you're feeling?",
                        "category": "growth",
                        "reasoning": f"Challenging emotions detected via {method_used}",
                        "confidence": ai_result.get("confidence", 0.7)
                    })
            
            # Ensure we have at least some prompts
            if not prompts:
                prompts = [
                    {
                        "prompt": "What aspect of today deserves deeper reflection?",
                        "category": "general_reflection",
                        "reasoning": f"General context analysis via {method_used}",
                        "confidence": ai_result.get("confidence", 0.5)
                    },
                    {
                        "prompt": "What patterns in your thoughts and feelings are you noticing?",
                        "category": "self_awareness",
                        "reasoning": f"Content analysis via {method_used}",
                        "confidence": ai_result.get("confidence", 0.5)
                    }
                ]
            
            return prompts[:5]  # Return top 5 prompts
            
        except Exception as e:
            logger.error(f"Error generating contextual prompts from AI: {e}")
            return []
    
    async def shutdown(self):
        """Shutdown the Enhanced AI Service and cleanup all resources"""
        logger.info("🔄 Shutting down Enhanced AI Service...")
        
        try:
            # Cleanup all AI models
            await self.cleanup()
            
            # Clear TfidfVectorizer to prevent memory leaks
            self.tfidf_vectorizer = None
            
            # Shutdown hardware-adaptive AI
            if self.adaptive_ai:
                await self.adaptive_ai.shutdown()
                self.adaptive_ai = None
            
            # Final GPU memory cleanup
            if self.gpu_memory_manager:
                # await self.gpu_memory_manager.cleanup_manager.emergency_gpu_cleanup()
                pass
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            
            # Clear all caches
            self._user_patterns_cache.clear()
            
            logger.info("✅ Enhanced AI Service shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during Enhanced AI Service shutdown: {e}")


# Global instance - initialized lazily
_enhanced_ai_service = None

def get_enhanced_ai_service() -> EnhancedAIService:
    """Get or create the global Enhanced AI Service instance (lazy initialization)"""
    global _enhanced_ai_service
    if _enhanced_ai_service is None:
        _enhanced_ai_service = EnhancedAIService()
    return _enhanced_ai_service

# Create legacy compatibility instance that doesn't auto-load models
class LegacyCompatibilityService:
    """Lightweight service for backward compatibility"""
    def __init__(self):
        self.enhanced_service = None
    
    def _get_enhanced_service(self):
        if self.enhanced_service is None:
            self.enhanced_service = get_enhanced_ai_service()
        return self.enhanced_service

# Legacy compatibility - these will be loaded only when first used
enhanced_ai_service = LegacyCompatibilityService()
