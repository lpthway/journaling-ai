# backend/app/auth/models.py
"""
Authentication-specific models and extensions to the base User model.
"""

from sqlalchemy import String, Boolean, DateTime, func, Index, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum as PyEnum
import uuid

from ..models.base import Base


class UserRole(PyEnum):
    """User role enumeration for role-based access control."""
    USER = "user"
    ADMIN = "admin"
    SUPERUSER = "superuser"


class AuthUser(Base):
    """
    Authentication extension to the User model with secure credentials.
    
    This model extends the base User model with authentication-specific fields
    while maintaining compatibility with the existing user management system.
    """
    __tablename__ = "auth_users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        index=True
    )
    
    # Core authentication information
    username: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        nullable=False,
        index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        nullable=False,
        index=True
    )
    
    # Secure password storage
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Account status and verification
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Role-based access control
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum"),
        nullable=False,
        default=UserRole.USER,
        index=True
    )
    
    # Password security
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    failed_login_attempts: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Authentication tracking
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(45))  # IPv6 support
    
    # Email verification
    verification_token: Mapped[Optional[str]] = mapped_column(String(255))
    verification_token_expires: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Password reset
    reset_token: Mapped[Optional[str]] = mapped_column(String(255))
    reset_token_expires: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # User profile information (optional)
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    language: Mapped[str] = mapped_column(String(10), default="en")
    
    # Relationships with refresh tokens
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Relationships with user data (added for enhanced models)
    entries: Mapped[List["Entry"]] = relationship(
        "Entry",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    topics: Mapped[List["Topic"]] = relationship(
        "Topic", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    sessions: Mapped[List["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    
    # Security indexes
    __table_args__ = (
        Index('ix_auth_users_email_active', 'email', 'is_active'),
        Index('ix_auth_users_username_active', 'username', 'is_active'),
        Index('ix_auth_users_verification', 'verification_token'),
        Index('ix_auth_users_reset', 'reset_token'),
        Index('ix_auth_users_locked', 'locked_until'),
    )
    
    def __repr__(self) -> str:
        return f"<AuthUser(id={self.id}, username={self.username})>"

    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked due to failed login attempts."""
        if not self.locked_until:
            return False
        return datetime.utcnow() < self.locked_until
    
    @property
    def can_reset_password(self) -> bool:
        """Check if user can reset password (has valid reset token)."""
        if not self.reset_token or not self.reset_token_expires:
            return False
        return datetime.utcnow() < self.reset_token_expires
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return self.role in [UserRole.ADMIN, UserRole.SUPERUSER] or self.is_superuser
    
    def has_role(self, required_role: UserRole) -> bool:
        """Check if user has the required role or higher."""
        role_hierarchy = {
            UserRole.USER: 1,
            UserRole.ADMIN: 2,
            UserRole.SUPERUSER: 3
        }
        user_level = role_hierarchy.get(self.role, 0)
        required_level = role_hierarchy.get(required_role, 999)
        return user_level >= required_level or self.is_superuser


class RefreshToken(Base):
    """
    Refresh token model for secure JWT token management.
    
    Implements secure refresh token rotation with automatic cleanup.
    """
    __tablename__ = "refresh_tokens"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    # Token information
    token: Mapped[str] = mapped_column(String(512), unique=True, nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Token lifecycle
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Security tracking
    created_ip: Mapped[Optional[str]] = mapped_column(String(45))  # IPv6 support
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Token rotation support
    replaced_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    
    # Relationships
    user: Mapped["AuthUser"] = relationship("AuthUser", back_populates="refresh_tokens")
    
    # Performance indexes
    __table_args__ = (
        Index('ix_refresh_tokens_user_active', 'user_id', 'is_revoked', 'expires_at'),
        Index('ix_refresh_tokens_cleanup', 'expires_at', 'is_revoked'),
    )
    
    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not revoked and not expired)."""
        return not self.is_revoked and not self.is_expired


class LoginAttempt(Base):
    """
    Login attempt tracking for security monitoring and rate limiting.
    """
    __tablename__ = "login_attempts"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    # Attempt information
    username_or_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False, index=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    
    # User ID (if successful login)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )
    
    # Failure reason (if unsuccessful)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Timestamp
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # Performance and security indexes
    __table_args__ = (
        Index('ix_login_attempts_user_time', 'username_or_email', 'attempted_at'),
        Index('ix_login_attempts_ip_time', 'ip_address', 'attempted_at'),
        Index('ix_login_attempts_success_time', 'success', 'attempted_at'),
    )
    
    def __repr__(self) -> str:
        return f"<LoginAttempt(username={self.username_or_email}, success={self.success})>"