# backend/app/encryption/service.py
"""
Main encryption service for sensitive data protection.

Implements hybrid encryption approach:
- Encrypt data at rest for storage
- Decrypt for AI analysis with user consent
- Admin override with comprehensive audit logging
- Future migration path to zero-knowledge architecture
"""

import base64
import secrets
import logging
from typing import Optional, Dict, Any, Union
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from datetime import datetime

from .models import EncryptedData, EncryptionContext, EncryptionAlgorithm
from .key_manager import key_manager
from ..core.exceptions import EncryptionException

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Comprehensive encryption service for sensitive user data.
    
    Features:
    - AES-256-GCM encryption for data at rest
    - User-derived encryption keys
    - Admin master key override (with audit logging)
    - AI processing consent mechanism
    - Key rotation support
    """
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize encryption service."""
        try:
            await key_manager.initialize()
            self._initialized = True
            logger.info("✅ Encryption service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Encryption service initialization failed: {e}")
            raise EncryptionException(
                "Encryption service initialization failed",
                context={"error": str(e)}
            )
    
    async def encrypt_user_data(
        self, 
        data: str, 
        user_id: str,
        context: Optional[EncryptionContext] = None
    ) -> EncryptedData:
        """
        Encrypt data using user's encryption key.
        
        Args:
            data: Plain text data to encrypt
            user_id: User identifier
            context: Optional encryption context for audit
            
        Returns:
            EncryptedData: Encrypted data with metadata
            
        Raises:
            EncryptionException: If encryption fails
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get user's encryption key
            user_key = key_manager.get_user_key(user_id)
            if not user_key:
                raise EncryptionException(
                    f"User encryption key not available for {user_id}",
                    context={"user_id": user_id}
                )
            
            # Generate unique key ID for this encryption
            key_id = f"user_key:{user_id}:{secrets.token_hex(8)}"
            
            # Encrypt data
            encrypted_data = self._encrypt_data(data, user_key, key_id)
            
            # Log encryption event
            if context:
                logger.info(
                    f"Data encrypted for user {user_id}: {context.operation}",
                    extra={
                        "user_id": user_id,
                        "operation": context.operation,
                        "data_size": len(data),
                        "timestamp": context.timestamp
                    }
                )
            
            return encrypted_data
            
        except Exception as e:
            logger.error(f"Failed to encrypt data for user {user_id}: {e}")
            raise EncryptionException(
                "Data encryption failed",
                context={"user_id": user_id, "error": str(e)}
            )
    
    async def decrypt_user_data(
        self, 
        encrypted_data: EncryptedData, 
        user_id: str,
        context: Optional[EncryptionContext] = None
    ) -> str:
        """
        Decrypt data using user's encryption key.
        
        Args:
            encrypted_data: Encrypted data container
            user_id: User identifier
            context: Optional decryption context for audit
            
        Returns:
            str: Decrypted plain text data
            
        Raises:
            EncryptionException: If decryption fails
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get user's encryption key
            user_key = key_manager.get_user_key(user_id)
            if not user_key:
                raise EncryptionException(
                    f"User encryption key not available for {user_id}",
                    context={"user_id": user_id}
                )
            
            # Decrypt data
            plain_text = self._decrypt_data(encrypted_data, user_key)
            
            # Log decryption event
            if context:
                logger.info(
                    f"Data decrypted for user {user_id}: {context.operation}",
                    extra={
                        "user_id": user_id,
                        "operation": context.operation,
                        "admin_access": context.admin_user_id is not None,
                        "ai_processing": context.operation == "ai_analysis",
                        "timestamp": context.timestamp
                    }
                )
            
            return plain_text
            
        except Exception as e:
            logger.error(f"Failed to decrypt data for user {user_id}: {e}")
            raise EncryptionException(
                "Data decryption failed",
                context={"user_id": user_id, "error": str(e)}
            )
    
    async def decrypt_for_admin(
        self, 
        encrypted_data: EncryptedData, 
        admin_user_id: str,
        reason: str
    ) -> str:
        """
        Decrypt data using admin master key (with audit logging).
        
        Args:
            encrypted_data: Encrypted data container
            admin_user_id: Admin user performing decryption
            reason: Reason for admin access
            
        Returns:
            str: Decrypted plain text data
            
        Raises:
            EncryptionException: If decryption fails
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get admin master key
            admin_key = key_manager.get_admin_master_key()
            
            # Try to decrypt with admin key
            # Note: In practice, data might need re-encryption with admin key
            # or admin key might be used to decrypt user keys
            plain_text = self._decrypt_data(encrypted_data, admin_key)
            
            # Log admin access (CRITICAL for audit)
            logger.warning(
                f"ADMIN ACCESS: Data decrypted by admin {admin_user_id}",
                extra={
                    "admin_user_id": admin_user_id,
                    "reason": reason,
                    "data_key_id": encrypted_data.key_id,
                    "timestamp": datetime.utcnow(),
                    "security_event": "admin_data_access"
                }
            )
            
            return plain_text
            
        except Exception as e:
            logger.error(f"Admin decryption failed for {admin_user_id}: {e}")
            raise EncryptionException(
                "Admin decryption failed",
                context={"admin_user_id": admin_user_id, "error": str(e)}
            )
    
    async def decrypt_for_ai_analysis(
        self, 
        encrypted_data: EncryptedData, 
        user_id: str,
        session_id: str,
        user_consent: bool = False
    ) -> str:
        """
        Decrypt data for AI analysis with user consent.
        
        Args:
            encrypted_data: Encrypted data container
            user_id: User identifier
            session_id: AI processing session identifier
            user_consent: Whether user has given consent
            
        Returns:
            str: Decrypted plain text data
            
        Raises:
            EncryptionException: If consent not given or decryption fails
        """
        if not self._initialized:
            await self.initialize()
        
        if not user_consent:
            raise EncryptionException(
                "AI processing requires user consent",
                context={"user_id": user_id, "session_id": session_id}
            )
        
        try:
            # Generate AI processing key
            ai_key = key_manager.generate_ai_processing_key(user_id, session_id)
            
            # Decrypt data (may need re-encryption with AI key in practice)
            user_key = key_manager.get_user_key(user_id)
            if not user_key:
                raise EncryptionException(f"User key not available for {user_id}")
            
            plain_text = self._decrypt_data(encrypted_data, user_key)
            
            # Log AI processing (for transparency)
            logger.info(
                f"Data decrypted for AI analysis: user {user_id}, session {session_id}",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "consent_given": user_consent,
                    "operation": "ai_analysis",
                    "timestamp": datetime.utcnow()
                }
            )
            
            return plain_text
            
        except Exception as e:
            logger.error(f"AI decryption failed for user {user_id}: {e}")
            raise EncryptionException(
                "AI decryption failed",
                context={"user_id": user_id, "session_id": session_id, "error": str(e)}
            )
        finally:
            # Clean up AI processing key
            key_manager.clear_ai_processing_key(session_id)
    
    def _encrypt_data(self, data: str, key: bytes, key_id: str) -> EncryptedData:
        """
        Low-level data encryption using AES-256-GCM.
        
        Args:
            data: Plain text data
            key: 32-byte encryption key
            key_id: Key identifier for metadata
            
        Returns:
            EncryptedData: Encrypted data container
        """
        try:
            # Create AES-GCM cipher
            aesgcm = AESGCM(key)
            
            # Generate random IV
            iv = secrets.token_bytes(12)  # 96-bit IV for GCM
            
            # Encrypt data (returns ciphertext + tag)
            encrypted_bytes = aesgcm.encrypt(iv, data.encode('utf-8'), None)
            
            # Split ciphertext and tag
            ciphertext = encrypted_bytes[:-16]  # All but last 16 bytes
            tag = encrypted_bytes[-16:]  # Last 16 bytes
            
            return EncryptedData(
                encrypted_content=base64.b64encode(ciphertext).decode(),
                algorithm=EncryptionAlgorithm.AES_256_GCM,
                key_id=key_id,
                iv=base64.b64encode(iv).decode(),
                tag=base64.b64encode(tag).decode(),
                metadata={"algorithm_version": "1.0", "key_length": len(key)}
            )
            
        except Exception as e:
            logger.error(f"Low-level encryption failed: {e}")
            raise
    
    def _decrypt_data(self, encrypted_data: EncryptedData, key: bytes) -> str:
        """
        Low-level data decryption using AES-256-GCM.
        
        Args:
            encrypted_data: Encrypted data container
            key: 32-byte decryption key
            
        Returns:
            str: Decrypted plain text data
        """
        try:
            if encrypted_data.algorithm != EncryptionAlgorithm.AES_256_GCM:
                raise ValueError(f"Unsupported algorithm: {encrypted_data.algorithm}")
            
            # Create AES-GCM cipher
            aesgcm = AESGCM(key)
            
            # Decode components
            ciphertext = base64.b64decode(encrypted_data.encrypted_content)
            iv = base64.b64decode(encrypted_data.iv)
            tag = base64.b64decode(encrypted_data.tag)
            
            # Combine ciphertext and tag for decryption
            encrypted_bytes = ciphertext + tag
            
            # Decrypt data
            plain_bytes = aesgcm.decrypt(iv, encrypted_bytes, None)
            
            return plain_bytes.decode('utf-8')
            
        except InvalidTag:
            logger.error("Decryption failed: Invalid authentication tag")
            raise EncryptionException("Data integrity verification failed")
        except Exception as e:
            logger.error(f"Low-level decryption failed: {e}")
            raise
    
    async def setup_user_encryption(self, user_id: str, password_hash: str) -> None:
        """
        Set up encryption for a user (derive and cache key).
        
        Args:
            user_id: User identifier
            password_hash: User's password hash from auth system
        """
        try:
            # Derive user encryption key
            user_key = key_manager.derive_user_key(user_id, password_hash)
            
            logger.info(f"Encryption setup completed for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to setup encryption for user {user_id}: {e}")
            raise EncryptionException(
                "User encryption setup failed",
                context={"user_id": user_id, "error": str(e)}
            )
    
    async def cleanup_user_encryption(self, user_id: str) -> None:
        """
        Clean up user encryption (clear cached keys).
        
        Args:
            user_id: User identifier
        """
        try:
            key_manager.clear_user_key_cache(user_id)
            logger.info(f"Encryption cleanup completed for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup encryption for user {user_id}: {e}")


# Global encryption service instance
encryption_service = EncryptionService()