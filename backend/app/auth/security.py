# backend/app/auth/security.py
"""
Authentication security utilities including password hashing and JWT handling.
"""

from datetime import datetime, timedelta
from typing import Optional, Union, Any
import secrets
import string
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
import re

from ..core.config import settings


# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordValidator:
    """Comprehensive password validation with security requirements."""
    
    def __init__(self):
        self.min_length = settings.security.password_min_length
        self.require_uppercase = settings.security.password_require_uppercase
        self.require_lowercase = settings.security.password_require_lowercase
        self.require_numbers = settings.security.password_require_numbers
    
    def validate_password(self, password: str) -> tuple[bool, list[str]]:
        """
        Validate password against security requirements.
        
        Returns:
            tuple: (is_valid, list_of_errors)
        """
        errors = []
        
        # Length check
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")
        
        # Uppercase check
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Lowercase check
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Numbers check
        if self.require_numbers and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        # Common patterns check
        if self._check_common_patterns(password):
            errors.append("Password contains common patterns that are not secure")
        
        return len(errors) == 0, errors
    
    def _check_common_patterns(self, password: str) -> bool:
        """Check for common insecure password patterns."""
        common_patterns = [
            r'123456',
            r'password',
            r'qwerty',
            r'abc123',
            r'admin',
            r'letmein'
        ]
        
        password_lower = password.lower()
        return any(re.search(pattern, password_lower) for pattern in common_patterns)


class PasswordHasher:
    """Secure password hashing using bcrypt."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password from database
            
        Returns:
            bool: True if password matches
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def needs_update(hashed_password: str) -> bool:
        """
        Check if password hash needs updating (e.g., old algorithm).
        
        Args:
            hashed_password: Current password hash
            
        Returns:
            bool: True if needs updating
        """
        return pwd_context.needs_update(hashed_password)


class JWTManager:
    """JWT token creation and validation."""
    
    def __init__(self):
        self.secret_key = settings.security.secret_key
        self.algorithm = settings.security.algorithm
        self.access_token_expire_minutes = settings.security.access_token_expire_minutes
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Token payload data
            expires_delta: Optional custom expiration time
            
        Returns:
            str: JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT refresh token.
        
        Args:
            data: Token payload data
            expires_delta: Optional custom expiration time (default: 7 days)
            
        Returns:
            str: JWT refresh token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=7)  # Refresh tokens live longer
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[dict]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token to verify
            token_type: Expected token type ('access' or 'refresh')
            
        Returns:
            dict or None: Token payload if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type
            if payload.get("type") != token_type:
                return None
            
            # Check expiration (jose automatically validates exp claim)
            return payload
            
        except JWTError:
            return None
    
    def get_token_subject(self, token: str) -> Optional[str]:
        """
        Extract subject (usually user ID) from token.
        
        Args:
            token: JWT token
            
        Returns:
            str or None: Token subject if valid
        """
        payload = self.verify_token(token)
        if payload:
            return payload.get("sub")
        return None


class TokenGenerator:
    """Generate secure random tokens for verification and password reset."""
    
    @staticmethod
    def generate_verification_token(length: int = 32) -> str:
        """
        Generate a secure verification token.
        
        Args:
            length: Token length (default: 32)
            
        Returns:
            str: Secure random token
        """
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def generate_reset_token(length: int = 48) -> str:
        """
        Generate a secure password reset token.
        
        Args:
            length: Token length (default: 48)
            
        Returns:
            str: Secure random token
        """
        # Use URL-safe characters for reset tokens
        alphabet = string.ascii_letters + string.digits + '-_'
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def generate_refresh_token_id(length: int = 64) -> str:
        """
        Generate a secure refresh token identifier.
        
        Args:
            length: Token length (default: 64)
            
        Returns:
            str: Secure random token ID
        """
        return secrets.token_urlsafe(length)


class SecurityUtils:
    """Additional security utilities."""
    
    @staticmethod
    def constant_time_compare(a: str, b: str) -> bool:
        """
        Constant-time string comparison to prevent timing attacks.
        
        Args:
            a: First string
            b: Second string
            
        Returns:
            bool: True if strings are equal
        """
        return secrets.compare_digest(a, b)
    
    @staticmethod
    def is_safe_redirect_url(url: str, allowed_hosts: list[str]) -> bool:
        """
        Check if redirect URL is safe (prevents open redirect vulnerabilities).
        
        Args:
            url: URL to check
            allowed_hosts: List of allowed host names
            
        Returns:
            bool: True if URL is safe for redirect
        """
        if not url:
            return False
        
        # Only allow relative URLs or URLs from allowed hosts
        if url.startswith('/'):
            return True
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc in allowed_hosts
        except Exception:
            return False


# Global instances
password_validator = PasswordValidator()
password_hasher = PasswordHasher()
jwt_manager = JWTManager()
token_generator = TokenGenerator()
security_utils = SecurityUtils()