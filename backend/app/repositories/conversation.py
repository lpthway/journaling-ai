# backend/app/repositories/conversation.py - Conversation Repository

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.postgresql import Conversation, ChatSession, JournalEntry
from app.repositories.base import BaseRepository

class ConversationRepository(BaseRepository[Conversation]):
    """Repository for conversation operations with session management"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Conversation)
    
    async def get_by_session_id(
        self, 
        session_id: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Conversation]:
        """Get all conversations for a session"""
        query = select(Conversation).where(
            Conversation.session_id == session_id
        ).order_by(asc(Conversation.created_at)).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_recent_conversations(
        self, 
        user_id: str, 
        limit: int = 20
    ) -> List[Conversation]:
        """Get recent conversations for a user across all sessions"""
        query = select(Conversation).join(ChatSession).where(
            ChatSession.user_id == user_id
        ).order_by(desc(Conversation.created_at)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def search_conversations(
        self, 
        user_id: str, 
        search_term: str, 
        limit: int = 20
    ) -> List[Conversation]:
        """Search conversations by content"""
        query = select(Conversation).join(ChatSession).where(
            and_(
                ChatSession.user_id == user_id,
                Conversation.user_message.contains(search_term) | 
                Conversation.ai_response.contains(search_term)
            )
        ).order_by(desc(Conversation.created_at)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_conversations_with_sources(
        self, 
        session_id: str
    ) -> List[Conversation]:
        """Get conversations that have source citations"""
        query = select(Conversation).where(
            and_(
                Conversation.session_id == session_id,
                Conversation.sources_used.isnot(None)
            )
        ).order_by(asc(Conversation.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_performance_metrics(
        self, 
        user_id: str, 
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get conversation performance metrics"""
        since = datetime.now() - timedelta(hours=hours)
        
        # Average processing time
        avg_time_query = select(func.avg(Conversation.processing_time_ms)).join(ChatSession).where(
            and_(
                ChatSession.user_id == user_id,
                Conversation.created_at >= since,
                Conversation.processing_time_ms.isnot(None)
            )
        )
        
        # Count conversations
        count_query = select(func.count(Conversation.id)).join(ChatSession).where(
            and_(
                ChatSession.user_id == user_id,
                Conversation.created_at >= since
            )
        )
        
        # Feedback stats
        positive_feedback_query = select(func.count(Conversation.id)).join(ChatSession).where(
            and_(
                ChatSession.user_id == user_id,
                Conversation.created_at >= since,
                Conversation.user_feedback == 'thumbs_up'
            )
        )
        
        # Execute queries
        avg_time_result = await self.session.execute(avg_time_query)
        count_result = await self.session.execute(count_query)
        positive_result = await self.session.execute(positive_feedback_query)
        
        total_conversations = count_result.scalar() or 0
        positive_feedback = positive_result.scalar() or 0
        
        return {
            "total_conversations": total_conversations,
            "average_processing_time_ms": round(avg_time_result.scalar() or 0, 2),
            "positive_feedback_count": positive_feedback,
            "positive_feedback_rate": round(positive_feedback / total_conversations * 100, 1) if total_conversations > 0 else 0,
            "period_hours": hours
        }
    
    async def add_feedback(
        self, 
        conversation_id: str, 
        feedback: str
    ) -> bool:
        """Add user feedback to a conversation"""
        if feedback not in ['thumbs_up', 'thumbs_down']:
            return False
        
        result = await self.update(conversation_id, user_feedback=feedback)
        return result is not None
    
    async def get_conversations_by_model(
        self, 
        user_id: str, 
        ai_model: str, 
        limit: int = 50
    ) -> List[Conversation]:
        """Get conversations for a specific AI model"""
        query = select(Conversation).join(ChatSession).where(
            and_(
                ChatSession.user_id == user_id,
                Conversation.ai_model_used == ai_model
            )
        ).order_by(desc(Conversation.created_at)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_slow_conversations(
        self, 
        user_id: str, 
        threshold_ms: float = 5000.0,
        limit: int = 20
    ) -> List[Conversation]:
        """Get conversations that took longer than threshold to process"""
        query = select(Conversation).join(ChatSession).where(
            and_(
                ChatSession.user_id == user_id,
                Conversation.processing_time_ms > threshold_ms
            )
        ).order_by(desc(Conversation.processing_time_ms)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
