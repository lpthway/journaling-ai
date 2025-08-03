### app/services/session_service.py

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import aiofiles
import logging
from app.models.session import (
    Session, SessionCreate, SessionUpdate, SessionResponse,
    Message, MessageCreate, MessageResponse, MessageRole,
    SessionType, SessionStatus
)

logger = logging.getLogger(__name__)

class SessionDatabaseService:
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.sessions_file = self.data_dir / "sessions.json"
        self.messages_file = self.data_dir / "messages.json"
        
        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)
        self._init_files()
    
    def _init_files(self):
        """Initialize JSON files if they don't exist"""
        if not self.sessions_file.exists():
            with open(self.sessions_file, 'w') as f:
                json.dump({}, f)
        
        if not self.messages_file.exists():
            with open(self.messages_file, 'w') as f:
                json.dump({}, f)
    
    async def _read_sessions(self) -> Dict[str, Any]:
        """Read sessions from JSON file"""
        try:
            async with aiofiles.open(self.sessions_file, 'r') as f:
                content = await f.read()
                return json.loads(content) if content else {}
        except Exception as e:
            logger.error(f"Error reading sessions: {e}")
            return {}
    
    async def _write_sessions(self, sessions: Dict[str, Any]):
        """Write sessions to JSON file"""
        try:
            async with aiofiles.open(self.sessions_file, 'w') as f:
                await f.write(json.dumps(sessions, indent=2, default=str))
        except Exception as e:
            logger.error(f"Error writing sessions: {e}")
    
    async def _read_messages(self) -> Dict[str, Any]:
        """Read messages from JSON file"""
        try:
            async with aiofiles.open(self.messages_file, 'r') as f:
                content = await f.read()
                return json.loads(content) if content else {}
        except Exception as e:
            logger.error(f"Error reading messages: {e}")
            return {}
    
    async def _write_messages(self, messages: Dict[str, Any]):
        """Write messages to JSON file"""
        try:
            async with aiofiles.open(self.messages_file, 'w') as f:
                await f.write(json.dumps(messages, indent=2, default=str))
        except Exception as e:
            logger.error(f"Error writing messages: {e}")
    
    # Session operations
    async def create_session(self, session_data: SessionCreate) -> Session:
        """Create a new conversation session"""
        sessions = await self._read_sessions()
        
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Generate title if not provided
        title = session_data.title or self._generate_session_title(session_data.session_type)
        
        session = Session(
            id=session_id,
            session_type=session_data.session_type,
            title=title,
            description=session_data.description,
            status=SessionStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            last_activity=now,
            message_count=0,
            metadata=session_data.metadata or {}
        )
        
        sessions[session_id] = session.model_dump()
        await self._write_sessions(sessions)
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        sessions = await self._read_sessions()
        session_data = sessions.get(session_id)
        
        if session_data:
            return Session(**session_data)
        return None
    
    async def get_sessions(self, limit: int = 50, status: Optional[SessionStatus] = None) -> List[Session]:
        """Get sessions with optional filtering"""
        sessions = await self._read_sessions()
        session_list = []
        
        for session_data in sessions.values():
            session = Session(**session_data)
            
            # Apply filters
            if status and session.status != status:
                continue
            
            session_list.append(session)
        
        # Sort by last activity (most recent first)
        session_list.sort(key=lambda x: x.last_activity or x.created_at, reverse=True)
        
        return session_list[:limit]
    
    async def update_session(self, session_id: str, session_update: SessionUpdate) -> Optional[Session]:
        """Update an existing session"""
        sessions = await self._read_sessions()
        
        if session_id not in sessions:
            return None
        
        session_data = sessions[session_id]
        session = Session(**session_data)
        
        # Update fields
        update_data = session_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(session, field, value)
        
        session.updated_at = datetime.utcnow()
        
        sessions[session_id] = session.model_dump()
        await self._write_sessions(sessions)
        
        return session
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and its messages"""
        sessions = await self._read_sessions()
        messages = await self._read_messages()
        
        if session_id not in sessions:
            return False
        
        # Delete session
        del sessions[session_id]
        await self._write_sessions(sessions)
        
        # Delete associated messages
        messages_to_delete = [msg_id for msg_id, msg_data in messages.items() 
                             if msg_data.get('session_id') == session_id]
        
        for msg_id in messages_to_delete:
            del messages[msg_id]
        
        await self._write_messages(messages)
        
        return True
    
    # Message operations
    async def add_message(self, session_id: str, message_data: MessageCreate) -> Message:
        """Add a message to a session"""
        messages = await self._read_messages()
        sessions = await self._read_sessions()
        
        message_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        message = Message(
            id=message_id,
            session_id=session_id,
            role=message_data.role,
            content=message_data.content,
            timestamp=now,
            metadata=message_data.metadata or {}
        )
        
        messages[message_id] = message.model_dump()
        await self._write_messages(messages)
        
        # Update session stats
        if session_id in sessions:
            sessions[session_id]['message_count'] += 1
            sessions[session_id]['last_activity'] = now.isoformat()
            sessions[session_id]['updated_at'] = now.isoformat()
            await self._write_sessions(sessions)
        
        return message
    
    async def get_session_messages(self, session_id: str, limit: int = 100) -> List[Message]:
        """Get messages for a session"""
        messages = await self._read_messages()
        session_messages = []
        
        for message_data in messages.values():
            if message_data.get('session_id') == session_id:
                session_messages.append(Message(**message_data))
        
        # Sort by timestamp (oldest first for conversation flow)
        session_messages.sort(key=lambda x: x.timestamp)
        
        return session_messages[-limit:] if limit else session_messages
    
    async def get_recent_messages(self, session_id: str, count: int = 5) -> List[Message]:
        """Get recent messages for context"""
        messages = await self.get_session_messages(session_id)
        return messages[-count:] if messages else []
    
    def _generate_session_title(self, session_type: SessionType) -> str:
        """Generate a title based on session type"""
        titles = {
            SessionType.REFLECTION_BUDDY: "Chat with your reflection buddy",
            SessionType.INNER_VOICE: "Exploring perspectives",
            SessionType.GROWTH_CHALLENGE: "Growth challenge session",
            SessionType.PATTERN_DETECTIVE: "Pattern exploration",
            SessionType.FREE_CHAT: "Free conversation"
        }
        
        base_title = titles.get(session_type, "Conversation session")
        timestamp = datetime.utcnow().strftime("%b %d")
        return f"{base_title} - {timestamp}"

# Global instance
session_service = SessionDatabaseService()
