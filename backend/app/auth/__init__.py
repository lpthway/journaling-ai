# backend/app/auth/__init__.py
"""
Authentication module providing comprehensive user management and security.

This module includes:
- JWT-based authentication with secure token management
- Password hashing and validation using bcrypt
- User registration and email verification
- Password reset functionality
- Rate limiting and security monitoring
- Role-based access control
- Session management with refresh token rotation
"""

from .models import AuthUser, RefreshToken, LoginAttempt
from .service import (
    AuthService, 
    AuthenticationError, 
    UserExistsError, 
    InvalidCredentialsError,
    AccountLockedError,
    TokenExpiredError
)
from .security import (
    PasswordValidator,
    PasswordHasher, 
    JWTManager,
    TokenGenerator,
    SecurityUtils,
    password_validator,
    password_hasher,
    jwt_manager,
    token_generator,
    security_utils
)
from .dependencies import (
    get_auth_service,
    get_current_user,
    get_current_user_optional,
    get_current_verified_user,
    get_current_superuser,
    require_user_id_match,
    CurrentUser,
    CurrentUserOptional,
    CurrentVerifiedUser,
    CurrentSuperuser,
    ClientInfo
)
from .routes import router as auth_router


__all__ = [
    # Models
    "AuthUser",
    "RefreshToken", 
    "LoginAttempt",
    
    # Service
    "AuthService",
    "AuthenticationError",
    "UserExistsError",
    "InvalidCredentialsError", 
    "AccountLockedError",
    "TokenExpiredError",
    
    # Security utilities
    "PasswordValidator",
    "PasswordHasher",
    "JWTManager", 
    "TokenGenerator",
    "SecurityUtils",
    "password_validator",
    "password_hasher",
    "jwt_manager",
    "token_generator",
    "security_utils",
    
    # Dependencies
    "get_auth_service",
    "get_current_user",
    "get_current_user_optional",
    "get_current_verified_user", 
    "get_current_superuser",
    "require_user_id_match",
    "CurrentUser",
    "CurrentUserOptional",
    "CurrentVerifiedUser",
    "CurrentSuperuser",
    "ClientInfo",
    
    # Router
    "auth_router"
]