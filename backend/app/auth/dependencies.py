# backend/app/auth/dependencies.py
"""
Authentication dependencies for FastAPI dependency injection.
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Annotated
import uuid

from .models import AuthUser
from .service import AuthService, TokenExpiredError
from .security import jwt_manager
from ..core.database import get_db


security = HTTPBearer(auto_error=False)


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Get authentication service instance."""
    return AuthService(db)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[AuthUser]:
    """
    Get current user from token (optional - returns None if not authenticated).
    
    Used for endpoints that work with or without authentication.
    """
    if not credentials:
        return None
    
    try:
        payload = jwt_manager.verify_token(credentials.credentials, "access")
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = await auth_service.get_user_by_id(user_id)
        if not user or not user.is_active:
            return None
        
        return user
        
    except Exception:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> AuthUser:
    """
    Get current user from token (required - raises exception if not authenticated).
    
    Used for protected endpoints that require authentication.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt_manager.verify_token(credentials.credentials, "access")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = await auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_verified_user(
    current_user: AuthUser = Depends(get_current_user)
) -> AuthUser:
    """
    Get current user but require email verification.
    
    Used for endpoints that require verified users.
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    
    return current_user


async def get_current_superuser(
    current_user: AuthUser = Depends(get_current_user)
) -> AuthUser:
    """
    Get current user but require superuser privileges.
    
    Used for admin-only endpoints.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges"
        )
    
    return current_user


def require_user_id_match(user_id_param: str):
    """
    Dependency factory to ensure user can only access their own resources.
    
    Args:
        user_id_param: The parameter name containing the user ID
        
    Returns:
        Dependency function that validates user ID
    """
    async def validate_user_id(
        request: Request,
        current_user: AuthUser = Depends(get_current_user)
    ) -> AuthUser:
        # Get user_id from path parameters
        path_params = request.path_params
        resource_user_id = path_params.get(user_id_param)
        
        if not resource_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID not provided"
            )
        
        try:
            resource_user_uuid = uuid.UUID(resource_user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        # Check if user is accessing their own resource or is superuser
        if current_user.id != resource_user_uuid and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return current_user
    
    return validate_user_id


class RateLimitDependency:
    """
    Rate limiting dependency to prevent abuse.
    """
    
    def __init__(self, max_attempts: int = 5, window_minutes: int = 15):
        self.max_attempts = max_attempts
        self.window_minutes = window_minutes
    
    async def __call__(
        self, 
        request: Request,
        auth_service: AuthService = Depends(get_auth_service)
    ):
        """Check rate limit for sensitive operations."""
        client_ip = self._get_client_ip(request)
        
        # Get recent login attempts from this IP
        from datetime import datetime, timedelta, timezone
        since_time = datetime.now(timezone.utc) - timedelta(minutes=self.window_minutes)
        
        attempts = await auth_service.get_login_attempts(
            ip_address=client_ip,
            limit=self.max_attempts + 1
        )
        
        # Filter attempts within the time window
        recent_attempts = [
            attempt for attempt in attempts 
            if attempt.attempted_at > since_time
        ]
        
        if len(recent_attempts) >= self.max_attempts:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many attempts. Try again in {self.window_minutes} minutes.",
                headers={"Retry-After": str(self.window_minutes * 60)}
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for X-Forwarded-For header (proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to client host
        return request.client.host if request.client else "unknown"


def get_client_info(request: Request) -> dict:
    """Extract client information from request for logging."""
    return {
        "ip_address": RateLimitDependency()._get_client_ip(request),
        "user_agent": request.headers.get("User-Agent", "unknown")
    }


# Pre-configured rate limit dependencies
login_rate_limit = RateLimitDependency(max_attempts=5, window_minutes=15)
register_rate_limit = RateLimitDependency(max_attempts=3, window_minutes=60)
password_reset_rate_limit = RateLimitDependency(max_attempts=3, window_minutes=60)

# Type annotations for common dependencies
CurrentUser = Annotated[AuthUser, Depends(get_current_user)]
CurrentUserOptional = Annotated[Optional[AuthUser], Depends(get_current_user_optional)]
CurrentVerifiedUser = Annotated[AuthUser, Depends(get_current_verified_user)]
CurrentSuperuser = Annotated[AuthUser, Depends(get_current_superuser)]
ClientInfo = Annotated[dict, Depends(get_client_info)]