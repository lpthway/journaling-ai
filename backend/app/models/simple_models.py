# backend/app/models/simple_models.py
"""
Simplified models for database recreation without complex indexes
"""

from sqlalchemy import (
    String, Integer, DateTime, Boolean, Text, Numeric, Index,
    ForeignKey, CheckConstraint, func
)
from sqlalchemy.dialects.postgresql import JSONB, UUID, TSVECTOR
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship
)
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

class Base(AsyncAttrs, DeclarativeBase):
    """Simplified base class with common patterns for all models."""
    
    # Common audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Soft deletion support
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )

class Topic(Base):
    """Simplified topic model"""
    __tablename__ = "topics"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    color: Mapped[str] = mapped_column(String(7), default="#3B82F6")
    icon: Mapped[Optional[str]] = mapped_column(String(50))
    
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False
    )
    
    tags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    psychology_domains: Mapped[List[str]] = mapped_column(JSONB, default=list)
    topic_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    entry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_entry_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    usage_statistics: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Simple indexes only
    __table_args__ = (
        Index('ix_topics_user_name', 'user_id', 'name'),
        Index('ix_topics_parent_sort', 'parent_id', 'sort_order'),
    )

class Entry(Base):
    """Simplified entry model without complex indexes"""
    __tablename__ = "entries"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    entry_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        default="journal"
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False
    )
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("topics.id", ondelete="SET NULL"),
        nullable=True
    )
    
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    reading_time_minutes: Mapped[int] = mapped_column(Integer, default=1)
    
    mood: Mapped[Optional[str]] = mapped_column(String(50))
    sentiment_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 4))
    emotion_analysis: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    tags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    auto_tags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    psychology_tags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    is_private: Mapped[bool] = mapped_column(Boolean, default=True)
    
    version: Mapped[int] = mapped_column(Integer, default=1)
    parent_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entries.id", ondelete="CASCADE"),
        nullable=True
    )
    
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    
    search_vector: Mapped[Optional[str]] = mapped_column(TSVECTOR)
    psychology_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    analysis_results: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Simple indexes only - no complex GIN trigram indexes
    __table_args__ = (
        Index('ix_entries_user_created', 'user_id', 'created_at'),
        Index('ix_entries_topic_created', 'topic_id', 'created_at'),
        Index('ix_entries_mood_sentiment', 'mood', 'sentiment_score'),
        Index('ix_entries_favorites', 'user_id', 'is_favorite', 'created_at'),
        
        # Basic constraints
        CheckConstraint('word_count >= 0', name='ck_entries_word_count_positive'),
        CheckConstraint('version >= 1', name='ck_entries_version_positive'),
        CheckConstraint('sentiment_score BETWEEN -1 AND 1', name='ck_entries_sentiment_range'),
    )
