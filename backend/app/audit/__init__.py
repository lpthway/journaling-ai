# backend/app/audit/__init__.py
"""
Audit service module for comprehensive security logging.

Provides:
- Separate audit database for security isolation
- Immutable audit log storage
- User action tracking
- Admin action monitoring  
- AI processing event logging
- Compliance reporting
"""

from .service import AuditService, audit_service
from .models import AuditEvent, UserAction, AdminAction, AIProcessingEvent, SecurityEvent
from .database import audit_database

__all__ = [
    "AuditService",
    "audit_service",
    "AuditEvent", 
    "UserAction",
    "AdminAction",
    "AIProcessingEvent",
    "SecurityEvent",
    "audit_database"
]