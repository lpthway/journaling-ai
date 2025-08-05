# backend/app/models/database_models.py
"""
Enterprise database models with advanced SQLAlchemy 2.0 features.

Design Principles:
- Normalized relational design with proper constraints
- JSONB columns for flexible metadata storage
- Comprehensive indexing strategy for performance
- Audit trails and soft deletion support
- Full-text search capabilities
"""

from sqlalchemy import (
    String, Integer, DateTime, Boolean, Text, Numeric, Index,
    ForeignKey, CheckConstraint, UniqueConstraint, func, text
)
from sqlalchemy.dialects.postgresql import JSONB, UUID, TSVECTOR
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship, validates
)
from sqlalchemy.sql import expression
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import uuid

class Base(AsyncAttrs, DeclarativeBase):
    """Enhanced base class with common patterns for all models."""
    
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
    
    @hybrid_property
    def is_active(self) -> bool:
        """Check if record is not soft-deleted."""
        return self.deleted_at is None

# User Management (Future-proofing for authentication)
class User(Base):
    """
    User model with comprehensive profile and preference management.
    
    Designed for scalability with authentication, personalization,
    and advanced user analytics capabilities.
    """
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        index=True
    )
    
    # Core user information
    username: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        nullable=False,
        index=True
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255), 
        unique=True, 
        nullable=True,
        index=True
    )
    
    # Profile information
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    language: Mapped[str] = mapped_column(String(10), default="en")
    
    # User preferences (JSONB for flexibility)
    preferences: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, 
        nullable=False, 
        default=dict
    )
    
    # Psychology and coaching preferences
    psychology_profile: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict
    )
    
    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    entries: Mapped[List["Entry"]] = relationship(
        "Entry", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    sessions: Mapped[List["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    topics: Mapped[List["Topic"]] = relationship(
        "Topic",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_users_active_created', 'is_active', 'created_at'),
        Index('ix_users_preferences_gin', 'preferences', postgresql_using='gin'),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"

# Topic Management with Enhanced Features
class Topic(Base):
    """
    Enhanced topic model with hierarchical organization and analytics.
    
    Features:
    - Hierarchical topic organization (parent/child relationships)
    - Rich metadata for psychology integration
    - Usage analytics and statistics
    - Color coding and visual customization
    """
    __tablename__ = "topics"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    # Core topic information
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    color: Mapped[str] = mapped_column(String(7), default="#3B82F6")  # Hex color
    icon: Mapped[Optional[str]] = mapped_column(String(50))  # Icon identifier
    
    # Hierarchical organization
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # User association
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Topic metadata and psychology integration
    tags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    psychology_domains: Mapped[List[str]] = mapped_column(JSONB, default=list)
    context_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Analytics and statistics
    entry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_entry_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    usage_statistics: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="topics")
    parent: Mapped[Optional["Topic"]] = relationship(
        "Topic", 
        remote_side=[id], 
        back_populates="children"
    )
    children: Mapped[List["Topic"]] = relationship(
        "Topic", 
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    entries: Mapped[List["Entry"]] = relationship(
        "Entry", 
        back_populates="topic"
    )
    
    # Constraints and indexes
    __table_args__ = (
        Index('ix_topics_user_name', 'user_id', 'name'),
        Index('ix_topics_parent_sort', 'parent_id', 'sort_order'),
        Index('ix_topics_psychology_gin', 'psychology_domains', postgresql_using='gin'),
        UniqueConstraint('user_id', 'name', 'parent_id', name='uq_topics_user_name_parent'),
    )

# Entry Templates for Structured Journaling
class EntryTemplate(Base):
    """
    Advanced entry templates with psychology integration and customization.
    
    Features:
    - Structured prompts and questions
    - Psychology domain alignment
    - User customization and sharing
    - Usage analytics and effectiveness tracking
    """
    __tablename__ = "entry_templates"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    # Template identification
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Template content
    content_template: Mapped[str] = mapped_column(Text, nullable=False)
    prompts: Mapped[List[str]] = mapped_column(JSONB, default=list)
    guided_questions: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    
    # Psychology integration
    psychology_domains: Mapped[List[str]] = mapped_column(JSONB, default=list)
    therapeutic_techniques: Mapped[List[str]] = mapped_column(JSONB, default=list)
    
    # Template metadata
    tags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    difficulty_level: Mapped[str] = mapped_column(String(20), default="beginner")
    estimated_time_minutes: Mapped[int] = mapped_column(Integer, default=10)
    
    # Usage and sharing
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    effectiveness_rating: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    
    # Owner (optional for public templates)
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationships
    created_by: Mapped[Optional["User"]] = relationship("User")
    
    __table_args__ = (
        Index('ix_templates_category_public', 'category', 'is_public'),
        Index('ix_templates_psychology_gin', 'psychology_domains', postgresql_using='gin'),
        Index('ix_templates_usage', 'usage_count', 'effectiveness_rating'),
    )

# Advanced Journal Entry Model
class Entry(Base):
    """
    Comprehensive journal entry model with advanced features.
    
    Features:
    - Full-text search with PostgreSQL TSVECTOR
    - Versioning and revision history
    - Rich metadata and psychology integration
    - Sentiment analysis and mood tracking
    - Advanced tagging and categorization
    """
    __tablename__ = "entries"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    # Core entry content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Entry classification
    entry_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        default="journal"
    )
    
    # User and topic associations
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("topics.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Content analysis and metadata
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    reading_time_minutes: Mapped[int] = mapped_column(Integer, default=1)
    
    # Sentiment and mood analysis
    mood: Mapped[Optional[str]] = mapped_column(String(50))
    sentiment_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    emotion_analysis: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Tagging and categorization
    tags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    auto_tags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    psychology_tags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    
    # User interaction features
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    is_private: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Versioning support
    version: Mapped[int] = mapped_column(Integer, default=1)
    parent_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entries.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # Template support
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entry_templates.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Full-text search support
    search_vector: Mapped[Optional[str]] = mapped_column(TSVECTOR)
    
    # Rich metadata for psychology integration
    psychology_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    analysis_results: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="entries")
    topic: Mapped[Optional["Topic"]] = relationship("Topic", back_populates="entries")
    template: Mapped[Optional["EntryTemplate"]] = relationship("EntryTemplate")
    parent_entry: Mapped[Optional["Entry"]] = relationship(
        "Entry", 
        remote_side=[id],
        back_populates="versions"
    )
    versions: Mapped[List["Entry"]] = relationship(
        "Entry",
        back_populates="parent_entry",
        cascade="all, delete-orphan"
    )
    
    # Advanced indexing strategy
    __table_args__ = (
        # Performance indexes
        Index('ix_entries_user_created', 'user_id', 'created_at'),
        Index('ix_entries_topic_created', 'topic_id', 'created_at'),
        Index('ix_entries_mood_sentiment', 'mood', 'sentiment_score'),
        Index('ix_entries_favorites', 'user_id', 'is_favorite', 'created_at'),
        
        # Full-text search indexes
        Index('ix_entries_search_vector', 'search_vector', postgresql_using='gin'),
        Index('ix_entries_title_text', 'title', postgresql_using='gin', postgresql_ops={'title': 'gin_trgm_ops'}),
        
        # JSONB indexes for metadata queries
        Index('ix_entries_tags_gin', 'tags', postgresql_using='gin'),
        Index('ix_entries_psychology_gin', 'psychology_metadata', postgresql_using='gin'),
        Index('ix_entries_analysis_gin', 'analysis_results', postgresql_using='gin'),
        
        # Constraints
        CheckConstraint('word_count >= 0', name='ck_entries_word_count_positive'),
        CheckConstraint('version >= 1', name='ck_entries_version_positive'),
        CheckConstraint('sentiment_score BETWEEN -1 AND 1', name='ck_entries_sentiment_range'),
    )
    
    @validates('content')
    def validate_content(self, key, content):
        """Automatically update word count when content changes."""
        if content:
            self.word_count = len(content.split())
            self.reading_time_minutes = max(1, self.word_count // 200)  # ~200 WPM
        return content

# Chat Session Management
class ChatSession(Base):
    """
    Advanced chat session model with comprehensive conversation management.
    
    Features:
    - Multiple session types with different AI personalities
    - Rich metadata and context tracking
    - Psychology integration and insights
    - Performance analytics and optimization
    """
    __tablename__ = "chat_sessions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    # Session identification
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Session type and configuration
    session_type: Mapped[str] = mapped_column(String(50), nullable=False)
    personality_config: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # User association
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Session status and management
    status: Mapped[str] = mapped_column(String(20), default="active")
    last_activity: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Session analytics
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    total_duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    average_response_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Psychology and coaching integration
    psychology_insights: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    coaching_notes: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    progress_tracking: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Tagging and categorization
    tags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    auto_tags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    
    # Session metadata
    session_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at"
    )
    
    __table_args__ = (
        Index('ix_sessions_user_created', 'user_id', 'created_at'),
        Index('ix_sessions_type_status', 'session_type', 'status'),
        Index('ix_sessions_activity', 'last_activity'),
        Index('ix_sessions_psychology_gin', 'psychology_insights', postgresql_using='gin'),
    )

# Chat Message Storage
class ChatMessage(Base):
    """
    Comprehensive chat message model with advanced analytics and context.
    
    Features:
    - Rich message metadata and analysis
    - Sentiment tracking and psychology insights
    - Performance monitoring and optimization
    - Context preservation and retrieval
    """
    __tablename__ = "chat_messages"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    # Message association
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Message content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system
    
    # Message timing and performance
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Message analysis
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    character_count: Mapped[int] = mapped_column(Integer, default=0)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    emotion_analysis: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Psychology and coaching context
    psychology_context: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    coaching_insights: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Message metadata
    message_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # AI model information (for assistant messages)
    model_used: Mapped[Optional[str]] = mapped_column(String(100))
    model_parameters: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Relationships
    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")
    
    __table_args__ = (
        Index('ix_messages_session_timestamp', 'session_id', 'timestamp'),
        Index('ix_messages_role_timestamp', 'role', 'timestamp'),
        Index('ix_messages_sentiment', 'sentiment_score'),
        Index('ix_messages_psychology_gin', 'psychology_context', postgresql_using='gin'),
    )
    
    @validates('content')
    def validate_content(self, key, content):
        """Automatically update word and character counts."""
        if content:
            self.word_count = len(content.split())
            self.character_count = len(content)
        return content