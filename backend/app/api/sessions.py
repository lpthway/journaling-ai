### app/api/sessions.py

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.models.session import (
    Session, SessionCreate, SessionUpdate, SessionResponse,
    MessageCreate, MessageResponse, MessageRole, SessionStatus, SessionType
)
from app.services.session_service import session_service
from app.services.conversation_service import conversation_service
from app.services.llm_service import llm_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

async def auto_tag_conversation(session_id: str):
    """Automatically generate tags for a conversation based on its content"""
    try:
        # Get session and messages
        session = await session_service.get_session(session_id)
        if not session:
            return
        
        messages = await session_service.get_session_messages(session_id)
        if not messages:
            return
        
        # Extract user messages for tagging
        user_messages = [msg for msg in messages if msg.role == MessageRole.USER]
        if len(user_messages) < 2:  # Need at least 2 user messages
            return
        
        # Combine user messages for analysis
        conversation_text = " ".join([msg.content for msg in user_messages])
        
        # Generate tags if we have enough content
        if len(conversation_text.strip()) > 20:
            auto_tags = await llm_service.generate_automatic_tags(conversation_text, "conversation")
            
            if auto_tags:
                # Get existing session tags
                existing_tags = session.tags if hasattr(session, 'tags') and session.tags else []
                existing_tags_lower = [tag.lower() for tag in existing_tags]
                
                # Add new tags that don't already exist
                new_tags = []
                for tag in auto_tags:
                    if tag.lower() not in existing_tags_lower:
                        new_tags.append(tag)
                
                if new_tags:
                    # Update session with new tags
                    all_tags = existing_tags + new_tags
                    update_data = SessionUpdate(tags=all_tags[:8])  # Limit to 8 tags
                    await session_service.update_session(session_id, update_data)
                    logger.info(f"Auto-tagged session {session_id} with tags: {new_tags}")
    
    except Exception as e:
        logger.error(f"Error auto-tagging conversation {session_id}: {e}")

@router.post("/", response_model=SessionResponse)
async def create_session(session_data: SessionCreate):
    """Create a new conversation session"""
    try:
        # Create the session
        session = await session_service.create_session(session_data)
        
        # Generate opening message from AI
        opening_message = await conversation_service.generate_opening_message(
            session.session_type, 
            session.metadata
        )
        
        # Add opening message to session
        await session_service.add_message(
            session.id,
            MessageCreate(content=opening_message, role=MessageRole.ASSISTANT)
        )
        
        # Get session with recent messages for response
        recent_messages = await session_service.get_recent_messages(session.id, 5)
        
        return SessionResponse(
            **session.model_dump(),
            recent_messages=[MessageResponse(**msg.model_dump()) for msg in recent_messages]
        )
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session")

@router.get("/", response_model=List[SessionResponse])
async def get_sessions(
    limit: int = Query(20, ge=1, le=100),
    status: Optional[SessionStatus] = Query(None)
):
    """Get conversation sessions"""
    try:
        sessions = await session_service.get_sessions(limit=limit, status=status)
        
        # Add recent messages to each session
        session_responses = []
        for session in sessions:
            recent_messages = await session_service.get_recent_messages(session.id, 3)
            session_responses.append(SessionResponse(
                **session.model_dump(),
                recent_messages=[MessageResponse(**msg.model_dump()) for msg in recent_messages]
            ))
        
        return session_responses
        
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sessions")

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get a specific session with its messages"""
    try:
        session = await session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get all messages for this session
        messages = await session_service.get_session_messages(session_id)
        
        return SessionResponse(
            **session.model_dump(),
            recent_messages=[MessageResponse(**msg.model_dump()) for msg in messages]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session")

@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(session_id: str, session_update: SessionUpdate):
    """Update a session"""
    try:
        updated_session = await session_service.update_session(session_id, session_update)
        if not updated_session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        recent_messages = await session_service.get_recent_messages(session_id, 5)
        
        return SessionResponse(
            **updated_session.model_dump(),
            recent_messages=[MessageResponse(**msg.model_dump()) for msg in recent_messages]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update session")

@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and all its messages"""
    try:
        success = await session_service.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete session")

@router.post("/{session_id}/messages", response_model=MessageResponse)
async def send_message(session_id: str, message_data: MessageCreate):
    """Send a message in a conversation session"""
    try:
        # Check if session exists
        session = await session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Add user message
        user_message = await session_service.add_message(
            session_id, 
            MessageCreate(content=message_data.content, role=MessageRole.USER, metadata=message_data.metadata)
        )
        
        # Get conversation history for context
        conversation_history = await session_service.get_session_messages(session_id)
        
        # Generate AI response
        ai_response = await conversation_service.generate_response(
            session.session_type,
            message_data.content,
            conversation_history,
            session.metadata
        )
        
        # Add AI response message
        ai_message = await session_service.add_message(
            session_id,
            MessageCreate(content=ai_response, role=MessageRole.ASSISTANT)
        )
        
        # Auto-tag conversation every 6 messages (3 exchanges)
        try:
            all_messages = await session_service.get_session_messages(session_id)
            message_count = len(all_messages)
            
            if message_count >= 6 and message_count % 6 == 0:
                await auto_tag_conversation(session_id)
        except Exception as e:
            logger.warning(f"Failed to auto-tag conversation {session_id}: {e}")
        
        return MessageResponse(**ai_message.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message to session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")

@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: str,
    limit: int = Query(100, ge=1, le=500)
):
    """Get messages for a session"""
    try:
        # Check if session exists
        session = await session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        messages = await session_service.get_session_messages(session_id, limit)
        
        return [MessageResponse(**msg.model_dump()) for msg in messages]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve messages")

@router.get("/{session_id}/suggestions")
async def get_follow_up_suggestions(session_id: str):
    """Get follow-up question suggestions for a session"""
    try:
        # Check if session exists
        session = await session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get recent messages for context
        recent_messages = await session_service.get_recent_messages(session_id, 5)
        
        # Generate suggestions
        suggestions = await conversation_service.suggest_follow_up_questions(
            session.session_type,
            recent_messages
        )
        
        return {
            "session_id": session_id,
            "suggestions": suggestions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting suggestions for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get suggestions")

@router.post("/{session_id}/pause")
async def pause_session(session_id: str):
    """Pause an active session"""
    try:
        session_update = SessionUpdate(status=SessionStatus.PAUSED)
        updated_session = await session_service.update_session(session_id, session_update)
        
        if not updated_session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session paused successfully", "status": updated_session.status}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to pause session")

@router.post("/{session_id}/resume")
async def resume_session(session_id: str):
    """Resume a paused session"""
    try:
        session = await session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Generate a resume message
        recent_messages = await session_service.get_recent_messages(session_id, 3)
        
        resume_message = "Welcome back! I'm glad you're continuing our conversation. What's been on your mind since we last talked?"
        
        # Add resume message
        ai_message = await session_service.add_message(
            session_id,
            MessageCreate(content=resume_message, role=MessageRole.ASSISTANT)
        )
        
        # Update session status
        session_update = SessionUpdate(status=SessionStatus.ACTIVE)
        updated_session = await session_service.update_session(session_id, session_update)
        
        return {
            "message": "Session resumed successfully",
            "status": updated_session.status,
            "resume_message": MessageResponse(**ai_message.model_dump())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to resume session")

# Session types endpoint for frontend
@router.get("/types/available")
async def get_available_session_types():
    """Get available session types with descriptions"""
    return {
        "session_types": [
            {
                "type": SessionType.REFLECTION_BUDDY,
                "name": "Reflection Buddy",
                "description": "Chat with a curious friend who asks thoughtful questions",
                "icon": "💭",
                "tags": ["casual", "friendly", "exploration"]
            },
            {
                "type": SessionType.INNER_VOICE,
                "name": "Inner Voice Assistant", 
                "description": "Explore different perspectives on situations and decisions",
                "icon": "🧠",
                "tags": ["perspective", "wisdom", "insight"]
            },
            {
                "type": SessionType.GROWTH_CHALLENGE,
                "name": "Growth Challenge",
                "description": "Take on challenges designed to promote personal growth",
                "icon": "🌱",
                "tags": ["growth", "challenge", "development"]
            },
            {
                "type": SessionType.PATTERN_DETECTIVE,
                "name": "Pattern Detective",
                "description": "Discover patterns in your thoughts and behaviors",
                "icon": "🔍", 
                "tags": ["patterns", "analysis", "insights"]
            },
            {
                "type": SessionType.FREE_CHAT,
                "name": "Free Chat",
                "description": "Open conversation about anything on your mind",
                "icon": "💬",
                "tags": ["open", "flexible", "general"]
            }
        ]
    }

@router.post("/{session_id}/auto-tag")
async def trigger_auto_tag(session_id: str):
    """Manually trigger automatic tagging for a conversation session"""
    try:
        # Check if session exists
        session = await session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Trigger auto-tagging
        await auto_tag_conversation(session_id)
        
        # Return updated session
        updated_session = await session_service.get_session(session_id)
        return SessionResponse(**updated_session.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering auto-tag for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to auto-tag session")