# backend/tests/auth_test_auth_service.py
"""
Comprehensive tests for the authentication service.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
import uuid

from app.auth.models import AuthUser, RefreshToken, LoginAttempt
from app.auth.service import (
    AuthService, 
    UserExistsError, 
    InvalidCredentialsError,
    AccountLockedError, 
    TokenExpiredError
)
from app.auth.schemas import UserCreate, LoginRequest, PasswordChange
from app.models.enhanced_models import Base


# Test Database Setup
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    # Use in-memory SQLite for fast testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine):
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def auth_service(db_session):
    """Create authentication service instance."""
    return AuthService(db_session)


@pytest.fixture
def sample_user_data():
    """Sample user registration data."""
    return UserCreate(
        username="testuser",
        email="test@example.com",
        password="SecurePassword123",
        password_confirm="SecurePassword123",
        display_name="Test User",
        timezone="America/New_York",
        language="en"
    )


class TestUserRegistration:
    """Test user registration functionality."""
    
    async def test_register_user_success(self, auth_service, sample_user_data):
        """Test successful user registration."""
        user = await auth_service.register_user(
            sample_user_data,
            ip_address="192.168.1.1"
        )
        
        assert user.username == sample_user_data.username.lower()
        assert user.email == sample_user_data.email.lower()
        assert user.display_name == sample_user_data.display_name
        assert user.timezone == sample_user_data.timezone
        assert user.language == sample_user_data.language
        assert user.is_active is True
        assert user.is_verified is False
        assert user.password_hash is not None
        assert user.verification_token is not None
        
    async def test_register_user_duplicate_username(self, auth_service, sample_user_data):
        """Test registration with duplicate username."""
        # Create first user
        await auth_service.register_user(sample_user_data, ip_address="192.168.1.1")
        
        # Try to create user with same username but different email
        duplicate_user_data = UserCreate(
            username="testuser",
            email="different@example.com",
            password="SecurePassword123",
            password_confirm="SecurePassword123"
        )
        
        with pytest.raises(UserExistsError, match="Username already exists"):
            await auth_service.register_user(duplicate_user_data, ip_address="192.168.1.1")
    
    async def test_register_user_duplicate_email(self, auth_service, sample_user_data):
        """Test registration with duplicate email."""
        # Create first user
        await auth_service.register_user(sample_user_data, ip_address="192.168.1.1")
        
        # Try to create user with same email but different username
        duplicate_user_data = UserCreate(
            username="differentuser",
            email="test@example.com",
            password="SecurePassword123",
            password_confirm="SecurePassword123"
        )
        
        with pytest.raises(UserExistsError, match="Email already exists"):
            await auth_service.register_user(duplicate_user_data, ip_address="192.168.1.1")
    
    async def test_register_user_weak_password(self, auth_service):
        """Test registration with weak password."""
        weak_password_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="weak",
            password_confirm="weak"
        )
        
        with pytest.raises(ValueError, match="Password validation failed"):
            await auth_service.register_user(weak_password_data, ip_address="192.168.1.1")


class TestUserAuthentication:
    """Test user authentication functionality."""
    
    async def test_authenticate_user_success_username(self, auth_service, sample_user_data):
        """Test successful authentication with username."""
        # Register user first
        user = await auth_service.register_user(sample_user_data, ip_address="192.168.1.1")
        
        # Authenticate with username
        login_data = LoginRequest(
            username_or_email=sample_user_data.username,
            password=sample_user_data.password,
            remember_me=False
        )
        
        auth_user, tokens = await auth_service.authenticate_user(
            login_data,
            ip_address="192.168.1.1",
            user_agent="test-browser"
        )
        
        assert auth_user.id == user.id
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "token_type" in tokens
        assert tokens["token_type"] == "bearer"
        
    async def test_authenticate_user_success_email(self, auth_service, sample_user_data):
        """Test successful authentication with email."""
        # Register user first
        user = await auth_service.register_user(sample_user_data, ip_address="192.168.1.1")
        
        # Authenticate with email
        login_data = LoginRequest(
            username_or_email=sample_user_data.email,
            password=sample_user_data.password,
            remember_me=True
        )
        
        auth_user, tokens = await auth_service.authenticate_user(
            login_data,
            ip_address="192.168.1.1",
            user_agent="test-browser"
        )
        
        assert auth_user.id == user.id
        
    async def test_authenticate_user_invalid_credentials(self, auth_service, sample_user_data):
        """Test authentication with invalid credentials."""
        # Register user first
        await auth_service.register_user(sample_user_data, ip_address="192.168.1.1")
        
        # Try to authenticate with wrong password
        login_data = LoginRequest(
            username_or_email=sample_user_data.username,
            password="WrongPassword123",
            remember_me=False
        )
        
        with pytest.raises(InvalidCredentialsError):
            await auth_service.authenticate_user(
                login_data,
                ip_address="192.168.1.1"
            )
    
    async def test_authenticate_user_nonexistent_user(self, auth_service):
        """Test authentication with non-existent user."""
        login_data = LoginRequest(
            username_or_email="nonexistent@example.com",
            password="SomePassword123",
            remember_me=False
        )
        
        with pytest.raises(InvalidCredentialsError):
            await auth_service.authenticate_user(
                login_data,
                ip_address="192.168.1.1"
            )
    
    async def test_authenticate_user_account_lockout(self, auth_service, sample_user_data, db_session):
        """Test account lockout after failed attempts."""
        # Register user first
        user = await auth_service.register_user(sample_user_data, ip_address="192.168.1.1")
        
        # Make multiple failed login attempts
        login_data = LoginRequest(
            username_or_email=sample_user_data.username,
            password="WrongPassword123",
            remember_me=False
        )
        
        # Try failed logins up to the limit
        for _ in range(AuthService.MAX_FAILED_ATTEMPTS):
            with pytest.raises(InvalidCredentialsError):
                await auth_service.authenticate_user(
                    login_data,
                    ip_address="192.168.1.1"
                )
        
        # Refresh user to get updated state
        await db_session.refresh(user)
        
        # Next attempt should raise AccountLockedError
        with pytest.raises(AccountLockedError):
            await auth_service.authenticate_user(
                login_data,
                ip_address="192.168.1.1"
            )


class TestTokenManagement:
    """Test token refresh and management."""
    
    async def test_refresh_token_success(self, auth_service, sample_user_data):
        """Test successful token refresh."""
        # Register and authenticate user
        user = await auth_service.register_user(sample_user_data, ip_address="192.168.1.1")
        
        login_data = LoginRequest(
            username_or_email=sample_user_data.username,
            password=sample_user_data.password,
            remember_me=False
        )
        
        auth_user, tokens = await auth_service.authenticate_user(
            login_data,
            ip_address="192.168.1.1",
            user_agent="test-browser"
        )
        
        # Refresh tokens
        new_tokens = await auth_service.refresh_token(tokens["refresh_token"])
        
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        assert new_tokens["access_token"] != tokens["access_token"]
        assert new_tokens["refresh_token"] != tokens["refresh_token"]
    
    async def test_refresh_token_invalid(self, auth_service):
        """Test refresh with invalid token."""
        with pytest.raises(TokenExpiredError):
            await auth_service.refresh_token("invalid_token")
    
    async def test_logout_user(self, auth_service, sample_user_data):
        """Test user logout."""
        # Register and authenticate user
        user = await auth_service.register_user(sample_user_data, ip_address="192.168.1.1")
        
        login_data = LoginRequest(
            username_or_email=sample_user_data.username,
            password=sample_user_data.password,
            remember_me=False
        )
        
        auth_user, tokens = await auth_service.authenticate_user(
            login_data,
            ip_address="192.168.1.1",
            user_agent="test-browser"
        )
        
        # Logout user
        success = await auth_service.logout_user(
            str(user.id), 
            tokens["refresh_token"]
        )
        
        assert success is True
        
        # Try to refresh with logged out token
        with pytest.raises(TokenExpiredError):
            await auth_service.refresh_token(tokens["refresh_token"])


class TestPasswordManagement:
    """Test password change and reset functionality."""
    
    async def test_change_password_success(self, auth_service, sample_user_data):
        """Test successful password change."""
        # Register user
        user = await auth_service.register_user(sample_user_data, ip_address="192.168.1.1")
        
        # Change password
        password_data = PasswordChange(
            current_password=sample_user_data.password,
            new_password="NewSecurePassword123",
            new_password_confirm="NewSecurePassword123"
        )
        
        success = await auth_service.change_password(str(user.id), password_data)
        assert success is True
        
        # Try to login with new password
        login_data = LoginRequest(
            username_or_email=sample_user_data.username,
            password="NewSecurePassword123",
            remember_me=False
        )
        
        auth_user, tokens = await auth_service.authenticate_user(
            login_data,
            ip_address="192.168.1.1"
        )
        
        assert auth_user.id == user.id
    
    async def test_change_password_wrong_current(self, auth_service, sample_user_data):
        """Test password change with wrong current password."""
        # Register user
        user = await auth_service.register_user(sample_user_data, ip_address="192.168.1.1")
        
        # Try to change password with wrong current password
        password_data = PasswordChange(
            current_password="WrongCurrentPassword",
            new_password="NewSecurePassword123",
            new_password_confirm="NewSecurePassword123"
        )
        
        with pytest.raises(InvalidCredentialsError):
            await auth_service.change_password(str(user.id), password_data)
    
    async def test_request_password_reset(self, auth_service, sample_user_data):
        """Test password reset request."""
        # Register user
        user = await auth_service.register_user(sample_user_data, ip_address="192.168.1.1")
        
        # Request password reset
        reset_token = await auth_service.request_password_reset(sample_user_data.email)
        
        assert reset_token is not None
        assert len(reset_token) > 0
    
    async def test_request_password_reset_nonexistent_user(self, auth_service):
        """Test password reset request for non-existent user."""
        reset_token = await auth_service.request_password_reset("nonexistent@example.com")
        
        # Should return None but not raise an error (security)
        assert reset_token is None


class TestEmailVerification:
    """Test email verification functionality."""
    
    async def test_verify_email_success(self, auth_service, sample_user_data, db_session):
        """Test successful email verification."""
        # Register user
        user = await auth_service.register_user(sample_user_data, ip_address="192.168.1.1")
        
        # User should not be verified initially
        assert user.is_verified is False
        assert user.verification_token is not None
        
        # Verify email
        success = await auth_service.verify_email(user.verification_token)
        assert success is True
        
        # Refresh user to check updated state
        await db_session.refresh(user)
        assert user.is_verified is True
        assert user.verification_token is None
    
    async def test_verify_email_invalid_token(self, auth_service):
        """Test email verification with invalid token."""
        success = await auth_service.verify_email("invalid_token")
        assert success is False


class TestSecurityFeatures:
    """Test security features and monitoring."""
    
    async def test_login_attempt_logging(self, auth_service, sample_user_data):
        """Test that login attempts are logged."""
        # Register user
        user = await auth_service.register_user(sample_user_data, ip_address="192.168.1.1")
        
        # Make a successful login
        login_data = LoginRequest(
            username_or_email=sample_user_data.username,
            password=sample_user_data.password,
            remember_me=False
        )
        
        await auth_service.authenticate_user(
            login_data,
            ip_address="192.168.1.1"
        )
        
        # Check that login attempts were logged
        attempts = await auth_service.get_login_attempts(user_id=str(user.id))
        
        # Should have registration attempt and login attempt
        assert len(attempts) >= 2
        
        # Check successful login attempt
        login_attempt = next((a for a in attempts if a.success), None)
        assert login_attempt is not None
        assert login_attempt.user_id == user.id
        assert login_attempt.ip_address == "192.168.1.1"
    
    async def test_cleanup_expired_tokens(self, auth_service, db_session):
        """Test cleanup of expired tokens."""
        # Create an expired refresh token
        expired_token = RefreshToken(
            token="expired_token",
            user_id=uuid.uuid4(),
            expires_at=datetime.utcnow() - timedelta(days=1),
            is_revoked=False
        )
        
        db_session.add(expired_token)
        await db_session.commit()
        
        # Run cleanup
        cleaned_count = await auth_service.cleanup_expired_tokens()
        
        assert cleaned_count > 0
        
        # Verify token was removed
        stmt = select(RefreshToken).where(RefreshToken.token == "expired_token")
        result = await db_session.scalar(stmt)
        assert result is None


# Performance and stress tests
class TestPerformance:
    """Test authentication system performance."""
    
    @pytest.mark.asyncio
    async def test_concurrent_registrations(self, auth_service):
        """Test concurrent user registrations."""
        async def register_user(i):
            user_data = UserCreate(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password="SecurePassword123",
                password_confirm="SecurePassword123"
            )
            return await auth_service.register_user(user_data, ip_address="192.168.1.1")
        
        # Register 10 users concurrently
        tasks = [register_user(i) for i in range(10)]
        users = await asyncio.gather(*tasks)
        
        assert len(users) == 10
        assert len(set(user.username for user in users)) == 10  # All unique
    
    @pytest.mark.asyncio
    async def test_concurrent_logins(self, auth_service):
        """Test concurrent user logins."""
        # Register a user first
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="SecurePassword123",
            password_confirm="SecurePassword123"
        )
        
        user = await auth_service.register_user(user_data, ip_address="192.168.1.1")
        
        async def login_user():
            login_data = LoginRequest(
                username_or_email="testuser",
                password="SecurePassword123",
                remember_me=False
            )
            return await auth_service.authenticate_user(
                login_data,
                ip_address="192.168.1.1"
            )
        
        # Perform 5 concurrent logins
        tasks = [login_user() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        # All should return the same user
        assert all(auth_user.id == user.id for auth_user, tokens in results)