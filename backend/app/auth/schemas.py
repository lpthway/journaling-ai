# backend/app/auth/schemas.py
"""
Pydantic schemas for authentication API requests and responses.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
import uuid


class UserBase(BaseModel):
    """Base user schema with common fields."""
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 characters)")
    email: EmailStr = Field(..., description="Valid email address")
    display_name: Optional[str] = Field(None, max_length=100, description="Display name")
    timezone: str = Field(default="UTC", max_length=50, description="User timezone")
    language: str = Field(default="en", max_length=10, description="Preferred language")


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, max_length=128, description="Password (8-128 characters)")
    password_confirm: str = Field(..., description="Password confirmation")
    
    @validator('password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must contain only letters, numbers, hyphens, and underscores')
        return v.lower()


class UserUpdate(BaseModel):
    """Schema for user profile updates."""
    display_name: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)


class PasswordChange(BaseModel):
    """Schema for password change."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    new_password_confirm: str = Field(..., description="New password confirmation")
    
    @validator('new_password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('New passwords do not match')
        return v


class PasswordReset(BaseModel):
    """Schema for password reset request."""
    email: EmailStr = Field(..., description="Email address")


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    new_password_confirm: str = Field(..., description="New password confirmation")
    
    @validator('new_password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('New passwords do not match')
        return v


class EmailVerification(BaseModel):
    """Schema for email verification."""
    token: str = Field(..., description="Email verification token")


class LoginRequest(BaseModel):
    """Schema for login request."""
    username_or_email: str = Field(..., description="Username or email address")
    password: str = Field(..., description="Password")
    remember_me: bool = Field(default=False, description="Remember login for extended period")


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str = Field(..., description="Refresh token")


class UserResponse(BaseModel):
    """Schema for user response."""
    id: uuid.UUID
    username: str
    email: str
    display_name: Optional[str]
    timezone: str
    language: str
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    """Detailed user profile schema."""
    id: uuid.UUID
    username: str
    email: str
    display_name: Optional[str]
    timezone: str
    language: str
    is_active: bool
    is_verified: bool
    is_superuser: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    failed_login_attempts: int
    locked_until: Optional[datetime]
    
    class Config:
        from_attributes = True


class LoginAttemptResponse(BaseModel):
    """Schema for login attempt response."""
    id: uuid.UUID
    username_or_email: str
    success: bool
    ip_address: str
    user_agent: Optional[str]
    user_id: Optional[uuid.UUID]
    failure_reason: Optional[str]
    attempted_at: datetime
    
    class Config:
        from_attributes = True


class SecurityInfo(BaseModel):
    """Schema for user security information."""
    failed_login_attempts: int
    is_locked: bool
    locked_until: Optional[datetime]
    last_login: Optional[datetime]
    last_login_ip: Optional[str]
    password_changed_at: Optional[datetime]
    active_sessions: int


class AuthStatus(BaseModel):
    """Schema for authentication status."""
    authenticated: bool
    user: Optional[UserResponse] = None
    permissions: List[str] = []
    session_expires_at: Optional[datetime] = None


class ApiError(BaseModel):
    """Standard API error response."""
    detail: str
    error_code: Optional[str] = None
    errors: Optional[dict] = None


class AuthConfig(BaseModel):
    """Schema for authentication configuration."""
    password_min_length: int
    password_require_uppercase: bool
    password_require_lowercase: bool
    password_require_numbers: bool
    access_token_expire_minutes: int
    max_failed_login_attempts: int = 5
    lockout_duration_minutes: int = 30