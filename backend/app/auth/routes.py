# backend/app/auth/routes.py
"""
Authentication API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from .schemas import (
    UserCreate, UserResponse, UserUpdate, UserProfile,
    LoginRequest, TokenResponse, RefreshTokenRequest,
    PasswordChange, PasswordReset, PasswordResetConfirm,
    EmailVerification, AuthStatus, SecurityInfo,
    LoginAttemptResponse, AuthConfig, ApiError,
    AdminUserCreate, AdminUserUpdate, SessionInfo, SecurityStats
)
from .service import (
    AuthService, UserExistsError, InvalidCredentialsError, 
    AccountLockedError, TokenExpiredError
)
from .models import UserRole
from .dependencies import (
    get_auth_service, get_current_user, get_current_user_optional,
    get_current_verified_user, get_current_superuser,
    login_rate_limit, register_rate_limit, password_reset_rate_limit,
    CurrentUser, CurrentUserOptional, CurrentVerifiedUser, CurrentSuperuser,
    ClientInfo, require_user_id_match
)
from ..core.database import get_db
from ..core.config import settings


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ApiError, "description": "Registration validation failed"},
        409: {"model": ApiError, "description": "User already exists"},
        429: {"model": ApiError, "description": "Too many registration attempts"}
    }
)
async def register_user(
    user_data: UserCreate,
    client_info: ClientInfo,
    auth_service: AuthService = Depends(get_auth_service),
    _rate_limit: None = Depends(register_rate_limit)
):
    """
    Register a new user account.
    
    - **username**: Unique username (3-50 characters, alphanumeric + underscore/hyphen)
    - **email**: Valid email address
    - **password**: Password meeting security requirements
    - **password_confirm**: Password confirmation (must match)
    - **display_name**: Optional display name
    - **timezone**: User timezone (default: UTC)
    - **language**: Preferred language (default: en)
    """
    try:
        user = await auth_service.register_user(
            user_data, 
            ip_address=client_info["ip_address"]
        )
        
        return UserResponse.from_orm(user)
        
    except UserExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        401: {"model": ApiError, "description": "Invalid credentials"},
        423: {"model": ApiError, "description": "Account locked"},
        429: {"model": ApiError, "description": "Too many login attempts"}
    }
)
async def login_user(
    login_data: LoginRequest,
    client_info: ClientInfo,
    auth_service: AuthService = Depends(get_auth_service),
    _rate_limit: None = Depends(login_rate_limit)
):
    """
    Authenticate user and return access/refresh tokens.
    
    - **username_or_email**: Username or email address
    - **password**: User password
    - **remember_me**: Extend session duration (optional)
    """
    try:
        user, tokens = await auth_service.authenticate_user(
            login_data,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"]
        )
        
        return TokenResponse(**tokens)
        
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    except AccountLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=str(e)
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={
        401: {"model": ApiError, "description": "Invalid or expired refresh token"}
    }
)
async def refresh_access_token(
    refresh_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token.
    
    - **refresh_token**: Valid refresh token
    """
    try:
        tokens = await auth_service.refresh_token(refresh_data.refresh_token)
        return TokenResponse(**tokens)
        
    except TokenExpiredError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ApiError, "description": "Not authenticated"}
    }
)
async def logout_user(
    refresh_data: RefreshTokenRequest,
    current_user: CurrentUser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout user by revoking refresh token.
    
    - **refresh_token**: Refresh token to revoke
    """
    await auth_service.logout_user(
        str(current_user.id), 
        refresh_data.refresh_token
    )


@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ApiError, "description": "Not authenticated"}
    }
)
async def logout_all_sessions(
    current_user: CurrentUser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout user from all sessions by revoking all refresh tokens.
    """
    await auth_service.logout_user(str(current_user.id))


@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        401: {"model": ApiError, "description": "Not authenticated"}
    }
)
async def get_current_user_info(current_user: CurrentUser):
    """
    Get current user information.
    """
    return UserResponse.from_orm(current_user)


@router.get(
    "/me/profile",
    response_model=UserProfile,
    responses={
        401: {"model": ApiError, "description": "Not authenticated"}
    }
)
async def get_current_user_profile(current_user: CurrentUser):
    """
    Get detailed current user profile including security information.
    """
    return UserProfile.from_orm(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
    responses={
        401: {"model": ApiError, "description": "Not authenticated"}
    }
)
async def update_current_user(
    user_update: UserUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user profile information.
    
    - **display_name**: Display name (optional)
    - **timezone**: User timezone (optional)
    - **language**: Preferred language (optional)
    """
    # Update user fields
    if user_update.display_name is not None:
        current_user.display_name = user_update.display_name
    if user_update.timezone is not None:
        current_user.timezone = user_update.timezone
    if user_update.language is not None:
        current_user.language = user_update.language
    
    await db.commit()
    await db.refresh(current_user)
    
    return UserResponse.from_orm(current_user)


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        400: {"model": ApiError, "description": "Password validation failed"},
        401: {"model": ApiError, "description": "Not authenticated or invalid current password"}
    }
)
async def change_password(
    password_data: PasswordChange,
    current_user: CurrentUser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Change user password.
    
    - **current_password**: Current password
    - **new_password**: New password meeting security requirements
    - **new_password_confirm**: New password confirmation
    """
    try:
        await auth_service.change_password(str(current_user.id), password_data)
        
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/request-password-reset",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        429: {"model": ApiError, "description": "Too many reset requests"}
    }
)
async def request_password_reset(
    reset_data: PasswordReset,
    auth_service: AuthService = Depends(get_auth_service),
    _rate_limit: None = Depends(password_reset_rate_limit)
):
    """
    Request password reset token (sent via email).
    
    - **email**: Email address associated with account
    
    Note: Always returns success for security reasons, even if email doesn't exist.
    """
    # Always return success to prevent email enumeration
    await auth_service.request_password_reset(reset_data.email)


@router.post(
    "/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        400: {"model": ApiError, "description": "Password validation failed"},
        401: {"model": ApiError, "description": "Invalid or expired reset token"}
    }
)
async def reset_password(
    reset_data: PasswordResetConfirm,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Reset password using reset token.
    
    - **token**: Password reset token (from email)
    - **new_password**: New password meeting security requirements
    - **new_password_confirm**: New password confirmation
    """
    try:
        await auth_service.reset_password(reset_data)
        
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired reset token"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/verify-email",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ApiError, "description": "Invalid or expired verification token"}
    }
)
async def verify_email(
    verification_data: EmailVerification,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Verify email address using verification token.
    
    - **token**: Email verification token (from email)
    """
    success = await auth_service.verify_email(verification_data.token)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired verification token"
        )


@router.get(
    "/status",
    response_model=AuthStatus
)
async def get_auth_status(current_user: CurrentUserOptional):
    """
    Get current authentication status.
    
    Works with or without authentication - returns user info if authenticated.
    """
    if current_user:
        return AuthStatus(
            authenticated=True,
            user=UserResponse.from_orm(current_user),
            permissions=["user"] + (["admin"] if current_user.is_superuser else [])
        )
    else:
        return AuthStatus(authenticated=False)


@router.get(
    "/me/security",
    response_model=SecurityInfo,
    responses={
        401: {"model": ApiError, "description": "Not authenticated"}
    }
)
async def get_security_info(
    current_user: CurrentUser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get user security information and statistics.
    """
    # Count active sessions (refresh tokens)
    from sqlalchemy import select, func
    from .models import RefreshToken
    from datetime import datetime
    
    db = auth_service.db
    
    stmt = select(func.count(RefreshToken.id)).where(
        RefreshToken.user_id == current_user.id,
        RefreshToken.is_revoked == False,
        RefreshToken.expires_at > datetime.utcnow()
    )
    active_sessions = await db.scalar(stmt) or 0
    
    return SecurityInfo(
        failed_login_attempts=current_user.failed_login_attempts,
        is_locked=current_user.is_locked,
        locked_until=current_user.locked_until,
        last_login=current_user.last_login,
        last_login_ip=current_user.last_login_ip,
        password_changed_at=current_user.password_changed_at,
        active_sessions=active_sessions
    )


@router.get(
    "/me/login-history",
    response_model=List[LoginAttemptResponse],
    responses={
        401: {"model": ApiError, "description": "Not authenticated"}
    }
)
async def get_login_history(
    current_user: CurrentUser,
    limit: int = 50,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get user's login attempt history.
    
    - **limit**: Maximum number of records to return (default: 50, max: 100)
    """
    limit = min(limit, 100)  # Cap at 100 for performance
    
    attempts = await auth_service.get_login_attempts(
        user_id=str(current_user.id),
        limit=limit
    )
    
    return [LoginAttemptResponse.from_orm(attempt) for attempt in attempts]


@router.get(
    "/config",
    response_model=AuthConfig
)
async def get_auth_config():
    """
    Get authentication configuration for client-side validation.
    """
    return AuthConfig(
        password_min_length=settings.security.password_min_length,
        password_require_uppercase=settings.security.password_require_uppercase,
        password_require_lowercase=settings.security.password_require_lowercase,
        password_require_numbers=settings.security.password_require_numbers,
        access_token_expire_minutes=settings.security.access_token_expire_minutes
    )


# Admin endpoints
admin_router = APIRouter(prefix="/admin", tags=["Admin"])


@admin_router.get(
    "/users",
    response_model=List[UserProfile],
    responses={
        401: {"model": ApiError, "description": "Not authenticated"},
        403: {"model": ApiError, "description": "Admin privileges required"}
    }
)
async def list_users(
    current_superuser: CurrentSuperuser,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    List all users (admin only).
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100, max: 1000)
    """
    from sqlalchemy import select
    from .models import AuthUser
    
    limit = min(limit, 1000)  # Cap at 1000 for performance
    
    stmt = select(AuthUser).offset(skip).limit(limit).order_by(AuthUser.created_at.desc())
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    return [UserProfile.from_orm(user) for user in users]


@admin_router.get(
    "/login-attempts",
    response_model=List[LoginAttemptResponse],
    responses={
        401: {"model": ApiError, "description": "Not authenticated"},
        403: {"model": ApiError, "description": "Admin privileges required"}
    }
)
async def list_login_attempts(
    current_superuser: CurrentSuperuser,
    ip_address: str = None,
    limit: int = 100,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    List login attempts (admin only).
    
    - **ip_address**: Filter by IP address (optional)
    - **limit**: Maximum number of records to return (default: 100, max: 1000)
    """
    limit = min(limit, 1000)  # Cap at 1000 for performance
    
    attempts = await auth_service.get_login_attempts(
        ip_address=ip_address,
        limit=limit
    )
    
    return [LoginAttemptResponse.from_orm(attempt) for attempt in attempts]


@admin_router.post(
    "/cleanup-tokens",
    responses={
        401: {"model": ApiError, "description": "Not authenticated"},
        403: {"model": ApiError, "description": "Admin privileges required"}
    }
)
async def cleanup_expired_tokens(
    current_superuser: CurrentSuperuser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Clean up expired tokens and old login attempts (admin only).
    """
    cleaned_count = await auth_service.cleanup_expired_tokens()
    
    return {"message": f"Cleaned up {cleaned_count} expired records"}


@admin_router.post(
    "/users/create",
    response_model=UserProfile,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ApiError, "description": "User creation validation failed"},
        401: {"model": ApiError, "description": "Not authenticated"},
        403: {"model": ApiError, "description": "Admin privileges required"},
        409: {"model": ApiError, "description": "User already exists"}
    }
)
async def admin_create_user(
    user_data: AdminUserCreate,
    current_superuser: CurrentSuperuser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Create new user with role assignment (admin only).
    """
    try:
        user = await auth_service.create_user_admin(
            user_data, 
            role=user_data.role,
            admin_user_id=str(current_superuser.id)
        )
        return UserProfile.from_orm(user)
        
    except UserExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@admin_router.put(
    "/users/{user_id}",
    response_model=UserProfile,
    responses={
        401: {"model": ApiError, "description": "Not authenticated"},
        403: {"model": ApiError, "description": "Admin privileges required"},
        404: {"model": ApiError, "description": "User not found"}
    }
)
async def admin_update_user(
    user_id: str,
    user_updates: AdminUserUpdate,
    current_superuser: CurrentSuperuser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Update user information and role (admin only).
    """
    updates = user_updates.dict(exclude_unset=True)
    
    user = await auth_service.update_user_admin(
        user_id, 
        updates,
        admin_user_id=str(current_superuser.id)
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserProfile.from_orm(user)


@admin_router.get(
    "/users/{user_id}/sessions",
    response_model=List[SessionInfo],
    responses={
        401: {"model": ApiError, "description": "Not authenticated"},
        403: {"model": ApiError, "description": "Admin privileges required"}
    }
)
async def admin_get_user_sessions(
    user_id: str,
    current_superuser: CurrentSuperuser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get all active sessions for a user (admin only).
    """
    sessions = await auth_service.get_user_sessions_admin(user_id)
    
    return [
        SessionInfo(
            id=session.id,
            user_id=session.user_id,
            created_ip=session.created_ip,
            user_agent=session.user_agent,
            expires_at=session.expires_at,
            created_at=session.created_at
        )
        for session in sessions
    ]


@admin_router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ApiError, "description": "Not authenticated"},
        403: {"model": ApiError, "description": "Admin privileges required"},
        404: {"model": ApiError, "description": "Session not found"}
    }
)
async def admin_revoke_session(
    session_id: str,
    current_superuser: CurrentSuperuser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Force logout a specific user session (admin only).
    """
    success = await auth_service.revoke_user_session_admin(
        session_id, 
        str(current_superuser.id)
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or already revoked"
        )


@admin_router.get(
    "/security/stats",
    response_model=SecurityStats,
    responses={
        401: {"model": ApiError, "description": "Not authenticated"},
        403: {"model": ApiError, "description": "Admin privileges required"}
    }
)
async def admin_get_security_stats(
    current_superuser: CurrentSuperuser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get security statistics and metrics (admin only).
    """
    stats = await auth_service.get_security_stats_admin()
    return SecurityStats(**stats)


# Include admin routes in main router
router.include_router(admin_router)