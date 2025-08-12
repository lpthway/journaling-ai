# backend/app/encryption/__init__.py
"""
Encryption service module for sensitive data protection.

Provides hybrid encryption approach:
- Encrypt data at rest for storage security
- Decrypt for AI analysis with user consent  
- Admin master key access with audit logging
- Future migration path to zero-knowledge architecture
"""

from .service import EncryptionService, encryption_service
from .key_manager import KeyManager, key_manager
from .models import EncryptedData, EncryptionContext, KeyRotationEvent

__all__ = [
    "EncryptionService",
    "encryption_service", 
    "KeyManager",
    "key_manager",
    "EncryptedData",
    "EncryptionContext", 
    "KeyRotationEvent"
]