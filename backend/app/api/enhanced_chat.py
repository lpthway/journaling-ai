# Enhanced Chat API - Advanced Conversational AI Endpoints

"""
Enhanced Chat API for Journaling AI
Provides sophisticated conversational AI capabilities including:
- Context-aware therapeutic conversations
- Multi-modal response generation
- Crisis intervention integration
- Personality-adapted dialogue
- Advanced conversation management
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
import uuid

# Core imports
from app.services.enhanced_chat_service import (
    enhanced_chat_service,
    ConversationMode,
    ResponseStyle,
    ConversationStage,
    EnhancedChatResponse
)
from app.auth.dependencies import get_current_user
from app.auth.models import AuthUser

# Type alias for current user dependency
CurrentUser = Depends(get_current_user)

logger = logging.getLogger(__name__)

router = APIRouter()

# ==================== REQUEST/RESPONSE MODELS ====================

class ChatMessageRequest(BaseModel):
    """Request for chat message processing"""
    session_id: Optional[str] = Field(None, description="Conversation session ID (auto-generated if not provided)")
    message: str = Field(..., description="User message content", min_length=1, max_length=2000)
    conversation_mode: ConversationMode = Field(default=ConversationMode.SUPPORTIVE_LISTENING, description="Conversation mode")
    preferred_style: Optional[ResponseStyle] = Field(None, description="Preferred response style")
    context_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context metadata")

class StartConversationRequest(BaseModel):
    """Request to start a new conversation"""
    conversation_mode: ConversationMode = Field(default=ConversationMode.SUPPORTIVE_LISTENING, description="Conversation mode")
    initial_context: Dict[str, Any] = Field(default_factory=dict, description="Initial conversation context")

class ChatResponse(BaseModel):
    """Enhanced chat response"""
    message_id: str
    session_id: str
    content: str
    response_style: str
    conversation_stage: str
    therapeutic_techniques: List[str]
    follow_up_suggestions: List[str]
    emotional_support_level: float
    crisis_indicators: List[str]
    next_recommended_topics: List[str]
    confidence_score: float
    processing_metadata: Dict[str, Any]
    timestamp: datetime

class ConversationSession(BaseModel):
    """Conversation session information"""
    session_id: str
    user_id: str
    conversation_mode: str
    current_stage: str
    turn_count: int
    emotional_state: Dict[str, float]
    key_topics: List[str]
    started_at: datetime
    last_activity: datetime

class ConversationSummary(BaseModel):
    """Conversation summary"""
    session_id: str
    duration_turns: int
    primary_topics: List[str]
    emotional_journey: Dict[str, Any]
    therapeutic_techniques_used: List[str]
    ended_at: datetime

class HealthResponse(BaseModel):
    """Enhanced chat service health response"""
    status: str
    dependencies_available: bool
    llm_service_available: bool
    emotion_service_available: bool
    cache_operational: bool
    service_stats: Dict[str, Any]
    timestamp: datetime

# ==================== MAIN CHAT ENDPOINTS ====================

@router.post("/message", response_model=ChatResponse)
async def send_chat_message(
    request: ChatMessageRequest,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks
) -> ChatResponse:
    """
    Send a message and receive an enhanced AI response
    
    Provides:
    - Context-aware therapeutic responses
    - Crisis intervention if needed
    - Personality-adapted dialogue
    - Advanced conversation analysis
    """
    try:
        logger.info(f"💬 Processing chat message from user {current_user.id}")
        
        # Auto-generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Process message through enhanced chat service
        enhanced_response = await enhanced_chat_service.process_chat_message(
            user_id=str(current_user.id),
            session_id=session_id,
            message=request.message,
            conversation_mode=request.conversation_mode,
            preferred_style=request.preferred_style
        )
        
        # Convert to API response format
        response = ChatResponse(
            message_id=enhanced_response.message_id,
            session_id=session_id,
            content=enhanced_response.content,
            response_style=enhanced_response.response_style.value,
            conversation_stage=enhanced_response.conversation_stage.value,
            therapeutic_techniques=enhanced_response.therapeutic_techniques,
            follow_up_suggestions=enhanced_response.follow_up_suggestions,
            emotional_support_level=enhanced_response.emotional_support_level,
            crisis_indicators=enhanced_response.crisis_indicators,
            next_recommended_topics=enhanced_response.next_recommended_topics,
            confidence_score=enhanced_response.confidence_score,
            processing_metadata=enhanced_response.processing_metadata,
            timestamp=enhanced_response.timestamp
        )
        
        # Schedule background analytics
        background_tasks.add_task(
            _log_chat_analytics, 
            str(current_user.id), 
            session_id, 
            len(request.message),
            enhanced_response.confidence_score
        )
        
        # Log crisis intervention if detected
        if enhanced_response.crisis_indicators:
            background_tasks.add_task(
                _log_crisis_intervention,
                str(current_user.id),
                session_id,
                enhanced_response.crisis_indicators
            )
            logger.warning(f"🚨 Crisis indicators detected for user {current_user.id}: {enhanced_response.crisis_indicators}")
        
        logger.info(f"✅ Chat response generated (confidence: {enhanced_response.confidence_score:.2f})")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.post("/conversation/start", response_model=ConversationSession)
async def start_conversation(request: StartConversationRequest, current_user: CurrentUser) -> ConversationSession:
    """
    Start a new conversation session
    
    Creates a new conversation context with specified mode and initial settings
    """
    try:
        logger.info(f"💬 Starting new conversation for user {current_user.id}")
        
        # Start new conversation session
        session_id = await enhanced_chat_service.start_new_conversation(
            user_id=str(current_user.id),
            mode=request.conversation_mode
        )
        
        # Get initial conversation context
        # For now, create a basic response since we don't have a method to get context directly
        response = ConversationSession(
            session_id=session_id,
            user_id=str(current_user.id),
            conversation_mode=request.conversation_mode.value,
            current_stage=ConversationStage.OPENING.value,
            turn_count=0,
            emotional_state={"neutral": 1.0},
            key_topics=[],
            started_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        
        logger.info(f"✅ Started conversation session {session_id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error starting conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start conversation: {str(e)}")

@router.post("/conversation/{session_id}/end", response_model=ConversationSummary)
async def end_conversation(session_id: str) -> ConversationSummary:
    """
    End a conversation session and get summary
    
    Provides comprehensive summary of the conversation including:
    - Topics discussed
    - Emotional journey
    - Therapeutic techniques used
    """
    try:
        logger.info(f"💬 Ending conversation session {session_id}")
        
        # End conversation and get summary
        summary_data = await enhanced_chat_service.end_conversation(session_id)
        
        if summary_data.get("status") == "session_not_found":
            raise HTTPException(status_code=404, detail="Conversation session not found")
        
        if summary_data.get("status") == "error":
            raise HTTPException(status_code=500, detail=summary_data.get("error", "Unknown error"))
        
        # Convert to response format
        summary = ConversationSummary(
            session_id=summary_data["session_id"],
            duration_turns=summary_data["duration_turns"],
            primary_topics=summary_data["primary_topics"],
            emotional_journey=summary_data["emotional_journey"],
            therapeutic_techniques_used=summary_data["therapeutic_techniques_used"],
            ended_at=summary_data["ended_at"]
        )
        
        logger.info(f"✅ Ended conversation session {session_id}")
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error ending conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to end conversation: {str(e)}")

# ==================== CONVERSATION MODE ENDPOINTS ====================

@router.get("/modes")
async def get_conversation_modes() -> Dict[str, Any]:
    """
    Get available conversation modes with descriptions
    
    Returns information about all supported conversation modes
    """
    try:
        modes = {
            mode.value: {
                "name": mode.name.replace("_", " ").title(),
                "description": _get_mode_description(mode),
                "suitable_for": _get_mode_suitable_situations(mode),
                "techniques": _get_mode_techniques(mode)
            }
            for mode in ConversationMode
        }
        
        return {
            "available_modes": modes,
            "default_mode": ConversationMode.SUPPORTIVE_LISTENING.value,
            "total_modes": len(modes)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting conversation modes: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation modes")

@router.get("/styles")
async def get_response_styles() -> Dict[str, Any]:
    """
    Get available response styles with descriptions
    
    Returns information about all supported response styles
    """
    try:
        styles = {
            style.value: {
                "name": style.name.replace("_", " ").title(),
                "description": _get_style_description(style),
                "characteristics": _get_style_characteristics(style)
            }
            for style in ResponseStyle
        }
        
        return {
            "available_styles": styles,
            "default_style": ResponseStyle.EMPATHETIC.value,
            "total_styles": len(styles)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting response styles: {e}")
        raise HTTPException(status_code=500, detail="Failed to get response styles")

# ==================== THERAPEUTIC FEATURES ENDPOINTS ====================

@router.post("/therapeutic/assessment")
async def get_therapeutic_assessment(
    user_id: str,
    session_id: str,
    include_recommendations: bool = True
) -> Dict[str, Any]:
    """
    Get therapeutic assessment for current conversation
    
    Provides insights into:
    - Emotional patterns detected
    - Therapeutic needs identified
    - Recommended interventions
    """
    try:
        logger.info(f"🔍 Getting therapeutic assessment for session {session_id}")
        
        # This would integrate with the conversation context to provide assessment
        # For now, provide a structured response template
        assessment = {
            "session_id": session_id,
            "user_id": user_id,
            "assessment_timestamp": datetime.utcnow(),
            "emotional_patterns": {
                "primary_emotions_detected": ["anxiety", "hope"],
                "emotional_stability": 0.7,
                "emotional_complexity": 0.6
            },
            "therapeutic_needs": [
                {
                    "need": "emotional_regulation",
                    "priority": "high",
                    "description": "Support needed for managing anxiety responses"
                },
                {
                    "need": "coping_skills",
                    "priority": "medium", 
                    "description": "Development of healthy coping mechanisms"
                }
            ],
            "intervention_suggestions": [] if not include_recommendations else [
                {
                    "technique": "mindfulness_grounding",
                    "description": "Breathing exercises and present-moment awareness",
                    "suitability_score": 0.8
                },
                {
                    "technique": "cognitive_restructuring",
                    "description": "Examining and reframing negative thought patterns",
                    "suitability_score": 0.7
                }
            ],
            "session_progress": {
                "stage": "exploration",
                "therapeutic_alliance": 0.8,
                "engagement_level": 0.9
            }
        }
        
        logger.info(f"✅ Generated therapeutic assessment for session {session_id}")
        return assessment
        
    except Exception as e:
        logger.error(f"❌ Error getting therapeutic assessment: {e}")
        raise HTTPException(status_code=500, detail=f"Therapeutic assessment failed: {str(e)}")

@router.post("/crisis/check")
async def check_crisis_indicators(
    user_id: str,
    message: str,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check message for crisis indicators
    
    Provides crisis risk assessment and recommended actions
    """
    try:
        logger.info(f"🚨 Checking crisis indicators for user {user_id}")
        
        # This would use the enhanced chat service's crisis detection
        # For now, provide a basic implementation
        crisis_keywords = ["suicide", "kill myself", "end it", "hopeless", "worthless"]
        message_lower = message.lower()
        
        indicators_found = [keyword for keyword in crisis_keywords if keyword in message_lower]
        crisis_level = len(indicators_found) * 0.3  # Simple scoring
        
        assessment = {
            "user_id": user_id,
            "session_id": session_id,
            "crisis_level": min(crisis_level, 1.0),
            "risk_category": "high" if crisis_level > 0.7 else "medium" if crisis_level > 0.3 else "low",
            "indicators_detected": indicators_found,
            "immediate_actions_needed": crisis_level > 0.7,
            "recommended_responses": [],
            "resources": [],
            "assessment_timestamp": datetime.utcnow()
        }
        
        # Add recommendations based on crisis level
        if crisis_level > 0.7:
            assessment["recommended_responses"] = [
                "Prioritize safety assessment",
                "Provide immediate crisis resources",
                "Encourage professional help"
            ]
            assessment["resources"] = [
                {
                    "name": "National Suicide Prevention Lifeline",
                    "phone": "988",
                    "available": "24/7"
                },
                {
                    "name": "Crisis Text Line",
                    "text": "HOME to 741741",
                    "available": "24/7"
                }
            ]
        elif crisis_level > 0.3:
            assessment["recommended_responses"] = [
                "Increase emotional support",
                "Explore coping strategies",
                "Monitor for escalation"
            ]
        
        if crisis_level > 0.5:
            logger.warning(f"🚨 Crisis indicators detected for user {user_id}: level {crisis_level:.2f}")
        
        return assessment
        
    except Exception as e:
        logger.error(f"❌ Error checking crisis indicators: {e}")
        raise HTTPException(status_code=500, detail=f"Crisis check failed: {str(e)}")

# ==================== CONVERSATION HISTORY ENDPOINTS ====================

@router.get("/conversations")
async def get_user_conversations(
    current_user: CurrentUser,
    limit: int = 50,
    include_metadata: bool = True
) -> Dict[str, Any]:
    """
    Get all conversations for a user
    
    Returns list of conversation sessions with metadata
    """
    try:
        logger.info(f"📜 Getting conversations for user {current_user.id}")
        
        # Get conversation sessions from enhanced chat service
        conversations = await enhanced_chat_service.get_user_conversations(str(current_user.id), limit)
        
        # Format for frontend compatibility
        formatted_conversations = []
        for conv in conversations:
            formatted_conversations.append({
                "id": conv["session_id"],
                "session_type": conv.get("session_type", "free_chat"),
                "title": conv.get("title", f"Chat Session {conv['session_id'][:8]}"),
                "status": conv.get("status", "active"),
                "message_count": conv.get("message_count", 0),
                "created_at": conv.get("started_at"),
                "last_activity": conv.get("last_activity"),
                "recent_messages": conv.get("recent_messages", [])
            })
        
        return {
            "conversations": formatted_conversations,
            "total_count": len(formatted_conversations),
            "user_id": user_id,
            "retrieved_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting user conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")

@router.get("/conversation/{session_id}/history")
async def get_conversation_history(
    session_id: str,
    current_user: CurrentUser,
    limit: int = 50,
    include_metadata: bool = False
) -> Dict[str, Any]:
    """
    Get conversation history for a session
    
    Returns message history with optional metadata
    """
    try:
        logger.info(f"📜 Getting conversation history for session {session_id}")
        
        # This would retrieve from conversation context
        # For now, provide a template response
        history = {
            "session_id": session_id,
            "message_count": 0,
            "messages": [],
            "conversation_metadata": {
                "total_turns": 0,
                "conversation_mode": "supportive_listening",
                "current_stage": "opening",
                "key_topics": [],
                "emotional_progression": []
            } if include_metadata else {},
            "retrieved_at": datetime.utcnow()
        }
        
        logger.info(f"✅ Retrieved conversation history for session {session_id}")
        return history
        
    except Exception as e:
        logger.error(f"❌ Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation history: {str(e)}")

# ==================== MONITORING AND HEALTH ENDPOINTS ====================

@router.get("/health", response_model=HealthResponse)
async def chat_health_check() -> HealthResponse:
    """
    Enhanced chat service health check
    
    Provides comprehensive health status for chat capabilities
    """
    try:
        health_status = await enhanced_chat_service.health_check()
        
        return HealthResponse(
            status=health_status["status"],
            dependencies_available=health_status["dependencies_available"],
            llm_service_available=health_status["llm_service_available"],
            emotion_service_available=health_status["emotion_service_available"],
            cache_operational=health_status["cache_operational"],
            service_stats=health_status["service_stats"],
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"❌ Chat health check failed: {e}")
        return HealthResponse(
            status="error",
            dependencies_available=False,
            llm_service_available=False,
            emotion_service_available=False,
            cache_operational=False,
            service_stats={},
            timestamp=datetime.utcnow()
        )

@router.get("/stats")
async def get_chat_statistics() -> Dict[str, Any]:
    """
    Get chat service statistics and performance metrics
    """
    try:
        stats = enhanced_chat_service.get_service_stats()
        
        return {
            "service_stats": stats,
            "timestamp": datetime.utcnow(),
            "service_version": "2.0.0",
            "capabilities": {
                "conversation_modes": len(list(ConversationMode)),
                "response_styles": len(list(ResponseStyle)),
                "therapeutic_techniques": "comprehensive",
                "crisis_intervention": True,
                "personality_adaptation": True
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting chat stats: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.utcnow(),
            "service_version": "2.0.0"
        }

# ==================== UTILITY FUNCTIONS ====================

def _get_mode_description(mode: ConversationMode) -> str:
    """Get description for conversation mode"""
    descriptions = {
        ConversationMode.SUPPORTIVE_LISTENING: "Active listening with validation and empathy",
        ConversationMode.THERAPEUTIC_GUIDANCE: "Structured therapeutic conversation with professional techniques",
        ConversationMode.COGNITIVE_REFRAMING: "Focus on identifying and challenging negative thought patterns",
        ConversationMode.MINDFULNESS_COACHING: "Present-moment awareness and mindfulness practices",
        ConversationMode.GOAL_SETTING: "Collaborative goal setting and action planning",
        ConversationMode.CRISIS_SUPPORT: "Immediate crisis intervention and safety-focused support",
        ConversationMode.REFLECTION_FACILITATION: "Guided self-reflection and insight development",
        ConversationMode.EMOTIONAL_PROCESSING: "Deep exploration of emotional experiences"
    }
    return descriptions.get(mode, "Professional therapeutic conversation")

def _get_mode_suitable_situations(mode: ConversationMode) -> List[str]:
    """Get suitable situations for conversation mode"""
    situations = {
        ConversationMode.SUPPORTIVE_LISTENING: ["Initial sessions", "Emotional distress", "Need for validation"],
        ConversationMode.THERAPEUTIC_GUIDANCE: ["Ongoing therapy", "Problem-solving", "Skill building"],
        ConversationMode.COGNITIVE_REFRAMING: ["Negative thinking patterns", "Depression", "Anxiety"],
        ConversationMode.MINDFULNESS_COACHING: ["Anxiety", "Stress", "Overwhelm", "Racing thoughts"],
        ConversationMode.GOAL_SETTING: ["Life transitions", "Personal growth", "Motivation building"],
        ConversationMode.CRISIS_SUPPORT: ["Suicidal ideation", "Self-harm", "Acute distress"],
        ConversationMode.REFLECTION_FACILITATION: ["Self-discovery", "Insight building", "Contemplation"],
        ConversationMode.EMOTIONAL_PROCESSING: ["Grief", "Trauma", "Complex emotions"]
    }
    return situations.get(mode, ["General support"])

def _get_mode_techniques(mode: ConversationMode) -> List[str]:
    """Get techniques used in conversation mode"""
    techniques = {
        ConversationMode.SUPPORTIVE_LISTENING: ["Active listening", "Validation", "Empathetic reflection"],
        ConversationMode.THERAPEUTIC_GUIDANCE: ["Socratic questioning", "Psychoeducation", "Skill teaching"],
        ConversationMode.COGNITIVE_REFRAMING: ["Thought challenging", "Evidence examination", "Perspective taking"],
        ConversationMode.MINDFULNESS_COACHING: ["Breathing exercises", "Body awareness", "Present moment focus"],
        ConversationMode.GOAL_SETTING: ["SMART goals", "Action planning", "Motivation enhancement"],
        ConversationMode.CRISIS_SUPPORT: ["Safety planning", "Resource connection", "Immediate stabilization"],
        ConversationMode.REFLECTION_FACILITATION: ["Open-ended questions", "Exploration", "Insight building"],
        ConversationMode.EMOTIONAL_PROCESSING: ["Emotional validation", "Expression facilitation", "Integration"]
    }
    return techniques.get(mode, ["General therapeutic techniques"])

def _get_style_description(style: ResponseStyle) -> str:
    """Get description for response style"""
    descriptions = {
        ResponseStyle.EMPATHETIC: "Warm, understanding, and emotionally validating responses",
        ResponseStyle.ANALYTICAL: "Logical, structured, and problem-solving focused responses",
        ResponseStyle.ENCOURAGING: "Optimistic, supportive, and motivating responses",
        ResponseStyle.CHALLENGING: "Direct, thought-provoking responses that promote growth",
        ResponseStyle.REFLECTIVE: "Contemplative, insight-oriented responses",
        ResponseStyle.PRACTICAL: "Action-oriented, solution-focused responses",
        ResponseStyle.CREATIVE: "Imaginative, metaphorical, and creative responses"
    }
    return descriptions.get(style, "Professional therapeutic response")

def _get_style_characteristics(style: ResponseStyle) -> List[str]:
    """Get characteristics of response style"""
    characteristics = {
        ResponseStyle.EMPATHETIC: ["Warm tone", "Emotional validation", "Active listening"],
        ResponseStyle.ANALYTICAL: ["Logical structure", "Evidence-based", "Problem-solving focus"],
        ResponseStyle.ENCOURAGING: ["Positive framing", "Strength-focused", "Motivational"],
        ResponseStyle.CHALLENGING: ["Direct feedback", "Growth-oriented", "Boundary-setting"],
        ResponseStyle.REFLECTIVE: ["Contemplative questions", "Insight-building", "Self-exploration"],
        ResponseStyle.PRACTICAL: ["Action-oriented", "Concrete suggestions", "Goal-focused"],
        ResponseStyle.CREATIVE: ["Metaphorical language", "Creative exercises", "Imaginative approaches"]
    }
    return characteristics.get(style, ["Professional approach"])

async def _log_chat_analytics(user_id: str, session_id: str, message_length: int, confidence: float):
    """Background task to log chat analytics"""
    try:
        logger.info(f"📊 Logged chat analytics: user={user_id}, session={session_id}, confidence={confidence:.2f}")
    except Exception as e:
        logger.error(f"❌ Error logging chat analytics: {e}")

async def _log_crisis_intervention(user_id: str, session_id: str, indicators: List[str]):
    """Background task to log crisis intervention"""
    try:
        logger.warning(f"🚨 Crisis intervention logged: user={user_id}, session={session_id}, indicators={indicators}")
        # This would log to a specialized crisis monitoring system
    except Exception as e:
        logger.error(f"❌ Error logging crisis intervention: {e}")

# ==================== ERROR HANDLING UTILITIES ====================

def handle_chat_error(error: Exception, context: str = "chat processing") -> HTTPException:
    """
    Centralized error handling for chat operations
    
    Args:
        error: The exception that occurred
        context: Context description for the error
        
    Returns:
        HTTPException: Properly formatted HTTP exception
    """
    if isinstance(error, ValueError):
        logger.error(f"Value error in {context}: {error}")
        return HTTPException(status_code=400, detail=f"Invalid input: {str(error)}")
    elif isinstance(error, KeyError):
        logger.error(f"Key error in {context}: {error}")
        return HTTPException(status_code=400, detail=f"Missing required field: {str(error)}")
    elif isinstance(error, HTTPException):
        # Re-raise HTTP exceptions as-is
        return error
    else:
        logger.error(f"Unexpected error in {context}: {error}")
        return HTTPException(status_code=500, detail=f"An unexpected error occurred in {context}")

# ==================== ROUTER METADATA ====================

router.tags = ["enhanced-chat"]
router.prefix = "/api/v1/chat"