# backend/app/encryption/key_manager.py
"""
Key management system for encryption service.

Handles:
- User-derived encryption keys
- Admin master keys (with future migration to user-consent-only)
- Key rotation and versioning
- Secure key storage and retrieval
"""

import os
import base64
import secrets
import hashlib
import logging
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta

from .models import KeyType, KeyRotationEvent
from ..core.config import settings

logger = logging.getLogger(__name__)


class KeyManager:
    """
    Secure key management for encryption operations.
    
    Features:
    - User-derived keys from authentication
    - Admin master keys with audit logging
    - Key versioning and rotation
    - Future zero-knowledge migration support
    """
    
    def __init__(self):
        self._admin_master_key: Optional[bytes] = None
        self._key_cache: Dict[str, bytes] = {}
        self._key_versions: Dict[str, int] = {}
        
    async def initialize(self) -> None:
        """Initialize key manager with master keys."""
        try:
            # Load or generate admin master key
            await self._load_admin_master_key()
            logger.info("✅ Key manager initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Key manager initialization failed: {e}")
            raise
    
    def derive_user_key(self, user_id: str, password_hash: str) -> bytes:
        """
        Derive encryption key from user's authentication data.
        
        Args:
            user_id: User identifier
            password_hash: User's password hash from auth system
            
        Returns:
            bytes: 32-byte encryption key
        """
        try:
            # Use user ID as salt base
            salt = hashlib.sha256(user_id.encode()).digest()[:16]
            
            # Derive key using PBKDF2 with password hash
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,  # High iteration count for security
                backend=default_backend()
            )
            
            key = kdf.derive(password_hash.encode())
            
            # Cache the key temporarily (in production, use secure cache)
            cache_key = f"user_key:{user_id}"
            self._key_cache[cache_key] = key
            
            return key
            
        except Exception as e:
            logger.error(f"Failed to derive user key for {user_id}: {e}")
            raise
    
    def get_user_key(self, user_id: str) -> Optional[bytes]:
        """
        Get cached user key.
        
        Args:
            user_id: User identifier
            
        Returns:
            bytes or None: Cached user key if available
        """
        cache_key = f"user_key:{user_id}"
        return self._key_cache.get(cache_key)
    
    def get_admin_master_key(self) -> bytes:
        """
        Get admin master key for emergency access.
        
        Note: This will be phased out in zero-knowledge migration.
        
        Returns:
            bytes: Admin master key
            
        Raises:
            RuntimeError: If master key not available
        """
        if not self._admin_master_key:
            raise RuntimeError("Admin master key not available")
        return self._admin_master_key
    
    def generate_ai_processing_key(self, user_id: str, session_id: str) -> bytes:
        """
        Generate temporary key for AI processing with user consent.
        
        Args:
            user_id: User identifier
            session_id: AI processing session identifier
            
        Returns:
            bytes: Temporary AI processing key
        """
        try:
            # Combine user key with session-specific data
            user_key = self.get_user_key(user_id)
            if not user_key:
                raise ValueError(f"User key not available for {user_id}")
            
            # Create session-specific key derivation
            session_salt = hashlib.sha256(f"{user_id}:{session_id}".encode()).digest()[:16]
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=session_salt,
                iterations=10000,  # Lower iterations for AI processing speed
                backend=default_backend()
            )
            
            ai_key = kdf.derive(user_key)
            
            # Cache temporarily for AI session
            cache_key = f"ai_key:{session_id}"
            self._key_cache[cache_key] = ai_key
            
            return ai_key
            
        except Exception as e:
            logger.error(f"Failed to generate AI processing key: {e}")
            raise
    
    async def rotate_admin_master_key(self, rotated_by: str, reason: str) -> KeyRotationEvent:
        """
        Rotate admin master key with audit logging.
        
        Args:
            rotated_by: Admin user ID performing rotation
            reason: Reason for rotation
            
        Returns:
            KeyRotationEvent: Rotation event details
        """
        rotation_event = KeyRotationEvent(
            key_id="admin_master",
            key_type=KeyType.ADMIN_MASTER_KEY,
            old_key_version=self._key_versions.get("admin_master", 1),
            new_key_version=self._key_versions.get("admin_master", 1) + 1,
            rotated_by=rotated_by,
            rotation_reason=reason
        )
        
        try:
            # Generate new master key
            new_master_key = secrets.token_bytes(32)
            
            # TODO: Re-encrypt all data with new key
            # This would be implemented in production with proper migration
            rotation_event.affected_records_count = 0  # Placeholder
            
            # Update master key
            old_key = self._admin_master_key
            self._admin_master_key = new_master_key
            self._key_versions["admin_master"] = rotation_event.new_key_version
            
            # Store new key securely
            await self._store_admin_master_key(new_master_key)
            
            rotation_event.rotation_completed = datetime.utcnow()
            rotation_event.status = "completed"
            
            logger.info(f"Admin master key rotated successfully by {rotated_by}")
            return rotation_event
            
        except Exception as e:
            rotation_event.status = "failed"
            logger.error(f"Admin master key rotation failed: {e}")
            raise
    
    def clear_user_key_cache(self, user_id: str) -> None:
        """Clear cached user key (e.g., on logout)."""
        cache_key = f"user_key:{user_id}"
        self._key_cache.pop(cache_key, None)
    
    def clear_ai_processing_key(self, session_id: str) -> None:
        """Clear AI processing key after session."""
        cache_key = f"ai_key:{session_id}"
        self._key_cache.pop(cache_key, None)
    
    async def _load_admin_master_key(self) -> None:
        """Load admin master key from secure storage."""
        try:
            # In production, this would load from a secure key management system
            # For now, use environment variable or generate if not exists
            key_b64 = os.getenv("ENCRYPTION_ADMIN_MASTER_KEY")
            
            if key_b64:
                self._admin_master_key = base64.b64decode(key_b64)
                logger.info("Loaded existing admin master key")
            else:
                # Generate new master key
                self._admin_master_key = secrets.token_bytes(32)
                await self._store_admin_master_key(self._admin_master_key)
                logger.warning("Generated new admin master key - store securely!")
            
            self._key_versions["admin_master"] = 1
            
        except Exception as e:
            logger.error(f"Failed to load admin master key: {e}")
            raise
    
    async def _store_admin_master_key(self, key: bytes) -> None:
        """Store admin master key securely."""
        try:
            # In production, this would store in a secure key management system
            # For now, just log a warning about secure storage
            key_b64 = base64.b64encode(key).decode()
            logger.warning(
                f"Store this admin master key securely: "
                f"ENCRYPTION_ADMIN_MASTER_KEY={key_b64}"
            )
            
            # TODO: Implement secure key storage (HSM, vault, etc.)
            
        except Exception as e:
            logger.error(f"Failed to store admin master key: {e}")
            raise


# Global key manager instance
key_manager = KeyManager()