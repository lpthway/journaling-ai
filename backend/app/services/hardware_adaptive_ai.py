"""
Hardware-Adaptive AI Service

This is the main orchestrator for the hardware-adaptive AI system that automatically
scales AI capabilities based on available hardware resources.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import json
from datetime import datetime

from ..core.hardware_profiler import HardwareProfiler, HardwareTier
from ..core.adaptive_memory_manager import AdaptiveMemoryManager
from ..core.adaptive_feature_manager import AdaptiveFeatureManager, AnalysisType, AnalysisResult
from ..core.runtime_hardware_monitor import RuntimeHardwareMonitor, HardwareChangeEvent

logger = logging.getLogger(__name__)

class HardwareAdaptiveAI:
    """Main hardware-adaptive AI service orchestrator"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or Path(__file__).parent.parent / "core" / "hardware_config.json"
        
        # Core components
        self.hardware_profiler = HardwareProfiler(self.config_path)
        self.memory_manager: Optional[AdaptiveMemoryManager] = None
        self.feature_manager: Optional[AdaptiveFeatureManager] = None
        self.hardware_monitor: Optional[RuntimeHardwareMonitor] = None
        
        # Current state
        self.current_tier: Optional[HardwareTier] = None
        self.initialization_time: Optional[datetime] = None
        self.is_initialized = False
        
        # User notification handlers
        self.user_notification_handlers = []
        
        logger.info("Hardware-Adaptive AI service created")
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the adaptive AI system"""
        logger.info("Initializing Hardware-Adaptive AI system...")
        
        try:
            # Detect hardware and classify tier
            system_info = self.hardware_profiler.detect_system_info()
            self.current_tier, classification_info = self.hardware_profiler.classify_hardware_tier(system_info)
            
            tier_config = classification_info.get('tier_config', {})
            memory_limit = tier_config.get('memory_limit', 100)
            
            # Initialize memory manager
            self.memory_manager = AdaptiveMemoryManager(
                hardware_tier=self.current_tier.value,
                memory_limit_mb=memory_limit
            )
            
            # Initialize feature manager
            self.feature_manager = AdaptiveFeatureManager(
                hardware_profiler=self.hardware_profiler,
                memory_manager=self.memory_manager
            )
            
            # Initialize hardware monitor
            self.hardware_monitor = RuntimeHardwareMonitor(
                hardware_profiler=self.hardware_profiler,
                memory_manager=self.memory_manager,
                feature_manager=self.feature_manager
            )
            
            # Set up callbacks
            self.hardware_monitor.add_change_callback(self._on_hardware_change)
            self.hardware_monitor.add_notification_callback(self._on_user_notification)
            
            # Start monitoring
            await self.hardware_monitor.start_monitoring()
            
            self.initialization_time = datetime.now()
            self.is_initialized = True
            
            initialization_result = {
                "status": "success",
                "tier": self.current_tier.value,
                "available_features": self.feature_manager.get_available_features(),
                "memory_limit_mb": memory_limit,
                "system_info": system_info,
                "reasoning": classification_info.get('reasoning', ''),
                "initialization_time": self.initialization_time.isoformat()
            }
            
            logger.info(f"Hardware-Adaptive AI initialized successfully with tier: {self.current_tier.value}")
            return initialization_result
            
        except Exception as e:
            logger.error(f"Failed to initialize Hardware-Adaptive AI: {e}")
            return {
                "status": "error",
                "error": str(e),
                "fallback_tier": "MINIMAL"
            }
    
    async def analyze_text(self, text: str, analysis_type: Union[str, AnalysisType] = 'auto',
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze text using best available method for current hardware"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            result = await self.feature_manager.analyze_text(text, analysis_type, context)
            
            return {
                "success": True,
                "analysis_type": result.analysis_type.value,
                "result": result.result,
                "confidence": result.confidence,
                "method_used": result.method_used,
                "processing_time": result.processing_time,
                "hardware_tier": result.hardware_tier,
                "fallback_used": result.fallback_used,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error in text analysis: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_result": await self._emergency_fallback_analysis(text)
            }
    
    async def batch_analyze(self, texts: List[str], analysis_type: Union[str, AnalysisType] = 'auto') -> List[Dict[str, Any]]:
        """Analyze multiple texts efficiently"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            results = await self.feature_manager.batch_analyze(texts, analysis_type)
            
            return [
                {
                    "success": True,
                    "analysis_type": result.analysis_type.value,
                    "result": result.result,
                    "confidence": result.confidence,
                    "method_used": result.method_used,
                    "processing_time": result.processing_time,
                    "hardware_tier": result.hardware_tier,
                    "fallback_used": result.fallback_used
                }
                for result in results
            ]
        
        except Exception as e:
            logger.error(f"Error in batch analysis: {e}")
            # Return individual fallback results
            fallback_results = []
            for text in texts:
                fallback_result = await self._emergency_fallback_analysis(text)
                fallback_results.append({
                    "success": False,
                    "error": str(e),
                    "fallback_result": fallback_result
                })
            return fallback_results
    
    async def _emergency_fallback_analysis(self, text: str) -> Dict[str, Any]:
        """Emergency fallback when all other methods fail"""
        try:
            # Basic text statistics that always work
            words = text.split()
            sentences = text.split('.')
            
            return {
                "analysis_type": "emergency_stats",
                "word_count": len(words),
                "sentence_count": len([s for s in sentences if s.strip()]),
                "character_count": len(text),
                "method": "emergency_fallback"
            }
        except Exception:
            return {
                "analysis_type": "emergency_stats",
                "error": "Complete analysis failure",
                "method": "emergency_fallback"
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        if not self.is_initialized:
            return {
                "status": "not_initialized",
                "message": "System not yet initialized"
            }
        
        feature_status = self.feature_manager.get_feature_status()
        memory_info = self.memory_manager.get_memory_info()
        monitoring_status = self.hardware_monitor.get_monitoring_status()
        
        return {
            "status": "operational",
            "initialization_time": self.initialization_time.isoformat(),
            "current_tier": self.current_tier.value,
            "hardware_info": self.hardware_profiler.detect_system_info(),
            "feature_status": feature_status,
            "memory_info": memory_info,
            "monitoring_status": monitoring_status,
            "uptime_seconds": (datetime.now() - self.initialization_time).total_seconds()
        }
    
    def get_available_features(self) -> Dict[str, Any]:
        """Get currently available features with detailed information"""
        if not self.is_initialized:
            return {"error": "System not initialized"}
        
        feature_status = self.feature_manager.get_feature_status()
        tier_config = self.hardware_profiler.get_tier_capabilities(self.current_tier)
        
        return {
            "current_tier": self.current_tier.value,
            "available_features": feature_status["available_features"],
            "feature_analysis": feature_status["feature_analysis"],
            "tier_description": tier_config.get("description", ""),
            "memory_limit_mb": tier_config.get("memory_limit", 100),
            "models_available": list(tier_config.get("models", {}).keys())
        }
    
    async def force_hardware_refresh(self) -> Dict[str, Any]:
        """Force a hardware refresh and capability update"""
        if not self.is_initialized:
            return {"error": "System not initialized"}
        
        logger.info("Forcing hardware refresh")
        
        try:
            # Reload hardware configuration
            config_reloaded = self.hardware_profiler.reload_config()
            
            # Force hardware check
            check_result = await self.hardware_monitor.force_hardware_check()
            
            # Get updated status
            new_status = self.get_system_status()
            
            return {
                "success": True,
                "config_reloaded": config_reloaded,
                "hardware_check": check_result,
                "new_status": new_status
            }
        
        except Exception as e:
            logger.error(f"Error in hardware refresh: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def suggest_optimizations(self) -> Dict[str, Any]:
        """Suggest system optimizations based on current hardware"""
        if not self.is_initialized:
            return {"error": "System not initialized"}
        
        suggestions = []
        system_info = self.hardware_profiler.detect_system_info()
        
        # RAM suggestions
        ram_gb = system_info["ram"]["total_gb"]
        if ram_gb < 4:
            suggestions.append({
                "type": "memory_upgrade",
                "priority": "high",
                "description": f"Consider upgrading RAM from {ram_gb:.1f}GB to at least 8GB for better AI performance",
                "expected_improvement": "Unlock STANDARD tier features including advanced sentiment analysis and topic modeling"
            })
        elif ram_gb < 8:
            suggestions.append({
                "type": "memory_upgrade",
                "priority": "medium",
                "description": f"Upgrade RAM from {ram_gb:.1f}GB to 16GB+ for premium AI features",
                "expected_improvement": "Enable HIGH_END tier with semantic search and auto-summarization"
            })
        
        # GPU suggestions
        gpu_info = system_info["gpu"]
        if not gpu_info["has_gpu"]:
            suggestions.append({
                "type": "gpu_addition",
                "priority": "medium",
                "description": "Add a dedicated GPU with 4GB+ memory for significant AI acceleration",
                "expected_improvement": "Faster model loading and processing, especially for complex analyses"
            })
        elif gpu_info["total_memory_mb"] < 4096:
            suggestions.append({
                "type": "gpu_upgrade",
                "priority": "low",
                "description": f"Consider GPU with more than {gpu_info['total_memory_mb']}MB for advanced features",
                "expected_improvement": "Better support for large models and batch processing"
            })
        
        # Storage suggestions
        storage_info = system_info["storage"]
        if storage_info["free_gb"] < 5:
            suggestions.append({
                "type": "storage_cleanup",
                "priority": "high",
                "description": f"Free up disk space (currently {storage_info['free_gb']:.1f}GB free)",
                "expected_improvement": "Ensure adequate space for AI model caching"
            })
        
        return {
            "current_tier": self.current_tier.value,
            "suggestions": suggestions,
            "system_score": self._calculate_system_score(system_info),
            "next_tier_requirements": self._get_next_tier_requirements()
        }
    
    def _calculate_system_score(self, system_info: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall system performance score"""
        ram_score = min(100, (system_info["ram"]["total_gb"] / 16) * 100)
        
        gpu_info = system_info["gpu"]
        if gpu_info["has_gpu"]:
            gpu_score = min(100, (gpu_info["total_memory_mb"] / 8192) * 100)
        else:
            gpu_score = 0
        
        cpu_cores = system_info["cpu"]["cores"]
        cpu_score = min(100, (cpu_cores / 8) * 100)
        
        overall_score = (ram_score * 0.4 + gpu_score * 0.4 + cpu_score * 0.2)
        
        return {
            "overall": round(overall_score, 1),
            "ram": round(ram_score, 1),
            "gpu": round(gpu_score, 1),
            "cpu": round(cpu_score, 1)
        }
    
    def _get_next_tier_requirements(self) -> Dict[str, Any]:
        """Get requirements for the next hardware tier"""
        tier_order = [HardwareTier.MINIMAL, HardwareTier.BASIC, HardwareTier.STANDARD, HardwareTier.HIGH_END]
        
        try:
            current_index = tier_order.index(self.current_tier)
            if current_index < len(tier_order) - 1:
                next_tier = tier_order[current_index + 1]
                next_config = self.hardware_profiler.get_tier_capabilities(next_tier)
                
                return {
                    "next_tier": next_tier.value,
                    "min_ram_gb": next_config.get("min_ram_gb", 0),
                    "min_gpu_memory_mb": next_config.get("min_gpu_memory_mb", 0),
                    "new_features": next_config.get("features", []),
                    "description": next_config.get("description", "")
                }
            else:
                return {
                    "message": "You're already at the highest tier!",
                    "current_tier": self.current_tier.value
                }
        except ValueError:
            return {"error": "Could not determine next tier"}
    
    def add_user_notification_handler(self, handler):
        """Add handler for user notifications"""
        self.user_notification_handlers.append(handler)
    
    async def _on_hardware_change(self, change_event: HardwareChangeEvent):
        """Handle hardware change events"""
        logger.info(f"Hardware change detected: {change_event.impact_description}")
        
        # Update current tier
        self.current_tier = change_event.new_tier
        
        # Log the change for analytics
        self._log_hardware_change(change_event)
    
    async def _on_user_notification(self, notification_type: str, data: Dict[str, Any]):
        """Handle user notification requests"""
        for handler in self.user_notification_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(notification_type, data)
                else:
                    handler(notification_type, data)
            except Exception as e:
                logger.error(f"Error in user notification handler: {e}")
    
    def _log_hardware_change(self, change_event: HardwareChangeEvent):
        """Log hardware changes for analytics and debugging"""
        log_entry = {
            "timestamp": change_event.timestamp.isoformat(),
            "change_type": change_event.change_type.value,
            "old_tier": change_event.old_tier.value,
            "new_tier": change_event.new_tier.value,
            "impact": change_event.impact_description
        }
        
        # This could be extended to write to a log file or database
        logger.info(f"Hardware change logged: {log_entry}")
    
    async def shutdown(self):
        """Clean shutdown of the adaptive AI system"""
        logger.info("Shutting down Hardware-Adaptive AI system")
        
        try:
            if self.hardware_monitor:
                await self.hardware_monitor.stop_monitoring()
            
            if self.memory_manager:
                await self.memory_manager.shutdown()
            
            self.is_initialized = False
            logger.info("Hardware-Adaptive AI system shutdown complete")
        
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

# Global instance for easy access
adaptive_ai: Optional[HardwareAdaptiveAI] = None

async def get_adaptive_ai() -> HardwareAdaptiveAI:
    """Get or create the global adaptive AI instance"""
    global adaptive_ai
    
    if adaptive_ai is None:
        adaptive_ai = HardwareAdaptiveAI()
        await adaptive_ai.initialize()
    
    return adaptive_ai

async def analyze_text_adaptive(text: str, analysis_type: str = 'auto', 
                              context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convenience function for adaptive text analysis"""
    ai = await get_adaptive_ai()
    return await ai.analyze_text(text, analysis_type, context)

async def get_system_capabilities() -> Dict[str, Any]:
    """Convenience function to get current system capabilities"""
    ai = await get_adaptive_ai()
    return ai.get_available_features()
