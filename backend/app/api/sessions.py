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
from app.services.entry_analytics_processor import entry_analytics_processor
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
        logger.info(f"Creating session with data: {session_data}")
        logger.info(f"Session type: {session_data.session_type}")
        
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
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to create session")

@router.get("/", response_model=List[SessionResponse])
async def get_sessions(
    limit: int = Query(20, ge=1, le=100),
    status: Optional[SessionStatus] = Query(None)
):
    """Get conversation sessions with optimized bulk loading"""
    try:
        # Get sessions directly from repository
        from app.core.database import database
        from app.repositories.session_repository import SessionRepository
        
        async with database.session_factory() as db:
            session_repo = SessionRepository(db)
            sessions = await session_repo.get_user_sessions(
                user_id="00000000-0000-0000-0000-000000000001",  # Use correct user ID from database
                limit=limit
            )
        
        session_responses = []
        for session in sessions:
            # Get recent messages for this session
            recent_messages = await session_repo.get_recent_messages(session.id, count=3)
            
            try:
                session_response = SessionResponse(
                    id=str(session.id),
                    session_type=SessionType(session.session_type),
                    title=session.title or f"Chat Session {str(session.id)[:8]}",
                    description=session.description,
                    status=SessionStatus(session.status),
                    created_at=session.created_at,
                    updated_at=session.updated_at,
                    last_activity=session.last_activity,
                    message_count=session.message_count or 0,
                    tags=session.tags or [],
                    metadata=session.session_metadata or {},
                    recent_messages=[
                        MessageResponse(
                            id=str(msg.id),
                            session_id=str(session.id),
                            content=msg.content or "",
                            role=MessageRole(msg.role),
                            timestamp=msg.created_at,
                            metadata=msg.message_metadata or {}
                        )
                        for msg in recent_messages if msg.content  # Only include messages with content
                    ]
                )
                session_responses.append(session_response)
            except Exception as validation_error:
                logger.warning(f"Skipping session {session.id} due to validation error: {validation_error}")
                continue
        
        return session_responses
        
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sessions")

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get a specific session with recent messages"""
    try:
        from app.core.database import database
        from app.repositories.session_repository import SessionRepository
        
        async with database.session_factory() as db:
            session_repo = SessionRepository(db)
            
            # Get session
            from sqlalchemy import select
            from app.models.enhanced_models import ChatSession
            session_query = select(ChatSession).where(ChatSession.id == session_id)
            session_result = await db.execute(session_query)
            session = session_result.scalar_one_or_none()
            
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            # Get recent messages
            recent_messages = await session_repo.get_recent_messages(session.id, count=50)  # Load more messages for chat view
            
            return SessionResponse(
                id=str(session.id),
                session_type=SessionType(session.session_type),
                title=session.title or f"Chat Session {str(session.id)[:8]}",
                description=session.description,
                status=SessionStatus(session.status),
                created_at=session.created_at,
                updated_at=session.updated_at,
                last_activity=session.last_activity,
                message_count=session.message_count or 0,
                tags=session.tags or [],
                metadata=session.session_metadata or {},
                recent_messages=[
                    MessageResponse(
                        id=str(msg.id),
                        session_id=str(session.id),
                        content=msg.content or "",
                        role=MessageRole(msg.role),
                        timestamp=msg.created_at,
                        metadata=msg.message_metadata or {}
                    )
                    for msg in recent_messages if msg.content
                ]
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
        
        # Get conversation history for context - Optimized to get only recent messages needed for AI context
        # This prevents loading full conversation history for each response
        conversation_history = await session_service.get_recent_messages(session_id, 10)
        
        # Generate AI response - FIXED: Only expect string response
        ai_response_text = await conversation_service.generate_response(
            message_data.content,
            session.session_type,
            conversation_history,  # Now uses recent messages instead of full history
            session.metadata
        )
        
        # Ensure ai_response_text is a string
        if not isinstance(ai_response_text, str):
            logger.error(f"Expected string response, got {type(ai_response_text)}: {ai_response_text}")
            ai_response_text = str(ai_response_text)  # Force conversion to string
        
        # Add AI response message
        ai_message = await session_service.add_message(
            session_id,
            MessageCreate(content=ai_response_text, role=MessageRole.ASSISTANT)  # ← FIXED: Pass string directly
        )
        
        # Auto-tag conversation every 6 messages (3 exchanges)
        try:
            all_messages = await session_service.get_session_messages(session_id)
            message_count = len(all_messages)
            
            if message_count >= 6 and message_count % 6 == 0:
                await auto_tag_conversation(session_id)
        except Exception as e:
            logger.warning(f"Failed to auto-tag conversation {session_id}: {e}")
        
        # Invalidate analytics cache for session update
        try:
            # Get user_id for cache invalidation (assuming default user for now)
            await entry_analytics_processor.invalidate_analytics_cache("default_user")
            logger.debug(f"Invalidated analytics cache for session update {session_id}")
        except Exception as e:
            # Don't let cache invalidation errors break session operations
            logger.warning(f"Failed to invalidate analytics cache for session {session_id}: {e}")
        
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
        # Get messages directly from repository
        from app.core.database import database
        from app.repositories.session_repository import SessionRepository
        
        async with database.session_factory() as db:
            session_repo = SessionRepository(db)
            
            # Check if session exists
            from sqlalchemy import select
            from app.models.enhanced_models import ChatSession
            session_query = select(ChatSession).where(ChatSession.id == session_id)
            session_result = await db.execute(session_query)
            session = session_result.scalar_one_or_none()
            
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            # Get messages for this session
            messages = await session_repo.get_messages(session_id, limit=limit)
            
            return [
                MessageResponse(
                    id=str(msg.id),
                    session_id=str(msg.session_id),
                    content=msg.content or "",
                    role=MessageRole(msg.role),
                    timestamp=msg.created_at,
                    metadata=msg.message_metadata or {}
                )
                for msg in messages if msg.content
            ]
        
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
        
        # Enhanced logging for debugging
        logger.info(f"Getting suggestions for session {session_id}, type: {session.session_type}")
        logger.info(f"Session type value: {session.session_type.value}")
        
        # Get recent messages for context
        recent_messages = await session_service.get_recent_messages(session_id, 5)
        logger.info(f"Found {len(recent_messages)} recent messages")
        
        # Generate suggestions with enhanced error handling
        try:
            suggestions = await conversation_service.suggest_follow_up_questions(
                recent_messages,
                session.session_type
            )
            
            logger.info(f"Generated {len(suggestions)} suggestions")
            
            return {
                "session_id": session_id,
                "session_type": session.session_type.value,
                "suggestions": suggestions
            }
            
        except AttributeError as ae:
            logger.error(f"AttributeError in suggestion generation: {ae}")
            logger.error(f"Session type: {type(session.session_type)}, value: {session.session_type}")
            raise HTTPException(status_code=500, detail="Session type configuration error")
            
        except TypeError as te:
            logger.error(f"TypeError in suggestion generation: {te}")
            logger.error(f"Recent messages type: {type(recent_messages)}")
            if recent_messages:
                logger.error(f"First message type: {type(recent_messages[0])}")
            raise HTTPException(status_code=500, detail="Message type configuration error")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting suggestions for session {session_id}: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


# Add this helper method to validate session types
def validate_session_type(session_type) -> bool:
    """Validate that session_type is a proper SessionType enum"""
    from app.models.session import SessionType
    
    if not isinstance(session_type, SessionType):
        logger.error(f"Invalid session type: {type(session_type)}, value: {session_type}")
        return False
    
    if session_type not in SessionType:
        logger.error(f"Unknown session type enum: {session_type}")
        return False
    
    return True

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