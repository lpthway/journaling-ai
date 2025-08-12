# backend/app/audit/models.py
"""
Audit log data models for comprehensive security tracking.
"""

from sqlalchemy import String, DateTime, Boolean, Text, Index, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
import uuid


class AuditBase(AsyncAttrs, DeclarativeBase):
    """Base class for audit tables with immutable design."""
    
    # Immutable audit fields - no updates allowed
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        index=True
    )
    
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # Correlation ID for tracing related events
    correlation_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)


class EventType(str, Enum):
    """Types of audit events."""
    USER_ACTION = "user_action"
    ADMIN_ACTION = "admin_action"
    AI_PROCESSING = "ai_processing"
    SECURITY_EVENT = "security_event"
    SYSTEM_EVENT = "system_event"


class ActionType(str, Enum):
    """Specific action types."""
    # User actions
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE_ENTRY = "create_entry"
    UPDATE_ENTRY = "update_entry"
    DELETE_ENTRY = "delete_entry"
    VIEW_ENTRY = "view_entry"
    EXPORT_DATA = "export_data"
    DELETE_ACCOUNT = "delete_account"
    
    # Admin actions
    ADMIN_LOGIN = "admin_login"
    VIEW_USER_DATA = "view_user_data"
    ADMIN_CREATE_USER = "admin_create_user"
    ADMIN_UPDATE_USER = "admin_update_user"
    ADMIN_DELETE_USER = "admin_delete_user"
    KEY_ROTATION = "key_rotation"
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    
    # AI processing
    AI_ANALYSIS_START = "ai_analysis_start"
    AI_ANALYSIS_COMPLETE = "ai_analysis_complete"
    DATA_DECRYPT_FOR_AI = "data_decrypt_for_ai"
    
    # Security events
    FAILED_LOGIN = "failed_login"
    ACCOUNT_LOCKED = "account_locked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    ENCRYPTION_KEY_ACCESS = "encryption_key_access"


class AuditEvent(AuditBase):
    """
    Universal audit event table for all security events.
    
    Designed for immutability and compliance requirements.
    """
    __tablename__ = "audit_events"
    
    # Event classification
    event_type: Mapped[EventType] = mapped_column(
        SQLEnum(EventType, name="event_type_enum"),
        nullable=False,
        index=True
    )
    action_type: Mapped[ActionType] = mapped_column(
        SQLEnum(ActionType, name="action_type_enum"),
        nullable=False,
        index=True
    )
    
    # Actor information
    user_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    admin_user_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    
    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    request_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Event details
    resource_type: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Security and compliance data
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    risk_level: Mapped[str] = mapped_column(String(20), default="low", index=True)
    compliance_tags: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Additional context data
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Data sensitivity markers
    contains_pii: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    data_classification: Mapped[str] = mapped_column(String(50), default="internal")
    
    # Performance and technical details
    response_time_ms: Mapped[Optional[int]] = mapped_column()
    error_code: Mapped[Optional[str]] = mapped_column(String(100))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Comprehensive indexing for performance and querying
    __table_args__ = (
        # Time-based queries (most common)
        Index('ix_audit_events_timestamp_desc', 'timestamp', postgresql_using='btree'),
        Index('ix_audit_events_date_trunc', func.date_trunc('day', 'timestamp')),
        
        # User activity queries
        Index('ix_audit_events_user_time', 'user_id', 'timestamp'),
        Index('ix_audit_events_user_action', 'user_id', 'action_type'),
        
        # Admin activity queries
        Index('ix_audit_events_admin_time', 'admin_user_id', 'timestamp'),
        Index('ix_audit_events_admin_actions', 'admin_user_id', 'action_type'),
        
        # Security monitoring
        Index('ix_audit_events_security', 'event_type', 'success', 'timestamp'),
        Index('ix_audit_events_risk', 'risk_level', 'timestamp'),
        Index('ix_audit_events_failed', 'success', 'timestamp', postgresql_where='success = false'),
        
        # Resource access tracking
        Index('ix_audit_events_resource', 'resource_type', 'resource_id', 'timestamp'),
        
        # IP and session tracking
        Index('ix_audit_events_ip_time', 'ip_address', 'timestamp'),
        Index('ix_audit_events_session', 'session_id', 'timestamp'),
        
        # Compliance and data protection
        Index('ix_audit_events_pii', 'contains_pii', 'timestamp'),
        Index('ix_audit_events_classification', 'data_classification', 'timestamp'),
        
        # JSONB indexes for metadata queries
        Index('ix_audit_events_metadata_gin', 'metadata', postgresql_using='gin'),
        Index('ix_audit_events_compliance_gin', 'compliance_tags', postgresql_using='gin'),
    )
    
    def __repr__(self) -> str:
        return f"<AuditEvent(id={self.id}, action={self.action_type}, user={self.user_id})>"


# Specialized models for different event types (views on main table)
class UserAction(AuditEvent):
    """View model for user actions."""
    __mapper_args__ = {
        'polymorphic_identity': EventType.USER_ACTION,
        'polymorphic_on': AuditEvent.event_type
    }


class AdminAction(AuditEvent):
    """View model for admin actions."""
    __mapper_args__ = {
        'polymorphic_identity': EventType.ADMIN_ACTION,
        'polymorphic_on': AuditEvent.event_type
    }


class AIProcessingEvent(AuditEvent):
    """View model for AI processing events."""
    __mapper_args__ = {
        'polymorphic_identity': EventType.AI_PROCESSING,
        'polymorphic_on': AuditEvent.event_type
    }


class SecurityEvent(AuditEvent):
    """View model for security events."""
    __mapper_args__ = {
        'polymorphic_identity': EventType.SECURITY_EVENT,
        'polymorphic_on': AuditEvent.event_type
    }


# Data retention and compliance tables
class AuditRetentionPolicy(AuditBase):
    """Audit log retention policies for compliance."""
    __tablename__ = "audit_retention_policies"
    
    policy_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    event_types: Mapped[list] = mapped_column(JSONB, nullable=False)
    retention_days: Mapped[int] = mapped_column(nullable=False)
    archive_after_days: Mapped[Optional[int]] = mapped_column()
    delete_after_days: Mapped[Optional[int]] = mapped_column()
    
    # Compliance requirements
    compliance_framework: Mapped[str] = mapped_column(String(50), nullable=False)
    legal_hold_exempt: Mapped[bool] = mapped_column(Boolean, default=False)
    
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    __table_args__ = (
        Index('ix_retention_policies_active', 'is_active'),
        Index('ix_retention_policies_compliance', 'compliance_framework'),
    )


class AuditArchive(AuditBase):
    """Archived audit events for long-term storage."""
    __tablename__ = "audit_archive"
    
    original_event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    archived_from_table: Mapped[str] = mapped_column(String(100), nullable=False)
    archive_reason: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # Original event data (compressed/serialized)
    event_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    
    # Archive metadata
    archived_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    archive_policy_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    
    __table_args__ = (
        Index('ix_audit_archive_original', 'original_event_id'),
        Index('ix_audit_archive_table', 'archived_from_table'),
        Index('ix_audit_archive_date', 'archived_at'),
    )