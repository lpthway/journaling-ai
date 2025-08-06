# backend/app/services/conversation_service.py - Simple conversation service using existing LLM service

from typing import List, Dict, Any, Optional
import logging
from app.services.llm_service import llm_service
from app.models.session import SessionType, MessageRole

logger = logging.getLogger(__name__)

class ConversationService:
    """
    Simple conversation service that wraps the existing LLM service
    to provide conversation-specific functionality for chat sessions.
    """
    
    async def generate_opening_message(self, session_type: SessionType, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate an opening message for a new conversation session"""
        try:
            session_type_prompts = {
                SessionType.COACHING: "Hello! I'm here to help you with personal growth and coaching. What would you like to explore today?",
                SessionType.THERAPY: "Hi there. I'm here to provide a supportive space for you to talk through whatever is on your mind. How are you feeling today?",
                SessionType.MENTORSHIP: "Welcome! I'm excited to help guide you on your journey. What area would you like to focus on or learn about?",
                SessionType.CASUAL: "Hey! I'm here for a friendly chat. What's on your mind today?",
                SessionType.REFLECTION: "Hi! I'm here to help you reflect on your thoughts and experiences. What would you like to think through together?",
                SessionType.GOAL_SETTING: "Hello! I'm here to help you set and work towards your goals. What would you like to achieve?",
                SessionType.CREATIVE: "Hi there! I'm here to explore creative ideas with you. What are you curious about or want to create?",
            }
            
            base_message = session_type_prompts.get(
                session_type, 
                "Hello! I'm here to help. What would you like to talk about today?"
            )
            
            # If context is provided, we could customize further
            if context and context.get('user_name'):
                base_message = f"Hello {context['user_name']}! " + base_message.split('Hello! ', 1)[1]
            
            return base_message
            
        except Exception as e:
            logger.error(f"Error generating opening message: {e}")
            return "Hello! I'm here to help. What would you like to talk about today?"
    
    async def generate_response(
        self, 
        user_message: str, 
        session_type: SessionType,
        conversation_history: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate an AI response based on user message and conversation context"""
        try:
            # Build context for LLM
            session_context = self._build_session_context(session_type, conversation_history, context)
            
            # Create a comprehensive prompt with context
            context_text = f"""
Session Type: {session_type.value}
Recent conversation context: {len(conversation_history)} messages exchanged

Previous messages:
""" + "\n".join([
                f"- {msg.get('role', 'unknown')}: {msg.get('content', '')[:100]}..."
                for msg in conversation_history[-3:] if conversation_history
            ])
            
            # Use existing LLM service
            response = await llm_service.generate_response(
                prompt=user_message,
                context=context_text
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating conversation response: {e}")
            return "I apologize, but I'm having trouble processing your message right now. Could you please try again?"
    
    async def suggest_follow_up_questions(
        self, 
        conversation_history: List[Dict[str, Any]], 
        session_type: SessionType
    ) -> List[str]:
        """Generate follow-up question suggestions based on conversation"""
        try:
            # Extract recent conversation for context
            recent_messages = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
            
            if not recent_messages:
                return self._get_default_follow_ups(session_type)
            
            # Build conversation summary
            conversation_text = "\n".join([
                f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
                for msg in recent_messages
            ])
            
            # Create prompt for generating follow-up questions
            prompt = f"""
Based on this {session_type.value} conversation, suggest 3 thoughtful follow-up questions:

{conversation_text}

Generate exactly 3 follow-up questions that would help continue this conversation meaningfully.
Format as a simple list, one question per line.
"""
            
            # Generate contextual follow-ups using LLM
            response = await llm_service.generate_response(prompt)
            
            # Parse response into list
            suggestions = [
                line.strip().lstrip('- ').lstrip('1. ').lstrip('2. ').lstrip('3. ')
                for line in response.split('\n') 
                if line.strip() and '?' in line
            ]
            
            # Fallback to defaults if LLM fails or gives poor results
            if not suggestions or len(suggestions) < 2:
                return self._get_default_follow_ups(session_type)
            
            return suggestions[:3]  # Return top 3 suggestions
            
        except Exception as e:
            logger.error(f"Error generating follow-up questions: {e}")
            return self._get_default_follow_ups(session_type)
    
    def _build_session_context(
        self, 
        session_type: SessionType, 
        conversation_history: List[Dict[str, Any]], 
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build context dictionary for LLM service"""
        session_context = {
            "session_type": session_type.value,
            "conversation_length": len(conversation_history),
            "recent_messages": conversation_history[-5:] if len(conversation_history) > 5 else conversation_history,
        }
        
        if context:
            session_context.update(context)
        
        return session_context
    
    def _get_default_follow_ups(self, session_type: SessionType) -> List[str]:
        """Get default follow-up questions based on session type"""
        default_suggestions = {
            SessionType.COACHING: [
                "What specific goals would you like to work towards?",
                "How do you typically handle challenging situations?",
                "What strengths do you feel you bring to this area?"
            ],
            SessionType.THERAPY: [
                "How are you feeling about what we've discussed?",
                "Is there anything else on your mind you'd like to explore?",
                "What support do you feel you need right now?"
            ],
            SessionType.MENTORSHIP: [
                "What skills would you like to develop further?",
                "Are there any specific challenges you're facing?",
                "What does success look like to you in this area?"
            ],
            SessionType.CASUAL: [
                "What's been the highlight of your day?",
                "Is there anything interesting you've been thinking about?",
                "How have you been spending your free time lately?"
            ],
            SessionType.REFLECTION: [
                "What insights have you gained from this reflection?",
                "How does this connect to your broader life experience?",
                "What would you like to explore more deeply?"
            ],
            SessionType.GOAL_SETTING: [
                "What steps could you take to move closer to this goal?",
                "What obstacles might you encounter, and how could you overcome them?",
                "How will you know when you've achieved what you're aiming for?"
            ],
            SessionType.CREATIVE: [
                "What creative ideas are you most excited about?",
                "How could you build on this concept further?",
                "What inspires your creative process?"
            ]
        }
        
        return default_suggestions.get(session_type, [
            "What would you like to explore next?",
            "How can I best support you?",
            "Is there anything else you'd like to discuss?"
        ])

# Create service instance
conversation_service = ConversationService()
