# AI Prompt Service - Dynamic Prompt Generation

"""
AI Prompt Service for Journaling AI
Replaces hardcoded prompts with dynamic AI-powered prompt generation
Integrates with Phase 2 cache patterns and AI Model Manager
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

# Phase 2 integration imports
from app.core.cache_patterns import CacheDomain, CachePatterns, CacheKeyBuilder
from app.services.cache_service import unified_cache_service
from app.services.ai_model_manager import ai_model_manager
from app.core.service_interfaces import ServiceRegistry

logger = logging.getLogger(__name__)

class PromptType(Enum):
    """Types of prompts that can be generated"""
    JOURNAL_ANALYSIS = "journal_analysis"
    EMOTION_RECOGNITION = "emotion_recognition"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    CRISIS_INTERVENTION = "crisis_intervention"
    THERAPY_SUGGESTION = "therapy_suggestion"
    PERSONAL_GROWTH = "personal_growth"
    TOPIC_GENERATION = "topic_generation"
    REFLECTION_GUIDANCE = "reflection_guidance"
    GOAL_SETTING = "goal_setting"
    MOOD_TRACKING = "mood_tracking"

class PromptContext(Enum):
    """Context in which prompts are used"""
    INITIAL_ASSESSMENT = "initial_assessment"
    ONGOING_THERAPY = "ongoing_therapy"
    CRISIS_SITUATION = "crisis_situation"
    SELF_REFLECTION = "self_reflection"
    GOAL_ACHIEVEMENT = "goal_achievement"
    EMOTIONAL_SUPPORT = "emotional_support"

@dataclass
class PromptRequest:
    """Request for dynamic prompt generation"""
    prompt_type: PromptType
    context: PromptContext
    user_profile: Optional[Dict[str, Any]] = None
    session_history: Optional[List[Dict[str, Any]]] = None
    specific_needs: Optional[List[str]] = None
    emotional_state: Optional[str] = None
    language: str = "en"
    tone: str = "supportive"
    length: str = "medium"  # short, medium, long

@dataclass 
class GeneratedPrompt:
    """Generated prompt with metadata"""
    text: str
    prompt_type: PromptType
    context: PromptContext
    confidence_score: float
    generation_method: str
    created_at: datetime
    metadata: Dict[str, Any]

class AIPromptService:
    """
    AI-powered Prompt Generation Service
    
    Replaces hardcoded prompts with intelligent, context-aware prompts that:
    - Adapt to individual user needs and psychological profiles
    - Consider session history and emotional state
    - Generate culturally appropriate and therapeutic content
    - Integrate with Phase 2 cache patterns for performance
    """
    
    def __init__(self):
        self.generation_strategies = self._initialize_generation_strategies()
        self.prompt_templates = self._initialize_base_templates()
        self.cultural_adaptations = self._initialize_cultural_adaptations()
        
        # Performance tracking
        self.generation_stats = {
            "total_generated": 0,
            "cache_hits": 0,
            "ai_generations": 0,
            "template_generations": 0
        }
        
        logger.info("🎯 AI Prompt Service initialized")

    def _initialize_generation_strategies(self) -> Dict[PromptType, str]:
        """Initialize AI generation strategies for each prompt type"""
        return {
            PromptType.JOURNAL_ANALYSIS: "zero_shot_guided",
            PromptType.EMOTION_RECOGNITION: "template_enhanced",
            PromptType.SENTIMENT_ANALYSIS: "context_aware",
            PromptType.CRISIS_INTERVENTION: "safety_first_generation",
            PromptType.THERAPY_SUGGESTION: "evidence_based_generation",
            PromptType.PERSONAL_GROWTH: "goal_oriented_generation",
            PromptType.TOPIC_GENERATION: "creative_generation",
            PromptType.REFLECTION_GUIDANCE: "socratic_generation",
            PromptType.GOAL_SETTING: "smart_framework_generation",
            PromptType.MOOD_TRACKING: "emotion_focused_generation"
        }

    def _initialize_base_templates(self) -> Dict[PromptType, Dict[str, str]]:
        """Initialize base templates for prompt generation"""
        return {
            PromptType.JOURNAL_ANALYSIS: {
                "structure": "Analyze the following journal entry for {focus_areas}. Consider {context_factors}.",
                "therapeutic_lens": "From a therapeutic perspective, examine {specific_aspects}.",
                "growth_oriented": "Identify growth opportunities and insights in {content_area}."
            },
            
            PromptType.EMOTION_RECOGNITION: {
                "empathetic": "Help identify the emotions expressed in this text with compassion and understanding.",
                "clinical": "Systematically analyze emotional indicators and patterns in the provided content.",
                "supportive": "Gently guide recognition of feelings and emotional experiences."
            },
            
            PromptType.CRISIS_INTERVENTION: {
                "immediate_safety": "Assess immediate safety concerns and provide appropriate support resources.",
                "de_escalation": "Use calming, supportive language to help reduce emotional intensity.",
                "resource_connection": "Connect with helpful resources and professional support options."
            },
            
            PromptType.THERAPY_SUGGESTION: {
                "cbt_approach": "Suggest cognitive-behavioral techniques based on identified thought patterns.",
                "mindfulness_based": "Recommend mindfulness and awareness practices for emotional regulation.",
                "solution_focused": "Focus on strengths and practical solutions for current challenges."
            },
            
            PromptType.PERSONAL_GROWTH: {
                "strength_based": "Identify personal strengths and opportunities for development.",
                "value_exploration": "Explore core values and alignment with life choices.",
                "goal_progression": "Map current progress toward personal and therapeutic goals."
            }
        }

    def _initialize_cultural_adaptations(self) -> Dict[str, Dict[str, Any]]:
        """Initialize cultural and linguistic adaptations"""
        return {
            "en": {
                "directness": "moderate",
                "emotional_expression": "encouraged",
                "therapeutic_terms": "accessible",
                "cultural_considerations": ["individualism", "self-advocacy"]
            },
            "es": {
                "directness": "gentle",
                "emotional_expression": "family-oriented",
                "therapeutic_terms": "culturally_sensitive",
                "cultural_considerations": ["family_context", "community_support"]
            },
            "de": {
                "directness": "structured",
                "emotional_expression": "methodical",
                "therapeutic_terms": "precise",
                "cultural_considerations": ["systematic_approach", "privacy"]
            },
            "fr": {
                "directness": "nuanced",
                "emotional_expression": "sophisticated",
                "therapeutic_terms": "philosophical",
                "cultural_considerations": ["intellectual_approach", "artistic_expression"]
            }
        }

    # ==================== MAIN PROMPT GENERATION ====================

    async def generate_prompt(self, request: PromptRequest) -> GeneratedPrompt:
        """
        Generate a dynamic, context-aware prompt
        
        Args:
            request: PromptRequest with context and requirements
            
        Returns:
            GeneratedPrompt with text and metadata
        """
        try:
            # Check cache first using Phase 2 patterns
            cache_key = self._build_prompt_cache_key(request)
            cached_prompt = await unified_cache_service.get_ai_model_instance(cache_key)
            
            if cached_prompt:
                self.generation_stats["cache_hits"] += 1
                logger.debug(f"🗃️ Using cached prompt for {request.prompt_type.value}")
                return cached_prompt
            
            # Generate new prompt
            generated_prompt = await self._generate_new_prompt(request)
            
            if generated_prompt:
                # Cache the generated prompt
                await unified_cache_service.set_ai_model_instance(
                    generated_prompt, cache_key, ttl=7200  # 2 hours
                )
                
                self.generation_stats["total_generated"] += 1
                logger.info(f"✨ Generated new prompt for {request.prompt_type.value}")
                
            return generated_prompt
            
        except Exception as e:
            logger.error(f"❌ Error generating prompt: {e}")
            return await self._fallback_prompt_generation(request)

    async def _generate_new_prompt(self, request: PromptRequest) -> GeneratedPrompt:
        """Generate a new prompt using AI or template-based methods"""
        strategy = self.generation_strategies.get(request.prompt_type, "template_enhanced")
        
        if strategy in ["zero_shot_guided", "context_aware", "creative_generation"]:
            return await self._ai_powered_generation(request, strategy)
        else:
            return await self._template_based_generation(request, strategy)

    # ==================== AI-POWERED GENERATION ====================

    async def _ai_powered_generation(self, request: PromptRequest, strategy: str) -> GeneratedPrompt:
        """Generate prompts using AI models"""
        try:
            # Get appropriate AI model
            model = await ai_model_manager.get_model("text_generator")
            
            if not model:
                logger.warning("📝 AI model unavailable, falling back to template generation")
                return await self._template_based_generation(request, "template_enhanced")
            
            # Build generation prompt
            generation_prompt = self._build_generation_prompt(request, strategy)
            
            # Generate with AI
            result = model(generation_prompt, max_length=512, num_return_sequences=1)
            generated_text = result[0]["generated_text"] if result else ""
            
            # Clean and validate generated text
            cleaned_text = self._clean_generated_text(generated_text, generation_prompt)
            
            if not cleaned_text:
                raise ValueError("Generated text is empty or invalid")
            
            self.generation_stats["ai_generations"] += 1
            
            return GeneratedPrompt(
                text=cleaned_text,
                prompt_type=request.prompt_type,
                context=request.context,
                confidence_score=0.85,
                generation_method=f"ai_{strategy}",
                created_at=datetime.utcnow(),
                metadata={
                    "model_used": "text_generator",
                    "strategy": strategy,
                    "language": request.language,
                    "user_context": bool(request.user_profile)
                }
            )
            
        except Exception as e:
            logger.error(f"❌ AI generation failed: {e}")
            return await self._template_based_generation(request, "template_enhanced")

    def _build_generation_prompt(self, request: PromptRequest, strategy: str) -> str:
        """Build prompt for AI text generation"""
        base_instruction = f"""
        Generate a therapeutic prompt for {request.prompt_type.value} in {request.context.value} context.
        
        Requirements:
        - Tone: {request.tone}
        - Length: {request.length}
        - Language: {request.language}
        """
        
        # Add user context if available
        if request.user_profile:
            base_instruction += f"\n- User context: {self._summarize_user_context(request.user_profile)}"
        
        if request.emotional_state:
            base_instruction += f"\n- Current emotional state: {request.emotional_state}"
        
        if request.specific_needs:
            base_instruction += f"\n- Specific focus areas: {', '.join(request.specific_needs)}"
        
        # Add strategy-specific instructions
        strategy_instructions = {
            "zero_shot_guided": "Use a structured, evidence-based therapeutic approach.",
            "context_aware": "Adapt the prompt to the specific user context and emotional state.",
            "creative_generation": "Be creative while maintaining therapeutic appropriateness."
        }
        
        base_instruction += f"\n\nApproach: {strategy_instructions.get(strategy, '')}"
        base_instruction += "\n\nGenerate only the therapeutic prompt text, without additional commentary:"
        
        return base_instruction

    def _clean_generated_text(self, generated_text: str, original_prompt: str) -> str:
        """Clean and validate AI-generated prompt text"""
        if not generated_text:
            return ""
        
        # Remove the original prompt from generated text
        if original_prompt in generated_text:
            generated_text = generated_text.replace(original_prompt, "").strip()
        
        # Clean up common AI generation artifacts
        lines = generated_text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('Generate', 'Note:', 'Remember:', 'Important:')):
                cleaned_lines.append(line)
        
        cleaned_text = '\n'.join(cleaned_lines).strip()
        
        # Validate minimum length and content
        if len(cleaned_text) < 20:
            return ""
        
        return cleaned_text

    # ==================== TEMPLATE-BASED GENERATION ====================

    async def _template_based_generation(self, request: PromptRequest, strategy: str) -> GeneratedPrompt:
        """Generate prompts using intelligent templates"""
        try:
            # Get base template
            templates = self.prompt_templates.get(request.prompt_type, {})
            
            if not templates:
                return await self._fallback_prompt_generation(request)
            
            # Select appropriate template variant
            template_key = self._select_template_variant(request, templates, strategy)
            base_template = templates.get(template_key, list(templates.values())[0])
            
            # Enhance template with context
            enhanced_prompt = await self._enhance_template_with_context(
                base_template, request, strategy
            )
            
            self.generation_stats["template_generations"] += 1
            
            return GeneratedPrompt(
                text=enhanced_prompt,
                prompt_type=request.prompt_type,
                context=request.context,
                confidence_score=0.75,
                generation_method=f"template_{strategy}",
                created_at=datetime.utcnow(),
                metadata={
                    "template_key": template_key,
                    "strategy": strategy,
                    "language": request.language,
                    "enhanced": True
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Template generation failed: {e}")
            return await self._fallback_prompt_generation(request)

    def _select_template_variant(self, request: PromptRequest, templates: Dict[str, str], 
                                strategy: str) -> str:
        """Select the most appropriate template variant"""
        # Strategy-based selection
        strategy_preferences = {
            "safety_first_generation": ["immediate_safety", "de_escalation"],
            "evidence_based_generation": ["clinical", "cbt_approach", "systematic"],
            "goal_oriented_generation": ["goal_progression", "strength_based"],
            "socratic_generation": ["empathetic", "supportive"],
            "emotion_focused_generation": ["empathetic", "mindfulness_based"]
        }
        
        preferred_keys = strategy_preferences.get(strategy, [])
        
        # Find best match
        for key in preferred_keys:
            if key in templates:
                return key
        
        # Context-based fallback
        context_preferences = {
            PromptContext.CRISIS_SITUATION: ["immediate_safety", "de_escalation"],
            PromptContext.ONGOING_THERAPY: ["therapeutic_lens", "cbt_approach"],
            PromptContext.SELF_REFLECTION: ["empathetic", "supportive"],
            PromptContext.EMOTIONAL_SUPPORT: ["supportive", "empathetic"]
        }
        
        context_keys = context_preferences.get(request.context, [])
        for key in context_keys:
            if key in templates:
                return key
        
        # Default to first available template
        return list(templates.keys())[0]

    async def _enhance_template_with_context(self, base_template: str, 
                                           request: PromptRequest, strategy: str) -> str:
        """Enhance base template with user context and personalization"""
        enhanced = base_template
        
        # Apply cultural adaptations
        cultural_context = self.cultural_adaptations.get(request.language, {})
        if cultural_context:
            enhanced = self._apply_cultural_adaptations(enhanced, cultural_context)
        
        # Add user-specific context
        if request.user_profile:
            enhanced = self._personalize_template(enhanced, request.user_profile)
        
        # Apply emotional state considerations
        if request.emotional_state:
            enhanced = self._adapt_for_emotional_state(enhanced, request.emotional_state)
        
        # Add specific focus areas
        if request.specific_needs:
            enhanced = self._incorporate_specific_needs(enhanced, request.specific_needs)
        
        # Apply tone and length adjustments
        enhanced = self._adjust_tone_and_length(enhanced, request.tone, request.length)
        
        return enhanced

    def _apply_cultural_adaptations(self, text: str, cultural_context: Dict[str, Any]) -> str:
        """Apply cultural adaptations to prompt text"""
        directness = cultural_context.get("directness", "moderate")
        
        if directness == "gentle":
            text = text.replace("Analyze", "Gently explore")
            text = text.replace("Identify", "Notice")
            text = text.replace("Examine", "Reflect on")
        elif directness == "structured":
            text = text.replace("explore", "systematically examine")
            text = text.replace("consider", "analyze")
        
        return text

    def _personalize_template(self, text: str, user_profile: Dict[str, Any]) -> str:
        """Personalize template based on user profile"""
        # Add personalization based on user preferences, history, etc.
        preferences = user_profile.get("therapy_preferences", {})
        
        if preferences.get("approach") == "cognitive_behavioral":
            text += " Focus on thought patterns and behavioral connections."
        elif preferences.get("approach") == "mindfulness_based":
            text += " Include mindfulness and present-moment awareness."
        
        return text

    def _adapt_for_emotional_state(self, text: str, emotional_state: str) -> str:
        """Adapt prompt based on current emotional state"""
        state_adaptations = {
            "anxious": " Use calming, reassuring language.",
            "depressed": " Focus on small, achievable steps and validation.",
            "angry": " Acknowledge feelings while promoting healthy expression.",
            "confused": " Provide clear structure and gentle guidance.",
            "overwhelmed": " Break down into manageable components."
        }
        
        adaptation = state_adaptations.get(emotional_state.lower(), "")
        return text + adaptation

    def _incorporate_specific_needs(self, text: str, specific_needs: List[str]) -> str:
        """Incorporate specific focus areas into the prompt"""
        if specific_needs:
            needs_text = f" Pay special attention to: {', '.join(specific_needs)}."
            return text + needs_text
        return text

    def _adjust_tone_and_length(self, text: str, tone: str, length: str) -> str:
        """Adjust prompt tone and length"""
        # Tone adjustments
        if tone == "formal":
            text = text.replace("you", "the individual")
        elif tone == "casual":
            text = text.replace("examine", "take a look at")
            text = text.replace("analyze", "think about")
        
        # Length adjustments
        if length == "short":
            # Keep it concise
            sentences = text.split('. ')
            text = '. '.join(sentences[:2]) + '.'
        elif length == "long":
            # Add more detailed guidance
            text += " Consider multiple perspectives and take your time with this reflection."
        
        return text

    # ==================== FALLBACK AND UTILITIES ====================

    async def _fallback_prompt_generation(self, request: PromptRequest) -> GeneratedPrompt:
        """Generate a basic fallback prompt when other methods fail"""
        fallback_prompts = {
            PromptType.JOURNAL_ANALYSIS: "Please reflect on your journal entry and consider what emotions and thoughts are present.",
            PromptType.EMOTION_RECOGNITION: "Take a moment to identify the feelings expressed in your writing.",
            PromptType.SENTIMENT_ANALYSIS: "Consider the overall emotional tone of your thoughts.",
            PromptType.CRISIS_INTERVENTION: "If you're experiencing distress, please consider reaching out for support.",
            PromptType.THERAPY_SUGGESTION: "Reflect on helpful strategies that might support your well-being.",
            PromptType.PERSONAL_GROWTH: "Consider what this experience teaches you about yourself.",
            PromptType.TOPIC_GENERATION: "What would you like to explore in your journaling today?",
            PromptType.REFLECTION_GUIDANCE: "Take some time to think deeply about your experiences.",
            PromptType.GOAL_SETTING: "What small step could you take toward your goals?",
            PromptType.MOOD_TRACKING: "How are you feeling right now, and what might be influencing your mood?"
        }
        
        fallback_text = fallback_prompts.get(
            request.prompt_type,
            "Take a moment to reflect on your thoughts and feelings."
        )
        
        return GeneratedPrompt(
            text=fallback_text,
            prompt_type=request.prompt_type,
            context=request.context,
            confidence_score=0.5,
            generation_method="fallback",
            created_at=datetime.utcnow(),
            metadata={"fallback": True, "language": request.language}
        )

    def _build_prompt_cache_key(self, request: PromptRequest) -> str:
        """Build cache key for prompt requests"""
        # Create hash of key request parameters
        key_data = {
            "type": request.prompt_type.value,
            "context": request.context.value,
            "language": request.language,
            "tone": request.tone,
            "length": request.length,
            "needs": sorted(request.specific_needs) if request.specific_needs else []
        }
        
        # Add user profile hash if available (for personalization)
        if request.user_profile:
            user_hash = hash(str(sorted(request.user_profile.items())))
            key_data["user_hash"] = user_hash
        
        return CachePatterns.ai_model_instance(
            f"prompt_{hash(str(sorted(key_data.items())))}", "latest"
        )

    def _summarize_user_context(self, user_profile: Dict[str, Any]) -> str:
        """Summarize user context for AI generation"""
        summary_parts = []
        
        if "therapy_goals" in user_profile:
            summary_parts.append(f"Goals: {', '.join(user_profile['therapy_goals'])}")
        
        if "preferences" in user_profile:
            prefs = user_profile["preferences"]
            if "communication_style" in prefs:
                summary_parts.append(f"Communication: {prefs['communication_style']}")
        
        if "emotional_patterns" in user_profile:
            patterns = user_profile["emotional_patterns"]
            if "common_triggers" in patterns:
                summary_parts.append(f"Triggers: {', '.join(patterns['common_triggers'][:3])}")
        
        return "; ".join(summary_parts)

    # ==================== BATCH OPERATIONS ====================

    async def generate_prompt_batch(self, requests: List[PromptRequest]) -> List[GeneratedPrompt]:
        """Generate multiple prompts efficiently"""
        logger.info(f"🔄 Generating batch of {len(requests)} prompts")
        
        # Process in parallel for better performance
        tasks = [self.generate_prompt(request) for request in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        successful_prompts = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Batch generation failed for request {i}: {result}")
                # Generate fallback
                fallback = await self._fallback_prompt_generation(requests[i])
                successful_prompts.append(fallback)
            else:
                successful_prompts.append(result)
        
        return successful_prompts

    # ==================== MONITORING AND STATISTICS ====================

    def get_generation_stats(self) -> Dict[str, Any]:
        """Get prompt generation statistics"""
        total = self.generation_stats["total_generated"]
        return {
            "total_generated": total,
            "cache_hit_rate": (self.generation_stats["cache_hits"] / max(total, 1)) * 100,
            "ai_generation_rate": (self.generation_stats["ai_generations"] / max(total, 1)) * 100,
            "template_generation_rate": (self.generation_stats["template_generations"] / max(total, 1)) * 100,
            "average_confidence": 0.75  # Placeholder - would track actual confidence scores
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on prompt generation system"""
        health = {
            "status": "healthy",
            "ai_model_available": False,
            "template_system_ready": True,
            "cache_operational": False,
            "generation_stats": self.get_generation_stats()
        }
        
        try:
            # Check AI model availability
            model = await ai_model_manager.get_model("text_generator")
            health["ai_model_available"] = model is not None
            
            # Check cache system
            test_key = "health_check_prompt"
            await unified_cache_service.set_ai_model_instance("test", test_key, ttl=60)
            cached_value = await unified_cache_service.get_ai_model_instance(test_key)
            health["cache_operational"] = cached_value is not None
            
        except Exception as e:
            health["status"] = "degraded"
            health["error"] = str(e)
        
        return health

# ==================== SERVICE INSTANCE ====================

# Global AI Prompt Service instance
ai_prompt_service = AIPromptService()

# Integration with Phase 2 Service Registry
def register_ai_prompt_service():
    """Register AI Prompt Service in Phase 2 service registry"""
    try:
        from app.core.service_interfaces import service_registry
        service_registry.register_service("ai_prompt_service", ai_prompt_service)
        logger.info("✅ AI Prompt Service registered in service registry")
    except Exception as e:
        logger.error(f"❌ Failed to register AI Prompt Service: {e}")

# Auto-register when module is imported
register_ai_prompt_service()
