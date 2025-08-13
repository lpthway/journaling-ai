# backend/app/services/session_service.py
"""
Session service for managing chat sessions.
"""

from typing import List, Dict, Any, Optional
from app.services.unified_database_service import unified_db_service
from app.models.session import SessionCreate, SessionUpdate, Session, MessageCreate, Message
from app.models.enhanced_models import ChatSession, ChatMessage
from app.core.database import database
from app.repositories.session_repository import SessionRepository
from sqlalchemy import select
import logging
import uuid

logger = logging.getLogger(__name__)

class SessionService:
    """Service for managing chat sessions"""
    
    def __init__(self):
        self.db = unified_db_service
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        try:
            async with database.get_session() as db:
                session_repo = SessionRepository(db)
                
                # Get session from database
                query = select(ChatSession).where(ChatSession.id == session_id)
                result = await db.execute(query)
                db_session = result.scalar_one_or_none()
                
                if not db_session:
                    return None
                
                # Convert to Session model
                return Session(
                    id=str(db_session.id),
                    session_type=db_session.session_type,
                    title=db_session.title or f"Chat Session {str(db_session.id)[:8]}",
                    description=db_session.description,
                    status=db_session.status,
                    created_at=db_session.created_at,
                    updated_at=db_session.updated_at,
                    last_activity=db_session.last_activity,
                    message_count=db_session.message_count or 0,
                    tags=db_session.tags or [],
                    metadata=db_session.session_metadata or {}
                )
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    async def create_session(self, session_data: SessionCreate, user_id: str) -> Session:
        """Create a new session"""
        try:
            # Use the unified database service to create session
            title = session_data.title or f"New {session_data.session_type.replace('_', ' ').title()}"
            
            if not user_id:
                raise ValueError("user_id is required for session creation")
            
            chat_session = await self.db.create_session(
                session_type=session_data.session_type.value,
                title=title,
                user_id=user_id,  # Use provided user ID (required)
                description=session_data.description,
                initial_message="Hello! How can I help you today?"
            )
            
            # Convert ChatSession to Session model
            return Session(
                id=str(chat_session.id),
                session_type=session_data.session_type,
                title=chat_session.title,
                description=chat_session.description,
                status=chat_session.status,
                created_at=chat_session.created_at,
                updated_at=chat_session.updated_at,
                last_activity=chat_session.last_activity,
                message_count=chat_session.message_count or 0,
                tags=chat_session.tags or [],
                metadata=chat_session.session_metadata or session_data.metadata or {}
            )
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    async def update_session(self, session_id: str, session_update: SessionUpdate) -> Optional[Session]:
        """Update a session"""
        try:
            async with database.get_session() as db:
                # Get session
                query = select(ChatSession).where(ChatSession.id == session_id)
                result = await db.execute(query)
                db_session = result.scalar_one_or_none()
                
                if not db_session:
                    return None
                
                # Update fields
                if session_update.title is not None:
                    db_session.title = session_update.title
                if session_update.description is not None:
                    db_session.description = session_update.description
                if session_update.status is not None:
                    db_session.status = session_update.status.value
                if session_update.tags is not None:
                    db_session.tags = session_update.tags
                if session_update.metadata is not None:
                    db_session.session_metadata = session_update.metadata
                
                await db.commit()
                await db.refresh(db_session)
                
                # Convert to Session model
                return Session(
                    id=str(db_session.id),
                    session_type=db_session.session_type,
                    title=db_session.title,
                    description=db_session.description,
                    status=db_session.status,
                    created_at=db_session.created_at,
                    updated_at=db_session.updated_at,
                    last_activity=db_session.last_activity,
                    message_count=db_session.message_count or 0,
                    tags=db_session.tags or [],
                    metadata=db_session.session_metadata or {}
                )
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        try:
            async with database.get_session() as db:
                # Get session
                query = select(ChatSession).where(ChatSession.id == session_id)
                result = await db.execute(query)
                db_session = result.scalar_one_or_none()
                
                if not db_session:
                    return False
                
                # Soft delete
                from datetime import datetime
                db_session.deleted_at = datetime.utcnow()
                await db.commit()
                
                return True
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    async def add_message(self, session_id: str, message_data: MessageCreate) -> Message:
        """Add message to session"""
        try:
            async with database.get_session() as db:
                session_repo = SessionRepository(db)
                
                # Add message to database
                db_message = await session_repo.add_message(
                    session_id=session_id,
                    content=message_data.content,
                    role=message_data.role.value,
                    message_metadata=message_data.metadata
                )
                
                await db.commit()
                await db.refresh(db_message)
                
                # Convert to Message model
                return Message(
                    id=str(db_message.id),
                    session_id=str(db_message.session_id),
                    content=db_message.content,
                    role=message_data.role,
                    timestamp=db_message.created_at,
                    metadata=db_message.message_metadata or {}
                )
        except Exception as e:
            logger.error(f"Error adding message to session {session_id}: {e}")
            raise
    
    async def get_session_messages(self, session_id: str, limit: int = 100) -> List[Message]:
        """Get messages for a session"""
        try:
            async with database.get_session() as db:
                session_repo = SessionRepository(db)
                
                # Get messages from database
                db_messages = await session_repo.get_messages(session_id, limit=limit)
                
                # Convert to Message models
                return [
                    Message(
                        id=str(msg.id),
                        session_id=str(msg.session_id),
                        content=msg.content,
                        role=msg.role,
                        timestamp=msg.created_at,
                        metadata=msg.message_metadata or {}
                    )
                    for msg in db_messages
                ]
        except Exception as e:
            logger.error(f"Error getting messages for session {session_id}: {e}")
            return []
    
    async def get_recent_messages(self, session_id: str, count: int = 10) -> List[Message]:
        """Get recent messages for a session"""
        try:
            async with database.get_session() as db:
                session_repo = SessionRepository(db)
                
                # Get recent messages from database
                db_messages = await session_repo.get_recent_messages(session_id, count=count)
                
                # Convert to Message models
                return [
                    Message(
                        id=str(msg.id),
                        session_id=str(msg.session_id),
                        content=msg.content,
                        role=msg.role,
                        timestamp=msg.created_at,
                        metadata=msg.message_metadata or {}
                    )
                    for msg in db_messages
                ]
        except Exception as e:
            logger.error(f"Error getting recent messages for session {session_id}: {e}")
            return []

    async def get_user_sessions(self, user_id: str, limit: int = 50) -> List[Session]:
        """Get sessions for a specific user"""
        try:
            async with database.get_session() as db:
                session_repo = SessionRepository(db)
                
                # Get user sessions from database
                db_sessions = await session_repo.get_user_sessions(user_id=user_id, limit=limit)
                
                # Convert to Session models
                return [
                    Session(
                        id=str(session.id),
                        session_type=session.session_type,
                        title=session.title or f"Chat Session {str(session.id)[:8]}",
                        description=session.description,
                        status=session.status,
                        created_at=session.created_at,
                        updated_at=session.updated_at,
                        last_activity=session.last_activity,
                        message_count=session.message_count or 0,
                        tags=session.tags or [],
                        metadata=session.session_metadata or {}
                    )
                    for session in db_sessions
                ]
        except Exception as e:
            logger.error(f"Error getting user sessions for {user_id}: {e}")
            return []

# Global session service instance
session_service = SessionService()
