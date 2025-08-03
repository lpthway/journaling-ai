"""
Hardware-Adaptive AI API Endpoints

FastAPI endpoints for the hardware-adaptive AI system that automatically
scales capabilities based on available hardware.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging

from ..services.hardware_adaptive_ai import get_adaptive_ai, analyze_text_adaptive, get_system_capabilities

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/adaptive-ai", tags=["Hardware-Adaptive AI"])

# Request/Response models
class TextAnalysisRequest(BaseModel):
    text: str
    analysis_type: str = "auto"
    context: Optional[Dict[str, Any]] = None

class BatchAnalysisRequest(BaseModel):
    texts: List[str]
    analysis_type: str = "auto"

class TextAnalysisResponse(BaseModel):
    success: bool
    analysis_type: str
    result: Any
    confidence: float
    method_used: str
    processing_time: float
    hardware_tier: str
    fallback_used: bool
    timestamp: str
    error: Optional[str] = None

class SystemStatusResponse(BaseModel):
    status: str
    current_tier: str
    hardware_info: Dict[str, Any]
    feature_status: Dict[str, Any]
    memory_info: Dict[str, Any]
    monitoring_status: Dict[str, Any]
    uptime_seconds: float

class CapabilitiesResponse(BaseModel):
    current_tier: str
    available_features: List[str]
    feature_analysis: Dict[str, Any]
    tier_description: str
    memory_limit_mb: int
    models_available: List[str]

@router.post("/analyze", response_model=TextAnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    """
    Analyze text using the best available AI method for current hardware
    
    Automatically selects the optimal analysis method based on:
    - Available hardware (RAM, GPU)
    - Current system load
    - Model availability
    
    Falls back gracefully to algorithmic methods if AI models unavailable.
    """
    try:
        result = await analyze_text_adaptive(
            text=request.text,
            analysis_type=request.analysis_type,
            context=request.context
        )
        return TextAnalysisResponse(**result)
    
    except Exception as e:
        logger.error(f"Error in adaptive text analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/batch-analyze")
async def batch_analyze_texts(request: BatchAnalysisRequest):
    """
    Analyze multiple texts efficiently using batch processing when possible
    
    Optimizes performance by:
    - Batching requests to AI models
    - Reusing loaded models across requests
    - Intelligent memory management
    """
    try:
        adaptive_ai = await get_adaptive_ai()
        results = await adaptive_ai.batch_analyze(
            texts=request.texts,
            analysis_type=request.analysis_type
        )
        return {"results": results, "batch_size": len(request.texts)}
    
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")

@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    """
    Get comprehensive system status including:
    - Current hardware tier
    - Available features
    - Memory usage
    - Model loading status
    - Hardware monitoring status
    """
    try:
        adaptive_ai = await get_adaptive_ai()
        status = adaptive_ai.get_system_status()
        return SystemStatusResponse(**status)
    
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.get("/capabilities", response_model=CapabilitiesResponse)
async def get_capabilities():
    """
    Get current AI capabilities based on detected hardware
    
    Returns:
    - Available analysis features
    - Hardware tier classification
    - Memory limits and model availability
    - Feature descriptions and requirements
    """
    try:
        capabilities = await get_system_capabilities()
        return CapabilitiesResponse(**capabilities)
    
    except Exception as e:
        logger.error(f"Error getting capabilities: {e}")
        raise HTTPException(status_code=500, detail=f"Capabilities check failed: {str(e)}")

@router.post("/force-hardware-refresh")
async def force_hardware_refresh():
    """
    Force immediate hardware detection and capability update
    
    Useful when:
    - Hardware has been upgraded
    - GPU drivers updated
    - System configuration changed
    """
    try:
        adaptive_ai = await get_adaptive_ai()
        result = await adaptive_ai.force_hardware_refresh()
        return result
    
    except Exception as e:
        logger.error(f"Error in hardware refresh: {e}")
        raise HTTPException(status_code=500, detail=f"Hardware refresh failed: {str(e)}")

@router.get("/optimization-suggestions")
async def get_optimization_suggestions():
    """
    Get personalized suggestions for improving AI performance
    
    Analyzes current hardware and suggests:
    - Memory upgrades for better tier access
    - GPU additions for acceleration
    - Storage optimizations
    - Configuration improvements
    """
    try:
        adaptive_ai = await get_adaptive_ai()
        suggestions = await adaptive_ai.suggest_optimizations()
        return suggestions
    
    except Exception as e:
        logger.error(f"Error getting optimization suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Optimization analysis failed: {str(e)}")

@router.get("/memory-status")
async def get_memory_status():
    """
    Get detailed memory usage and model loading status
    
    Provides insights into:
    - Current memory usage by loaded models
    - Available memory for new models
    - Model loading/unloading activity
    - Memory pressure indicators
    """
    try:
        adaptive_ai = await get_adaptive_ai()
        if not adaptive_ai.memory_manager:
            raise HTTPException(status_code=503, detail="Memory manager not initialized")
        
        memory_info = adaptive_ai.memory_manager.get_memory_info()
        return memory_info
    
    except Exception as e:
        logger.error(f"Error getting memory status: {e}")
        raise HTTPException(status_code=500, detail=f"Memory status check failed: {str(e)}")

@router.get("/feature-compatibility/{analysis_type}")
async def check_feature_compatibility(analysis_type: str):
    """
    Check if a specific analysis type is supported on current hardware
    
    Returns:
    - Compatibility status (AI-powered vs fallback)
    - Required hardware tier
    - Alternative analysis options
    - Performance expectations
    """
    try:
        adaptive_ai = await get_adaptive_ai()
        if not adaptive_ai.feature_manager:
            raise HTTPException(status_code=503, detail="Feature manager not initialized")
        
        is_supported = adaptive_ai.feature_manager.can_perform_analysis(analysis_type)
        feature_status = adaptive_ai.feature_manager.get_feature_status()
        
        analysis_info = feature_status["feature_analysis"].get(analysis_type, {})
        
        return {
            "analysis_type": analysis_type,
            "supported": is_supported,
            "method": analysis_info.get("method", "unknown"),
            "tier_required": analysis_info.get("tier_required", "MINIMAL"),
            "current_tier": adaptive_ai.current_tier.value,
            "recommendations": []
        }
    
    except Exception as e:
        logger.error(f"Error checking feature compatibility: {e}")
        raise HTTPException(status_code=500, detail=f"Compatibility check failed: {str(e)}")

@router.post("/cleanup-memory")
async def cleanup_memory():
    """
    Force cleanup of unused AI models to free memory
    
    Useful when:
    - System is running low on memory
    - Switching to memory-intensive tasks
    - Preparing for large batch operations
    """
    try:
        adaptive_ai = await get_adaptive_ai()
        if not adaptive_ai.memory_manager:
            raise HTTPException(status_code=503, detail="Memory manager not initialized")
        
        memory_before = adaptive_ai.memory_manager.get_memory_info()
        await adaptive_ai.memory_manager.cleanup_unused_models()
        memory_after = adaptive_ai.memory_manager.get_memory_info()
        
        freed_mb = memory_before["memory_usage_mb"] - memory_after["memory_usage_mb"]
        
        return {
            "success": True,
            "memory_freed_mb": freed_mb,
            "memory_before": memory_before,
            "memory_after": memory_after
        }
    
    except Exception as e:
        logger.error(f"Error in memory cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"Memory cleanup failed: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Simple health check for the adaptive AI system
    
    Returns basic operational status without heavy processing
    """
    try:
        adaptive_ai = await get_adaptive_ai()
        
        return {
            "status": "healthy",
            "initialized": adaptive_ai.is_initialized,
            "current_tier": adaptive_ai.current_tier.value if adaptive_ai.current_tier else None,
            "timestamp": adaptive_ai.initialization_time.isoformat() if adaptive_ai.initialization_time else None
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# Integration endpoints for existing AI features
@router.post("/enhanced-analysis")
async def enhanced_analysis_with_adaptation(
    text: str,
    analysis_types: List[str] = ["sentiment", "emotion", "topic"],
    context: Optional[Dict[str, Any]] = None
):
    """
    Enhanced analysis that combines multiple AI techniques
    
    Automatically adapts the analysis pipeline based on:
    - Available hardware capabilities
    - Text length and complexity
    - Context requirements
    
    Returns comprehensive results using best available methods.
    """
    try:
        adaptive_ai = await get_adaptive_ai()
        
        results = {}
        for analysis_type in analysis_types:
            result = await adaptive_ai.analyze_text(text, analysis_type, context)
            results[analysis_type] = result
        
        # Combine results into unified response
        combined_confidence = sum(r.get("confidence", 0) for r in results.values()) / len(results)
        methods_used = list(set(r.get("method_used", "unknown") for r in results.values()))
        
        return {
            "text": text,
            "analysis_results": results,
            "combined_confidence": combined_confidence,
            "methods_used": methods_used,
            "hardware_tier": adaptive_ai.current_tier.value,
            "processing_summary": {
                "total_analyses": len(analysis_types),
                "ai_powered": len([r for r in results.values() if not r.get("fallback_used", True)]),
                "fallback_used": len([r for r in results.values() if r.get("fallback_used", True)])
            }
        }
    
    except Exception as e:
        logger.error(f"Error in enhanced analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Enhanced analysis failed: {str(e)}")
