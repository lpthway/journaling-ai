# backend/app/repositories/session_repository.py
"""
Advanced chat session repository with conversation management.

Features:
- Session lifecycle management
- Message threading and context preservation
- Performance analytics and optimization
- Psychology integration tracking
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, desc, text, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import logging
from ..models.enhanced_models import ChatSession, ChatMessage, User
from .enhanced_base import EnhancedBaseRepository

logger = logging.getLogger(__name__)

class SessionRepository(EnhancedBaseRepository[ChatSession]):
    """
    Specialized repository for chat session management.
    
    Optimized for:
    - Real-time conversation handling
    - Message context preservation
    - Session analytics and insights
    - Performance at conversational scale
    """
    
    def __init__(self, session):
        super().__init__(session, ChatSession)
    
    async def create_with_initial_message(
        self,
        user_id: str,
        session_type: str,
        title: str,
        initial_message: str,
        **kwargs
    ) -> ChatSession:
        """
        Create session with initial AI greeting message.
        
        Ensures:
        - Proper session initialization
        - Consistent message threading
        - Initial context establishment
        """
        # Create session
        session = ChatSession(
            user_id=user_id,
            session_type=session_type,
            title=title,
            last_activity=datetime.utcnow(),
            **kwargs
        )
        
        created_session = await self.create(session)
        
        # Add initial message
        initial_msg = ChatMessage(
            session_id=created_session.id,
            content=initial_message,
            role='assistant',
            word_count=len(initial_message.split()),
            character_count=len(initial_message)
        )
        
        self.session.add(initial_msg)
        
        # Update session message count
        created_session.message_count = 1
        
        await self.session.flush()
        await self.session.refresh(created_session)
        
        return created_session
    
    async def add_message(
        self,
        session_id: str,
        content: str,
        role: str,
        **kwargs
    ) -> ChatMessage:
        """
        Add message to session with automatic analytics.
        
        Updates:
        - Session activity timestamp
        - Message count statistics
        - Content analysis metrics
        """
        message = ChatMessage(
            session_id=session_id,
            content=content,
            role=role,
            word_count=len(content.split()),
            character_count=len(content),
            **kwargs
        )
        
        self.session.add(message)
        
        # Update session activity
        session_update = text("""
            UPDATE chat_sessions 
            SET 
                last_activity = CURRENT_TIMESTAMP,
                message_count = message_count + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :session_id
        """)
        
        await self.session.execute(session_update, {"session_id": session_id})
        await self.session.flush()
        
        return message
    
    async def get_messages(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[ChatMessage]:
        """Get messages for a session with proper ordering."""
        query = select(ChatMessage).where(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_recent_messages(
        self,
        session_id: str,
        count: int = 10
    ) -> List[ChatMessage]:
        """Get recent messages for context in AI responses."""
        query = select(ChatMessage).where(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.desc()).limit(count)
        
        result = await self.session.execute(query)
        return list(reversed(result.scalars().all()))  # Return in chronological order
    
    async def get_sessions_by_type(
        self,
        user_id: str,
        session_type: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[ChatSession]:
        """Get sessions filtered by type."""
        query = select(ChatSession).where(
            and_(
                ChatSession.user_id == user_id,
                ChatSession.session_type == session_type,
                ChatSession.deleted_at.is_(None)
            )
        ).order_by(ChatSession.last_activity.desc()).offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_session_analytics(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate comprehensive session analytics.
        
        Returns:
        - Session type preferences
        - Usage patterns and trends
        - Engagement metrics
        - Psychology integration effectiveness
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Session type distribution
        type_query = select(
            ChatSession.session_type,
            func.count(ChatSession.id).label('count'),
            func.avg(ChatSession.message_count).label('avg_messages'),
            func.sum(ChatSession.total_duration_minutes).label('total_duration')
        ).where(
            and_(
                ChatSession.user_id == user_id,
                ChatSession.created_at >= start_date,
                ChatSession.deleted_at.is_(None)
            )
        ).group_by(ChatSession.session_type)
        
        type_result = await self.session.execute(type_query)
        session_types = {
            row.session_type: {
                'count': row.count,
                'avg_messages': float(row.avg_messages) if row.avg_messages else 0,
                'total_duration': row.total_duration or 0
            }
            for row in type_result.all()
        }
        
        # Daily usage patterns
        daily_query = select(
            func.date(ChatSession.created_at).label('date'),
            func.count(ChatSession.id).label('sessions_created'),
            func.sum(ChatSession.message_count).label('total_messages')
        ).where(
            and_(
                ChatSession.user_id == user_id,
                ChatSession.created_at >= start_date,
                ChatSession.deleted_at.is_(None)
            )
        ).group_by(func.date(ChatSession.created_at)).order_by('date')
        
        daily_result = await self.session.execute(daily_query)
        daily_patterns = [
            {
                'date': row.date.isoformat(),
                'sessions_created': row.sessions_created,
                'total_messages': row.total_messages or 0
            }
            for row in daily_result.all()
        ]
        
        return {
            'period_days': days,
            'session_types': session_types,
            'daily_patterns': daily_patterns,
            'total_sessions': sum(data['count'] for data in session_types.values())
        }
    
    async def search_sessions(
        self,
        user_id: str,
        query: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[ChatSession]:
        """Search sessions by title or description."""
        search_query = select(ChatSession).where(
            and_(
                ChatSession.user_id == user_id,
                or_(
                    ChatSession.title.ilike(f'%{query}%'),
                    ChatSession.description.ilike(f'%{query}%')
                ),
                ChatSession.deleted_at.is_(None)
            )
        ).order_by(ChatSession.last_activity.desc()).offset(offset).limit(limit)
        
        result = await self.session.execute(search_query)
        return list(result.scalars().all())
    
    async def get_active_sessions(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[ChatSession]:
        """Get most recently active sessions."""
        query = select(ChatSession).where(
            and_(
                ChatSession.user_id == user_id,
                ChatSession.status == 'active',
                ChatSession.deleted_at.is_(None)
            )
        ).order_by(ChatSession.last_activity.desc()).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_session_duration(
        self,
        session_id: str,
        duration_minutes: int
    ) -> bool:
        """Update session duration for analytics."""
        try:
            update_query = text("""
                UPDATE chat_sessions 
                SET 
                    total_duration_minutes = total_duration_minutes + :duration,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :session_id
            """)
            
            await self.session.execute(update_query, {
                "session_id": session_id,
                "duration": duration_minutes
            })
            
            return True
        except Exception as e:
            logger.error(f"Error updating session duration: {e}")
            return False
    
    async def close_session(self, session_id: str) -> bool:
        """Mark session as closed/completed."""
        try:
            session = await self.get_by_id(session_id)
            if session:
                session.status = 'closed'
                session.updated_at = datetime.utcnow()
                await self.session.flush()
                return True
            return False
        except Exception as e:
            logger.error(f"Error closing session: {e}")
            return False