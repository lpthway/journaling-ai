"""
Runtime Hardware Monitoring System

This module continuously monitors hardware changes and adapts AI capabilities
in real-time without requiring application restart.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .hardware_profiler import HardwareProfiler, HardwareTier
from .adaptive_memory_manager import AdaptiveMemoryManager
from .adaptive_feature_manager import AdaptiveFeatureManager

logger = logging.getLogger(__name__)

class HardwareChangeType(Enum):
    """Types of hardware changes"""
    MEMORY_UPGRADE = "memory_upgrade"
    MEMORY_DOWNGRADE = "memory_downgrade"
    GPU_ADDED = "gpu_added"
    GPU_REMOVED = "gpu_removed"
    GPU_MEMORY_CHANGE = "gpu_memory_change"
    TIER_UPGRADE = "tier_upgrade"
    TIER_DOWNGRADE = "tier_downgrade"

@dataclass
class HardwareChangeEvent:
    """Hardware change event information"""
    change_type: HardwareChangeType
    timestamp: datetime
    old_info: Dict[str, Any]
    new_info: Dict[str, Any]
    old_tier: HardwareTier
    new_tier: HardwareTier
    impact_description: str

class RuntimeHardwareMonitor:
    """Monitor hardware changes and adapt capabilities"""
    
    def __init__(self, hardware_profiler: HardwareProfiler, 
                 memory_manager: AdaptiveMemoryManager,
                 feature_manager: AdaptiveFeatureManager):
        self.hardware_profiler = hardware_profiler
        self.memory_manager = memory_manager
        self.feature_manager = feature_manager
        
        # Monitoring settings
        self.check_interval = 300  # 5 minutes
        self.significant_change_threshold = 0.1  # 10% change
        
        # Current state
        self.current_hardware_info = None
        self.current_tier = None
        self.last_check_time = None
        
        # Event handling
        self.change_callbacks: List[Callable[[HardwareChangeEvent], None]] = []
        self.notification_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        
        # Background task
        self.monitor_task: Optional[asyncio.Task] = None
        self.is_monitoring = False
        
        # Initialize current state
        self._initialize_current_state()
    
    def _initialize_current_state(self):
        """Initialize current hardware state"""
        try:
            self.current_hardware_info = self.hardware_profiler.detect_system_info()
            self.current_tier, _ = self.hardware_profiler.classify_hardware_tier(self.current_hardware_info)
            self.last_check_time = datetime.now()
            logger.info(f"Hardware monitor initialized with tier: {self.current_tier.value}")
        except Exception as e:
            logger.error(f"Failed to initialize hardware state: {e}")
    
    def add_change_callback(self, callback: Callable[[HardwareChangeEvent], None]):
        """Add callback for hardware change events"""
        self.change_callbacks.append(callback)
    
    def add_notification_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Add callback for user notifications"""
        self.notification_callbacks.append(callback)
    
    async def start_monitoring(self):
        """Start continuous hardware monitoring"""
        if self.is_monitoring:
            logger.warning("Hardware monitoring already running")
            return
        
        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Hardware monitoring started")
    
    async def stop_monitoring(self):
        """Stop hardware monitoring"""
        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Hardware monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                await asyncio.sleep(self.check_interval)
                await self._check_hardware_changes()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in hardware monitoring loop: {e}")
                # Continue monitoring despite errors
                await asyncio.sleep(self.check_interval)
    
    async def _check_hardware_changes(self):
        """Check for hardware changes and handle them"""
        try:
            # Get current hardware info
            new_hardware_info = self.hardware_profiler.detect_system_info()
            new_tier, _ = self.hardware_profiler.classify_hardware_tier(new_hardware_info)
            
            # Detect changes
            changes = self._detect_changes(self.current_hardware_info, new_hardware_info)
            
            if changes:
                logger.info(f"Hardware changes detected: {[change.change_type.value for change in changes]}")
                
                # Handle each change
                for change in changes:
                    await self._handle_hardware_change(change)
                    
                    # Notify callbacks
                    for callback in self.change_callbacks:
                        try:
                            await self._safe_callback(callback, change)
                        except Exception as e:
                            logger.error(f"Error in change callback: {e}")
                
                # Update current state
                self.current_hardware_info = new_hardware_info
                self.current_tier = new_tier
            
            self.last_check_time = datetime.now()
            
        except Exception as e:
            logger.error(f"Error checking hardware changes: {e}")
    
    def _detect_changes(self, old_info: Dict[str, Any], new_info: Dict[str, Any]) -> List[HardwareChangeEvent]:
        """Detect significant hardware changes"""
        changes = []
        
        if not old_info or not new_info:
            return changes
        
        current_time = datetime.now()
        old_tier, _ = self.hardware_profiler.classify_hardware_tier(old_info)
        new_tier, _ = self.hardware_profiler.classify_hardware_tier(new_info)
        
        # Check RAM changes
        old_ram = old_info.get('ram', {}).get('total_gb', 0)
        new_ram = new_info.get('ram', {}).get('total_gb', 0)
        
        if abs(new_ram - old_ram) > old_ram * self.significant_change_threshold:
            change_type = HardwareChangeType.MEMORY_UPGRADE if new_ram > old_ram else HardwareChangeType.MEMORY_DOWNGRADE
            changes.append(HardwareChangeEvent(
                change_type=change_type,
                timestamp=current_time,
                old_info=old_info,
                new_info=new_info,
                old_tier=old_tier,
                new_tier=new_tier,
                impact_description=f"RAM changed from {old_ram:.1f}GB to {new_ram:.1f}GB"
            ))
        
        # Check GPU changes
        old_gpu = old_info.get('gpu', {})
        new_gpu = new_info.get('gpu', {})
        
        old_has_gpu = old_gpu.get('has_gpu', False)
        new_has_gpu = new_gpu.get('has_gpu', False)
        
        if old_has_gpu != new_has_gpu:
            change_type = HardwareChangeType.GPU_ADDED if new_has_gpu else HardwareChangeType.GPU_REMOVED
            changes.append(HardwareChangeEvent(
                change_type=change_type,
                timestamp=current_time,
                old_info=old_info,
                new_info=new_info,
                old_tier=old_tier,
                new_tier=new_tier,
                impact_description=f"GPU {'added' if new_has_gpu else 'removed'}"
            ))
        
        elif old_has_gpu and new_has_gpu:
            old_gpu_mem = old_gpu.get('total_memory_mb', 0)
            new_gpu_mem = new_gpu.get('total_memory_mb', 0)
            
            if abs(new_gpu_mem - old_gpu_mem) > max(old_gpu_mem * self.significant_change_threshold, 512):
                changes.append(HardwareChangeEvent(
                    change_type=HardwareChangeType.GPU_MEMORY_CHANGE,
                    timestamp=current_time,
                    old_info=old_info,
                    new_info=new_info,
                    old_tier=old_tier,
                    new_tier=new_tier,
                    impact_description=f"GPU memory changed from {old_gpu_mem}MB to {new_gpu_mem}MB"
                ))
        
        # Check tier changes
        if old_tier != new_tier:
            change_type = HardwareChangeType.TIER_UPGRADE if new_tier.value > old_tier.value else HardwareChangeType.TIER_DOWNGRADE
            changes.append(HardwareChangeEvent(
                change_type=change_type,
                timestamp=current_time,
                old_info=old_info,
                new_info=new_info,
                old_tier=old_tier,
                new_tier=new_tier,
                impact_description=f"Hardware tier changed from {old_tier.value} to {new_tier.value}"
            ))
        
        return changes
    
    async def _handle_hardware_change(self, change: HardwareChangeEvent):
        """Handle a specific hardware change"""
        logger.info(f"Handling hardware change: {change.impact_description}")
        
        try:
            if change.change_type in [HardwareChangeType.TIER_UPGRADE, HardwareChangeType.TIER_DOWNGRADE]:
                await self._handle_tier_change(change)
            
            elif change.change_type in [HardwareChangeType.MEMORY_UPGRADE, HardwareChangeType.MEMORY_DOWNGRADE]:
                await self._handle_memory_change(change)
            
            elif change.change_type in [HardwareChangeType.GPU_ADDED, HardwareChangeType.GPU_REMOVED, 
                                       HardwareChangeType.GPU_MEMORY_CHANGE]:
                await self._handle_gpu_change(change)
            
            # Send user notification
            await self._send_user_notification(change)
            
        except Exception as e:
            logger.error(f"Error handling hardware change {change.change_type.value}: {e}")
    
    async def _handle_tier_change(self, change: HardwareChangeEvent):
        """Handle hardware tier changes"""
        if change.change_type == HardwareChangeType.TIER_UPGRADE:
            logger.info(f"Hardware tier upgraded: {change.old_tier.value} -> {change.new_tier.value}")
            
            # Update memory manager
            new_memory_limit = self.hardware_profiler.get_memory_limit(change.new_tier)
            self.memory_manager.memory_limit_mb = new_memory_limit
            self.memory_manager.hardware_tier = change.new_tier.value
            
            # Update feature manager
            upgrade_info = await self.feature_manager.upgrade_features(change.new_tier)
            
            # Offer data re-analysis if significant upgrade
            if self._is_significant_upgrade(change.old_tier, change.new_tier):
                await self._offer_data_reanalysis(change, upgrade_info)
        
        else:  # Tier downgrade
            logger.warning(f"Hardware tier downgraded: {change.old_tier.value} -> {change.new_tier.value}")
            
            # Update memory manager with new limits
            new_memory_limit = self.hardware_profiler.get_memory_limit(change.new_tier)
            old_limit = self.memory_manager.memory_limit_mb
            self.memory_manager.memory_limit_mb = new_memory_limit
            self.memory_manager.hardware_tier = change.new_tier.value
            
            # Force cleanup if new limit is lower
            if new_memory_limit < old_limit:
                current_usage = self.memory_manager.memory_usage_mb
                if current_usage > new_memory_limit:
                    cleanup_needed = current_usage - new_memory_limit + 100  # Extra buffer
                    await self.memory_manager._free_memory(cleanup_needed)
            
            # Update feature manager
            self.feature_manager.current_tier = change.new_tier
            self.feature_manager.tier_config = self.hardware_profiler.get_tier_capabilities(change.new_tier)
    
    async def _handle_memory_change(self, change: HardwareChangeEvent):
        """Handle memory changes"""
        new_tier_config = self.hardware_profiler.get_tier_capabilities(change.new_tier)
        new_memory_limit = new_tier_config.get('memory_limit', 100)
        
        old_limit = self.memory_manager.memory_limit_mb
        self.memory_manager.memory_limit_mb = new_memory_limit
        
        if change.change_type == HardwareChangeType.MEMORY_UPGRADE:
            logger.info(f"Memory upgraded: {old_limit}MB -> {new_memory_limit}MB")
            # Memory upgrade allows loading more models - no immediate action needed
            
        else:  # Memory downgrade
            logger.warning(f"Memory downgraded: {old_limit}MB -> {new_memory_limit}MB")
            # May need to free up memory
            current_usage = self.memory_manager.memory_usage_mb
            if current_usage > new_memory_limit:
                cleanup_needed = current_usage - new_memory_limit + 100
                await self.memory_manager._free_memory(cleanup_needed)
    
    async def _handle_gpu_change(self, change: HardwareChangeEvent):
        """Handle GPU changes"""
        if change.change_type == HardwareChangeType.GPU_ADDED:
            logger.info("GPU added - enabling GPU acceleration")
            # GPU models will be loaded automatically when needed
            await self._prepare_gpu_models(change.new_tier)
            
        elif change.change_type == HardwareChangeType.GPU_REMOVED:
            logger.warning("GPU removed - falling back to CPU")
            # Force cleanup of GPU models and switch to CPU
            await self.memory_manager._cleanup_gpu_memory()
            await self.memory_manager._force_cleanup()
            
        else:  # GPU memory change
            logger.info(f"GPU memory changed: {change.impact_description}")
            # Adjust memory limits if needed
            await self._adjust_gpu_memory_usage(change)
    
    async def _prepare_gpu_models(self, tier: HardwareTier):
        """Prepare GPU-optimized models when GPU is detected"""
        try:
            # This would pre-load commonly used models for better performance
            # For now, just log the capability
            logger.info(f"GPU detected - tier {tier.value} models will use GPU acceleration")
        except Exception as e:
            logger.error(f"Error preparing GPU models: {e}")
    
    async def _adjust_gpu_memory_usage(self, change: HardwareChangeEvent):
        """Adjust memory usage based on GPU memory changes"""
        new_gpu_memory = change.new_info.get('gpu', {}).get('total_memory_mb', 0)
        
        # Reserve some GPU memory for the system
        reserved_memory = min(1024, new_gpu_memory * 0.1)  # 10% or 1GB, whichever is smaller
        usable_memory = new_gpu_memory - reserved_memory
        
        # Adjust memory manager if GPU memory is substantial
        if usable_memory > 2048:  # More than 2GB GPU memory
            # Can be more aggressive with model loading
            self.memory_manager.max_concurrent_models = min(5, usable_memory // 1024)
        else:
            # Conservative approach
            self.memory_manager.max_concurrent_models = 2
    
    def _is_significant_upgrade(self, old_tier: HardwareTier, new_tier: HardwareTier) -> bool:
        """Check if upgrade is significant enough to offer re-analysis"""
        tier_values = {
            HardwareTier.MINIMAL: 0,
            HardwareTier.BASIC: 1,
            HardwareTier.STANDARD: 2,
            HardwareTier.HIGH_END: 3
        }
        
        return tier_values[new_tier] - tier_values[old_tier] >= 1
    
    async def _offer_data_reanalysis(self, change: HardwareChangeEvent, upgrade_info: Dict[str, Any]):
        """Offer to re-analyze existing data with new capabilities"""
        notification_data = {
            "type": "hardware_upgrade",
            "title": "New AI Features Available!",
            "message": f"Your hardware has been upgraded to {change.new_tier.value}. "
                      f"New features: {', '.join(upgrade_info.get('added_features', []))}",
            "action": "offer_reanalysis",
            "upgrade_info": upgrade_info
        }
        
        for callback in self.notification_callbacks:
            try:
                await self._safe_callback(callback, "data_reanalysis_offer", notification_data)
            except Exception as e:
                logger.error(f"Error in notification callback: {e}")
    
    async def _send_user_notification(self, change: HardwareChangeEvent):
        """Send user notification about hardware change"""
        if change.change_type == HardwareChangeType.TIER_UPGRADE:
            notification_data = {
                "type": "tier_upgrade",
                "title": "Hardware Capabilities Improved",
                "message": f"Your system has been upgraded from {change.old_tier.value} to {change.new_tier.value}. "
                          f"New AI features are now available!",
                "level": "success"
            }
        elif change.change_type == HardwareChangeType.TIER_DOWNGRADE:
            notification_data = {
                "type": "tier_downgrade", 
                "title": "Hardware Capabilities Changed",
                "message": f"Your system tier changed from {change.old_tier.value} to {change.new_tier.value}. "
                          f"Some features may be temporarily unavailable.",
                "level": "warning"
            }
        elif change.change_type == HardwareChangeType.GPU_ADDED:
            notification_data = {
                "type": "gpu_added",
                "title": "GPU Detected",
                "message": "GPU detected! AI processing will now be accelerated.",
                "level": "success"
            }
        elif change.change_type == HardwareChangeType.GPU_REMOVED:
            notification_data = {
                "type": "gpu_removed",
                "title": "GPU Removed",
                "message": "GPU no longer detected. AI processing will continue on CPU.",
                "level": "info"
            }
        else:
            notification_data = {
                "type": "hardware_change",
                "title": "Hardware Change Detected",
                "message": change.impact_description,
                "level": "info"
            }
        
        for callback in self.notification_callbacks:
            try:
                await self._safe_callback(callback, "hardware_change", notification_data)
            except Exception as e:
                logger.error(f"Error in notification callback: {e}")
    
    async def _safe_callback(self, callback: Callable, *args):
        """Safely execute callback with error handling"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args)
            else:
                callback(*args)
        except Exception as e:
            logger.error(f"Error in callback execution: {e}")
    
    async def force_hardware_check(self) -> Dict[str, Any]:
        """Force an immediate hardware check"""
        logger.info("Forcing hardware check")
        
        old_info = self.current_hardware_info
        old_tier = self.current_tier
        
        # Re-detect hardware
        new_info = self.hardware_profiler.detect_system_info()
        new_tier, classification_info = self.hardware_profiler.classify_hardware_tier(new_info)
        
        # Detect and handle changes
        changes = self._detect_changes(old_info, new_info)
        
        if changes:
            for change in changes:
                await self._handle_hardware_change(change)
            
            self.current_hardware_info = new_info
            self.current_tier = new_tier
        
        return {
            "changes_detected": len(changes),
            "changes": [
                {
                    "type": change.change_type.value,
                    "description": change.impact_description,
                    "timestamp": change.timestamp.isoformat()
                }
                for change in changes
            ],
            "current_tier": new_tier.value,
            "hardware_info": new_info
        }
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            "is_monitoring": self.is_monitoring,
            "check_interval": self.check_interval,
            "last_check": self.last_check_time.isoformat() if self.last_check_time else None,
            "current_tier": self.current_tier.value if self.current_tier else None,
            "registered_callbacks": {
                "change_callbacks": len(self.change_callbacks),
                "notification_callbacks": len(self.notification_callbacks)
            }
        }
