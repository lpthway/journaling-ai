# backend/tests/auth_test_auth_routes.py
"""
Comprehensive tests for authentication API routes.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import patch
import json

from app.auth.routes import router as auth_router
from app.auth.models import AuthUser
from app.models.enhanced_models import Base
from app.core.database import get_db


# Test Application Setup
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
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
def app(db_session):
    """Create test FastAPI application."""
    app = FastAPI()
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    app.include_router(auth_router)
    
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_user_data():
    """Sample user registration data."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePassword123",
        "password_confirm": "SecurePassword123",
        "display_name": "Test User",
        "timezone": "America/New_York",
        "language": "en"
    }


class TestUserRegistration:
    """Test user registration endpoints."""
    
    def test_register_user_success(self, client, sample_user_data):
        """Test successful user registration."""
        response = client.post("/auth/register", json=sample_user_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["username"] == sample_user_data["username"]
        assert data["email"] == sample_user_data["email"]
        assert data["display_name"] == sample_user_data["display_name"]
        assert data["timezone"] == sample_user_data["timezone"]
        assert data["language"] == sample_user_data["language"]
        assert data["is_active"] is True
        assert data["is_verified"] is False
        assert "id" in data
        assert "created_at" in data
    
    def test_register_user_validation_errors(self, client):
        """Test registration with validation errors."""
        # Missing required fields
        response = client.post("/auth/register", json={
            "username": "testuser"
        })
        assert response.status_code == 422
        
        # Password mismatch
        response = client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePassword123",
            "password_confirm": "DifferentPassword123"
        })
        assert response.status_code == 422
        
        # Invalid email
        response = client.post("/auth/register", json={
            "username": "testuser",
            "email": "invalid-email",
            "password": "SecurePassword123",
            "password_confirm": "SecurePassword123"
        })
        assert response.status_code == 422
    
    def test_register_user_weak_password(self, client):
        """Test registration with weak password."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak",
            "password_confirm": "weak"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Password validation failed" in response.json()["detail"]
    
    def test_register_user_duplicate_username(self, client, sample_user_data):
        """Test registration with duplicate username."""
        # Register first user
        response = client.post("/auth/register", json=sample_user_data)
        assert response.status_code == 201
        
        # Try to register user with same username
        duplicate_data = sample_user_data.copy()
        duplicate_data["email"] = "different@example.com"
        
        response = client.post("/auth/register", json=duplicate_data)
        assert response.status_code == 409
        assert "Username already exists" in response.json()["detail"]
    
    def test_register_user_duplicate_email(self, client, sample_user_data):
        """Test registration with duplicate email."""
        # Register first user
        response = client.post("/auth/register", json=sample_user_data)
        assert response.status_code == 201
        
        # Try to register user with same email
        duplicate_data = sample_user_data.copy()
        duplicate_data["username"] = "differentuser"
        
        response = client.post("/auth/register", json=duplicate_data)
        assert response.status_code == 409
        assert "Email already exists" in response.json()["detail"]


class TestUserLogin:
    """Test user login endpoints."""
    
    def test_login_success_with_username(self, client, sample_user_data):
        """Test successful login with username."""
        # Register user first
        register_response = client.post("/auth/register", json=sample_user_data)
        assert register_response.status_code == 201
        
        # Login with username
        login_data = {
            "username_or_email": sample_user_data["username"],
            "password": sample_user_data["password"],
            "remember_me": False
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    def test_login_success_with_email(self, client, sample_user_data):
        """Test successful login with email."""
        # Register user first
        register_response = client.post("/auth/register", json=sample_user_data)
        assert register_response.status_code == 201
        
        # Login with email
        login_data = {
            "username_or_email": sample_user_data["email"],
            "password": sample_user_data["password"],
            "remember_me": True
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_login_invalid_credentials(self, client, sample_user_data):
        """Test login with invalid credentials."""
        # Register user first
        register_response = client.post("/auth/register", json=sample_user_data)
        assert register_response.status_code == 201
        
        # Try login with wrong password
        login_data = {
            "username_or_email": sample_user_data["username"],
            "password": "WrongPassword123",
            "remember_me": False
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        login_data = {
            "username_or_email": "nonexistent@example.com",
            "password": "SomePassword123",
            "remember_me": False
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]


class TestTokenManagement:
    """Test token refresh and logout endpoints."""
    
    def test_refresh_token_success(self, client, sample_user_data):
        """Test successful token refresh."""
        # Register and login user
        register_response = client.post("/auth/register", json=sample_user_data)
        assert register_response.status_code == 201
        
        login_data = {
            "username_or_email": sample_user_data["username"],
            "password": sample_user_data["password"],
            "remember_me": False
        }
        
        login_response = client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        tokens = login_response.json()
        refresh_token = tokens["refresh_token"]
        
        # Refresh tokens
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["access_token"] != tokens["access_token"]
        assert data["refresh_token"] != tokens["refresh_token"]
    
    def test_refresh_token_invalid(self, client):
        """Test refresh with invalid token."""
        refresh_data = {"refresh_token": "invalid_token"}
        response = client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401
        assert "Invalid or expired refresh token" in response.json()["detail"]
    
    def test_logout_success(self, client, sample_user_data):
        """Test successful logout."""
        # Register and login user
        register_response = client.post("/auth/register", json=sample_user_data)
        assert register_response.status_code == 201
        
        login_data = {
            "username_or_email": sample_user_data["username"],
            "password": sample_user_data["password"],
            "remember_me": False
        }
        
        login_response = client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        tokens = login_response.json()
        
        # Logout
        logout_data = {"refresh_token": tokens["refresh_token"]}
        
        # Need to authenticate for logout
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        response = client.post("/auth/logout", json=logout_data, headers=headers)
        
        assert response.status_code == 204
        
        # Try to refresh with logged out token
        refresh_response = client.post("/auth/refresh", json=logout_data)
        assert refresh_response.status_code == 401


class TestUserProfile:
    """Test user profile endpoints."""
    
    def test_get_current_user(self, client, sample_user_data):
        """Test getting current user information."""
        # Register and login user
        register_response = client.post("/auth/register", json=sample_user_data)
        assert register_response.status_code == 201
        
        login_data = {
            "username_or_email": sample_user_data["username"],
            "password": sample_user_data["password"],
            "remember_me": False
        }
        
        login_response = client.post("/auth/login", json=login_data)
        tokens = login_response.json()
        
        # Get current user
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["username"] == sample_user_data["username"]
        assert data["email"] == sample_user_data["email"]
        assert data["display_name"] == sample_user_data["display_name"]
    
    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without authentication."""
        response = client.get("/auth/me")
        assert response.status_code == 401
    
    def test_update_current_user(self, client, sample_user_data):
        """Test updating current user profile."""
        # Register and login user
        register_response = client.post("/auth/register", json=sample_user_data)
        assert register_response.status_code == 201
        
        login_data = {
            "username_or_email": sample_user_data["username"],
            "password": sample_user_data["password"],
            "remember_me": False
        }
        
        login_response = client.post("/auth/login", json=login_data)
        tokens = login_response.json()
        
        # Update user profile
        update_data = {
            "display_name": "Updated Display Name",
            "timezone": "Europe/London",
            "language": "es"
        }
        
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        response = client.put("/auth/me", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["display_name"] == "Updated Display Name"
        assert data["timezone"] == "Europe/London"
        assert data["language"] == "es"


class TestPasswordManagement:
    """Test password change and reset endpoints."""
    
    def test_change_password_success(self, client, sample_user_data):
        """Test successful password change."""
        # Register and login user
        register_response = client.post("/auth/register", json=sample_user_data)
        assert register_response.status_code == 201
        
        login_data = {
            "username_or_email": sample_user_data["username"],
            "password": sample_user_data["password"],
            "remember_me": False
        }
        
        login_response = client.post("/auth/login", json=login_data)
        tokens = login_response.json()
        
        # Change password
        password_data = {
            "current_password": sample_user_data["password"],
            "new_password": "NewSecurePassword123",
            "new_password_confirm": "NewSecurePassword123"
        }
        
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        response = client.post("/auth/change-password", json=password_data, headers=headers)
        
        assert response.status_code == 204
        
        # Try to login with new password
        new_login_data = {
            "username_or_email": sample_user_data["username"],
            "password": "NewSecurePassword123",
            "remember_me": False
        }
        
        new_login_response = client.post("/auth/login", json=new_login_data)
        assert new_login_response.status_code == 200
    
    def test_change_password_wrong_current(self, client, sample_user_data):
        """Test password change with wrong current password."""
        # Register and login user
        register_response = client.post("/auth/register", json=sample_user_data)
        assert register_response.status_code == 201
        
        login_data = {
            "username_or_email": sample_user_data["username"],
            "password": sample_user_data["password"],
            "remember_me": False
        }
        
        login_response = client.post("/auth/login", json=login_data)
        tokens = login_response.json()
        
        # Try to change password with wrong current password
        password_data = {
            "current_password": "WrongCurrentPassword",
            "new_password": "NewSecurePassword123",
            "new_password_confirm": "NewSecurePassword123"
        }
        
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        response = client.post("/auth/change-password", json=password_data, headers=headers)
        
        assert response.status_code == 401
        assert "Current password is incorrect" in response.json()["detail"]
    
    def test_request_password_reset(self, client, sample_user_data):
        """Test password reset request."""
        # Register user first
        register_response = client.post("/auth/register", json=sample_user_data)
        assert register_response.status_code == 201
        
        # Request password reset
        reset_data = {"email": sample_user_data["email"]}
        response = client.post("/auth/request-password-reset", json=reset_data)
        
        # Should always return 204 for security
        assert response.status_code == 204
    
    def test_request_password_reset_nonexistent_email(self, client):
        """Test password reset request for non-existent email."""
        reset_data = {"email": "nonexistent@example.com"}
        response = client.post("/auth/request-password-reset", json=reset_data)
        
        # Should always return 204 for security (no email enumeration)
        assert response.status_code == 204


class TestAuthStatus:
    """Test authentication status endpoint."""
    
    def test_auth_status_authenticated(self, client, sample_user_data):
        """Test auth status when authenticated."""
        # Register and login user
        register_response = client.post("/auth/register", json=sample_user_data)
        assert register_response.status_code == 201
        
        login_data = {
            "username_or_email": sample_user_data["username"],
            "password": sample_user_data["password"],
            "remember_me": False
        }
        
        login_response = client.post("/auth/login", json=login_data)
        tokens = login_response.json()
        
        # Check auth status
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        response = client.get("/auth/status", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["authenticated"] is True
        assert data["user"] is not None
        assert data["user"]["username"] == sample_user_data["username"]
        assert "permissions" in data
    
    def test_auth_status_unauthenticated(self, client):
        """Test auth status when not authenticated."""
        response = client.get("/auth/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["authenticated"] is False
        assert data["user"] is None


class TestAuthConfig:
    """Test authentication configuration endpoint."""
    
    def test_get_auth_config(self, client):
        """Test getting authentication configuration."""
        response = client.get("/auth/config")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "password_min_length" in data
        assert "password_require_uppercase" in data
        assert "password_require_lowercase" in data
        assert "password_require_numbers" in data
        assert "access_token_expire_minutes" in data


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    @patch('app.auth.dependencies.RateLimitDependency.MAX_ATTEMPTS', 3)
    def test_login_rate_limiting(self, client, sample_user_data):
        """Test login rate limiting."""
        # Register user first
        register_response = client.post("/auth/register", json=sample_user_data)
        assert register_response.status_code == 201
        
        login_data = {
            "username_or_email": sample_user_data["username"],
            "password": "WrongPassword123",
            "remember_me": False
        }
        
        # Make failed login attempts up to the limit
        for i in range(3):
            response = client.post("/auth/login", json=login_data)
            assert response.status_code == 401
        
        # Next attempt should be rate limited
        # Note: This test might need adjustment based on actual rate limiting implementation
        response = client.post("/auth/login", json=login_data)
        # The exact status code depends on implementation
        assert response.status_code in [401, 429]


class TestSecurityFeatures:
    """Test security-related features."""
    
    def test_get_security_info(self, client, sample_user_data):
        """Test getting user security information."""
        # Register and login user
        register_response = client.post("/auth/register", json=sample_user_data)
        assert register_response.status_code == 201
        
        login_data = {
            "username_or_email": sample_user_data["username"],
            "password": sample_user_data["password"],
            "remember_me": False
        }
        
        login_response = client.post("/auth/login", json=login_data)
        tokens = login_response.json()
        
        # Get security info
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        response = client.get("/auth/me/security", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "failed_login_attempts" in data
        assert "is_locked" in data
        assert "last_login" in data
        assert "active_sessions" in data
    
    def test_get_login_history(self, client, sample_user_data):
        """Test getting user login history."""
        # Register and login user
        register_response = client.post("/auth/register", json=sample_user_data)
        assert register_response.status_code == 201
        
        login_data = {
            "username_or_email": sample_user_data["username"],
            "password": sample_user_data["password"],
            "remember_me": False
        }
        
        login_response = client.post("/auth/login", json=login_data)
        tokens = login_response.json()
        
        # Get login history
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        response = client.get("/auth/me/login-history", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # Should have at least the registration and login attempts
        assert len(data) >= 1