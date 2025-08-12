# backend/app/encryption/models.py
"""
Data models for encryption system.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import uuid


class EncryptionAlgorithm(str, Enum):
    """Supported encryption algorithms."""
    AES_256_GCM = "aes_256_gcm"
    CHACHA20_POLY1305 = "chacha20_poly1305"


class KeyType(str, Enum):
    """Types of encryption keys."""
    USER_KEY = "user_key"
    ADMIN_MASTER_KEY = "admin_master_key"
    AI_PROCESSING_KEY = "ai_processing_key"


class EncryptionContext(BaseModel):
    """Context information for encryption/decryption operations."""
    user_id: str
    operation: str  # "encrypt", "decrypt", "ai_analysis"
    reason: Optional[str] = None
    admin_user_id: Optional[str] = None  # For admin access
    consent_given: bool = False  # For AI processing
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EncryptedData(BaseModel):
    """Encrypted data container with metadata."""
    encrypted_content: str  # Base64 encoded encrypted data
    algorithm: EncryptionAlgorithm
    key_id: str  # Reference to the key used
    iv: str  # Base64 encoded initialization vector
    tag: str  # Base64 encoded authentication tag
    metadata: Dict[str, Any] = Field(default_factory=dict)
    encrypted_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class KeyRotationEvent(BaseModel):
    """Key rotation event for audit logging."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key_id: str
    key_type: KeyType
    old_key_version: Optional[int] = None
    new_key_version: int
    rotated_by: str  # Admin user ID
    rotation_reason: str
    affected_records_count: int = 0
    rotation_started: datetime = Field(default_factory=datetime.utcnow)
    rotation_completed: Optional[datetime] = None
    status: str = "in_progress"  # "in_progress", "completed", "failed"
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }