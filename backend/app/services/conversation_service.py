# backend/app/services/conversation_service.py - Enhanced with Psychology Integration & Robust Type Handling

import json
import random
from typing import List, Dict, Any, Optional, Tuple, Union
import logging
from datetime import datetime, timedelta
from app.models.session import SessionType, Message, MessageRole
from app.services.llm_service import llm_service
from app.services.database_service import db_service
from app.services.session_service import session_service
from app.services.psychology_knowledge_service import psychology_knowledge_service, PsychologyDomain

logger = logging.getLogger(__name__)

class SessionTypeHandler:
    """
    Centralized handler for session type operations with fail-safe mechanisms.
    
    Features:
    - Type-safe enum normalization with fallback handling
    - Performance-optimized configuration caching
    - Comprehensive error recovery
    - Clear separation of concerns
    """
    
    def __init__(self):
        """Initialize the session type handler with optimized configurations."""
        self._session_configs = self._build_session_configurations()
        self._string_to_enum_cache = self._build_string_mapping_cache()
        
    def _build_session_configurations(self) -> Dict[SessionType, Dict[str, Any]]:
        """
        Build comprehensive session type configurations.
        
        Returns:
            Dict mapping SessionType enums to their complete configurations
        """
        return {
            SessionType.REFLECTION_BUDDY: {
                "name": "Reflection Buddy",
                "personality": "warm, curious, and supportive",
                "approach": "Uses active listening and open-ended questions informed by person-centered therapy principles",
                "psychology_domains": [PsychologyDomain.CBT, PsychologyDomain.EMOTIONAL_REGULATION],
                "greeting_style": "warm and approachable with genuine curiosity",
                "default_suggestions": [
                    "How does that make you feel when you really sit with it?",
                    "What patterns do you notice in this experience?",
                    "Can you tell me more about what that means to you?",
                    "What would self-compassion look like in this situation?"
                ],
                "fallback_response": "I'm here to listen and explore this with you. Can you tell me more about what you're experiencing?"
            },
            
            SessionType.INNER_VOICE: {
                "name": "Inner Voice Guide",
                "personality": "wise, contemplative, and insightful",
                "approach": "Guides perspective-taking and internal reflection using proven therapeutic methods",
                "psychology_domains": [PsychologyDomain.MINDFULNESS, PsychologyDomain.POSITIVE_PSYCHOLOGY],
                "greeting_style": "thoughtful and introspective with depth",
                "default_suggestions": [
                    "What would your wisest self say about this?",
                    "How might you view this situation with fresh eyes?",
                    "What perspective would bring you most peace?",
                    "What does your intuition tell you about this?"
                ],
                "fallback_response": "Let's pause and reflect together. What feels most important to you right now?"
            },
            
            SessionType.GROWTH_CHALLENGE: {
                "name": "Growth Coach",
                "personality": "encouraging, motivational, and empowering",
                "approach": "Structured challenges with supportive accountability using habit formation science",
                "psychology_domains": [PsychologyDomain.HABIT_FORMATION, PsychologyDomain.POSITIVE_PSYCHOLOGY],
                "greeting_style": "energetic and goal-oriented with optimism",
                "default_suggestions": [
                    "What's one small step you could take today?",
                    "How could you turn this challenge into growth?",
                    "What strengths do you have that could help here?",
                    "What would progress look like for you?"
                ],
                "fallback_response": "That's interesting. What would growth look like in this situation?"
            },
            
            SessionType.PATTERN_DETECTIVE: {
                "name": "Pattern Detective",
                "personality": "observant, analytical, and insightful",
                "approach": "Data-driven insights with actionable suggestions using CBT frameworks",
                "psychology_domains": [PsychologyDomain.CBT, PsychologyDomain.SOCIAL_PSYCHOLOGY],
                "greeting_style": "curious and analytical with systematic thinking",
                "default_suggestions": [
                    "Have you noticed this pattern before?",
                    "What triggers this feeling or behavior?",
                    "What would breaking this pattern look like?",
                    "What patterns actually serve you well?"
                ],
                "fallback_response": "I'm curious about the patterns here. What do you notice when you step back and observe?"
            },
            
            SessionType.FREE_CHAT: {
                "name": "Supportive Companion",
                "personality": "flexible, adaptive, and supportive",
                "approach": "Integrates multiple therapeutic modalities as appropriate to the conversation",
                "psychology_domains": [PsychologyDomain.CBT, PsychologyDomain.MINDFULNESS, PsychologyDomain.EMOTIONAL_REGULATION],
                "greeting_style": "warm and adaptive to user's energy",
                "default_suggestions": [
                    "What's most important to you about this?",
                    "How are you feeling about all of this?",
                    "What would help you move forward?",
                    "What support do you need right now?"
                ],
                "fallback_response": "I'm here to support you. What's on your mind?"
            }
        }
    
    def _build_string_mapping_cache(self) -> Dict[str, SessionType]:
        """
        Build optimized string-to-enum mapping cache.
        
        Returns:
            Dict mapping various string representations to SessionType enums
        """
        mapping = {}
        
        for session_type in SessionType:
            # Add enum name mappings
            mapping[session_type.name.lower()] = session_type
            mapping[session_type.name.upper()] = session_type
            mapping[session_type.name] = session_type
            
            # Add enum value mappings
            mapping[session_type.value.lower()] = session_type
            mapping[session_type.value.upper()] = session_type
            mapping[session_type.value] = session_type
            
            # Add common variations
            normalized_value = session_type.value.replace('_', ' ').lower()
            mapping[normalized_value] = session_type
            
            # Add config name mappings
            config = self._session_configs[session_type]
            mapping[config["name"].lower()] = session_type
        
        return mapping
    
    def normalize_session_type(self, session_type: Any) -> SessionType:
        """
        Normalize any session type input to a valid SessionType enum.
        
        Args:
            session_type: Input that should represent a session type
                         (can be SessionType, str, int, or any other type)
        
        Returns:
            SessionType: Valid SessionType enum with fail-safe fallback
        """
        try:
            # Case 1: Already a SessionType enum
            if isinstance(session_type, SessionType):
                return session_type
            
            # Case 2: String representation
            if isinstance(session_type, str):
                # Try direct cache lookup first (most common case)
                if session_type in self._string_to_enum_cache:
                    return self._string_to_enum_cache[session_type]
                
                # Try case-insensitive lookup
                lower_type = session_type.lower()
                if lower_type in self._string_to_enum_cache:
                    return self._string_to_enum_cache[lower_type]
                
                # Try with underscores replaced
                normalized = session_type.replace(' ', '_').lower()
                if normalized in self._string_to_enum_cache:
                    return self._string_to_enum_cache[normalized]
            
            # Case 3: Integer (enum index)
            if isinstance(session_type, int):
                session_types = list(SessionType)
                if 0 <= session_type < len(session_types):
                    return session_types[session_type]
            
            # Case 4: Dictionary with session type info
            if isinstance(session_type, dict):
                if 'session_type' in session_type:
                    return self.normalize_session_type(session_type['session_type'])
                if 'type' in session_type:
                    return self.normalize_session_type(session_type['type'])
            
            logger.warning(f"Unable to normalize session type: {session_type} (type: {type(session_type)})")
            
        except Exception as e:
            logger.error(f"Error normalizing session type {session_type}: {e}")
        
        # Fail-safe: return default session type
        logger.info("Falling back to FREE_CHAT session type")
        return SessionType.FREE_CHAT
    
    def get_session_config(self, session_type: SessionType) -> Dict[str, Any]:
        """
        Get configuration for a session type with fail-safe handling.
        
        Args:
            session_type: SessionType enum
            
        Returns:
            Dict containing session configuration
        """
        try:
            return self._session_configs[session_type]
        except KeyError:
            logger.warning(f"No configuration found for session type: {session_type}")
            return self._session_configs[SessionType.FREE_CHAT]
    
    def validate_message_role(self, role: Any) -> MessageRole:
        """
        Validate and normalize message role input.
        
        Args:
            role: Input that should represent a message role
            
        Returns:
            MessageRole: Valid MessageRole enum
        """
        try:
            # Case 1: Already a MessageRole enum
            if isinstance(role, MessageRole):
                return role
            
            # Case 2: String representation
            if isinstance(role, str):
                role_upper = role.upper()
                for message_role in MessageRole:
                    if message_role.name == role_upper or message_role.value == role_upper:
                        return message_role
            
            # Case 3: Integer
            if isinstance(role, int):
                roles = list(MessageRole)
                if 0 <= role < len(roles):
                    return roles[role]
            
        except Exception as e:
            logger.error(f"Error validating message role {role}: {e}")
        
        # Fail-safe: return default role
        return MessageRole.USER


class EnhancedConversationService:
    """
    Enhanced conversation service with professional psychology knowledge integration.
    
    Provides evidence-based, research-backed conversational AI that combines:
    - Personality-based conversation styles
    - Professional psychology insights
    - Personal context from journal entries
    - Source attribution for credibility
    - Robust type handling and error recovery
    """
    
    def __init__(self):
        self.llm_service = llm_service
        self.psychology_service = psychology_knowledge_service
        self.session_handler = SessionTypeHandler()
        
        # Enhanced personality definitions with psychology integration
        # Using the original structure but with type handler integration
        self.personalities = {
            SessionType.REFLECTION_BUDDY: {
                "name": "Reflection Buddy",
                "tone": "warm, curious, and supportive",
                "style": "Uses active listening and open-ended questions informed by person-centered therapy principles",
                "approach": "Facilitates self-discovery through gentle exploration and reflection",
                "psychology_domains": [PsychologyDomain.CBT, PsychologyDomain.EMOTIONAL_REGULATION],
                "greeting_style": "warm and approachable with genuine curiosity"
            },
            
            SessionType.INNER_VOICE: {
                "name": "Inner Voice Guide", 
                "tone": "wise, contemplative, and insightful",
                "style": "Helps access internal wisdom using mindfulness and self-compassion techniques",
                "approach": "Guides perspective-taking and internal reflection using proven therapeutic methods",
                "psychology_domains": [PsychologyDomain.MINDFULNESS, PsychologyDomain.POSITIVE_PSYCHOLOGY],
                "greeting_style": "thoughtful and introspective with depth"
            },
            
            SessionType.GROWTH_CHALLENGE: {
                "name": "Growth Coach",
                "tone": "encouraging, motivational, and empowering",
                "style": "Uses evidence-based behavior change techniques and positive psychology principles",
                "approach": "Structured challenges with supportive accountability using habit formation science",
                "psychology_domains": [PsychologyDomain.HABIT_FORMATION, PsychologyDomain.POSITIVE_PSYCHOLOGY],
                "greeting_style": "energetic and goal-oriented with optimism"
            },
            
            SessionType.PATTERN_DETECTIVE: {
                "name": "Pattern Detective",
                "tone": "observant, analytical, and insightful", 
                "style": "Uses cognitive-behavioral analysis to identify thought and behavior patterns",
                "approach": "Data-driven insights with actionable suggestions using CBT frameworks",
                "psychology_domains": [PsychologyDomain.CBT, PsychologyDomain.SOCIAL_PSYCHOLOGY],
                "greeting_style": "curious and analytical with systematic thinking"
            },
            
            SessionType.FREE_CHAT: {
                "name": "Supportive Companion",
                "tone": "flexible, adaptive, and supportive",
                "style": "Adapts therapeutic approach based on user needs and conversation flow",
                "approach": "Integrates multiple therapeutic modalities as appropriate to the conversation",
                "psychology_domains": [PsychologyDomain.CBT, PsychologyDomain.MINDFULNESS, PsychologyDomain.EMOTIONAL_REGULATION],
                "greeting_style": "warm and adaptive to user's energy"
            }
        }
    
    async def generate_opening_message(self, session_type: Union[SessionType, str, Any], context: Dict[str, Any] = None) -> str:
        """
        Generate psychology-informed opening message for a new session.
        
        Args:
            session_type: Session type (will be normalized internally)
            context: Optional context dictionary
            
        Returns:
            str: Psychology-informed opening message
        """
        try:
            # Normalize session type with robust handling
            normalized_session_type = self.session_handler.normalize_session_type(session_type)
            logger.debug(f"Normalized session type for opening: {session_type} -> {normalized_session_type}")
            
            personality = self.personalities[normalized_session_type]
            user_name = context.get('user_name', 'friend') if context else 'friend'
            
            # Get recent journal context for personalization
            recent_entries = await self._get_recent_journal_context()
            mood_context = await self._get_recent_mood_context()
            
            # Get relevant psychology knowledge for the session type
            psychology_insights = await self._get_opening_psychology_context(normalized_session_type, recent_entries)
            
            # Base opening messages with psychology integration
            opening_templates = {
                SessionType.REFLECTION_BUDDY: [
                    f"Hey {user_name}! 😊 I'm here as your reflection buddy, drawing on active listening techniques to help you explore your thoughts. How are you feeling right now?",
                    f"Hi there! I'm curious to hear what's been going through your mind lately. Using person-centered approaches, I'm here to help you discover your own insights.",
                    f"Hello {user_name}! Research shows that reflective conversation can significantly improve self-awareness. What would you like to explore together today?"
                ],
                
                SessionType.INNER_VOICE: [
                    f"Hello {user_name}. Let's tap into your inner wisdom using mindfulness principles. Take a moment to notice what you're experiencing right now - what situation or feeling would you like to examine more deeply?",
                    f"Hi there. Drawing on contemplative practices, I'm here to help you access different perspectives. What's something you've been wondering about or feeling uncertain about?",
                    f"Welcome, {user_name}. Sometimes we need to step back and listen to our inner voice. What's asking for your attention today?"
                ],
                
                SessionType.GROWTH_CHALLENGE: [
                    f"Hey {user_name}! Ready for some evidence-based growth? 🌱 Research in habit formation shows that small, consistent changes create lasting transformation. What area of your life would you like to develop?",
                    f"Hi there! I'm excited to help you explore new possibilities using positive psychology principles. What challenge or growth opportunity is calling to you?",
                    f"Welcome to your growth session, {user_name}! Studies show that goal-setting combined with social support dramatically increases success. Let's discover something new about your potential today."
                ],
                
                SessionType.PATTERN_DETECTIVE: [
                    f"Hello {user_name}! 🔍 Using cognitive-behavioral analysis, I've noticed some interesting themes in your recent reflections. Want to explore what patterns might be emerging?",
                    f"Hi there! As your pattern detective, I use evidence-based observation techniques to spot trends. What patterns have you noticed in your thoughts or behaviors lately?",
                    f"Hey {user_name}! Research shows that pattern recognition is key to personal growth. I love connecting dots and finding insights - what recurring themes are you curious about?"
                ],
                
                SessionType.FREE_CHAT: [
                    f"Hi {user_name}! I'm here as your supportive companion, ready to adapt my approach based on what you need. What's on your mind today?",
                    f"Hello! I'm here to chat about whatever feels important to you, using therapeutic principles as appropriate. How can I support you right now?",
                    f"Hey {user_name}! Whether you need reflection, problem-solving, or just someone to listen, I'm here with evidence-based support. What would be most helpful?"
                ]
            }
            
            base_messages = opening_templates.get(normalized_session_type, opening_templates[SessionType.FREE_CHAT])
            base_message = random.choice(base_messages)
            
            # Add personalized context if available
            if recent_entries or mood_context or psychology_insights:
                context_addition = await self._generate_contextual_opening(
                    normalized_session_type, recent_entries, mood_context, psychology_insights
                )
                if context_addition:
                    base_message += f"\n\n{context_addition}"
            
            return base_message
            
        except Exception as e:
            logger.error(f"Error generating opening message: {e}")
            return "Hello! I'm here to support you in our conversation. What's on your mind today?"

    async def generate_response(
        self, 
        session_type: Union[SessionType, str, Any], 
        user_message: str,
        conversation_history: List[Message], 
        context: Dict[str, Any] = None
    ) -> str:
        """
        Generate psychology-informed AI response with source attribution.
        
        Args:
            session_type: Session type (will be normalized internally)
            user_message: User's input message
            conversation_history: Previous conversation messages
            context: Optional context dictionary
        
        Returns:
            str: The AI response text only (citations handled separately)
        """
        try:
            # Normalize session type with robust handling
            normalized_session_type = self.session_handler.normalize_session_type(session_type)
            logger.debug(f"Normalized session type for response: {session_type} -> {normalized_session_type}")
            
            # Get journal context for richer understanding
            journal_context = await self._get_relevant_journal_context(user_message)
            
            # Generate evidence-based response with citations
            response, citations = await self.llm_service.generate_evidence_based_response(
                user_message=user_message,
                conversation_history=[
                    {"role": msg.role, "content": msg.content} 
                    for msg in conversation_history
                ],
                journal_context=journal_context,
                session_type=normalized_session_type.value
            )
            
            # Post-process response to ensure conversational tone
            response = self._post_process_response(response, normalized_session_type)
            
            logger.info(f"Generated psychology-informed response with {len(citations)} citations")
            
            # Store citations in session metadata if needed
            if citations and context:
                context['psychology_citations'] = citations
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating enhanced response: {e}")
            # Fallback to basic response using type handler
            normalized_session_type = self.session_handler.normalize_session_type(session_type)
            fallback_response = self._get_fallback_response(normalized_session_type)
            return fallback_response
    
    async def suggest_follow_up_questions(
        self, 
        session_type: Union[SessionType, str, Any],  # Accept any type and normalize
        recent_messages: List[Message],
        psychology_context: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """
        Generate psychology-informed follow-up question suggestions with robust type handling.
        
        Args:
            session_type: Session type (will be normalized internally)
            recent_messages: Recent conversation messages
            psychology_context: Optional psychology knowledge context
            
        Returns:
            List of follow-up question suggestions
        """
        try:
            # Normalize session type with fail-safe handling
            normalized_session_type = self.session_handler.normalize_session_type(session_type)
            logger.debug(f"Normalized session type for suggestions: {session_type} -> {normalized_session_type}")
            
            if not recent_messages:
                # Return default suggestions for the session type using handler
                config = self.session_handler.get_session_config(normalized_session_type)
                return config["default_suggestions"][:3]

            # Extract last user message with robust role validation
            last_user_message = None
            for msg in reversed(recent_messages):
                validated_role = self.session_handler.validate_message_role(msg.role)
                if validated_role == MessageRole.USER:
                    last_user_message = msg.content
                    break

            if not last_user_message:
                # Fallback to default suggestions
                config = self.session_handler.get_session_config(normalized_session_type)
                return config["default_suggestions"][:3]

            # Get psychology-informed suggestions based on session type
            personality = self.personalities.get(normalized_session_type, {})
            
            if not personality:
                # Additional fallback for unknown session types
                logger.warning(f"Unknown session type: {normalized_session_type}, using default")
                personality = self.personalities.get(SessionType.FREE_CHAT, {})

            # Base suggestions by session type with psychology integration
            base_suggestions = {
                SessionType.REFLECTION_BUDDY: [
                    "How does that make you feel when you really sit with it?",
                    "What patterns do you notice in this experience?",
                    "Can you tell me more about what that means to you?",
                    "What would self-compassion look like in this situation?"
                ],
                
                SessionType.INNER_VOICE: [
                    "What would your wisest self say about this?",
                    "How might you view this situation with fresh eyes?",
                    "What perspective would bring you most peace?",
                    "What does your intuition tell you about this?"
                ],
                
                SessionType.GROWTH_CHALLENGE: [
                    "What's one small step you could take today?",
                    "How could you turn this challenge into growth?",
                    "What strengths do you have that could help here?",
                    "What would progress look like for you?"
                ],
                
                SessionType.PATTERN_DETECTIVE: [
                    "Have you noticed this pattern before?",
                    "What triggers this feeling or behavior?",
                    "What would breaking this pattern look like?",
                    "What patterns actually serve you well?"
                ],
                
                SessionType.FREE_CHAT: [
                    "What's most important to you about this?",
                    "How are you feeling about all of this?",
                    "What would help you move forward?",
                    "What support do you need right now?"
                ]
            }
            
            suggestions = base_suggestions.get(normalized_session_type, base_suggestions[SessionType.FREE_CHAT])
            
            # Enhance suggestions with psychology context if available
            if psychology_context:
                try:
                    enhanced_suggestions = await self._enhance_suggestions_with_psychology(
                        suggestions, psychology_context, last_user_message
                    )
                    return enhanced_suggestions[:3]
                except Exception as e:
                    logger.warning(f"Failed to enhance suggestions with psychology: {e}")
                    # Fall back to base suggestions
            
            return suggestions[:3]
            
        except Exception as e:
            logger.error(f"Error generating follow-up suggestions: {e}")
            # Ultimate fallback: generic questions
            return [
                "Can you tell me more about that?",
                "How are you feeling about this situation?",
                "What would be most helpful to explore next?"
            ]
    
    # === PRIVATE HELPER METHODS ===
    # All original helper methods preserved with enhanced error handling
    
    async def _get_opening_psychology_context(
        self, 
        session_type: SessionType, 
        recent_entries: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Get relevant psychology knowledge for session opening"""
        try:
            personality = self.personalities[session_type]
            
            # Create search query based on session type and recent entries
            search_context = f"conversation opening {session_type.value}"
            if recent_entries:
                search_context += f" {recent_entries[:200]}"
            
            # Get psychology knowledge for the session's preferred domains
            psychology_insights = await self.psychology_service.get_knowledge_for_context(
                user_message=search_context,
                preferred_domains=personality["psychology_domains"],
                max_sources=2
            )
            
            return psychology_insights
            
        except Exception as e:
            logger.error(f"Error getting opening psychology context: {e}")
            return []
    
    async def _get_relevant_journal_context(self, user_message: str) -> Optional[str]:
        """Get relevant journal context for the user's message"""
        try:
            # Get recent entries that might be relevant
            recent_entries = await db_service.get_entries(limit=5)
            
            if not recent_entries:
                return None
            
            # Simple relevance check based on keywords
            user_words = set(user_message.lower().split())
            relevant_entries = []
            
            for entry in recent_entries:
                entry_words = set(entry.content.lower().split())
                common_words = user_words.intersection(entry_words)
                
                # If there are common meaningful words, include the entry
                if len(common_words) > 2:
                    relevant_entries.append(entry)
            
            if relevant_entries:
                # Combine relevant entry summaries
                context_parts = []
                for entry in relevant_entries[:2]:  # Max 2 entries
                    context_parts.append(f"Recent journal entry: {entry.content[:150]}...")
                
                return " ".join(context_parts)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting journal context: {e}")
            return None
    
    async def _enhance_suggestions_with_psychology(
        self,
        base_suggestions: List[str],
        psychology_context: List[Dict[str, Any]],
        user_message: str
    ) -> List[str]:
        """Enhance follow-up suggestions using psychology knowledge"""
        try:
            # Extract key techniques from psychology context
            techniques = []
            for source in psychology_context:
                techniques.extend(source.get('techniques', [])[:2])
            
            # Create enhanced suggestions incorporating techniques
            enhanced = base_suggestions.copy()
            
            if 'cognitive restructuring' in techniques:
                enhanced.append("What evidence supports or challenges that thought?")
            
            if 'mindfulness' in techniques or 'mindfulness meditation' in techniques:
                enhanced.append("What would happen if you just observed this feeling without judgment?")
            
            if 'behavioral activation' in techniques:
                enhanced.append("What activity might help shift your mood right now?")
            
            if 'HALT' in techniques:
                enhanced.append("Are you hungry, angry, lonely, or tired right now?")
            
            return enhanced[:4]  # Return top 4 suggestions
            
        except Exception as e:
            logger.error(f"Error enhancing suggestions: {e}")
            return base_suggestions
    
    def _post_process_response(self, response: str, session_type: SessionType) -> str:
        """Post-process AI response to ensure appropriate tone and length"""
        response = response.strip()
        
        # Remove unwanted prefixes
        prefixes_to_remove = [
            "As a Reflection Buddy:",
            "As an Inner Voice Guide:",
            "As a Growth Coach:",
            "As a Pattern Detective:",
            "As a Supportive Companion:",
            "AI:",
            "Assistant:"
        ]
        
        for prefix in prefixes_to_remove:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()
        
        # Ensure appropriate length (not too long for conversation)
        if len(response) > 600:
            sentences = response.split('. ')
            response = '. '.join(sentences[:4]) + '.'
        
        return response
    
    def _get_fallback_response(self, session_type: SessionType) -> str:
        """Get fallback response when enhanced generation fails"""
        try:
            # Use session handler for consistent fallback responses
            config = self.session_handler.get_session_config(session_type)
            return config["fallback_response"]
        except Exception as e:
            logger.error(f"Error getting fallback response: {e}")
            return "I'm here to listen. What would be most helpful to talk about?"
    
    async def _get_recent_journal_context(self) -> Optional[str]:
        """Get context from recent journal entries"""
        try:
            recent_entries = await db_service.get_entries(limit=3)
            if recent_entries:
                themes = []
                for entry in recent_entries:
                    if len(entry.content) > 50:
                        themes.append(entry.title or entry.content[:100])
                
                if themes:
                    return f"Recent themes: {', '.join(themes)}"
        except Exception as e:
            logger.error(f"Error getting journal context: {e}")
        
        return None
    
    async def _get_recent_mood_context(self) -> Optional[str]:
        """Get context from recent mood patterns"""
        try:
            mood_stats = await db_service.get_mood_statistics(7)
            if mood_stats and mood_stats.get('mood_distribution'):
                moods = mood_stats['mood_distribution']
                if moods:
                    dominant_mood = max(moods.items(), key=lambda x: x[1])[0]
                    return f"Recent mood trend: {dominant_mood.replace('_', ' ')}"
        except Exception as e:
            logger.error(f"Error getting mood context: {e}")
        
        return None
    
    async def _generate_contextual_opening(
        self,
        session_type: SessionType,
        recent_entries: Optional[str],
        mood_context: Optional[str], 
        psychology_insights: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Generate contextual addition to opening message"""
        context_parts = []
        
        if recent_entries:
            context_parts.append(recent_entries)
        if mood_context:
            context_parts.append(mood_context)
        
        if not context_parts and not psychology_insights:
            return None
        
        context_info = " | ".join(context_parts)
        
        # Add psychology-informed context based on session type
        if session_type == SessionType.PATTERN_DETECTIVE and psychology_insights:
            techniques = []
            for insight in psychology_insights:
                techniques.extend(insight.get('techniques', [])[:1])
            
            if techniques:
                return f"I noticed some interesting themes lately: {context_info}. Using {techniques[0]} approaches, want to explore these patterns?"
        
        elif session_type == SessionType.REFLECTION_BUDDY and context_info:
            return f"I see you've been reflecting on some meaningful topics recently. How are you feeling about everything?"
        
        elif session_type == SessionType.GROWTH_CHALLENGE and psychology_insights:
            return f"Based on your recent reflections, I have some evidence-based growth ideas that might interest you."
        
        return None


# Global instance
conversation_service = EnhancedConversationService()