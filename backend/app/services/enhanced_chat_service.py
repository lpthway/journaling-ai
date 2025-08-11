# Enhanced AI Chat Service - Sophisticated Conversational AI

"""
Enhanced AI Chat Service for Journaling AI
Provides sophisticated conversational AI capabilities including:
- Context-aware dialogue management
- Therapeutic conversation patterns
- Personality-adapted responses
- Multi-turn conversation memory
- Crisis intervention integration
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# Core imports
from app.core.cache_patterns import CacheDomain, CachePatterns, CacheKeyBuilder
from app.services.cache_service import unified_cache_service
from app.services.ai_model_manager import ai_model_manager
from app.services.ai_emotion_service import ai_emotion_service
from app.services.ai_prompt_service import ai_prompt_service
from app.services.ai_intervention_service import ai_intervention_service
from app.services.advanced_ai_service import advanced_ai_service
from app.services.llm_service import llm_service
from app.core.service_interfaces import ServiceRegistry
from app.repositories.session_repository import SessionRepository
from app.models.enhanced_models import ChatSession
from app.core.database import get_db_session
from sqlalchemy import select

logger = logging.getLogger(__name__)

class ConversationMode(Enum):
    """Different conversation modes"""
    SUPPORTIVE_LISTENING = "supportive_listening"
    THERAPEUTIC_GUIDANCE = "therapeutic_guidance"
    COGNITIVE_REFRAMING = "cognitive_reframing"
    MINDFULNESS_COACHING = "mindfulness_coaching"
    GOAL_SETTING = "goal_setting"
    CRISIS_SUPPORT = "crisis_support"
    REFLECTION_FACILITATION = "reflection_facilitation"
    EMOTIONAL_PROCESSING = "emotional_processing"

class ResponseStyle(Enum):
    """AI response styles"""
    EMPATHETIC = "empathetic"
    ANALYTICAL = "analytical"
    ENCOURAGING = "encouraging"
    CHALLENGING = "challenging"
    REFLECTIVE = "reflective"
    PRACTICAL = "practical"
    CREATIVE = "creative"

class ConversationStage(Enum):
    """Stages of therapeutic conversation"""
    OPENING = "opening"
    EXPLORATION = "exploration"
    INSIGHT_BUILDING = "insight_building"
    ACTION_PLANNING = "action_planning"
    CLOSURE = "closure"
    FOLLOW_UP = "follow_up"

@dataclass
class ConversationContext:
    """Context for ongoing conversation"""
    session_id: str
    user_id: str
    conversation_mode: ConversationMode
    response_style: ResponseStyle
    current_stage: ConversationStage
    turn_count: int
    emotional_state: Dict[str, float]
    key_topics: List[str]
    therapeutic_goals: List[str]
    personality_profile: Optional[Dict[str, Any]]
    conversation_history: List[Dict[str, Any]]
    last_updated: datetime

@dataclass
class ChatMessage:
    """Individual chat message"""
    message_id: str
    session_id: str
    user_id: str
    content: str
    sender: str  # 'user' or 'assistant'
    timestamp: datetime
    emotion_analysis: Optional[Dict[str, Any]]
    intent_classification: Optional[str]
    response_metadata: Optional[Dict[str, Any]]

@dataclass
class EnhancedChatResponse:
    """Enhanced AI chat response with rich metadata"""
    message_id: str
    content: str
    response_style: ResponseStyle
    conversation_stage: ConversationStage
    therapeutic_techniques: List[str]
    follow_up_suggestions: List[str]
    emotional_support_level: float
    crisis_indicators: List[str]
    next_recommended_topics: List[str]
    confidence_score: float
    processing_metadata: Dict[str, Any]
    timestamp: datetime

class EnhancedChatService:
    """
    Enhanced AI Chat Service providing sophisticated conversational capabilities
    
    Features:
    - Context-aware dialogue management
    - Therapeutic conversation patterns
    - Personality-adapted responses
    - Multi-turn conversation memory
    - Crisis intervention integration
    - Advanced conversation analysis
    """
    
    def __init__(self):
        self.active_conversations = {}
        self.conversation_templates = self._initialize_conversation_templates()
        self.therapeutic_techniques = self._initialize_therapeutic_techniques()
        self.response_generators = self._initialize_response_generators()
        
        # Performance tracking
        self.chat_stats = {
            "total_conversations": 0,
            "messages_processed": 0,
            "crisis_interventions": 0,
            "therapeutic_insights": 0,
            "user_satisfaction_scores": []
        }
        
        logger.info("💬 Enhanced Chat Service initialized")

    def _initialize_conversation_templates(self) -> Dict[ConversationMode, Dict[str, Any]]:
        """Initialize conversation templates for different modes"""
        return {
            ConversationMode.SUPPORTIVE_LISTENING: {
                "opening": "I'm here to listen and support you. What's on your mind today?",
                "techniques": ["active_listening", "validation", "empathetic_reflection"],
                "response_patterns": [
                    "It sounds like you're feeling {emotion}. That must be {intensity} for you.",
                    "I hear that {situation} is really affecting you. Can you tell me more?",
                    "Thank you for sharing that with me. How are you coping with this?"
                ],
                "transition_cues": ["deeper_exploration", "emotional_validation", "coping_strategies"]
            },
            
            ConversationMode.THERAPEUTIC_GUIDANCE: {
                "opening": "Let's explore this together. What would be most helpful to focus on?",
                "techniques": ["socratic_questioning", "cognitive_restructuring", "behavioral_activation"],
                "response_patterns": [
                    "What evidence do we have for that thought? Let's examine it together.",
                    "How might we reframe this situation in a more balanced way?",
                    "What small steps could you take toward addressing this challenge?"
                ],
                "transition_cues": ["insight_building", "action_planning", "skill_building"]
            },
            
            ConversationMode.MINDFULNESS_COACHING: {
                "opening": "Let's take a moment to connect with the present. How are you feeling right now?",
                "techniques": ["mindfulness_meditation", "breathing_exercises", "body_awareness"],
                "response_patterns": [
                    "Notice what you're experiencing without judgment. What do you observe?",
                    "Let's focus on your breathing. Can you feel the rhythm of your breath?",
                    "What physical sensations are you aware of in this moment?"
                ],
                "transition_cues": ["present_moment_awareness", "acceptance", "grounding"]
            },
            
            ConversationMode.CRISIS_SUPPORT: {
                "opening": "I'm concerned about you. You're important, and I want to help. Are you safe right now?",
                "techniques": ["safety_assessment", "crisis_intervention", "resource_connection"],
                "response_patterns": [
                    "Your safety is the most important thing right now. Let's talk about getting you support.",
                    "These feelings are temporary, even though they feel overwhelming now.",
                    "There are people trained to help with exactly what you're experiencing."
                ],
                "transition_cues": ["safety_planning", "resource_connection", "professional_support"]
            }
        }

    def _initialize_therapeutic_techniques(self) -> Dict[str, Dict[str, Any]]:
        """Initialize therapeutic technique implementations"""
        return {
            "cognitive_restructuring": {
                "description": "Help identify and challenge negative thought patterns",
                "prompts": [
                    "What evidence supports this thought? What evidence contradicts it?",
                    "How might a good friend view this situation?",
                    "What would you tell someone else in this situation?"
                ],
                "indicators": ["negative_self_talk", "catastrophic_thinking", "all_or_nothing"]
            },
            
            "behavioral_activation": {
                "description": "Encourage engagement in meaningful activities",
                "prompts": [
                    "What activities used to bring you joy or satisfaction?",
                    "What's one small thing you could do today that might help?",
                    "How could you break this goal into smaller, manageable steps?"
                ],
                "indicators": ["withdrawal", "decreased_activity", "loss_of_interest"]
            },
            
            "mindfulness_grounding": {
                "description": "Bring attention to the present moment",
                "prompts": [
                    "Can you name 5 things you can see, 4 you can touch, 3 you can hear?",
                    "Let's take three deep breaths together. Focus on the sensation.",
                    "What's one thing you can appreciate about this moment?"
                ],
                "indicators": ["anxiety", "racing_thoughts", "dissociation"]
            },
            
            "validation": {
                "description": "Acknowledge and validate emotional experiences",
                "prompts": [
                    "Your feelings make complete sense given what you've experienced.",
                    "It's understandable that you'd feel this way.",
                    "Many people would struggle with something like this."
                ],
                "indicators": ["self_doubt", "emotional_invalidation", "isolation"]
            }
        }

    def _initialize_response_generators(self) -> Dict[ResponseStyle, Dict[str, Any]]:
        """Initialize response generation patterns for different styles"""
        return {
            ResponseStyle.EMPATHETIC: {
                "tone_markers": ["warm", "understanding", "gentle"],
                "language_patterns": ["I hear", "It sounds like", "That must be"],
                "emotional_validation": True,
                "directness_level": 0.3
            },
            
            ResponseStyle.ANALYTICAL: {
                "tone_markers": ["thoughtful", "structured", "logical"],
                "language_patterns": ["Let's examine", "Consider this", "What if we"],
                "emotional_validation": False,
                "directness_level": 0.8
            },
            
            ResponseStyle.ENCOURAGING: {
                "tone_markers": ["optimistic", "supportive", "energizing"],
                "language_patterns": ["You can", "I believe", "You've shown"],
                "emotional_validation": True,
                "directness_level": 0.6
            },
            
            ResponseStyle.REFLECTIVE: {
                "tone_markers": ["contemplative", "insightful", "curious"],
                "language_patterns": ["What do you think", "I wonder if", "It seems like"],
                "emotional_validation": True,
                "directness_level": 0.4
            }
        }

    # ==================== MAIN CHAT PROCESSING ====================

    async def process_chat_message(self, user_id: str, session_id: str, message: str, 
                                  conversation_mode: ConversationMode = ConversationMode.SUPPORTIVE_LISTENING,
                                  preferred_style: Optional[ResponseStyle] = None) -> EnhancedChatResponse:
        """
        Process a chat message and generate an enhanced AI response
        
        Args:
            user_id: User identifier
            session_id: Conversation session ID
            message: User message content
            conversation_mode: Desired conversation mode
            preferred_style: Preferred response style
            
        Returns:
            Enhanced chat response with rich metadata
        """
        try:
            start_time = datetime.utcnow()
            logger.info(f"💬 Processing chat message for user {user_id} in session {session_id}")
            
            # Get or create conversation context
            context = await self._get_conversation_context(user_id, session_id, conversation_mode)
            
            # Analyze user message
            message_analysis = await self._analyze_user_message(message, context)
            
            # Check for crisis indicators
            crisis_level = await self._assess_crisis_indicators(message, message_analysis, context)
            
            # Adapt conversation mode if needed
            if crisis_level > 0.7:
                conversation_mode = ConversationMode.CRISIS_SUPPORT
                context.conversation_mode = conversation_mode
            
            # Determine response style
            response_style = preferred_style or await self._determine_response_style(
                message_analysis, context
            )
            
            # Generate AI response
            ai_response = await self._generate_contextual_response(
                message, message_analysis, context, response_style
            )
            
            # Apply therapeutic techniques if appropriate
            enhanced_response = await self._apply_therapeutic_techniques(
                ai_response, message_analysis, context
            )
            
            # Generate follow-up suggestions
            follow_ups = await self._generate_follow_up_suggestions(
                message_analysis, context, response_style
            )
            
            # Update conversation context
            await self._update_conversation_context(
                context, message, enhanced_response, message_analysis
            )
            
            # Calculate confidence and metadata
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            confidence_score = await self._calculate_response_confidence(
                enhanced_response, message_analysis, context
            )
            
            # Build enhanced response
            response = EnhancedChatResponse(
                message_id=str(uuid.uuid4()),
                content=enhanced_response,
                response_style=response_style,
                conversation_stage=context.current_stage,
                therapeutic_techniques=self._identify_used_techniques(enhanced_response),
                follow_up_suggestions=follow_ups,
                emotional_support_level=self._calculate_emotional_support_level(enhanced_response),
                crisis_indicators=message_analysis.get("crisis_indicators", []),
                next_recommended_topics=self._suggest_next_topics(context),
                confidence_score=confidence_score,
                processing_metadata={
                    "processing_time_seconds": processing_time,
                    "conversation_turn": context.turn_count,
                    "mode_adapted": conversation_mode != context.conversation_mode,
                    "techniques_applied": len(self._identify_used_techniques(enhanced_response)),
                    "crisis_level_detected": crisis_level
                },
                timestamp=datetime.utcnow()
            )
            
            # Persist to database
            await self._persist_conversation_to_db(user_id, session_id, message, response, conversation_mode)
            
            # Update statistics
            self.chat_stats["messages_processed"] += 1
            if crisis_level > 0.7:
                self.chat_stats["crisis_interventions"] += 1
            
            logger.info(f"✅ Generated enhanced chat response (confidence: {confidence_score:.2f}, processing: {processing_time:.2f}s)")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error processing chat message: {e}")
            return await self._generate_fallback_response(user_id, session_id, message)

    async def _get_conversation_context(self, user_id: str, session_id: str, 
                                       mode: ConversationMode) -> ConversationContext:
        """Get or create conversation context"""
        try:
            cache_key = f"chat_context_{session_id}"
            cached_context = await unified_cache_service.get_ai_analysis_result(cache_key)
            
            if cached_context:
                # Ensure we have a proper ConversationContext object
                if isinstance(cached_context, ConversationContext):
                    return cached_context
                elif isinstance(cached_context, dict):
                    # Reconstruct from dict if needed
                    return ConversationContext(**cached_context)
                else:
                    logger.warning(f"⚠️ Invalid cached context type: {type(cached_context)}, creating new context")
                    # Continue to create new context
            
            # Get user personality profile for context adaptation
            personality_profile = None
            try:
                # Fetch recent user entries for personality analysis
                entries = await self._fetch_recent_entries(user_id, 50)
                if len(entries) >= 10:
                    personality = await advanced_ai_service.generate_personality_profile(user_id, entries)
                    personality_profile = {
                        "dimensions": {dim.name: score for dim, score in personality.dimensions.items()},
                        "traits": personality.traits,
                        "communication_style": personality.communication_style
                    }
            except Exception as e:
                logger.warning(f"⚠️ Could not load personality profile: {e}")
            
            # Create new context
            context = ConversationContext(
                session_id=session_id,
                user_id=user_id,
                conversation_mode=mode,
                response_style=ResponseStyle.EMPATHETIC,  # Default style
                current_stage=ConversationStage.OPENING,
                turn_count=0,
                emotional_state={"neutral": 1.0},
                key_topics=[],
                therapeutic_goals=[],
                personality_profile=personality_profile,
                conversation_history=[],
                last_updated=datetime.utcnow()
            )
            
            # Cache context
            await unified_cache_service.set_ai_analysis_result(context, cache_key, ttl=3600)  # 1 hour
            
            return context
            
        except Exception as e:
            logger.error(f"❌ Error getting conversation context: {e}")
            return self._create_fallback_context(user_id, session_id, mode)

    async def _analyze_user_message(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """Analyze user message for emotional content and intent"""
        try:
            # Emotion analysis
            emotion_analysis = await ai_emotion_service.analyze_emotions(message)
            
            # Intent classification (simplified implementation)
            intent = self._classify_message_intent(message, context)
            
            # Topic extraction
            topics = self._extract_message_topics(message)
            
            # Crisis indicators
            crisis_indicators = self._detect_crisis_language(message)
            
            # Therapeutic needs assessment
            therapeutic_needs = self._assess_therapeutic_needs(message, emotion_analysis)
            
            return {
                "emotion_analysis": {
                    "primary_emotion": emotion_analysis.primary_emotion.emotion,
                    "sentiment": emotion_analysis.sentiment_polarity,
                    "intensity": emotion_analysis.primary_emotion.score,
                    "patterns": emotion_analysis.detected_patterns
                },
                "intent": intent,
                "topics": topics,
                "crisis_indicators": crisis_indicators,
                "therapeutic_needs": therapeutic_needs,
                "message_length": len(message.split()),
                "emotional_complexity": emotion_analysis.emotional_complexity
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing user message: {e}")
            return {
                "emotion_analysis": {"primary_emotion": "neutral", "sentiment": 0.0, "intensity": 0.5},
                "intent": "unknown",
                "topics": [],
                "crisis_indicators": [],
                "therapeutic_needs": []
            }

    async def _generate_contextual_response(self, message: str, analysis: Dict[str, Any], 
                                          context: ConversationContext, 
                                          style: ResponseStyle) -> str:
        """Generate contextual AI response using LLM"""
        try:
            # Build context-aware prompt
            prompt = await self._build_contextual_prompt(message, analysis, context, style)
            
            # Generate response using LLM service
            response = await llm_service.generate_response(
                prompt=prompt,
                context=context.conversation_history[-3:] if context and context.conversation_history else None
            )
            
            # Post-process response for therapeutic appropriateness
            processed_response = self._post_process_response(response, analysis, context, style)
            
            return processed_response
            
        except Exception as e:
            logger.error(f"❌ Error generating contextual response: {e}")
            return self._generate_template_response(analysis, context, style)

    async def _build_contextual_prompt(self, message: str, analysis: Dict[str, Any], 
                                     context: ConversationContext, style: ResponseStyle) -> str:
        """Build context-aware prompt for LLM"""
        try:
            # Base therapeutic context
            base_prompt = f"""You are a compassionate AI therapeutic assistant. 

Current conversation context:
- Mode: {context.conversation_mode.value}
- Stage: {context.current_stage.value}
- Turn: {context.turn_count}
- User's primary emotion: {analysis['emotion_analysis']['primary_emotion']}
- Response style requested: {style.value}

Conversation history (last 3 exchanges):
{self._format_conversation_history(context.conversation_history[-6:])}

User's current message: "{message}"

Therapeutic guidelines:
- Be empathetic and non-judgmental
- Use active listening techniques
- Adapt your response to the user's emotional state
- Provide support without giving medical advice
- If crisis indicators are present, prioritize safety and resources"""

            # Add personality adaptation if available
            if context.personality_profile:
                personality_info = context.personality_profile
                base_prompt += f"""

User personality insights:
- Communication style: {personality_info.get('communication_style', 'unknown')}
- Key traits: {', '.join(personality_info.get('traits', []))}
- Adapt your response to match their preferred communication style."""

            # Add conversation mode specific guidance
            mode_guidance = self.conversation_templates.get(context.conversation_mode, {})
            if mode_guidance:
                techniques = mode_guidance.get("techniques", [])
                base_prompt += f"""

Mode-specific techniques to consider: {', '.join(techniques)}
"""

            # Add crisis support if needed
            if analysis.get("crisis_indicators"):
                base_prompt += """

IMPORTANT: Crisis indicators detected. Prioritize:
1. Immediate safety assessment
2. Validation and support
3. Professional resource suggestions
4. Do not attempt therapy beyond your scope"""

            base_prompt += f"""

Generate a {style.value} response that:
1. Acknowledges their emotional state
2. Provides appropriate support
3. Uses therapeutic communication techniques
4. Maintains professional boundaries
5. Is conversational and natural (avoid being overly clinical)

Response:"""

            return base_prompt
            
        except Exception as e:
            logger.error(f"❌ Error building contextual prompt: {e}")
            return f"Please respond empathetically to: {message}"

    def _format_conversation_history(self, history: List[Dict[str, Any]]) -> str:
        """Format conversation history for prompt context"""
        if not history:
            return "No previous conversation."
        
        formatted = []
        for exchange in history[-3:]:  # Last 3 exchanges
            if exchange.get("sender") == "user":
                formatted.append(f"User: {exchange.get('content', '')}")
            else:
                formatted.append(f"Assistant: {exchange.get('content', '')}")
        
        return "\n".join(formatted)

    async def _apply_therapeutic_techniques(self, response: str, analysis: Dict[str, Any], 
                                          context: ConversationContext) -> str:
        """Apply therapeutic techniques to enhance response"""
        try:
            enhanced_response = response
            
            # Apply validation if emotional distress is detected
            if analysis["emotion_analysis"]["sentiment"] < -0.3:
                validation_phrase = self._generate_validation_phrase(analysis)
                enhanced_response = f"{validation_phrase} {enhanced_response}"
            
            # Apply cognitive restructuring prompts if negative thinking detected
            negative_patterns = ["always", "never", "terrible", "awful", "can't"]
            if any(pattern in response.lower() for pattern in negative_patterns):
                restructuring_prompt = self._generate_restructuring_prompt()
                enhanced_response += f" {restructuring_prompt}"
            
            # Add mindfulness elements if anxiety detected
            if "anxious" in analysis["emotion_analysis"]["primary_emotion"] or "worry" in response.lower():
                mindfulness_element = self._generate_mindfulness_prompt()
                enhanced_response += f" {mindfulness_element}"
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"❌ Error applying therapeutic techniques: {e}")
            return response

    async def _generate_follow_up_suggestions(self, analysis: Dict[str, Any], 
                                            context: ConversationContext, 
                                            style: ResponseStyle) -> List[str]:
        """Generate follow-up conversation suggestions"""
        try:
            suggestions = []
            
            # Emotion-based suggestions
            primary_emotion = analysis["emotion_analysis"]["primary_emotion"]
            if primary_emotion in ["sad", "depressed"]:
                suggestions.extend([
                    "Would you like to explore what might be contributing to these feelings?",
                    "Are there any activities that usually help lift your mood?",
                    "How has your self-care been lately?"
                ])
            elif primary_emotion in ["anxious", "worried"]:
                suggestions.extend([
                    "Would a grounding exercise be helpful right now?",
                    "What specific worries are weighing on your mind?",
                    "Have you tried any relaxation techniques?"
                ])
            elif primary_emotion in ["angry", "frustrated"]:
                suggestions.extend([
                    "What triggered these feelings for you?",
                    "How do you usually handle frustration?",
                    "Would it help to talk through what's bothering you?"
                ])
            
            # Context-based suggestions
            if context.current_stage == ConversationStage.EXPLORATION:
                suggestions.append("Is there a deeper layer to this that you'd like to explore?")
            elif context.current_stage == ConversationStage.INSIGHT_BUILDING:
                suggestions.append("What insights are emerging for you from this conversation?")
            
            # Crisis support suggestions
            if analysis.get("crisis_indicators"):
                suggestions.extend([
                    "Are you feeling safe right now?",
                    "Would it be helpful to talk about support resources?",
                    "How can I best support you in this moment?"
                ])
            
            return suggestions[:3]  # Limit to top 3 suggestions
            
        except Exception as e:
            logger.error(f"❌ Error generating follow-up suggestions: {e}")
            return ["How are you feeling about what we've discussed?"]

    # ==================== HELPER METHODS ====================

    def _classify_message_intent(self, message: str, context: ConversationContext) -> str:
        """Classify user message intent"""
        message_lower = message.lower()
        
        # Crisis-related intents
        if any(word in message_lower for word in ["hurt", "die", "kill", "end", "hopeless"]):
            return "crisis_support_needed"
        
        # Emotional expression intents
        if any(word in message_lower for word in ["feel", "feeling", "emotion", "mood"]):
            return "emotional_expression"
        
        # Problem-solving intents
        if any(word in message_lower for word in ["help", "problem", "issue", "struggle"]):
            return "problem_solving"
        
        # Reflection intents
        if any(word in message_lower for word in ["think", "realize", "understand", "insight"]):
            return "reflection_sharing"
        
        # Goal-oriented intents
        if any(word in message_lower for word in ["goal", "want", "plan", "change"]):
            return "goal_discussion"
        
        return "general_conversation"

    def _extract_message_topics(self, message: str) -> List[str]:
        """Extract key topics from user message"""
        # Simplified topic extraction
        topic_keywords = {
            "relationships": ["relationship", "partner", "friend", "family", "love"],
            "work": ["work", "job", "career", "boss", "colleague"],
            "health": ["health", "sick", "pain", "doctor", "medicine"],
            "emotions": ["emotion", "feeling", "mood", "happy", "sad", "angry"],
            "stress": ["stress", "pressure", "overwhelmed", "busy", "tired"],
            "growth": ["grow", "learn", "improve", "better", "progress"]
        }
        
        topics = []
        message_lower = message.lower()
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                topics.append(topic)
        
        return topics

    def _detect_crisis_language(self, message: str) -> List[str]:
        """Detect crisis indicators in message"""
        crisis_indicators = []
        message_lower = message.lower()
        
        # Suicidal ideation
        if any(word in message_lower for word in ["kill myself", "end it", "die", "suicide"]):
            crisis_indicators.append("suicidal_ideation")
        
        # Self-harm
        if any(word in message_lower for word in ["hurt myself", "cut", "harm", "punish myself"]):
            crisis_indicators.append("self_harm")
        
        # Hopelessness
        if any(word in message_lower for word in ["hopeless", "no point", "give up", "worthless"]):
            crisis_indicators.append("hopelessness")
        
        # Severe distress
        if any(word in message_lower for word in ["can't take it", "overwhelmed", "breaking down"]):
            crisis_indicators.append("severe_distress")
        
        return crisis_indicators

    def _assess_therapeutic_needs(self, message: str, emotion_analysis) -> List[str]:
        """Assess therapeutic needs from message"""
        needs = []
        
        # Emotional regulation needs
        if emotion_analysis.primary_emotion.score > 0.8:
            needs.append("emotional_regulation")
        
        # Cognitive restructuring needs
        negative_thinking = ["always", "never", "terrible", "awful", "hopeless"]
        if any(word in message.lower() for word in negative_thinking):
            needs.append("cognitive_restructuring")
        
        # Social support needs
        isolation_words = ["alone", "lonely", "no one", "isolated"]
        if any(word in message.lower() for word in isolation_words):
            needs.append("social_support")
        
        # Coping skills needs
        overwhelm_words = ["overwhelmed", "can't handle", "too much"]
        if any(word in message.lower() for word in overwhelm_words):
            needs.append("coping_skills")
        
        return needs

    async def _assess_crisis_indicators(self, message: str, analysis: Dict[str, Any], 
                                      context: ConversationContext) -> float:
        """Assess crisis level from 0 to 1"""
        crisis_score = 0.0
        
        # Crisis language indicators
        crisis_indicators = analysis.get("crisis_indicators", [])
        if "suicidal_ideation" in crisis_indicators:
            crisis_score += 0.8
        elif "self_harm" in crisis_indicators:
            crisis_score += 0.6
        elif "hopelessness" in crisis_indicators:
            crisis_score += 0.4
        
        # Emotional intensity
        emotion_analysis = analysis["emotion_analysis"]
        if emotion_analysis["primary_emotion"] in ["sadness", "despair"] and emotion_analysis["intensity"] > 0.8:
            crisis_score += 0.3
        
        # Rapid emotional deterioration (if we have conversation history)
        if context.conversation_history:
            recent_emotions = [exchange.get("emotion_analysis", {}).get("sentiment", 0) 
                             for exchange in context.conversation_history[-3:]]
            if len(recent_emotions) > 1:
                trend = recent_emotions[-1] - recent_emotions[0]
                if trend < -0.5:  # Significant negative trend
                    crisis_score += 0.2
        
        return min(crisis_score, 1.0)

    async def _determine_response_style(self, analysis: Dict[str, Any], 
                                       context: ConversationContext) -> ResponseStyle:
        """Determine appropriate response style"""
        # Crisis situations require empathetic style
        if analysis.get("crisis_indicators"):
            return ResponseStyle.EMPATHETIC
        
        # Adapt to personality if available
        if context.personality_profile:
            comm_style = context.personality_profile.get("communication_style", "")
            if comm_style == "analytical":
                return ResponseStyle.ANALYTICAL
            elif comm_style == "emotional":
                return ResponseStyle.EMPATHETIC
        
        # Adapt to emotional state
        emotion = analysis["emotion_analysis"]["primary_emotion"]
        if emotion in ["sad", "depressed", "anxious"]:
            return ResponseStyle.EMPATHETIC
        elif emotion in ["confused", "uncertain"]:
            return ResponseStyle.REFLECTIVE
        elif emotion in ["motivated", "excited"]:
            return ResponseStyle.ENCOURAGING
        
        return ResponseStyle.EMPATHETIC  # Default to empathetic

    def _post_process_response(self, response: str, analysis: Dict[str, Any], 
                              context: ConversationContext, style: ResponseStyle) -> str:
        """Post-process response for appropriateness"""
        # Remove potential harmful content
        harmful_phrases = ["you should", "you must", "just think positive", "get over it"]
        for phrase in harmful_phrases:
            if phrase in response.lower():
                response = response.replace(phrase, "you might consider")
        
        # Ensure empathetic tone for distressed users
        if analysis["emotion_analysis"]["sentiment"] < -0.5:
            if not any(empathetic in response.lower() for empathetic in ["understand", "hear", "validate"]):
                response = f"I understand this is difficult. {response}"
        
        # Add professional boundaries reminder if advice-giving detected
        advice_indicators = ["you should do", "the best thing to do", "you need to"]
        if any(indicator in response.lower() for indicator in advice_indicators):
            response += " Remember, these are just suggestions for you to consider."
        
        return response

    def _generate_template_response(self, analysis: Dict[str, Any], 
                                   context: ConversationContext, style: ResponseStyle) -> str:
        """Generate template response when LLM fails"""
        emotion = analysis["emotion_analysis"]["primary_emotion"]
        
        templates = {
            ResponseStyle.EMPATHETIC: {
                "sad": "I can hear that you're going through a difficult time. Your feelings are completely valid.",
                "anxious": "It sounds like you're feeling anxious right now. That can be really overwhelming.",
                "angry": "I can sense your frustration. It's understandable to feel this way.",
                "default": "Thank you for sharing that with me. I'm here to listen and support you."
            },
            ResponseStyle.REFLECTIVE: {
                "default": "That's interesting to explore. What do you think might be behind these feelings?"
            },
            ResponseStyle.ENCOURAGING: {
                "default": "It takes courage to share these thoughts. You're taking an important step."
            }
        }
        
        style_templates = templates.get(style, templates[ResponseStyle.EMPATHETIC])
        return style_templates.get(emotion, style_templates["default"])

    def _generate_validation_phrase(self, analysis: Dict[str, Any]) -> str:
        """Generate validation phrase based on emotional state"""
        emotion = analysis["emotion_analysis"]["primary_emotion"]
        intensity = analysis["emotion_analysis"]["intensity"]
        
        if intensity > 0.7:
            return f"I can really hear how {emotion} you're feeling right now."
        else:
            return f"It makes sense that you'd be feeling {emotion} about this."

    def _generate_restructuring_prompt(self) -> str:
        """Generate cognitive restructuring prompt"""
        prompts = [
            "I wonder if there might be another way to look at this situation?",
            "What evidence do we have for and against that thought?",
            "How might a good friend view this differently?"
        ]
        import random
        return random.choice(prompts)

    def _generate_mindfulness_prompt(self) -> str:
        """Generate mindfulness grounding prompt"""
        prompts = [
            "Would it be helpful to take a moment to focus on your breathing?",
            "Can you notice what you're feeling in your body right now?",
            "Let's take a pause and connect with the present moment."
        ]
        import random
        return random.choice(prompts)

    async def _update_conversation_context(self, context: ConversationContext, 
                                         user_message: str, ai_response: str, 
                                         analysis: Dict[str, Any]):
        """Update conversation context with new exchange"""
        try:
            # Add to conversation history
            context.conversation_history.extend([
                {
                    "sender": "user",
                    "content": user_message,
                    "timestamp": datetime.utcnow(),
                    "emotion_analysis": analysis["emotion_analysis"]
                },
                {
                    "sender": "assistant", 
                    "content": ai_response,
                    "timestamp": datetime.utcnow()
                }
            ])
            
            # Keep only last 10 exchanges
            context.conversation_history = context.conversation_history[-10:]
            
            # Update emotional state
            context.emotional_state = {
                analysis["emotion_analysis"]["primary_emotion"]: analysis["emotion_analysis"]["intensity"]
            }
            
            # Update topics
            new_topics = analysis.get("topics", [])
            for topic in new_topics:
                if topic not in context.key_topics:
                    context.key_topics.append(topic)
            
            # Progress conversation stage
            context.turn_count += 1
            if context.turn_count > 5 and context.current_stage == ConversationStage.OPENING:
                context.current_stage = ConversationStage.EXPLORATION
            elif context.turn_count > 10 and context.current_stage == ConversationStage.EXPLORATION:
                context.current_stage = ConversationStage.INSIGHT_BUILDING
            
            # Update timestamp
            context.last_updated = datetime.utcnow()
            
            # Save to cache
            cache_key = f"chat_context_{context.session_id}"
            await unified_cache_service.set_ai_analysis_result(context, cache_key, ttl=3600)
            
        except Exception as e:
            logger.error(f"❌ Error updating conversation context: {e}")

    def _identify_used_techniques(self, response: str) -> List[str]:
        """Identify therapeutic techniques used in response"""
        techniques = []
        response_lower = response.lower()
        
        if any(word in response_lower for word in ["understand", "hear", "validate"]):
            techniques.append("validation")
        
        if any(word in response_lower for word in ["what do you think", "how do you see", "wonder"]):
            techniques.append("socratic_questioning")
        
        if any(word in response_lower for word in ["breathe", "notice", "present moment"]):
            techniques.append("mindfulness")
        
        if any(word in response_lower for word in ["evidence", "another way", "different perspective"]):
            techniques.append("cognitive_restructuring")
        
        return techniques

    def _calculate_emotional_support_level(self, response: str) -> float:
        """Calculate emotional support level of response"""
        support_indicators = ["understand", "here for you", "support", "care", "validate"]
        empathy_indicators = ["feel", "hear", "sense", "difficult", "overwhelming"]
        
        support_score = sum(1 for indicator in support_indicators if indicator in response.lower())
        empathy_score = sum(1 for indicator in empathy_indicators if indicator in response.lower())
        
        total_words = len(response.split())
        support_ratio = (support_score + empathy_score) / max(total_words, 1)
        
        return min(support_ratio * 10, 1.0)  # Scale to 0-1

    def _suggest_next_topics(self, context: ConversationContext) -> List[str]:
        """Suggest next conversation topics"""
        suggestions = []
        
        # Based on current emotional state
        primary_emotion = list(context.emotional_state.keys())[0] if context.emotional_state else "neutral"
        
        if primary_emotion in ["sad", "depressed"]:
            suggestions.extend(["self-care strategies", "support systems", "meaningful activities"])
        elif primary_emotion in ["anxious", "worried"]:
            suggestions.extend(["coping techniques", "stress management", "grounding exercises"])
        elif primary_emotion in ["angry", "frustrated"]:
            suggestions.extend(["communication skills", "boundary setting", "conflict resolution"])
        
        # Based on conversation stage
        if context.current_stage == ConversationStage.EXPLORATION:
            suggestions.append("deeper exploration of feelings")
        elif context.current_stage == ConversationStage.INSIGHT_BUILDING:
            suggestions.append("action planning")
        
        return suggestions[:3]

    async def _calculate_response_confidence(self, response: str, analysis: Dict[str, Any], 
                                           context: ConversationContext) -> float:
        """Calculate confidence score for response quality"""
        confidence_factors = []
        
        # Length appropriateness (not too short or too long)
        response_length = len(response.split())
        if 20 <= response_length <= 150:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.5)
        
        # Therapeutic technique usage
        techniques_used = self._identify_used_techniques(response)
        confidence_factors.append(min(len(techniques_used) * 0.3, 0.9))
        
        # Emotional appropriateness
        emotion = analysis["emotion_analysis"]["primary_emotion"]
        if emotion in ["sad", "anxious"] and any(word in response.lower() for word in ["understand", "support"]):
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.6)
        
        # Context continuity
        if context.turn_count > 3:  # Multi-turn conversation
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.6)
        
        return sum(confidence_factors) / len(confidence_factors)

    async def _fetch_recent_entries(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch recent user entries for context"""
        try:
            # This would fetch from the database
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"❌ Error fetching recent entries: {e}")
            return []

    def _create_fallback_context(self, user_id: str, session_id: str, mode: ConversationMode) -> ConversationContext:
        """Create fallback context when normal creation fails"""
        return ConversationContext(
            session_id=session_id,
            user_id=user_id,
            conversation_mode=mode,
            response_style=ResponseStyle.EMPATHETIC,
            current_stage=ConversationStage.OPENING,
            turn_count=0,
            emotional_state={"neutral": 1.0},
            key_topics=[],
            therapeutic_goals=[],
            personality_profile=None,
            conversation_history=[],
            last_updated=datetime.utcnow()
        )

    async def _generate_fallback_response(self, user_id: str, session_id: str, message: str) -> EnhancedChatResponse:
        """Generate fallback response when main processing fails"""
        return EnhancedChatResponse(
            message_id=str(uuid.uuid4()),
            content="I'm here to listen and support you. Can you tell me more about what's on your mind?",
            response_style=ResponseStyle.EMPATHETIC,
            conversation_stage=ConversationStage.OPENING,
            therapeutic_techniques=["active_listening"],
            follow_up_suggestions=["How are you feeling right now?"],
            emotional_support_level=0.7,
            crisis_indicators=[],
            next_recommended_topics=["current feelings"],
            confidence_score=0.3,
            processing_metadata={"fallback_response": True},
            timestamp=datetime.utcnow()
        )

    # ==================== CONVERSATION MANAGEMENT ====================

    async def start_new_conversation(self, user_id: str, mode: ConversationMode = ConversationMode.SUPPORTIVE_LISTENING) -> str:
        """Start a new conversation session"""
        try:
            session_id = str(uuid.uuid4())
            context = await self._get_conversation_context(user_id, session_id, mode)
            
            self.chat_stats["total_conversations"] += 1
            
            logger.info(f"💬 Started new conversation session {session_id} for user {user_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"❌ Error starting new conversation: {e}")
            raise

    async def end_conversation(self, session_id: str) -> Dict[str, Any]:
        """End conversation and generate summary"""
        try:
            cache_key = f"chat_context_{session_id}"
            context = await unified_cache_service.get_ai_analysis_result(cache_key)
            
            if not context:
                return {"status": "session_not_found"}
            
            # Generate conversation summary
            summary = {
                "session_id": session_id,
                "duration_turns": context.turn_count,
                "primary_topics": context.key_topics,
                "emotional_journey": self._summarize_emotional_journey(context),
                "therapeutic_techniques_used": self._summarize_techniques_used(context),
                "ended_at": datetime.utcnow()
            }
            
            # Clean up context
            await unified_cache_service.delete(cache_key)
            
            logger.info(f"💬 Ended conversation session {session_id}")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error ending conversation: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_user_conversations(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all conversations for a user"""
        try:
            # Query the database for chat sessions
            from app.core.database import database
            if not database.session_factory:
                logger.error("Database not initialized")
                return []
            
            async with database.session_factory() as db:
                session_repo = SessionRepository(db)
                sessions = await session_repo.get_user_sessions(user_id, limit=limit)
                
                conversations = []
                for session in sessions:
                    conversations.append({
                        "session_id": session.id,
                        "session_type": session.session_type,
                        "title": session.title or f"Chat Session {session.id[:8]}",
                        "status": session.status,
                        "message_count": session.message_count,
                        "started_at": session.created_at,
                        "last_activity": session.last_activity,
                        "recent_messages": []  # Could be populated from messages if needed
                    })
                
                logger.info(f"📜 Retrieved {len(conversations)} conversations for user {user_id}")
                return conversations
            
        except Exception as e:
            logger.error(f"❌ Error getting user conversations: {e}")
            return []
    
    async def _persist_conversation_to_db(self, user_id: str, session_id: str, user_message: str, 
                                         ai_response: EnhancedChatResponse, conversation_mode: ConversationMode):
        """Persist conversation to database"""
        try:
            from app.core.database import database
            if not database.session_factory:
                logger.error("Database not initialized")
                return
            
            async with database.session_factory() as db:
                session_repo = SessionRepository(db)
                
                # Check if session exists in database directly
                session_query = select(ChatSession).where(ChatSession.id == session_id)
                result = await db.execute(session_query)
                existing_session = result.scalar_one_or_none()
                
                if existing_session:
                    logger.info(f"📋 Found existing session: {session_id}")
                else:
                    logger.info(f"📝 Creating new session: {session_id}")
                    # Session doesn't exist, create it
                    session_type = self._map_conversation_mode_to_session_type(conversation_mode)
                    new_session = ChatSession(
                        id=session_id,
                        user_id=user_id,
                        session_type=session_type,
                        title=f"Chat Session {session_id[:8]}",
                        status='active',
                        message_count=0,
                        last_activity=datetime.utcnow()
                    )
                    db.add(new_session)
                    await db.flush()  # Ensure session is created before adding messages
                    logger.info(f"✅ Created new chat session: {session_id}")
                
                # Add user message
                await session_repo.add_message(
                    session_id=session_id,
                    content=user_message,
                    role='user'
                )
                
                # Add AI response
                await session_repo.add_message(
                    session_id=session_id,
                    content=ai_response.content,
                    role='assistant'
                )
                
                await db.commit()
                logger.info(f"💾 Persisted conversation to database: session {session_id}")
                
        except Exception as e:
            logger.error(f"❌ Error persisting conversation to database: {e}")
            # Rollback on error
            try:
                if 'db' in locals():
                    await db.rollback()
            except:
                pass
    
    def _map_conversation_mode_to_session_type(self, mode: ConversationMode) -> str:
        """Map conversation mode to session type"""
        mapping = {
            ConversationMode.SUPPORTIVE_LISTENING: "free_chat",
            ConversationMode.THERAPEUTIC_GUIDANCE: "reflection_buddy", 
            ConversationMode.COGNITIVE_REFRAMING: "pattern_detective",
            ConversationMode.MINDFULNESS_COACHING: "inner_voice",
            ConversationMode.GOAL_SETTING: "growth_challenge",
            ConversationMode.CRISIS_SUPPORT: "free_chat",
            ConversationMode.REFLECTION_FACILITATION: "reflection_buddy",
            ConversationMode.EMOTIONAL_PROCESSING: "reflection_buddy"
        }
        return mapping.get(mode, "free_chat")

    def _summarize_emotional_journey(self, context: ConversationContext) -> Dict[str, Any]:
        """Summarize the emotional journey of the conversation"""
        if not context.conversation_history:
            return {"journey": "No emotional data available"}
        
        emotions_over_time = []
        for exchange in context.conversation_history:
            if exchange.get("sender") == "user" and exchange.get("emotion_analysis"):
                emotions_over_time.append(exchange["emotion_analysis"]["primary_emotion"])
        
        return {
            "emotions_expressed": emotions_over_time,
            "dominant_emotion": max(set(emotions_over_time), key=emotions_over_time.count) if emotions_over_time else "neutral",
            "emotional_progression": "stable" if len(set(emotions_over_time)) <= 2 else "varied"
        }

    def _summarize_techniques_used(self, context: ConversationContext) -> List[str]:
        """Summarize therapeutic techniques used in conversation"""
        techniques = set()
        for exchange in context.conversation_history:
            if exchange.get("sender") == "assistant":
                content = exchange.get("content", "")
                techniques.update(self._identify_used_techniques(content))
        
        return list(techniques)

    # ==================== MONITORING AND HEALTH ====================

    def get_service_stats(self) -> Dict[str, Any]:
        """Get chat service statistics"""
        avg_satisfaction = sum(self.chat_stats["user_satisfaction_scores"]) / max(len(self.chat_stats["user_satisfaction_scores"]), 1)
        
        return {
            "total_conversations": self.chat_stats["total_conversations"],
            "messages_processed": self.chat_stats["messages_processed"],
            "crisis_interventions": self.chat_stats["crisis_interventions"],
            "therapeutic_insights": self.chat_stats["therapeutic_insights"],
            "average_user_satisfaction": avg_satisfaction,
            "active_conversations": len(self.active_conversations),
            "service_status": "operational"
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on enhanced chat service"""
        health = {
            "status": "healthy",
            "dependencies_available": True,
            "llm_service_available": False,
            "emotion_service_available": False,
            "cache_operational": False,
            "service_stats": self.get_service_stats()
        }
        
        try:
            # Check LLM service
            llm_health = await llm_service.health_check()
            health["llm_service_available"] = llm_health.get("status") == "healthy"
            
            # Check emotion service
            emotion_health = await ai_emotion_service.health_check()
            health["emotion_service_available"] = emotion_health.get("status") == "healthy"
            
            # Check cache
            test_key = "health_check_enhanced_chat"
            test_context = self._create_fallback_context("test_user", "test_session", ConversationMode.SUPPORTIVE_LISTENING)
            await unified_cache_service.set_ai_analysis_result(test_context, test_key, ttl=60)
            cached_context = await unified_cache_service.get_ai_analysis_result(test_key)
            health["cache_operational"] = cached_context is not None
            
            # Overall status
            if not health["llm_service_available"] or not health["emotion_service_available"]:
                health["status"] = "degraded"
            
        except Exception as e:
            health["status"] = "error"
            health["error"] = str(e)
        
        return health

# ==================== SERVICE INSTANCE ====================

# Global Enhanced Chat Service instance
enhanced_chat_service = EnhancedChatService()

# Integration with service registry
def register_enhanced_chat_service():
    """Register Enhanced Chat Service in service registry"""
    try:
        from app.core.service_interfaces import service_registry
        service_registry.register_service("enhanced_chat_service", enhanced_chat_service)
        logger.info("✅ Enhanced Chat Service registered in service registry")
    except Exception as e:
        logger.error(f"❌ Failed to register Enhanced Chat Service: {e}")

# Auto-register when module is imported
register_enhanced_chat_service()

# Export key classes and functions
__all__ = [
    'EnhancedChatService',
    'enhanced_chat_service',
    'ConversationMode',
    'ResponseStyle',
    'ConversationStage',
    'ConversationContext',
    'ChatMessage',
    'EnhancedChatResponse'
]