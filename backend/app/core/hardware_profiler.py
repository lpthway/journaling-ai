"""
Hardware Detection and Classification System

This module detects system hardware capabilities and classifies them into
appropriate tiers for AI model deployment.
"""

import psutil
import platform
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum
import subprocess
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class HardwareTier(Enum):
    """Hardware capability tiers"""
    MINIMAL = "MINIMAL"
    BASIC = "BASIC"  
    STANDARD = "STANDARD"
    HIGH_END = "HIGH_END"

class HardwareProfiler:
    """Detect and classify hardware capabilities"""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = Path(__file__).parent / "hardware_config.json"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._gpu_info_cache = None
        
    def _load_config(self) -> Dict[str, Any]:
        """Load hardware configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load hardware config: {e}")
            # Return minimal fallback config
            return {
                "hardware_tiers": {
                    "MINIMAL": {"memory_limit": 100, "features": ["basic_stats"]}
                }
            }
    
    def detect_system_info(self) -> Dict[str, Any]:
        """Detect comprehensive system information"""
        info = {
            "ram": self._detect_ram(),
            "cpu": self._detect_cpu(),
            "gpu": self._detect_gpu_enhanced(),  # Enhanced GPU detection
            "storage": self._detect_storage(),
            "platform": self._detect_platform()
        }
        
        logger.info(f"Detected hardware: {info}")
        return info
    
    def _detect_ram(self) -> Dict[str, Any]:
        """Detect RAM information"""
        try:
            memory = psutil.virtual_memory()
            return {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_percent": memory.percent
            }
        except Exception as e:
            logger.error(f"Failed to detect RAM: {e}")
            return {"total_gb": 2.0, "available_gb": 1.0, "used_percent": 50.0}
    
    def _detect_cpu(self) -> Dict[str, Any]:
        """Detect CPU information"""
        try:
            return {
                "cores": psutil.cpu_count(logical=False),
                "logical_cores": psutil.cpu_count(logical=True),
                "frequency_mhz": psutil.cpu_freq().max if psutil.cpu_freq() else 0,
                "usage_percent": psutil.cpu_percent(interval=1)
            }
        except Exception as e:
            logger.error(f"Failed to detect CPU: {e}")
            return {"cores": 2, "logical_cores": 4, "frequency_mhz": 2000, "usage_percent": 50.0}
    
    def _detect_gpu(self) -> Dict[str, Any]:
        """Detect GPU information with multiple fallback methods"""
        if self._gpu_info_cache is not None:
            return self._gpu_info_cache
            
        gpu_info = {
            "has_gpu": False,
            "total_memory_mb": 0,
            "available_memory_mb": 0,
            "gpu_names": [],
            "cuda_available": False,
            "driver_version": None
        }
        
        # Method 1: Try nvidia-smi
        try:
            gpu_info.update(self._detect_gpu_nvidia_smi())
            if gpu_info["has_gpu"]:
                self._gpu_info_cache = gpu_info
                return gpu_info
        except Exception as e:
            logger.debug(f"nvidia-smi detection failed: {e}")
        
        # Method 2: Try PyTorch CUDA
        try:
            gpu_info.update(self._detect_gpu_pytorch())
            if gpu_info["has_gpu"]:
                self._gpu_info_cache = gpu_info
                return gpu_info
        except Exception as e:
            logger.debug(f"PyTorch CUDA detection failed: {e}")
        
        # Method 3: Try system commands
        try:
            gpu_info.update(self._detect_gpu_system())
        except Exception as e:
            logger.debug(f"System GPU detection failed: {e}")
        
        self._gpu_info_cache = gpu_info
        return gpu_info
    
    def _detect_gpu_enhanced(self) -> Dict[str, Any]:
        """Enhanced GPU detection with detailed memory analysis and process monitoring"""
        # Start with basic GPU detection
        basic_gpu_info = self._detect_gpu()
        
        # Add enhanced memory analysis and process monitoring
        enhanced_info = basic_gpu_info.copy()
        
        if basic_gpu_info.get("has_gpu", False):
            # Add detailed GPU memory analysis
            detailed_memory = self._get_detailed_gpu_memory()
            enhanced_info["detailed_memory"] = detailed_memory
            
            # Add process conflict detection
            process_conflicts = self._detect_gpu_process_conflicts()
            enhanced_info["process_conflicts"] = process_conflicts
            
            # Add memory pressure assessment
            memory_pressure = self._assess_memory_pressure(detailed_memory)
            enhanced_info["memory_pressure"] = memory_pressure
            enhanced_info["safe_to_load_models"] = memory_pressure != "CRITICAL"
            
            # Update available memory based on detailed analysis
            enhanced_info["available_memory_mb"] = detailed_memory.get("available_for_models", 0)
        
        return enhanced_info
    
    def _get_detailed_gpu_memory(self) -> Dict[str, Any]:
        """Use nvidia-smi and PyTorch to get comprehensive GPU memory info"""
        memory_info = {
            "total_mb": 0,
            "used_mb": 0,
            "free_mb": 0,
            "usage_percent": 0,
            "available_for_models": 0,
            "pytorch_memory": {},
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        try:
            # System-level memory info from nvidia-smi
            result = subprocess.run([
                "nvidia-smi", "--query-gpu=memory.total,memory.used,memory.free",
                "--format=csv,noheader,nounits"
            ], capture_output=True, text=True, check=True, timeout=10)
            
            line = result.stdout.strip()
            if line:
                parts = [int(p.strip()) for p in line.split(',')]
                total_mb, used_mb, free_mb = parts
                
                usage_percent = (used_mb / total_mb) * 100
                # Reserve 500MB safety buffer for system stability
                available_for_models = max(0, free_mb - 500)
                
                memory_info.update({
                    "total_mb": total_mb,
                    "used_mb": used_mb,
                    "free_mb": free_mb,
                    "usage_percent": round(usage_percent, 1),
                    "available_for_models": available_for_models
                })
        
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.warning(f"Could not get detailed GPU memory from nvidia-smi: {e}")
        
        # PyTorch-specific memory info (if available)
        try:
            import torch
            if torch.cuda.is_available():
                memory_info["pytorch_memory"] = {
                    "allocated_mb": torch.cuda.memory_allocated() // (1024 * 1024),
                    "reserved_mb": torch.cuda.memory_reserved() // (1024 * 1024),
                    "max_allocated_mb": torch.cuda.max_memory_allocated() // (1024 * 1024),
                    "max_reserved_mb": torch.cuda.max_memory_reserved() // (1024 * 1024)
                }
        except ImportError:
            logger.debug("PyTorch not available for memory analysis")
        except Exception as e:
            logger.warning(f"Could not get PyTorch memory info: {e}")
        
        return memory_info
    
    def _detect_gpu_process_conflicts(self) -> List[Dict[str, Any]]:
        """Detect potentially conflicting GPU processes"""
        try:
            result = subprocess.run([
                "nvidia-smi", "--query-compute-apps=pid,process_name,used_memory",
                "--format=csv,noheader"
            ], capture_output=True, text=True, check=True, timeout=10)
            
            gpu_processes = []
            current_pid = os.getpid()
            project_path = "/home/abrasko/Projects/journaling-ai"
            
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
                            "is_current": pid == current_pid,
                            "is_python": "python" in process_name.lower()
                        }
                        
                        # Try to get more process details
                        try:
                            proc = psutil.Process(pid)
                            cmdline = proc.cmdline()
                            process_info.update({
                                "cmdline": cmdline,
                                "cwd": proc.cwd(),
                                "is_journaling_ai": project_path in str(cmdline) or project_path in proc.cwd(),
                                "is_duplicate": (project_path in str(cmdline) or project_path in proc.cwd()) and pid != current_pid
                            })
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            process_info.update({
                                "cmdline": [],
                                "cwd": "",
                                "is_journaling_ai": False,
                                "is_duplicate": False
                            })
                        
                        gpu_processes.append(process_info)
            
            return gpu_processes
        
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.warning(f"Could not detect GPU processes: {e}")
            return []
    
    def _assess_memory_pressure(self, gpu_memory: Dict[str, Any]) -> str:
        """Assess GPU memory pressure level"""
        usage_percent = gpu_memory.get("usage_percent", 0)
        available_mb = gpu_memory.get("available_for_models", 0)
        
        if usage_percent > 95 or available_mb < 200:
            return "CRITICAL"  # Cannot load any models
        elif usage_percent > 85 or available_mb < 1000:
            return "HIGH"      # Can only load small models
        elif usage_percent > 70 or available_mb < 2000:
            return "MEDIUM"    # Limited model loading
        else:
            return "LOW"       # Normal operation

    def get_current_gpu_status(self) -> Dict[str, Any]:
        """Get real-time GPU status for monitoring"""
        return self._detect_gpu_enhanced()
    
    def _detect_gpu_nvidia_smi(self) -> Dict[str, Any]:
        """Detect GPU using nvidia-smi"""
        try:
            result = subprocess.run([
                'nvidia-smi', 
                '--query-gpu=name,memory.total,memory.free,driver_version',
                '--format=csv,noheader,nounits'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                gpu_names = []
                total_memory = 0
                available_memory = 0
                driver_version = None
                
                for line in lines:
                    if line.strip():
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 4:
                            gpu_names.append(parts[0])
                            total_memory += int(parts[1])
                            available_memory += int(parts[2])
                            if driver_version is None:
                                driver_version = parts[3]
                
                if gpu_names:
                    return {
                        "has_gpu": True,
                        "total_memory_mb": total_memory,
                        "available_memory_mb": available_memory,
                        "gpu_names": gpu_names,
                        "cuda_available": True,
                        "driver_version": driver_version
                    }
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            pass
        
        return {"has_gpu": False}
    
    def _detect_gpu_pytorch(self) -> Dict[str, Any]:
        """Detect GPU using PyTorch"""
        try:
            import torch
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                gpu_names = []
                total_memory = 0
                available_memory = 0
                
                for i in range(gpu_count):
                    props = torch.cuda.get_device_properties(i)
                    gpu_names.append(props.name)
                    total_memory += props.total_memory // (1024 * 1024)  # Convert to MB
                    
                    # Get available memory
                    torch.cuda.set_device(i)
                    torch.cuda.empty_cache()
                    available_memory += (torch.cuda.get_device_properties(i).total_memory - 
                                       torch.cuda.memory_allocated(i)) // (1024 * 1024)
                
                return {
                    "has_gpu": True,
                    "total_memory_mb": total_memory,
                    "available_memory_mb": available_memory,
                    "gpu_names": gpu_names,
                    "cuda_available": True,
                    "driver_version": torch.version.cuda
                }
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"PyTorch GPU detection error: {e}")
        
        return {"has_gpu": False}
    
    def _detect_gpu_system(self) -> Dict[str, Any]:
        """Detect GPU using system commands as fallback"""
        gpu_info = {"has_gpu": False}
        
        try:
            # Try lspci on Linux
            if platform.system() == "Linux":
                result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    gpu_lines = [line for line in result.stdout.split('\n') 
                               if 'VGA' in line or 'Display' in line or 'NVIDIA' in line or 'AMD' in line]
                    if gpu_lines:
                        gpu_info["has_gpu"] = True
                        gpu_info["gpu_names"] = [line.split(':')[-1].strip() for line in gpu_lines]
                        # Cannot reliably detect memory without specific drivers
                        gpu_info["total_memory_mb"] = 0
                        gpu_info["available_memory_mb"] = 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return gpu_info
    
    def _detect_storage(self) -> Dict[str, Any]:
        """Detect storage information"""
        try:
            disk_usage = psutil.disk_usage('/')
            return {
                "total_gb": round(disk_usage.total / (1024**3), 2),
                "free_gb": round(disk_usage.free / (1024**3), 2),
                "used_percent": round((disk_usage.used / disk_usage.total) * 100, 2)
            }
        except Exception as e:
            logger.error(f"Failed to detect storage: {e}")
            return {"total_gb": 50.0, "free_gb": 10.0, "used_percent": 80.0}
    
    def _detect_platform(self) -> Dict[str, Any]:
        """Detect platform information"""
        try:
            return {
                "system": platform.system(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor()
            }
        except Exception as e:
            logger.error(f"Failed to detect platform: {e}")
            return {"system": "Unknown", "version": "", "machine": "", "processor": ""}
    
    def classify_hardware_tier(self, system_info: Optional[Dict[str, Any]] = None) -> Tuple[HardwareTier, Dict[str, Any]]:
        """Classify hardware into appropriate tier with detailed reasoning"""
        if system_info is None:
            system_info = self.detect_system_info()
        
        ram_gb = system_info["ram"]["total_gb"]
        gpu_memory_mb = system_info["gpu"]["total_memory_mb"]
        has_gpu = system_info["gpu"]["has_gpu"]
        
        # Classification logic with detailed scoring
        score_details = {
            "ram_score": self._score_ram(ram_gb),
            "gpu_score": self._score_gpu(gpu_memory_mb, has_gpu),
            "cpu_score": self._score_cpu(system_info["cpu"]),
            "total_score": 0
        }
        
        score_details["total_score"] = (
            score_details["ram_score"] * 0.4 +
            score_details["gpu_score"] * 0.4 +
            score_details["cpu_score"] * 0.2
        )
        
        # Determine tier based on score and hard constraints
        suggested_tier = self._determine_tier_from_score(score_details["total_score"], ram_gb, gpu_memory_mb)
        
        # CRITICAL: Adjust tier based on actual GPU memory availability and pressure
        gpu_info = system_info.get("gpu", {})
        reasoning = []
        
        if gpu_info.get("has_gpu", False):
            memory_pressure = gpu_info.get("memory_pressure", "LOW")
            available_mb = gpu_info.get("detailed_memory", {}).get("available_for_models", gpu_memory_mb)
            process_conflicts = gpu_info.get("process_conflicts", [])
            
            # Add memory pressure reasoning
            reasoning.append(f"GPU memory pressure: {memory_pressure}")
            reasoning.append(f"Available GPU memory: {available_mb}MB")
            
            # Check for process conflicts
            duplicate_processes = [p for p in process_conflicts if p.get("is_duplicate", False)]
            if duplicate_processes:
                reasoning.append(f"🚨 {len(duplicate_processes)} duplicate processes detected using GPU memory")
            
            # Force tier downgrade if memory pressure too high
            if memory_pressure == "CRITICAL":
                reasoning.append("🚨 CRITICAL GPU memory pressure - forcing MINIMAL tier")
                suggested_tier = HardwareTier.MINIMAL
            elif memory_pressure == "HIGH":
                reasoning.append("⚠️ HIGH GPU memory pressure - reducing tier capabilities")
                if suggested_tier == HardwareTier.HIGH_END:
                    suggested_tier = HardwareTier.STANDARD
                elif suggested_tier == HardwareTier.STANDARD:
                    suggested_tier = HardwareTier.BASIC
            
            # Additional check: If less than 1GB available, force lower tier
            if available_mb < 1000:
                reasoning.append(f"⚠️ Low GPU memory available ({available_mb}MB) - limiting model size")
                if suggested_tier in [HardwareTier.HIGH_END, HardwareTier.STANDARD]:
                    suggested_tier = HardwareTier.BASIC
        
        # Get tier configuration
        tier_config = self.config["hardware_tiers"].get(suggested_tier.value, {})
        
        # Generate final reasoning
        base_reasoning = self._generate_reasoning(suggested_tier, score_details, ram_gb, gpu_memory_mb, has_gpu)
        if reasoning:
            final_reasoning = base_reasoning + " | " + " | ".join(reasoning)
        else:
            final_reasoning = base_reasoning
        
        classification_info = {
            "tier": suggested_tier,
            "score_details": score_details,
            "system_info": system_info,
            "tier_config": tier_config,
            "reasoning": final_reasoning,
            "gpu_memory_available": available_mb if has_gpu else 0,
            "memory_pressure_level": memory_pressure if has_gpu else "N/A",
            "process_conflicts_detected": len(duplicate_processes) if has_gpu else 0
        }
        
        logger.info(f"Hardware classified as {suggested_tier.value}: {final_reasoning}")
        return suggested_tier, classification_info
    
    def _score_ram(self, ram_gb: float) -> float:
        """Score RAM capacity (0-100)"""
        if ram_gb < 2:
            return 0
        elif ram_gb < 4:
            return 25
        elif ram_gb < 8:
            return 50
        elif ram_gb < 16:
            return 75
        else:
            return 100
    
    def _score_gpu(self, gpu_memory_mb: int, has_gpu: bool) -> float:
        """Score GPU capability (0-100)"""
        if not has_gpu or gpu_memory_mb == 0:
            return 0
        elif gpu_memory_mb < 2048:
            return 25
        elif gpu_memory_mb < 6144:
            return 50
        elif gpu_memory_mb < 12288:
            return 75
        else:
            return 100
    
    def _score_cpu(self, cpu_info: Dict[str, Any]) -> float:
        """Score CPU capability (0-100)"""
        cores = cpu_info.get("cores", 2)
        frequency = cpu_info.get("frequency_mhz", 2000)
        
        core_score = min(cores / 8 * 50, 50)  # Max 50 points for cores
        freq_score = min(frequency / 3000 * 50, 50)  # Max 50 points for frequency
        
        return core_score + freq_score
    
    def _determine_tier_from_score(self, total_score: float, ram_gb: float, gpu_memory_mb: int) -> HardwareTier:
        """Determine tier from score with hard constraints"""
        # Hard constraints override score-based classification
        if ram_gb < 3:
            return HardwareTier.MINIMAL
        elif ram_gb < 7:
            return HardwareTier.BASIC
        elif ram_gb < 15:
            return HardwareTier.STANDARD
        else:
            # For high-end, prefer systems with substantial GPU memory
            if gpu_memory_mb >= 4096:
                return HardwareTier.HIGH_END
            else:
                return HardwareTier.STANDARD
    
    def _generate_reasoning(self, tier: HardwareTier, score_details: Dict[str, Any], 
                          ram_gb: float, gpu_memory_mb: int, has_gpu: bool) -> str:
        """Generate human-readable reasoning for tier classification"""
        reasoning_parts = [
            f"RAM: {ram_gb:.1f}GB (score: {score_details['ram_score']:.0f})",
            f"GPU: {'Yes' if has_gpu else 'No'}" + (f" with {gpu_memory_mb}MB" if has_gpu else "") + 
            f" (score: {score_details['gpu_score']:.0f})",
            f"CPU score: {score_details['cpu_score']:.0f}",
            f"Total score: {score_details['total_score']:.0f}"
        ]
        return " | ".join(reasoning_parts)
    
    def get_tier_capabilities(self, tier: HardwareTier) -> Dict[str, Any]:
        """Get capabilities for a specific tier"""
        return self.config["hardware_tiers"].get(tier.value, {})
    
    def get_available_features(self, tier: HardwareTier) -> list:
        """Get available features for a tier"""
        tier_config = self.get_tier_capabilities(tier)
        return tier_config.get("features", [])
    
    def get_memory_limit(self, tier: HardwareTier) -> int:
        """Get memory limit for a tier in MB"""
        tier_config = self.get_tier_capabilities(tier)
        return tier_config.get("memory_limit", 100)
    
    def reload_config(self) -> bool:
        """Reload hardware configuration from file"""
        try:
            self.config = self._load_config()
            self._gpu_info_cache = None  # Clear cache to re-detect GPU
            logger.info("Hardware configuration reloaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to reload hardware config: {e}")
            return False
