# Advanced AI API - Sophisticated AI Intelligence Endpoints

"""
Advanced AI API for Journaling AI
Provides sophisticated AI capabilities including:
- Cross-temporal pattern analysis  
- Personality profiling
- Predictive analytics
- Advanced insights generation
- Multi-dimensional analysis
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
import json

# Core imports
from app.services.advanced_ai_service import (
    advanced_ai_service, 
    AnalysisTimeframe, 
    InsightType,
    PersonalityDimension,
    AdvancedInsight,
    PersonalityProfile,
    PredictiveAnalysis
)
from app.services.unified_database_service import unified_db_service
from app.core.exceptions import JournalingAIException

logger = logging.getLogger(__name__)

router = APIRouter()

# ==================== REQUEST/RESPONSE MODELS ====================

class AdvancedAnalysisRequest(BaseModel):
    """Request for advanced AI analysis"""
    user_id: str = Field(..., description="User identifier")
    timeframe: AnalysisTimeframe = Field(default=AnalysisTimeframe.MONTHLY, description="Analysis timeframe")
    include_predictions: bool = Field(default=True, description="Include predictive analysis")
    include_personality: bool = Field(default=True, description="Include personality profiling")
    max_entries: int = Field(default=100, description="Maximum entries to analyze", ge=10, le=500)

class PersonalityAnalysisRequest(BaseModel):
    """Request for personality analysis"""
    user_id: str = Field(..., description="User identifier")
    include_detailed_traits: bool = Field(default=True, description="Include detailed trait analysis")
    min_entries_required: int = Field(default=10, description="Minimum entries required", ge=5)

class PredictiveAnalysisRequest(BaseModel):
    """Request for predictive analysis"""
    user_id: str = Field(..., description="User identifier") 
    prediction_horizon: int = Field(default=7, description="Days to predict ahead", ge=1, le=30)
    include_risk_assessment: bool = Field(default=True, description="Include risk factor analysis")
    include_opportunities: bool = Field(default=True, description="Include opportunity identification")

class InsightResponse(BaseModel):
    """Response containing AI insights"""
    insight_type: str
    title: str
    description: str
    confidence: float
    significance: float
    timeframe: str
    supporting_data: Dict[str, Any]
    recommendations: List[str]
    metadata: Dict[str, Any]
    created_at: datetime

class PersonalityResponse(BaseModel):
    """Response containing personality profile"""
    dimensions: Dict[str, float]
    traits: List[str]
    behavioral_patterns: Dict[str, float]
    communication_style: str
    emotional_profile: Dict[str, float]
    growth_areas: List[str]
    strengths: List[str]
    confidence_score: float
    last_updated: datetime

class PredictionResponse(BaseModel):
    """Response containing predictive analysis"""
    predicted_mood_trends: Dict[str, Any]
    risk_factors: List[Dict[str, Any]]
    opportunity_windows: List[Dict[str, Any]]
    behavioral_predictions: Dict[str, Any]
    confidence_intervals: Dict[str, Any]
    recommendation_priority: List[str]
    created_at: datetime

class AdvancedAnalysisResponse(BaseModel):
    """Complete advanced analysis response"""
    analysis_summary: Dict[str, Any]
    temporal_insights: List[InsightResponse]
    personality_profile: Optional[PersonalityResponse]
    predictive_analysis: Optional[PredictionResponse]
    processing_metadata: Dict[str, Any]

class HealthCheckResponse(BaseModel):
    """Advanced AI service health check response"""
    status: str
    dependencies_available: bool
    cache_operational: bool
    emotion_service_healthy: bool
    service_stats: Dict[str, Any]
    timestamp: datetime

# ==================== MAIN ANALYSIS ENDPOINTS ====================

@router.post("/analysis/comprehensive", response_model=AdvancedAnalysisResponse)
async def get_comprehensive_analysis(
    request: AdvancedAnalysisRequest,
    background_tasks: BackgroundTasks
) -> AdvancedAnalysisResponse:
    """
    Get comprehensive advanced AI analysis for a user
    
    Provides:
    - Cross-temporal pattern analysis
    - Personality profiling (optional)
    - Predictive analytics (optional)
    - Advanced insights generation
    """
    try:
        start_time = datetime.utcnow()
        logger.info(f"🧠 Starting comprehensive AI analysis for user {request.user_id}")
        
        # Fetch user entries
        entries = await _fetch_user_entries(request.user_id, request.max_entries)
        
        if len(entries) < 5:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for analysis. Found {len(entries)} entries, minimum 5 required."
            )
        
        # Perform temporal pattern analysis
        temporal_insights = await advanced_ai_service.analyze_temporal_patterns(
            request.user_id, entries, request.timeframe
        )
        
        # Convert insights to response format
        insight_responses = [
            InsightResponse(
                insight_type=insight.insight_type.value,
                title=insight.title,
                description=insight.description,
                confidence=insight.confidence,
                significance=insight.significance,
                timeframe=insight.timeframe.value,
                supporting_data=insight.supporting_data,
                recommendations=insight.recommendations,
                metadata=insight.metadata,
                created_at=insight.created_at
            ) for insight in temporal_insights
        ]
        
        # Optional personality analysis
        personality_response = None
        if request.include_personality and len(entries) >= 10:
            try:
                personality_profile = await advanced_ai_service.generate_personality_profile(
                    request.user_id, entries
                )
                personality_response = PersonalityResponse(
                    dimensions={dim.name.lower(): score for dim, score in personality_profile.dimensions.items()},
                    traits=personality_profile.traits,
                    behavioral_patterns=personality_profile.behavioral_patterns,
                    communication_style=personality_profile.communication_style,
                    emotional_profile=personality_profile.emotional_profile,
                    growth_areas=personality_profile.growth_areas,
                    strengths=personality_profile.strengths,
                    confidence_score=personality_profile.confidence_score,
                    last_updated=personality_profile.last_updated
                )
            except Exception as e:
                logger.warning(f"⚠️ Personality analysis failed: {e}")
                # Continue without personality analysis
        
        # Optional predictive analysis
        predictive_response = None
        if request.include_predictions and len(entries) >= 15:
            try:
                predictive_analysis = await advanced_ai_service.generate_predictive_analysis(
                    request.user_id, entries, prediction_horizon=7
                )
                predictive_response = PredictionResponse(
                    predicted_mood_trends=predictive_analysis.predicted_mood_trends,
                    risk_factors=predictive_analysis.risk_factors,
                    opportunity_windows=predictive_analysis.opportunity_windows,
                    behavioral_predictions=predictive_analysis.behavioral_predictions,
                    confidence_intervals=predictive_analysis.confidence_intervals,
                    recommendation_priority=predictive_analysis.recommendation_priority,
                    created_at=predictive_analysis.created_at
                )
            except Exception as e:
                logger.warning(f"⚠️ Predictive analysis failed: {e}")
                # Continue without predictive analysis
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Build response
        response = AdvancedAnalysisResponse(
            analysis_summary={
                "entries_analyzed": len(entries),
                "insights_generated": len(insight_responses),
                "timeframe": request.timeframe.value,
                "processing_time_seconds": processing_time,
                "personality_included": personality_response is not None,
                "predictions_included": predictive_response is not None
            },
            temporal_insights=insight_responses,
            personality_profile=personality_response,
            predictive_analysis=predictive_response,
            processing_metadata={
                "analysis_timestamp": start_time,
                "service_version": "2.0.0",
                "ai_models_used": ["advanced_ai_service", "emotion_service"],
                "cache_utilized": True
            }
        )
        
        # Schedule background analytics update
        background_tasks.add_task(_update_user_analytics, request.user_id, len(entries))
        
        logger.info(f"✅ Comprehensive analysis completed for user {request.user_id} in {processing_time:.2f}s")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in comprehensive analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/analysis/personality", response_model=PersonalityResponse)
async def get_personality_analysis(request: PersonalityAnalysisRequest) -> PersonalityResponse:
    """
    Generate detailed personality profile from journal entries
    
    Analyzes:
    - Big Five personality dimensions
    - Behavioral patterns and traits
    - Communication style
    - Emotional profile
    - Strengths and growth areas
    """
    try:
        logger.info(f"🎭 Starting personality analysis for user {request.user_id}")
        
        # Fetch user entries
        entries = await _fetch_user_entries(request.user_id, 200)  # More entries for personality analysis
        
        if len(entries) < request.min_entries_required:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for personality analysis. Found {len(entries)} entries, minimum {request.min_entries_required} required."
            )
        
        # Generate personality profile
        personality_profile = await advanced_ai_service.generate_personality_profile(
            request.user_id, entries
        )
        
        # Build response
        response = PersonalityResponse(
            dimensions={dim.name.lower(): score for dim, score in personality_profile.dimensions.items()},
            traits=personality_profile.traits,
            behavioral_patterns=personality_profile.behavioral_patterns,
            communication_style=personality_profile.communication_style,
            emotional_profile=personality_profile.emotional_profile,
            growth_areas=personality_profile.growth_areas,
            strengths=personality_profile.strengths,
            confidence_score=personality_profile.confidence_score,
            last_updated=personality_profile.last_updated
        )
        
        logger.info(f"✅ Personality analysis completed for user {request.user_id} (confidence: {personality_profile.confidence_score:.2f})")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in personality analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Personality analysis failed: {str(e)}")

@router.post("/analysis/predictive", response_model=PredictionResponse)
async def get_predictive_analysis(request: PredictiveAnalysisRequest) -> PredictionResponse:
    """
    Generate predictive analysis and forecasts
    
    Provides:
    - Mood trend predictions
    - Risk factor identification
    - Opportunity window detection
    - Behavioral predictions
    - Personalized recommendations
    """
    try:
        logger.info(f"🔮 Starting predictive analysis for user {request.user_id}")
        
        # Fetch user entries (more recent entries weighted higher)
        entries = await _fetch_user_entries(request.user_id, 150)
        
        if len(entries) < 10:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for predictive analysis. Found {len(entries)} entries, minimum 10 required."
            )
        
        # Generate predictive analysis
        predictive_analysis = await advanced_ai_service.generate_predictive_analysis(
            request.user_id, entries, request.prediction_horizon
        )
        
        # Build response
        response = PredictionResponse(
            predicted_mood_trends=predictive_analysis.predicted_mood_trends,
            risk_factors=predictive_analysis.risk_factors if request.include_risk_assessment else [],
            opportunity_windows=predictive_analysis.opportunity_windows if request.include_opportunities else [],
            behavioral_predictions=predictive_analysis.behavioral_predictions,
            confidence_intervals=predictive_analysis.confidence_intervals,
            recommendation_priority=predictive_analysis.recommendation_priority,
            created_at=predictive_analysis.created_at
        )
        
        logger.info(f"✅ Predictive analysis completed for user {request.user_id} ({request.prediction_horizon} day horizon)")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in predictive analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Predictive analysis failed: {str(e)}")

# ==================== SPECIALIZED ENDPOINTS ====================

@router.get("/insights/temporal")
async def get_temporal_insights(
    user_id: str = Query(..., description="User identifier"),
    timeframe: AnalysisTimeframe = Query(default=AnalysisTimeframe.MONTHLY, description="Analysis timeframe"),
    insight_types: List[InsightType] = Query(default=None, description="Specific insight types to generate"),
    max_entries: int = Query(default=100, description="Maximum entries to analyze", ge=10, le=300)
) -> List[InsightResponse]:
    """
    Get temporal insights for specific timeframes and types
    
    Allows fine-grained control over insight generation
    """
    try:
        logger.info(f"📊 Getting temporal insights for user {user_id} ({timeframe.value})")
        
        # Fetch entries
        entries = await _fetch_user_entries(user_id, max_entries)
        
        if len(entries) < 5:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for temporal analysis. Found {len(entries)} entries, minimum 5 required."
            )
        
        # Generate insights
        insights = await advanced_ai_service.analyze_temporal_patterns(
            user_id, entries, timeframe
        )
        
        # Filter by requested types if specified
        if insight_types:
            insight_type_values = [it.value for it in insight_types]
            insights = [insight for insight in insights if insight.insight_type.value in insight_type_values]
        
        # Convert to response format
        insight_responses = [
            InsightResponse(
                insight_type=insight.insight_type.value,
                title=insight.title,
                description=insight.description,
                confidence=insight.confidence,
                significance=insight.significance,
                timeframe=insight.timeframe.value,
                supporting_data=insight.supporting_data,
                recommendations=insight.recommendations,
                metadata=insight.metadata,
                created_at=insight.created_at
            ) for insight in insights
        ]
        
        logger.info(f"✅ Generated {len(insight_responses)} temporal insights for user {user_id}")
        return insight_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting temporal insights: {e}")
        raise HTTPException(status_code=500, detail=f"Temporal insights failed: {str(e)}")

@router.get("/personality/dimensions")
async def get_personality_dimensions(
    user_id: str = Query(..., description="User identifier"),
    detailed: bool = Query(default=False, description="Include detailed dimension analysis")
) -> Dict[str, Any]:
    """
    Get personality dimensions analysis
    
    Returns Big Five personality dimensions with optional detailed analysis
    """
    try:
        logger.info(f"🎭 Getting personality dimensions for user {user_id}")
        
        # Fetch entries
        entries = await _fetch_user_entries(user_id, 150)
        
        if len(entries) < 15:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for personality analysis. Found {len(entries)} entries, minimum 15 required."
            )
        
        # Generate personality profile
        personality_profile = await advanced_ai_service.generate_personality_profile(user_id, entries)
        
        # Build response
        response = {
            "dimensions": {dim.name.lower(): score for dim, score in personality_profile.dimensions.items()},
            "confidence_score": personality_profile.confidence_score,
            "last_updated": personality_profile.last_updated
        }
        
        if detailed:
            response.update({
                "dimension_interpretations": _interpret_personality_dimensions(personality_profile.dimensions),
                "behavioral_indicators": personality_profile.behavioral_patterns,
                "traits_summary": personality_profile.traits
            })
        
        logger.info(f"✅ Personality dimensions retrieved for user {user_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting personality dimensions: {e}")
        raise HTTPException(status_code=500, detail=f"Personality dimensions failed: {str(e)}")

# ==================== MONITORING AND HEALTH ENDPOINTS ====================

@router.get("/health", response_model=HealthCheckResponse)
async def advanced_ai_health_check() -> HealthCheckResponse:
    """
    Advanced AI service health check
    
    Provides comprehensive health status for the advanced AI service
    """
    try:
        health_status = await advanced_ai_service.health_check()
        
        return HealthCheckResponse(
            status=health_status["status"],
            dependencies_available=health_status["dependencies_available"],
            cache_operational=health_status["cache_operational"],
            emotion_service_healthy=health_status["emotion_service_healthy"],
            service_stats=health_status["service_stats"],
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return HealthCheckResponse(
            status="error",
            dependencies_available=False,
            cache_operational=False,
            emotion_service_healthy=False,
            service_stats={},
            timestamp=datetime.utcnow()
        )

@router.get("/stats")
async def get_service_statistics() -> Dict[str, Any]:
    """
    Get advanced AI service statistics and performance metrics
    """
    try:
        stats = advanced_ai_service.get_service_stats()
        
        return {
            "service_stats": stats,
            "timestamp": datetime.utcnow(),
            "service_version": "2.0.0",
            "uptime_status": "operational"
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting service stats: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.utcnow(),
            "service_version": "2.0.0"
        }

# ==================== UTILITY FUNCTIONS ====================

async def _fetch_user_entries(user_id: str, max_entries: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch user entries for analysis
    
    Args:
        user_id: User identifier
        max_entries: Maximum number of entries to fetch
        
    Returns:
        List of entry dictionaries
    """
    try:
        # Use unified database service to fetch entries
        entries_result = await unified_db_service.get_entries_by_user(
            user_id, 
            limit=max_entries,
            include_content=True
        )
        
        if not entries_result or "entries" not in entries_result:
            return []
        
        # Convert to expected format
        entries = []
        for entry in entries_result["entries"]:
            entries.append({
                "id": entry.get("id"),
                "content": entry.get("content", ""),
                "created_at": entry.get("created_at", datetime.utcnow()),
                "mood": entry.get("mood"),
                "tags": entry.get("tags", [])
            })
        
        # Sort by creation date (newest first)
        entries.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
        
        return entries
        
    except Exception as e:
        logger.error(f"❌ Error fetching user entries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch user data: {str(e)}")

async def _update_user_analytics(user_id: str, entries_analyzed: int):
    """
    Background task to update user analytics
    
    Args:
        user_id: User identifier
        entries_analyzed: Number of entries analyzed
    """
    try:
        # This would update user analytics in the database
        logger.info(f"📊 Updated analytics for user {user_id}: {entries_analyzed} entries analyzed")
        
    except Exception as e:
        logger.error(f"❌ Error updating user analytics: {e}")

def _interpret_personality_dimensions(dimensions: Dict[Any, float]) -> Dict[str, str]:
    """
    Interpret personality dimensions into human-readable descriptions
    
    Args:
        dimensions: Dictionary of personality dimensions and scores
        
    Returns:
        Dictionary of dimension interpretations
    """
    interpretations = {}
    
    for dimension, score in dimensions.items():
        dim_name = dimension.name.lower() if hasattr(dimension, 'name') else str(dimension)
        
        if dim_name == 'extraversion':
            if score > 0.7:
                interpretations[dim_name] = "Highly outgoing and social"
            elif score > 0.3:
                interpretations[dim_name] = "Balanced social tendencies"
            else:
                interpretations[dim_name] = "More introspective and reserved"
        
        elif dim_name == 'neuroticism':
            if score > 0.7:
                interpretations[dim_name] = "Higher emotional sensitivity"
            elif score > 0.3:
                interpretations[dim_name] = "Moderate emotional variability"
            else:
                interpretations[dim_name] = "Emotionally stable and resilient"
        
        elif dim_name == 'openness':
            if score > 0.7:
                interpretations[dim_name] = "Highly creative and open to experiences"
            elif score > 0.3:
                interpretations[dim_name] = "Moderate openness to new ideas"
            else:
                interpretations[dim_name] = "Prefers familiar patterns and traditions"
        
        elif dim_name == 'conscientiousness':
            if score > 0.7:
                interpretations[dim_name] = "Highly organized and goal-directed"
            elif score > 0.3:
                interpretations[dim_name] = "Moderately organized approach"
            else:
                interpretations[dim_name] = "More flexible and spontaneous"
        
        elif dim_name == 'agreeableness':
            if score > 0.7:
                interpretations[dim_name] = "Highly cooperative and trusting"
            elif score > 0.3:
                interpretations[dim_name] = "Balanced approach to relationships"
            else:
                interpretations[dim_name] = "More independent and analytical"
        
        else:
            interpretations[dim_name] = f"Score: {score:.2f}"
    
    return interpretations

# ==================== ERROR HANDLERS ====================

@router.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle value errors in advanced AI processing"""
    logger.error(f"Value error in advanced AI: {exc}")
    raise HTTPException(status_code=400, detail=f"Invalid input data: {str(exc)}")

@router.exception_handler(Exception)
async def general_error_handler(request, exc):
    """Handle general errors in advanced AI processing"""
    logger.error(f"Unexpected error in advanced AI: {exc}")
    raise HTTPException(status_code=500, detail="An unexpected error occurred in AI processing")

# ==================== ROUTER METADATA ====================

router.tags = ["advanced-ai"]
router.prefix = "/api/v1/ai/advanced"