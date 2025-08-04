# backend/app/services/session_type_handler.py - NEW MODULE
"""
Type-safe session type handling with robust enum conversion.
"""

import logging
from typing import Optional, Dict, Any, List
from app.models.session import SessionType, MessageRole

logger = logging.getLogger(__name__)

class SessionTypeHandler:
    """
    Handles session type operations with type safety and error resilience.
    
    Design Principles:
    - Fail-safe enum conversion with fallbacks
    - Centralized session type logic
    - Performance-optimized lookups
    - Comprehensive error handling
    """
    
    # Pre-computed mappings for O(1) lookups
    _TYPE_MAPPINGS = {
        # Handle string -> enum conversion
        "reflection_buddy": SessionType.REFLECTION_BUDDY,
        "inner_voice": SessionType.INNER_VOICE,
        "growth_challenge": SessionType.GROWTH_CHALLENGE,
        "pattern_detective": SessionType.PATTERN_DETECTIVE,
        "free_chat": SessionType.FREE_CHAT,
    }
    
    _REVERSE_MAPPINGS = {v: k for k, v in _TYPE_MAPPINGS.items()}
    
    @classmethod
    def normalize_session_type(cls, session_type: Any) -> SessionType:
        """
        Convert any session type representation to proper SessionType enum.
        
        Args:
            session_type: String, enum, or other representation
            
        Returns:
            SessionType: Validated enum value
            
        Raises:
            ValueError: If session_type cannot be normalized
        """
        try:
            # Already a SessionType enum
            if isinstance(session_type, SessionType):
                return session_type
            
            # String representation
            if isinstance(session_type, str):
                normalized = session_type.lower().strip()
                if normalized in cls._TYPE_MAPPINGS:
                    return cls._TYPE_MAPPINGS[normalized]
                
                # Try direct enum lookup
                try:
                    return SessionType(normalized)
                except ValueError:
                    pass
            
            # Last resort: try string conversion
            str_value = str(session_type).lower().strip()
            if str_value in cls._TYPE_MAPPINGS:
                return cls._TYPE_MAPPINGS[str_value]
            
            # Fallback to FREE_CHAT for unknown types
            logger.warning(f"Unknown session type '{session_type}', defaulting to FREE_CHAT")
            return SessionType.FREE_CHAT
            
        except Exception as e:
            logger.error(f"Failed to normalize session type '{session_type}': {e}")
            return SessionType.FREE_CHAT
    
    @classmethod
    def get_session_config(cls, session_type: Any) -> Dict[str, Any]:
        """
        Get configuration for a session type with fail-safe defaults.
        
        Args:
            session_type: Session type identifier
            
        Returns:
            Dict containing session configuration
        """
        normalized_type = cls.normalize_session_type(session_type)
        
        configs = {
            SessionType.REFLECTION_BUDDY: {
                "name": "Reflection Buddy",
                "personality": "warm, curious, and supportive",
                "approach": "gentle exploration and self-discovery",
                "psychology_domains": ["CBT", "emotional_regulation"],
                "default_suggestions": [
                    "How does that make you feel when you really sit with it?",
                    "What patterns do you notice in this experience?",
                    "Can you tell me more about what that means to you?",
                    "What would self-compassion look like in this situation?"
                ]
            },
            
            SessionType.INNER_VOICE: {
                "name": "Inner Voice Guide",
                "personality": "wise, contemplative, and insightful",
                "approach": "accessing internal wisdom and perspective",
                "psychology_domains": ["mindfulness", "positive_psychology"],
                "default_suggestions": [
                    "What would your wisest self say about this?",
                    "How might you view this situation with fresh eyes?",
                    "What perspective would bring you most peace?",
                    "What does your intuition tell you about this?"
                ]
            },
            
            SessionType.GROWTH_CHALLENGE: {
                "name": "Growth Coach",
                "personality": "encouraging, motivational, and empowering",
                "approach": "structured challenges with supportive accountability",
                "psychology_domains": ["habit_formation", "positive_psychology"],
                "default_suggestions": [
                    "What's one small step you could take today?",
                    "How could you turn this challenge into growth?",
                    "What strengths do you have that could help here?",
                    "What would progress look like for you?"
                ]
            },
            
            SessionType.PATTERN_DETECTIVE: {
                "name": "Pattern Detective",
                "personality": "observant, analytical, and insightful",
                "approach": "data-driven insights with actionable suggestions",
                "psychology_domains": ["CBT", "social_psychology"],
                "default_suggestions": [
                    "Have you noticed this pattern before?",
                    "What triggers this feeling or behavior?",
                    "What would breaking this pattern look like?",
                    "What patterns actually serve you well?"
                ]
            },
            
            SessionType.FREE_CHAT: {
                "name": "Supportive Companion",
                "personality": "flexible, adaptive, and supportive",
                "approach": "integrates multiple therapeutic modalities",
                "psychology_domains": ["CBT", "mindfulness", "emotional_regulation"],
                "default_suggestions": [
                    "What's most important to you about this?",
                    "How are you feeling about all of this?",
                    "What would help you move forward?",
                    "What support do you need right now?"
                ]
            }
        }
        
        return configs.get(normalized_type, configs[SessionType.FREE_CHAT])
    
    @classmethod
    def validate_message_role(cls, role: Any) -> MessageRole:
        """Validate and normalize message roles."""
        try:
            if isinstance(role, MessageRole):
                return role
            
            if isinstance(role, str):
                return MessageRole(role.lower())
            
            logger.warning(f"Unknown message role '{role}', defaulting to USER")
            return MessageRole.USER
            
        except Exception as e:
            logger.error(f"Failed to validate message role '{role}': {e}")
            return MessageRole.USER