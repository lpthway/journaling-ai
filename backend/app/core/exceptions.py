"""
Custom exception hierarchy for structured error handling.

Provides:
- Hierarchical exception structure
- Detailed error context and correlation IDs
- HTTP status code mapping
- Proper logging integration
"""

import uuid
from typing import Optional, Dict, Any
from datetime import datetime

class JournalingAIException(Exception):
    """
    Base exception for all application errors.
    
    Features:
    - Correlation ID for error tracking
    - Structured error context
    - Timestamp for debugging
    - HTTP status code mapping
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat()
        }

class DatabaseException(JournalingAIException):
    """Database operation errors."""
    http_status_code = 500

class ValidationException(JournalingAIException):
    """Data validation errors."""
    http_status_code = 400

class AuthenticationException(JournalingAIException):
    """Authentication errors."""
    http_status_code = 401

class AuthorizationException(JournalingAIException):
    """Authorization errors."""
    http_status_code = 403

class NotFoundException(JournalingAIException):
    """Resource not found errors."""
    http_status_code = 404

class ConflictException(JournalingAIException):
    """Resource conflict errors."""
    http_status_code = 409

class RateLimitException(JournalingAIException):
    """Rate limiting errors."""
    http_status_code = 429

# Specific business logic exceptions
class EntryValidationException(ValidationException):
    """Journal entry validation errors."""
    pass

class SessionNotFoundException(NotFoundException):
    """Chat session not found."""
    pass

class UserAuthenticationException(AuthenticationException):
    """User authentication failures."""
    pass

class MigrationException(DatabaseException):
    """Data migration errors."""
    pass

class AnalyticsException(DatabaseException):
    """Analytics calculation errors."""
    pass
