# backend/app/auth/service.py
"""
Authentication service providing comprehensive user management and security.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update, delete
from sqlalchemy.exc import IntegrityError
import uuid
import secrets

from .models import AuthUser, RefreshToken, LoginAttempt, UserRole
from .schemas import UserCreate, LoginRequest, PasswordChange, PasswordReset, PasswordResetConfirm
from .security import (
    password_validator, 
    password_hasher, 
    jwt_manager, 
    token_generator,
    security_utils
)
from ..core.config import settings


class AuthenticationError(Exception):
    """Base exception for authentication errors."""
    pass


class UserExistsError(AuthenticationError):
    """Raised when trying to create a user that already exists."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid."""
    pass


class AccountLockedError(AuthenticationError):
    """Raised when account is locked due to failed login attempts."""
    pass


class TokenExpiredError(AuthenticationError):
    """Raised when token is expired."""
    pass


class AuthService:
    """Comprehensive authentication service."""
    
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def register_user(
        self, 
        user_data: UserCreate,
        ip_address: Optional[str] = None
    ) -> AuthUser:
        """
        Register a new user with validation and security checks.
        
        Args:
            user_data: User registration data
            ip_address: User's IP address for tracking
            
        Returns:
            AuthUser: Created user instance
            
        Raises:
            UserExistsError: If username or email already exists
            ValueError: If password validation fails
        """
        # Validate password
        is_valid, errors = password_validator.validate_password(user_data.password)
        if not is_valid:
            raise ValueError(f"Password validation failed: {', '.join(errors)}")
        
        # Check if user already exists
        existing_user = await self._get_user_by_username_or_email(
            user_data.username, user_data.email
        )
        if existing_user:
            if existing_user.username == user_data.username:
                raise UserExistsError("Username already exists")
            else:
                raise UserExistsError("Email already exists")
        
        # Create new user
        password_hash = password_hasher.hash_password(user_data.password)
        verification_token = token_generator.generate_verification_token()
        
        new_user = AuthUser(
            username=user_data.username.lower(),
            email=user_data.email.lower(),
            password_hash=password_hash,
            display_name=user_data.display_name,
            timezone=user_data.timezone,
            language=user_data.language,
            verification_token=verification_token,
            verification_token_expires=datetime.utcnow() + timedelta(days=1),  # 24 hours
            password_changed_at=datetime.utcnow()
        )
        
        try:
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            
            # Log registration attempt
            await self._log_login_attempt(
                username_or_email=user_data.username,
                success=True,
                ip_address=ip_address,
                user_id=new_user.id,
                failure_reason=None
            )
            
            return new_user
            
        except IntegrityError as e:
            await self.db.rollback()
            if "username" in str(e):
                raise UserExistsError("Username already exists")
            elif "email" in str(e):
                raise UserExistsError("Email already exists")
            else:
                raise AuthenticationError("Registration failed due to database constraint")
    
    async def authenticate_user(
        self, 
        login_data: LoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[AuthUser, dict]:
        """
        Authenticate user and return user and tokens.
        
        Args:
            login_data: Login credentials
            ip_address: User's IP address
            user_agent: User's browser/client info
            
        Returns:
            tuple: (AuthUser, tokens_dict)
            
        Raises:
            InvalidCredentialsError: If credentials are invalid
            AccountLockedError: If account is locked
        """
        user = await self._get_user_by_username_or_email(
            login_data.username_or_email, login_data.username_or_email
        )
        
        # Check if user exists and is active
        if not user or not user.is_active:
            await self._log_login_attempt(
                username_or_email=login_data.username_or_email,
                success=False,
                ip_address=ip_address,
                user_id=None,
                failure_reason="invalid_credentials"
            )
            raise InvalidCredentialsError("Invalid credentials")
        
        # Check if account is locked
        if user.is_locked:
            await self._log_login_attempt(
                username_or_email=login_data.username_or_email,
                success=False,
                ip_address=ip_address,
                user_id=user.id,
                failure_reason="account_locked"
            )
            raise AccountLockedError(f"Account is locked until {user.locked_until}")
        
        # Verify password
        if not password_hasher.verify_password(login_data.password, user.password_hash):
            await self._handle_failed_login(user, ip_address)
            await self._log_login_attempt(
                username_or_email=login_data.username_or_email,
                success=False,
                ip_address=ip_address,
                user_id=user.id,
                failure_reason="invalid_password"
            )
            raise InvalidCredentialsError("Invalid credentials")
        
        # Successful login - reset failed attempts and update last login
        await self._handle_successful_login(user, ip_address)
        
        # Generate tokens
        tokens = await self._generate_tokens_for_user(
            user, login_data.remember_me, ip_address, user_agent
        )
        
        # Log successful login
        await self._log_login_attempt(
            username_or_email=login_data.username_or_email,
            success=True,
            ip_address=ip_address,
            user_id=user.id,
            failure_reason=None
        )
        
        return user, tokens
    
    async def refresh_token(self, refresh_token: str) -> dict:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token string
            
        Returns:
            dict: New tokens
            
        Raises:
            TokenExpiredError: If refresh token is invalid/expired
        """
        # Verify JWT refresh token
        payload = jwt_manager.verify_token(refresh_token, "refresh")
        if not payload:
            raise TokenExpiredError("Invalid or expired refresh token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise TokenExpiredError("Invalid token payload")
        
        # Get refresh token from database
        stmt = select(RefreshToken).where(
            and_(
                RefreshToken.token == refresh_token,
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.utcnow()
            )
        )
        db_token = await self.db.scalar(stmt)
        
        if not db_token:
            raise TokenExpiredError("Refresh token not found or expired")
        
        # Get user
        user = await self._get_user_by_id(user_id)
        if not user or not user.is_active:
            raise TokenExpiredError("User not found or inactive")
        
        # Revoke old refresh token
        db_token.is_revoked = True
        
        # Generate new tokens
        tokens = await self._generate_tokens_for_user(
            user, False, db_token.created_ip, db_token.user_agent
        )
        
        await self.db.commit()
        return tokens
    
    async def logout_user(self, user_id: str, refresh_token: Optional[str] = None) -> bool:
        """
        Logout user by revoking refresh tokens.
        
        Args:
            user_id: User ID
            refresh_token: Specific refresh token to revoke (optional)
            
        Returns:
            bool: Success status
        """
        if refresh_token:
            # Revoke specific token
            stmt = update(RefreshToken).where(
                and_(
                    RefreshToken.token == refresh_token,
                    RefreshToken.user_id == user_id
                )
            ).values(is_revoked=True)
        else:
            # Revoke all tokens for user
            stmt = update(RefreshToken).where(
                RefreshToken.user_id == user_id
            ).values(is_revoked=True)
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def change_password(
        self, 
        user_id: str, 
        password_data: PasswordChange
    ) -> bool:
        """
        Change user password with validation.
        
        Args:
            user_id: User ID
            password_data: Password change data
            
        Returns:
            bool: Success status
            
        Raises:
            InvalidCredentialsError: If current password is wrong
            ValueError: If new password validation fails
        """
        user = await self._get_user_by_id(user_id)
        if not user:
            raise InvalidCredentialsError("User not found")
        
        # Verify current password
        if not password_hasher.verify_password(
            password_data.current_password, user.password_hash
        ):
            raise InvalidCredentialsError("Current password is incorrect")
        
        # Validate new password
        is_valid, errors = password_validator.validate_password(password_data.new_password)
        if not is_valid:
            raise ValueError(f"New password validation failed: {', '.join(errors)}")
        
        # Update password
        user.password_hash = password_hasher.hash_password(password_data.new_password)
        user.password_changed_at = datetime.utcnow()
        
        # Revoke all refresh tokens (force re-login on all devices)
        await self.logout_user(user_id)
        
        await self.db.commit()
        return True
    
    async def request_password_reset(self, email: str) -> Optional[str]:
        """
        Generate password reset token for user.
        
        Args:
            email: User email address
            
        Returns:
            str or None: Reset token if user exists
        """
        user = await self._get_user_by_username_or_email(None, email)
        if not user or not user.is_active:
            # Return None but don't indicate whether user exists (security)
            return None
        
        # Generate reset token
        reset_token = token_generator.generate_reset_token()
        user.reset_token = reset_token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)  # 1 hour
        
        await self.db.commit()
        return reset_token
    
    async def reset_password(self, reset_data: PasswordResetConfirm) -> bool:
        """
        Reset user password using reset token.
        
        Args:
            reset_data: Password reset confirmation data
            
        Returns:
            bool: Success status
            
        Raises:
            TokenExpiredError: If reset token is invalid/expired
            ValueError: If new password validation fails
        """
        # Find user by reset token
        stmt = select(AuthUser).where(
            and_(
                AuthUser.reset_token == reset_data.token,
                AuthUser.reset_token_expires > datetime.utcnow(),
                AuthUser.is_active == True
            )
        )
        user = await self.db.scalar(stmt)
        
        if not user:
            raise TokenExpiredError("Invalid or expired reset token")
        
        # Validate new password
        is_valid, errors = password_validator.validate_password(reset_data.new_password)
        if not is_valid:
            raise ValueError(f"Password validation failed: {', '.join(errors)}")
        
        # Update password and clear reset token
        user.password_hash = password_hasher.hash_password(reset_data.new_password)
        user.password_changed_at = datetime.utcnow()
        user.reset_token = None
        user.reset_token_expires = None
        user.failed_login_attempts = 0
        user.locked_until = None
        
        # Revoke all refresh tokens
        await self.logout_user(str(user.id))
        
        await self.db.commit()
        return True
    
    async def verify_email(self, token: str) -> bool:
        """
        Verify user email using verification token.
        
        Args:
            token: Email verification token
            
        Returns:
            bool: Success status
        """
        stmt = select(AuthUser).where(
            and_(
                AuthUser.verification_token == token,
                AuthUser.verification_token_expires > datetime.utcnow(),
                AuthUser.is_active == True
            )
        )
        user = await self.db.scalar(stmt)
        
        if not user:
            return False
        
        # Mark as verified and clear verification token
        user.is_verified = True
        user.verification_token = None
        user.verification_token_expires = None
        
        await self.db.commit()
        return True
    
    async def get_user_by_id(self, user_id: str) -> Optional[AuthUser]:
        """Get user by ID."""
        return await self._get_user_by_id(user_id)
    
    async def get_login_attempts(
        self, 
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        limit: int = 50
    ) -> List[LoginAttempt]:
        """
        Get login attempts for security monitoring.
        
        Args:
            user_id: Filter by user ID (optional)
            ip_address: Filter by IP address (optional)
            limit: Maximum number of results
            
        Returns:
            List[LoginAttempt]: Login attempts
        """
        stmt = select(LoginAttempt).order_by(LoginAttempt.attempted_at.desc()).limit(limit)
        
        if user_id:
            stmt = stmt.where(LoginAttempt.user_id == user_id)
        if ip_address:
            stmt = stmt.where(LoginAttempt.ip_address == ip_address)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired refresh tokens and login attempts.
        
        Returns:
            int: Number of records cleaned up
        """
        now = datetime.utcnow()
        
        # Delete expired refresh tokens
        refresh_stmt = delete(RefreshToken).where(
            or_(
                RefreshToken.expires_at < now,
                RefreshToken.is_revoked == True
            )
        )
        refresh_result = await self.db.execute(refresh_stmt)
        
        # Delete old login attempts (older than 30 days)
        login_stmt = delete(LoginAttempt).where(
            LoginAttempt.attempted_at < (now - timedelta(days=30))
        )
        login_result = await self.db.execute(login_stmt)
        
        await self.db.commit()
        
        return refresh_result.rowcount + login_result.rowcount
    
    # Private helper methods
    
    async def _get_user_by_id(self, user_id: str) -> Optional[AuthUser]:
        """Get user by ID."""
        try:
            uuid_id = uuid.UUID(user_id)
            stmt = select(AuthUser).where(AuthUser.id == uuid_id)
            return await self.db.scalar(stmt)
        except ValueError:
            return None
    
    async def _get_user_by_username_or_email(
        self, 
        username: Optional[str], 
        email: Optional[str]
    ) -> Optional[AuthUser]:
        """Get user by username or email."""
        conditions = []
        if username:
            conditions.append(AuthUser.username == username.lower())
        if email:
            conditions.append(AuthUser.email == email.lower())
        
        if not conditions:
            return None
        
        stmt = select(AuthUser).where(or_(*conditions))
        return await self.db.scalar(stmt)
    
    async def _generate_tokens_for_user(
        self, 
        user: AuthUser, 
        remember_me: bool = False,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> dict:
        """Generate access and refresh tokens for user."""
        # Create token data
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email
        }
        
        # Generate access token
        access_token_expires = timedelta(minutes=settings.security.access_token_expire_minutes)
        access_token = jwt_manager.create_access_token(
            data=token_data, 
            expires_delta=access_token_expires
        )
        
        # Generate refresh token with unique identifier to prevent duplicates
        refresh_token_expires = timedelta(days=30 if remember_me else 7)
        
        # Add unique timestamp to prevent duplicate tokens
        import time
        refresh_token_data = {
            **token_data,
            "iat": int(time.time()),  # Issued at timestamp for uniqueness
            "jti": f"{user.id}_{int(time.time() * 1000000)}"  # Unique token identifier
        }
        
        refresh_token_jwt = jwt_manager.create_refresh_token(
            data=refresh_token_data,
            expires_delta=refresh_token_expires
        )
        
        # Store refresh token in database
        db_refresh_token = RefreshToken(
            token=refresh_token_jwt,
            user_id=user.id,
            expires_at=datetime.utcnow() + refresh_token_expires,
            created_ip=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(db_refresh_token)
        await self.db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token_jwt,
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds())
        }
    
    async def _handle_failed_login(self, user: AuthUser, ip_address: Optional[str]):
        """Handle failed login attempt."""
        user.failed_login_attempts += 1
        
        if user.failed_login_attempts >= self.MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
        
        await self.db.commit()
    
    async def _handle_successful_login(self, user: AuthUser, ip_address: Optional[str]):
        """Handle successful login."""
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        user.last_login_ip = ip_address
        
        await self.db.commit()
    
    async def _log_login_attempt(
        self,
        username_or_email: str,
        success: bool,
        ip_address: Optional[str],
        user_id: Optional[uuid.UUID] = None,
        failure_reason: Optional[str] = None
    ):
        """Log login attempt for security monitoring."""
        attempt = LoginAttempt(
            username_or_email=username_or_email,
            success=success,
            ip_address=ip_address or "unknown",
            user_id=user_id,
            failure_reason=failure_reason
        )
        
        self.db.add(attempt)
        await self.db.commit()
    
    # Admin Management Methods
    
    async def create_user_admin(
        self, 
        user_data: UserCreate, 
        role: UserRole = UserRole.USER,
        admin_user_id: str = None
    ) -> AuthUser:
        """
        Admin-only user creation with role assignment.
        
        Args:
            user_data: User creation data
            role: Role to assign to user
            admin_user_id: ID of admin creating the user
            
        Returns:
            AuthUser: Created user
        """
        # Validate password
        is_valid, errors = password_validator.validate_password(user_data.password)
        if not is_valid:
            raise ValueError(f"Password validation failed: {', '.join(errors)}")
        
        # Check if user already exists
        existing_user = await self._get_user_by_username_or_email(
            user_data.username, user_data.email
        )
        if existing_user:
            if existing_user.username == user_data.username:
                raise UserExistsError("Username already exists")
            else:
                raise UserExistsError("Email already exists")
        
        # Create new user with specified role
        password_hash = password_hasher.hash_password(user_data.password)
        
        new_user = AuthUser(
            username=user_data.username.lower(),
            email=user_data.email.lower(),
            password_hash=password_hash,
            display_name=user_data.display_name,
            timezone=user_data.timezone,
            language=user_data.language,
            role=role,
            is_verified=True,  # Admin-created users are pre-verified
            password_changed_at=datetime.utcnow()
        )
        
        try:
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            return new_user
            
        except IntegrityError as e:
            await self.db.rollback()
            if "username" in str(e):
                raise UserExistsError("Username already exists")
            elif "email" in str(e):
                raise UserExistsError("Email already exists")
            else:
                raise AuthenticationError("User creation failed")
    
    async def update_user_admin(
        self, 
        user_id: str, 
        updates: dict,
        admin_user_id: str = None
    ) -> Optional[AuthUser]:
        """
        Admin-only user updates including role changes.
        
        Args:
            user_id: Target user ID
            updates: Dictionary of fields to update
            admin_user_id: ID of admin making changes
            
        Returns:
            AuthUser or None: Updated user
        """
        user = await self._get_user_by_id(user_id)
        if not user:
            return None
        
        # Update allowed fields
        allowed_fields = {
            'username', 'email', 'display_name', 'timezone', 'language',
            'is_active', 'is_verified', 'role'
        }
        
        for field, value in updates.items():
            if field in allowed_fields and hasattr(user, field):
                setattr(user, field, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def list_users_admin(
        self, 
        skip: int = 0, 
        limit: int = 100,
        role_filter: Optional[UserRole] = None,
        active_only: bool = False
    ) -> List[AuthUser]:
        """
        Admin-only user listing with filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            role_filter: Filter by specific role
            active_only: Only return active users
            
        Returns:
            List[AuthUser]: Filtered user list
        """
        stmt = select(AuthUser).offset(skip).limit(limit).order_by(AuthUser.created_at.desc())
        
        if role_filter:
            stmt = stmt.where(AuthUser.role == role_filter)
        if active_only:
            stmt = stmt.where(AuthUser.is_active == True)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_user_sessions_admin(self, user_id: str) -> List[RefreshToken]:
        """
        Admin-only view of user's active sessions.
        
        Args:
            user_id: Target user ID
            
        Returns:
            List[RefreshToken]: Active refresh tokens for user
        """
        stmt = select(RefreshToken).where(
            and_(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.utcnow()
            )
        ).order_by(RefreshToken.created_at.desc())
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def revoke_user_session_admin(self, session_id: str, admin_user_id: str) -> bool:
        """
        Admin-only forced session termination.
        
        Args:
            session_id: Refresh token ID to revoke
            admin_user_id: ID of admin performing action
            
        Returns:
            bool: Success status
        """
        stmt = update(RefreshToken).where(
            RefreshToken.id == session_id
        ).values(is_revoked=True)
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def get_security_stats_admin(self) -> dict:
        """
        Admin-only security statistics.
        
        Returns:
            dict: Security metrics and statistics
        """
        # Get user counts by role
        role_stats = await self.db.execute(
            select(AuthUser.role, func.count(AuthUser.id))
            .group_by(AuthUser.role)
        )
        
        # Get login attempt stats
        failed_attempts_today = await self.db.scalar(
            select(func.count(LoginAttempt.id))
            .where(
                and_(
                    LoginAttempt.success == False,
                    LoginAttempt.attempted_at > datetime.utcnow() - timedelta(days=1)
                )
            )
        )
        
        # Get active session count
        active_sessions = await self.db.scalar(
            select(func.count(RefreshToken.id))
            .where(
                and_(
                    RefreshToken.is_revoked == False,
                    RefreshToken.expires_at > datetime.utcnow()
                )
            )
        )
        
        return {
            "user_counts_by_role": dict(role_stats.fetchall()),
            "failed_attempts_today": failed_attempts_today or 0,
            "active_sessions": active_sessions or 0,
            "last_updated": datetime.utcnow()
        }