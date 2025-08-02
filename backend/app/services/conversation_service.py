### app/services/conversation_service.py

import json
import random
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
from app.models.session import SessionType, Message, MessageRole
from app.services.llm_service import llm_service
from app.services.database_service import db_service
from app.services.session_service import session_service

logger = logging.getLogger(__name__)

class ConversationPersonality:
    """Defines AI personality traits for different session types"""
    
    REFLECTION_BUDDY = {
        "name": "Reflection Buddy",
        "tone": "casual and friendly",
        "style": "curious friend who asks thoughtful questions",
        "approach": "gentle exploration through friendly conversation",
        "greeting_style": "warm and approachable"
    }
    
    INNER_VOICE = {
        "name": "Inner Voice Guide",
        "tone": "wise and contemplative", 
        "style": "helps explore different perspectives",
        "approach": "guides self-discovery through perspective-taking",
        "greeting_style": "thoughtful and introspective"
    }
    
    GROWTH_CHALLENGE = {
        "name": "Growth Coach",
        "tone": "encouraging and motivational",
        "style": "supportive challenger who promotes growth",
        "approach": "structured challenges with positive reinforcement",
        "greeting_style": "energetic and goal-oriented"
    }
    
    PATTERN_DETECTIVE = {
        "name": "Pattern Detective",
        "tone": "observant and insightful",
        "style": "analytical friend who notices patterns",
        "approach": "data-driven insights with actionable suggestions",
        "greeting_style": "curious and analytical"
    }

class ConversationService:
    def __init__(self):
        self.personalities = {
            SessionType.REFLECTION_BUDDY: ConversationPersonality.REFLECTION_BUDDY,
            SessionType.INNER_VOICE: ConversationPersonality.INNER_VOICE,
            SessionType.GROWTH_CHALLENGE: ConversationPersonality.GROWTH_CHALLENGE,
            SessionType.PATTERN_DETECTIVE: ConversationPersonality.PATTERN_DETECTIVE,
            SessionType.FREE_CHAT: ConversationPersonality.REFLECTION_BUDDY
        }
    
    async def generate_opening_message(self, session_type: SessionType, context: Dict[str, Any] = None) -> str:
        """Generate an opening message for a new session"""
        personality = self.personalities[session_type]
        user_name = context.get('user_name', 'friend') if context else 'friend'
        
        # Get recent journal context for personalization
        recent_entries = await self._get_recent_journal_context()
        mood_context = await self._get_recent_mood_context()
        
        opening_prompts = {
            SessionType.REFLECTION_BUDDY: [
                f"Hey {user_name}! 😊 How are you feeling right now? I'm here to chat about whatever's on your mind.",
                f"Hi there! What's been going through your head lately? I'm curious to hear what you're thinking about.",
                f"Hello {user_name}! I'm here as your reflection buddy. What would you like to explore together today?"
            ],
            
            SessionType.INNER_VOICE: [
                f"Hello {user_name}. Let's take a moment to explore different perspectives on what you're experiencing. What situation or feeling would you like to examine more deeply?",
                f"Hi there. I'm here to help you hear your inner wisdom. What's something you've been wondering about or struggling with?",
                f"Welcome, {user_name}. Sometimes we need to step back and see things from different angles. What's on your mind today?"
            ],
            
            SessionType.GROWTH_CHALLENGE: [
                f"Hey {user_name}! Ready for some growth? 🌱 I have some interesting challenges that might help you develop new insights about yourself.",
                f"Hi there! I'm excited to help you explore new aspects of yourself. What area of your life would you like to grow in?",
                f"Welcome to your growth session, {user_name}! Let's discover something new about yourself today."
            ],
            
            SessionType.PATTERN_DETECTIVE: [
                f"Hello {user_name}! 🔍 I've been noticing some interesting patterns in your recent entries. Want to explore what they might mean?",
                f"Hi there! As your pattern detective, I've spotted some trends in your journaling. Shall we investigate together?",
                f"Hey {user_name}! I love connecting dots and finding insights. What patterns have you noticed in your life lately?"
            ]
        }
        
        base_messages = opening_prompts.get(session_type, opening_prompts[SessionType.REFLECTION_BUDDY])
        base_message = random.choice(base_messages)
        
        # Add personalized context if available
        if recent_entries or mood_context:
            context_addition = await self._generate_contextual_opening(session_type, recent_entries, mood_context)
            if context_addition:
                base_message += f"\n\n{context_addition}"
        
        return base_message
    
    async def generate_response(self, session_type: SessionType, user_message: str, 
                              conversation_history: List[Message], context: Dict[str, Any] = None) -> str:
        """Generate AI response based on conversation context"""
        personality = self.personalities[session_type]
        
        # Build conversation context for LLM
        conversation_context = self._build_conversation_context(conversation_history)
        
        # Create personality-specific prompt
        system_prompt = self._create_system_prompt(session_type, personality, context)
        
        # Generate response using LLM
        full_prompt = f"{system_prompt}\n\nConversation so far:\n{conversation_context}\n\nUser just said: {user_message}\n\nRespond as the {personality['name']}:"
        
        try:
            response = await llm_service.generate_response(full_prompt)
            
            # Post-process response to ensure quality
            response = self._post_process_response(response, session_type)
            
            return response
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._get_fallback_response(session_type)
    
    async def suggest_follow_up_questions(self, session_type: SessionType, 
                                        recent_messages: List[Message]) -> List[str]:
        """Generate follow-up question suggestions"""
        if not recent_messages:
            return []
        
        last_user_message = None
        for msg in reversed(recent_messages):
            if msg.role == MessageRole.USER:
                last_user_message = msg.content
                break
        
        if not last_user_message:
            return []
        
        suggestions = {
            SessionType.REFLECTION_BUDDY: [
                "How does that make you feel?",
                "What do you think caused that?",
                "Can you tell me more about that?",
                "What would you like to be different?"
            ],
            
            SessionType.INNER_VOICE: [
                "What would your wise future self say about this?",
                "How might your best friend view this situation?",
                "What perspective am I missing here?",
                "What would love do in this situation?"
            ],
            
            SessionType.GROWTH_CHALLENGE: [
                "What's one small step you could take today?",
                "What would happen if you tried a different approach?",
                "What strengths could you use here?",
                "What would growth look like in this situation?"
            ],
            
            SessionType.PATTERN_DETECTIVE: [
                "Have you noticed this pattern before?",
                "What triggers this feeling/behavior?",
                "What would breaking this pattern look like?",
                "What patterns serve you well?"
            ]
        }
        
        return suggestions.get(session_type, suggestions[SessionType.REFLECTION_BUDDY])[:3]
    
    def _create_system_prompt(self, session_type: SessionType, personality: Dict[str, Any], 
                             context: Dict[str, Any] = None) -> str:
        """Create personality-specific system prompt"""
        base_prompt = f"""You are the {personality['name']}, an AI companion for journaling and self-reflection.

Your personality:
- Tone: {personality['tone']}
- Style: {personality['style']}
- Approach: {personality['approach']}

Guidelines:
- Keep responses conversational and under 3 sentences
- Ask thoughtful follow-up questions
- Be empathetic and non-judgmental
- Focus on helping the user reflect and gain insights
- Avoid giving direct advice; instead guide them to their own conclusions
- Use the user's name occasionally to make it personal
- Be authentic and warm in your responses

Remember: You're having a real conversation with someone who trusts you with their thoughts."""

        # Add session-specific guidelines
        if session_type == SessionType.REFLECTION_BUDDY:
            base_prompt += "\n\nAs a Reflection Buddy, be curious and ask the kinds of questions a good friend would ask. Help them process their thoughts and feelings."
        
        elif session_type == SessionType.INNER_VOICE:
            base_prompt += "\n\nAs an Inner Voice Guide, help them explore different perspectives. Ask 'What would X say?' or 'How might Y view this?' to broaden their viewpoint."
        
        elif session_type == SessionType.GROWTH_CHALLENGE:
            base_prompt += "\n\nAs a Growth Coach, gently challenge them to grow. Suggest small experiments or new ways of thinking. Be encouraging and celebrate progress."
        
        elif session_type == SessionType.PATTERN_DETECTIVE:
            base_prompt += "\n\nAs a Pattern Detective, help them notice recurring themes in their life. Point out patterns you observe and ask about connections."
        
        return base_prompt
    
    def _build_conversation_context(self, messages: List[Message]) -> str:
        """Build conversation context from message history"""
        context_parts = []
        
        for msg in messages[-10:]:  # Last 10 messages for context
            role_label = "You" if msg.role == MessageRole.ASSISTANT else "User"
            context_parts.append(f"{role_label}: {msg.content}")
        
        return "\n".join(context_parts)
    
    def _post_process_response(self, response: str, session_type: SessionType) -> str:
        """Post-process AI response to ensure quality"""
        # Remove any unwanted prefixes
        response = response.strip()
        
        # Remove common AI prefixes
        prefixes_to_remove = [
            "As a Reflection Buddy:",
            "As an Inner Voice Guide:",
            "As a Growth Coach:",
            "As a Pattern Detective:",
            "AI:",
            "Assistant:"
        ]
        
        for prefix in prefixes_to_remove:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()
        
        # Ensure response isn't too long
        if len(response) > 500:
            sentences = response.split('. ')
            response = '. '.join(sentences[:3]) + '.'
        
        return response
    
    def _get_fallback_response(self, session_type: SessionType) -> str:
        """Get fallback response when AI generation fails"""
        fallbacks = {
            SessionType.REFLECTION_BUDDY: "I'm here to listen. Can you tell me more about what you're experiencing?",
            SessionType.INNER_VOICE: "Let's pause and reflect. What feels most important to you right now?",
            SessionType.GROWTH_CHALLENGE: "That's interesting. What would growth look like in this situation?",
            SessionType.PATTERN_DETECTIVE: "I'm curious about the patterns here. What do you notice?"
        }
        
        return fallbacks.get(session_type, "I'm here to listen. What's on your mind?")
    
    async def _get_recent_journal_context(self) -> Optional[str]:
        """Get context from recent journal entries"""
        try:
            recent_entries = await db_service.get_entries(limit=3)
            if recent_entries:
                # Get themes from recent entries without being too specific
                themes = []
                for entry in recent_entries:
                    if len(entry.content) > 50:  # Only substantial entries
                        themes.append(entry.title or entry.content[:100])
                
                if themes:
                    return f"Recent themes: {', '.join(themes)}"
        except Exception as e:
            logger.error(f"Error getting journal context: {e}")
        
        return None
    
    async def _get_recent_mood_context(self) -> Optional[str]:
        """Get context from recent mood patterns"""
        try:
            mood_stats = await db_service.get_mood_statistics(7)  # Last week
            if mood_stats and mood_stats.get('mood_distribution'):
                # Find dominant mood
                moods = mood_stats['mood_distribution']
                if moods:
                    dominant_mood = max(moods.items(), key=lambda x: x[1])[0]
                    return f"Recent mood trend: {dominant_mood.replace('_', ' ')}"
        except Exception as e:
            logger.error(f"Error getting mood context: {e}")
        
        return None
    
    async def _generate_contextual_opening(self, session_type: SessionType, 
                                         recent_entries: Optional[str], 
                                         mood_context: Optional[str]) -> Optional[str]:
        """Generate contextual addition to opening message"""
        if not recent_entries and not mood_context:
            return None
        
        context_parts = []
        if recent_entries:
            context_parts.append(recent_entries)
        if mood_context:
            context_parts.append(mood_context)
        
        context_info = " | ".join(context_parts)
        
        if session_type == SessionType.PATTERN_DETECTIVE:
            return f"I noticed some interesting themes lately: {context_info}. Want to explore these patterns?"
        elif session_type == SessionType.REFLECTION_BUDDY:
            return f"I see you've been reflecting on some meaningful topics recently. How are you feeling about everything?"
        
        return None

# Global instance
conversation_service = ConversationService()