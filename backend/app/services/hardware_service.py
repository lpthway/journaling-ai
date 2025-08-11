"""
Hardware Detection and Adaptive Model Selection Service
Automatically detects system capabilities and selects optimal AI models
"""
import asyncio
import logging
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import psutil
import torch

logger = logging.getLogger(__name__)

@dataclass
class HardwareSpecs:
    """System hardware specifications"""
    # GPU Info
    has_gpu: bool = False
    gpu_name: str = ""
    gpu_memory_gb: float = 0.0
    gpu_compute_capability: float = 0.0
    cuda_available: bool = False
    
    # CPU Info  
    cpu_cores: int = 0
    cpu_threads: int = 0
    cpu_freq_ghz: float = 0.0
    
    # Memory Info
    ram_gb: float = 0.0
    
    # Performance Tier
    performance_tier: str = "basic"  # basic, standard, high, enterprise

@dataclass 
class ModelConfig:
    """Model configuration with hardware requirements"""
    model_name: str
    memory_requirement_gb: float
    min_compute_capability: float = 0.0
    prefers_gpu: bool = True
    fallback_model: Optional[str] = None

class HardwareService:
    """Detects hardware and selects optimal models"""
    
    def __init__(self):
        self.specs: Optional[HardwareSpecs] = None
        self.model_configs: Dict[str, Dict[str, ModelConfig]] = {}
        self._initialize_model_configs()
    
    async def detect_hardware(self) -> HardwareSpecs:
        """Detect system hardware capabilities"""
        try:
            specs = HardwareSpecs()
            
            # === GPU Detection ===
            if torch.cuda.is_available():
                specs.cuda_available = True
                specs.has_gpu = True
                
                # Get GPU details via nvidia-smi
                try:
                    result = subprocess.run([
                        "nvidia-smi", "--query-gpu=name,memory.total,compute_cap",
                        "--format=csv,noheader,nounits"
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        gpu_info = result.stdout.strip().split(", ")
                        specs.gpu_name = gpu_info[0]
                        specs.gpu_memory_gb = float(gpu_info[1]) / 1024  # MB to GB
                        specs.gpu_compute_capability = float(gpu_info[2])
                except Exception as e:
                    logger.warning(f"Could not get GPU details via nvidia-smi: {e}")
                    # Fallback to PyTorch
                    specs.gpu_name = torch.cuda.get_device_name(0)
                    specs.gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            
            # === CPU Detection ===
            specs.cpu_cores = psutil.cpu_count(logical=False)
            specs.cpu_threads = psutil.cpu_count(logical=True)
            try:
                cpu_freq = psutil.cpu_freq()
                specs.cpu_freq_ghz = cpu_freq.max / 1000 if cpu_freq else 0.0
            except:
                specs.cpu_freq_ghz = 0.0
            
            # === Memory Detection ===
            memory = psutil.virtual_memory()
            specs.ram_gb = memory.total / (1024**3)
            
            # === Performance Tier Classification ===
            specs.performance_tier = self._classify_performance_tier(specs)
            
            self.specs = specs
            logger.info(f"🔍 Hardware detected: {specs.performance_tier} tier")
            logger.info(f"   GPU: {specs.gpu_name} ({specs.gpu_memory_gb:.1f}GB)")
            logger.info(f"   CPU: {specs.cpu_cores}c/{specs.cpu_threads}t @ {specs.cpu_freq_ghz:.1f}GHz")
            logger.info(f"   RAM: {specs.ram_gb:.1f}GB")
            
            return specs
            
        except Exception as e:
            logger.error(f"Hardware detection failed: {e}")
            # Return basic specs as fallback
            return HardwareSpecs(
                cpu_cores=psutil.cpu_count(logical=False) or 4,
                cpu_threads=psutil.cpu_count(logical=True) or 8,
                ram_gb=psutil.virtual_memory().total / (1024**3),
                performance_tier="basic"
            )
    
    def _classify_performance_tier(self, specs: HardwareSpecs) -> str:
        """Classify hardware into performance tiers"""
        # Enterprise: High-end GPU + lots of VRAM + RAM
        if specs.gpu_memory_gb >= 16 and specs.ram_gb >= 32:
            return "enterprise"
        
        # High: Good GPU with decent VRAM
        elif specs.gpu_memory_gb >= 8 and specs.ram_gb >= 16:
            return "high"
        
        # Standard: Some GPU or good CPU
        elif specs.gpu_memory_gb >= 4 or (specs.cpu_cores >= 8 and specs.ram_gb >= 16):
            return "standard"
        
        # Basic: Limited resources
        else:
            return "basic"
    
    def _initialize_model_configs(self):
        """Initialize model configurations for different tasks"""
        
        # === EMBEDDING MODELS ===
        self.model_configs["embeddings"] = {
            "basic": ModelConfig(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                memory_requirement_gb=0.5,
                prefers_gpu=False
            ),
            "standard": ModelConfig(
                model_name="sentence-transformers/all-mpnet-base-v2", 
                memory_requirement_gb=1.5,
                prefers_gpu=True,
                fallback_model="sentence-transformers/all-MiniLM-L6-v2"
            ),
            "high": ModelConfig(
                model_name="intfloat/e5-large-v2",
                memory_requirement_gb=3.0,
                min_compute_capability=7.0,
                prefers_gpu=True,
                fallback_model="sentence-transformers/all-mpnet-base-v2"
            ),
            "enterprise": ModelConfig(
                model_name="intfloat/multilingual-e5-large",
                memory_requirement_gb=4.0,
                min_compute_capability=7.5,
                prefers_gpu=True,
                fallback_model="intfloat/e5-large-v2"
            )
        }
        
        # === EMOTION ANALYSIS MODELS ===
        self.model_configs["emotion"] = {
            "basic": ModelConfig(
                model_name="j-hartmann/emotion-english-distilroberta-base",
                memory_requirement_gb=0.8,
                prefers_gpu=False
            ),
            "standard": ModelConfig(
                model_name="j-hartmann/emotion-english-roberta-large",
                memory_requirement_gb=2.0,
                prefers_gpu=True,
                fallback_model="j-hartmann/emotion-english-distilroberta-base"
            ),
            "high": ModelConfig(
                model_name="microsoft/DialoGPT-medium",
                memory_requirement_gb=3.5,
                min_compute_capability=7.0,
                prefers_gpu=True,
                fallback_model="j-hartmann/emotion-english-roberta-large"
            ),
            "enterprise": ModelConfig(
                model_name="microsoft/DialoGPT-large", 
                memory_requirement_gb=6.0,
                min_compute_capability=7.5,
                prefers_gpu=True,
                fallback_model="microsoft/DialoGPT-medium"
            )
        }
        
        # === SENTIMENT ANALYSIS MODELS ===
        self.model_configs["sentiment"] = {
            "basic": ModelConfig(
                model_name="cardiffnlp/twitter-roberta-base-sentiment-latest",
                memory_requirement_gb=1.0,
                prefers_gpu=False
            ),
            "standard": ModelConfig(
                model_name="nlptown/bert-base-multilingual-uncased-sentiment",
                memory_requirement_gb=1.5,
                prefers_gpu=True,
                fallback_model="cardiffnlp/twitter-roberta-base-sentiment-latest"
            ),
            "high": ModelConfig(
                model_name="cardiffnlp/twitter-roberta-base-sentiment-latest",
                memory_requirement_gb=2.5,
                min_compute_capability=7.0,
                prefers_gpu=True,
                fallback_model="nlptown/bert-base-multilingual-uncased-sentiment"
            ),
            "enterprise": ModelConfig(
                model_name="cardiffnlp/twitter-roberta-base-sentiment-latest",
                memory_requirement_gb=4.0,
                min_compute_capability=7.5,
                prefers_gpu=True,
                fallback_model="cardiffnlp/twitter-roberta-base-sentiment-latest"
            )
        }
        
        # === TEXT CLASSIFICATION MODELS ===
        self.model_configs["classification"] = {
            "basic": ModelConfig(
                model_name="facebook/bart-base",
                memory_requirement_gb=1.5,
                prefers_gpu=False
            ),
            "standard": ModelConfig(
                model_name="facebook/bart-large-mnli",
                memory_requirement_gb=3.0,
                prefers_gpu=True,
                fallback_model="facebook/bart-base"
            ),
            "high": ModelConfig(
                model_name="cardiffnlp/twitter-roberta-base-sentiment-latest",
                memory_requirement_gb=3.0,
                min_compute_capability=6.0,
                prefers_gpu=True,
                fallback_model="facebook/bart-large-mnli"
            ),
            "enterprise": ModelConfig(
                model_name="cardiffnlp/twitter-roberta-base-sentiment-latest",
                memory_requirement_gb=4.0,
                min_compute_capability=6.0,
                prefers_gpu=True,
                fallback_model="cardiffnlp/twitter-roberta-base-sentiment-latest"
            )
        }
    
    def get_optimal_model(self, task: str) -> Tuple[str, bool]:
        """Get optimal model for task based on hardware"""
        if not self.specs:
            raise RuntimeError("Hardware not detected. Call detect_hardware() first.")
        
        if task not in self.model_configs:
            raise ValueError(f"Unknown task: {task}")
        
        # Force basic embedding model to match existing ChromaDB dimensions (384)
        if task == "embeddings":
            config = self.model_configs[task]["basic"]  # Always use basic 384-dim model
        else:
            tier = self.specs.performance_tier
            config = self.model_configs[task][tier]
        
        # Check if hardware can handle this model
        if (config.prefers_gpu and 
            (not self.specs.has_gpu or 
             self.specs.gpu_memory_gb < config.memory_requirement_gb or
             self.specs.gpu_compute_capability < config.min_compute_capability)):
            
            # Try fallback
            if config.fallback_model:
                logger.warning(f"Using fallback model {config.fallback_model} for {task}")
                return config.fallback_model, False
        
        # Force CPU mode due to CUDA memory exhaustion
        return config.model_name, False  # Always use CPU until GPU memory is freed
    
    def get_all_optimal_models(self) -> Dict[str, Tuple[str, bool]]:
        """Get optimal models for all tasks"""
        return {
            task: self.get_optimal_model(task)
            for task in self.model_configs.keys()
        }
    
    def get_hardware_summary(self) -> Dict:
        """Get hardware summary for logging/debugging"""
        if not self.specs:
            return {"status": "not_detected"}
        
        return {
            "performance_tier": self.specs.performance_tier,
            "gpu": {
                "available": self.specs.has_gpu,
                "name": self.specs.gpu_name,
                "memory_gb": self.specs.gpu_memory_gb,
                "compute_capability": self.specs.gpu_compute_capability
            },
            "cpu": {
                "cores": self.specs.cpu_cores,
                "threads": self.specs.cpu_threads,
                "freq_ghz": self.specs.cpu_freq_ghz
            },
            "memory_gb": self.specs.ram_gb
        }

# Global instance
hardware_service = HardwareService()
