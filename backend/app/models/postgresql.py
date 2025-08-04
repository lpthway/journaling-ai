# backend/app/models/postgresql.py - Enterprise SQLAlchemy Models

from datetime import datetime, date
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, Date,
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class User(Base):
    """User model with privacy controls and preferences"""
    __tablename__ = "users"
    
    # Primary Key
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Basic Information
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Privacy & Security
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    privacy_level: Mapped[str] = mapped_column(String(20), default="private", nullable=False)
    
    # Preferences (JSONB for flexibility)
    preferences: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=lambda: {
        "language": "en",
        "timezone": "UTC",
        "ai_model": "llama3.2",
        "sentiment_analysis": True,
        "psychology_insights": True,
        "notification_settings": {
            "daily_reflection": True,
            "weekly_summary": False,
            "mood_alerts": True
        }
    })
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    entries = relationship("JournalEntry", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    analytics = relationship("UserAnalytics", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_users_username", "username"),
        Index("idx_users_email", "email"),
        Index("idx_users_created_at", "created_at"),
        CheckConstraint("privacy_level IN ('public', 'friends', 'private')", name="check_privacy_level")
    )

class JournalEntry(Base):
    """Journal entries with rich metadata and analysis"""
    __tablename__ = "journal_entries"
    
    # Primary Key
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign Keys
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    
    # Content
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    raw_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Original before processing
    
    # Metadata
    entry_date: Mapped[date] = mapped_column(Date, nullable=False, default=func.current_date())
    mood_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    
    # AI Analysis Results (JSONB for performance and flexibility)
    sentiment_analysis: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    emotion_analysis: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    topic_analysis: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    psychology_insights: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    # Vector Embeddings (for semantic search)
    embedding_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    embedding_vector: Mapped[Optional[List[float]]] = mapped_column(ARRAY(Float), nullable=True)
    
    # Classification & Tags
    categories: Mapped[List[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    is_private: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="entries")
    conversations = relationship("Conversation", back_populates="entry")
    
    # Performance Indexes
    __table_args__ = (
        Index("idx_entries_user_date", "user_id", "entry_date"),
        Index("idx_entries_user_created", "user_id", "created_at"),
        Index("idx_entries_mood", "mood_score"),
        Index("idx_entries_categories", "categories", postgresql_using="gin"),
        Index("idx_entries_tags", "tags", postgresql_using="gin"),
        Index("idx_entries_content_search", "content", postgresql_using="gin", postgresql_ops={"content": "gin_trgm_ops"}),
        CheckConstraint("mood_score >= 1.0 AND mood_score <= 10.0", name="check_mood_range"),
        CheckConstraint("word_count >= 0", name="check_word_count")
    )

class ChatSession(Base):
    """Chat sessions for AI conversations"""
    __tablename__ = "chat_sessions"
    
    # Primary Key
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign Keys
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    
    # Session Metadata
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    session_type: Mapped[str] = mapped_column(String(50), default="general", nullable=False)
    context: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, default=dict)
    
    # AI Configuration
    ai_model: Mapped[str] = mapped_column(String(50), default="llama3.2", nullable=False)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    temperature: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    
    # Session State
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_activity: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    conversations = relationship("Conversation", back_populates="session", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_sessions_user_activity", "user_id", "last_activity"),
        Index("idx_sessions_user_created", "user_id", "created_at"),
        Index("idx_sessions_type", "session_type"),
        CheckConstraint("temperature >= 0.0 AND temperature <= 2.0", name="check_temperature_range"),
        CheckConstraint("session_type IN ('general', 'therapy', 'analysis', 'reflection')", name="check_session_type")
    )

class Conversation(Base):
    """Individual messages within chat sessions"""
    __tablename__ = "conversations"
    
    # Primary Key
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign Keys
    session_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("chat_sessions.id"), nullable=False)
    entry_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("journal_entries.id"), nullable=True)
    
    # Message Content
    user_message: Mapped[str] = mapped_column(Text, nullable=False)
    ai_response: Mapped[str] = mapped_column(Text, nullable=False)
    
    # AI Processing Metadata
    processing_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_model_used: Mapped[str] = mapped_column(String(50), nullable=False)
    token_usage: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    # Sources & Citations
    sources_used: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSONB, nullable=True)
    citations: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    
    # Quality Metrics
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    user_feedback: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # thumbs_up, thumbs_down
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ChatSession", back_populates="conversations")
    entry = relationship("JournalEntry", back_populates="conversations")
    
    # Performance Indexes
    __table_args__ = (
        Index("idx_conversations_session_created", "session_id", "created_at"),
        Index("idx_conversations_entry", "entry_id"),
        Index("idx_conversations_processing_time", "processing_time_ms"),
        CheckConstraint("confidence_score >= 0.0 AND confidence_score <= 1.0", name="check_confidence_range"),
        CheckConstraint("user_feedback IN ('thumbs_up', 'thumbs_down')", name="check_feedback_values")
    )

class PsychologyContent(Base):
    """Psychology content database for AI responses"""
    __tablename__ = "psychology_content"
    
    # Primary Key
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Content Classification
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)  # technique, theory, exercise
    
    # Content
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metadata
    source: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    evidence_level: Mapped[str] = mapped_column(String(20), default="moderate", nullable=False)
    
    # Classification & Search
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    keywords: Mapped[List[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    
    # Vector Embeddings
    embedding_vector: Mapped[Optional[List[float]]] = mapped_column(ARRAY(Float), nullable=True)
    
    # Usage Tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    effectiveness_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Performance Indexes
    __table_args__ = (
        Index("idx_psychology_category", "category", "subcategory"),
        Index("idx_psychology_type", "content_type"),
        Index("idx_psychology_tags", "tags", postgresql_using="gin"),
        Index("idx_psychology_keywords", "keywords", postgresql_using="gin"),
        Index("idx_psychology_content_search", "content", postgresql_using="gin", postgresql_ops={"content": "gin_trgm_ops"}),
        Index("idx_psychology_effectiveness", "effectiveness_score"),
        CheckConstraint("evidence_level IN ('high', 'moderate', 'low', 'theoretical')", name="check_evidence_level"),
        CheckConstraint("content_type IN ('technique', 'theory', 'exercise', 'assessment', 'intervention')", name="check_content_type")
    )

class UserAnalytics(Base):
    """Pre-computed analytics for fast dashboard loading"""
    __tablename__ = "user_analytics"
    
    # Primary Key
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign Keys
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    
    # Analytics Period
    period_type: Mapped[str] = mapped_column(String(20), nullable=False)  # daily, weekly, monthly, yearly
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Entry Statistics
    total_entries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_words: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_mood: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Sentiment Trends (JSONB for complex analytics)
    sentiment_trends: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    emotion_patterns: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    topic_distribution: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    # Behavioral Insights
    writing_consistency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    peak_writing_hours: Mapped[Optional[List[int]]] = mapped_column(ARRAY(Integer), nullable=True)
    most_active_days: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    
    # Psychology Metrics
    stress_indicators: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    growth_metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    therapy_progress: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    # Performance Metadata
    computation_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    data_freshness: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="analytics")
    
    # Performance Indexes & Constraints
    __table_args__ = (
        Index("idx_analytics_user_period", "user_id", "period_type", "period_start"),
        Index("idx_analytics_freshness", "data_freshness"),
        Index("idx_analytics_computation", "computation_time_ms"),
        UniqueConstraint("user_id", "period_type", "period_start", name="uq_user_analytics_period"),
        CheckConstraint("period_type IN ('daily', 'weekly', 'monthly', 'yearly')", name="check_period_type"),
        CheckConstraint("avg_mood >= 1.0 AND avg_mood <= 10.0", name="check_avg_mood_range"),
        CheckConstraint("writing_consistency >= 0.0 AND writing_consistency <= 1.0", name="check_consistency_range")
    )

# Migration Tracking
class MigrationLog(Base):
    """Track data migration progress and validation"""
    __tablename__ = "migration_logs"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Migration Details
    migration_type: Mapped[str] = mapped_column(String(50), nullable=False)  # users, entries, sessions, etc.
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)
    records_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_successful: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Status & Validation
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    validation_passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    # Performance
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index("idx_migration_type_status", "migration_type", "status"),
        Index("idx_migration_started", "started_at"),
        CheckConstraint("status IN ('pending', 'running', 'completed', 'failed')", name="check_migration_status")
    )
