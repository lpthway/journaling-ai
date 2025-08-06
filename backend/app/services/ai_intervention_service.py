# AI Intervention Service - Intelligent Crisis Response

"""
AI Intervention Service for Journaling AI
Replaces hardcoded crisis intervention templates with intelligent, context-aware responses
Integrates with Phase 2 cache patterns and AI Model Manager
Provides evidence-based therapeutic interventions
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

# Phase 2 integration imports
from app.core.cache_patterns import CacheDomain, CachePatterns, CacheKeyBuilder
from app.services.cache_service import unified_cache_service
from app.services.ai_model_manager import ai_model_manager
from app.services.ai_emotion_service import ai_emotion_service, EmotionAnalysis
from app.services.ai_prompt_service import ai_prompt_service, PromptRequest, PromptType, PromptContext
from app.core.service_interfaces import ServiceRegistry

logger = logging.getLogger(__name__)

class CrisisLevel(Enum):
    """Crisis severity levels"""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class InterventionType(Enum):
    """Types of therapeutic interventions"""
    IMMEDIATE_SAFETY = "immediate_safety"
    CRISIS_STABILIZATION = "crisis_stabilization"
    EMOTIONAL_REGULATION = "emotional_regulation"
    COGNITIVE_RESTRUCTURING = "cognitive_restructuring"
    BEHAVIORAL_ACTIVATION = "behavioral_activation"
    MINDFULNESS_GROUNDING = "mindfulness_grounding"
    SOCIAL_CONNECTION = "social_connection"
    PROFESSIONAL_REFERRAL = "professional_referral"
    SELF_CARE_GUIDANCE = "self_care_guidance"
    COPING_STRATEGIES = "coping_strategies"

class TherapeuticApproach(Enum):
    """Evidence-based therapeutic approaches"""
    CBT = "cognitive_behavioral_therapy"
    DBT = "dialectical_behavior_therapy"
    ACT = "acceptance_commitment_therapy"
    MINDFULNESS = "mindfulness_based"
    SOLUTION_FOCUSED = "solution_focused"
    TRAUMA_INFORMED = "trauma_informed"
    PERSON_CENTERED = "person_centered"

@dataclass
class CrisisIndicator:
    """Individual crisis indicator with severity"""
    indicator: str
    severity: float
    confidence: float
    description: str
    immediate_risk: bool

@dataclass
class InterventionRecommendation:
    """Therapeutic intervention recommendation"""
    intervention_type: InterventionType
    therapeutic_approach: TherapeuticApproach
    priority: int
    description: str
    specific_techniques: List[str]
    estimated_duration: str
    prerequisites: List[str]
    contraindications: List[str]

@dataclass
class CrisisAssessment:
    """Comprehensive crisis assessment"""
    crisis_level: CrisisLevel
    risk_factors: List[CrisisIndicator]
    protective_factors: List[str]
    immediate_interventions: List[InterventionRecommendation]
    followup_interventions: List[InterventionRecommendation]
    safety_plan_needed: bool
    professional_referral_urgent: bool
    assessment_confidence: float
    assessment_metadata: Dict[str, Any]
    created_at: datetime

@dataclass
class PersonalizedIntervention:
    """Personalized intervention response"""
    intervention_text: str
    intervention_type: InterventionType
    therapeutic_approach: TherapeuticApproach
    personalization_factors: List[str]
    expected_outcomes: List[str]
    followup_suggestions: List[str]
    crisis_level: CrisisLevel
    confidence_score: float
    generation_metadata: Dict[str, Any]
    created_at: datetime

class AIInterventionService:
    """
    AI-powered Intervention Service
    
    Provides intelligent, evidence-based therapeutic interventions that:
    - Assess crisis levels and risk factors automatically
    - Generate personalized intervention responses
    - Adapt to individual user contexts and therapeutic needs
    - Integrate multiple evidence-based therapeutic approaches
    - Provide safety assessment and professional referral guidance
    """
    
    def __init__(self):
        self.crisis_indicators = self._initialize_crisis_indicators()
        self.intervention_templates = self._initialize_intervention_templates()
        self.therapeutic_techniques = self._initialize_therapeutic_techniques()
        self.safety_resources = self._initialize_safety_resources()
        
        # Performance tracking
        self.intervention_stats = {
            "total_assessments": 0,
            "crisis_detections": 0,
            "interventions_generated": 0,
            "safety_referrals": 0,
            "cache_hits": 0
        }
        
        logger.info("🆘 AI Intervention Service initialized")

    def _initialize_crisis_indicators(self) -> Dict[str, Dict[str, Any]]:
        """Initialize crisis detection indicators"""
        return {
            # High-risk indicators
            "suicidal_ideation": {
                "keywords": ["kill myself", "end it all", "not worth living", "better off dead", 
                           "suicide", "die", "hurt myself", "end my life"],
                "severity_base": 0.9,
                "immediate_risk": True,
                "description": "Expressions of suicidal thoughts or intent"
            },
            
            "self_harm": {
                "keywords": ["cut myself", "hurt myself", "self-harm", "cutting", "burning", 
                           "punish myself", "deserve pain"],
                "severity_base": 0.8,
                "immediate_risk": True,
                "description": "Expressions of self-injurious behavior"
            },
            
            "substance_crisis": {
                "keywords": ["overdose", "too many pills", "drinking too much", "can't stop drinking",
                           "using again", "relapse", "blackout drunk"],
                "severity_base": 0.8,
                "immediate_risk": True,
                "description": "Substance use crisis indicators"
            },
            
            # Moderate-risk indicators
            "severe_depression": {
                "keywords": ["hopeless", "worthless", "nothing matters", "can't go on", 
                           "empty inside", "numb", "no point"],
                "severity_base": 0.7,
                "immediate_risk": False,
                "description": "Severe depressive symptoms"
            },
            
            "panic_overwhelm": {
                "keywords": ["can't breathe", "panic attack", "losing control", "going crazy",
                           "heart racing", "can't calm down", "overwhelmed"],
                "severity_base": 0.6,
                "immediate_risk": False,
                "description": "Panic and overwhelming anxiety"
            },
            
            "social_isolation": {
                "keywords": ["no one cares", "all alone", "no friends", "isolated", 
                           "nobody understands", "cutting people off"],
                "severity_base": 0.5,
                "immediate_risk": False,
                "description": "Severe social isolation"
            },
            
            # Warning indicators
            "emotional_escalation": {
                "keywords": ["rage", "explosive", "losing it", "can't control", 
                           "violent thoughts", "want to hurt"],
                "severity_base": 0.7,
                "immediate_risk": True,
                "description": "Emotional dysregulation and potential violence"
            },
            
            "trauma_response": {
                "keywords": ["flashback", "triggered", "reliving", "can't escape memories",
                           "nightmare", "intrusive thoughts"],
                "severity_base": 0.6,
                "immediate_risk": False,
                "description": "Trauma response indicators"
            }
        }

    def _initialize_intervention_templates(self) -> Dict[InterventionType, Dict[str, Any]]:
        """Initialize intervention response templates"""
        return {
            InterventionType.IMMEDIATE_SAFETY: {
                "priority": 1,
                "approaches": [TherapeuticApproach.TRAUMA_INFORMED, TherapeuticApproach.PERSON_CENTERED],
                "base_template": "Your safety and well-being are the top priority right now.",
                "techniques": ["safety_planning", "crisis_hotline_connection", "immediate_environment_assessment"],
                "duration": "immediate",
                "followup_required": True
            },
            
            InterventionType.CRISIS_STABILIZATION: {
                "priority": 2,
                "approaches": [TherapeuticApproach.DBT, TherapeuticApproach.CBT],
                "base_template": "Let's work together to help you feel more stable and grounded.",
                "techniques": ["distress_tolerance", "emotion_regulation", "grounding_exercises"],
                "duration": "15-30 minutes",
                "followup_required": True
            },
            
            InterventionType.EMOTIONAL_REGULATION: {
                "priority": 3,
                "approaches": [TherapeuticApproach.DBT, TherapeuticApproach.MINDFULNESS],
                "base_template": "These intense emotions are temporary and manageable.",
                "techniques": ["breathing_exercises", "progressive_muscle_relaxation", "emotional_labeling"],
                "duration": "10-20 minutes",
                "followup_required": False
            },
            
            InterventionType.COGNITIVE_RESTRUCTURING: {
                "priority": 4,
                "approaches": [TherapeuticApproach.CBT, TherapeuticApproach.ACT],
                "base_template": "Let's examine these thoughts and consider alternative perspectives.",
                "techniques": ["thought_challenging", "cognitive_defusion", "perspective_taking"],
                "duration": "20-30 minutes",
                "followup_required": False
            },
            
            InterventionType.MINDFULNESS_GROUNDING: {
                "priority": 3,
                "approaches": [TherapeuticApproach.MINDFULNESS, TherapeuticApproach.ACT],
                "base_template": "Let's bring your attention to the present moment.",
                "techniques": ["5_4_3_2_1_grounding", "body_scan", "mindful_breathing"],
                "duration": "5-15 minutes",
                "followup_required": False
            },
            
            InterventionType.BEHAVIORAL_ACTIVATION: {
                "priority": 5,
                "approaches": [TherapeuticApproach.CBT, TherapeuticApproach.SOLUTION_FOCUSED],
                "base_template": "Small, manageable actions can help improve how you're feeling.",
                "techniques": ["activity_scheduling", "behavioral_experiments", "goal_setting"],
                "duration": "varies",
                "followup_required": True
            },
            
            InterventionType.SOCIAL_CONNECTION: {
                "priority": 4,
                "approaches": [TherapeuticApproach.PERSON_CENTERED, TherapeuticApproach.SOLUTION_FOCUSED],
                "base_template": "Connection with others can be a powerful source of support.",
                "techniques": ["support_network_mapping", "communication_skills", "social_goals"],
                "duration": "ongoing",
                "followup_required": True
            }
        }

    def _initialize_therapeutic_techniques(self) -> Dict[str, Dict[str, Any]]:
        """Initialize specific therapeutic techniques"""
        return {
            # Crisis Techniques
            "safety_planning": {
                "description": "Develop a step-by-step plan for crisis situations",
                "steps": ["identify_warning_signs", "coping_strategies", "social_contacts", "professional_contacts", "environment_safety"],
                "contraindications": [],
                "evidence_level": "strong"
            },
            
            "grounding_exercises": {
                "description": "Techniques to reconnect with present moment",
                "steps": ["5_things_see", "4_things_touch", "3_things_hear", "2_things_smell", "1_thing_taste"],
                "contraindications": ["severe_dissociation"],
                "evidence_level": "moderate"
            },
            
            # Emotional Regulation
            "breathing_exercises": {
                "description": "Structured breathing to regulate nervous system",
                "steps": ["box_breathing", "4_7_8_breathing", "belly_breathing"],
                "contraindications": ["respiratory_conditions"],
                "evidence_level": "strong"
            },
            
            "progressive_muscle_relaxation": {
                "description": "Systematic muscle tension and relaxation",
                "steps": ["muscle_groups_identification", "tension_relaxation_cycles", "body_awareness"],
                "contraindications": ["muscle_injuries"],
                "evidence_level": "strong"
            },
            
            # Cognitive Techniques
            "thought_challenging": {
                "description": "Examine and restructure negative thought patterns",
                "steps": ["identify_thoughts", "examine_evidence", "consider_alternatives", "balanced_thinking"],
                "contraindications": ["psychosis", "severe_depression"],
                "evidence_level": "strong"
            },
            
            "cognitive_defusion": {
                "description": "Create distance from difficult thoughts",
                "steps": ["observe_thoughts", "defusion_techniques", "value_based_action"],
                "contraindications": [],
                "evidence_level": "moderate"
            },
            
            # Behavioral Techniques
            "activity_scheduling": {
                "description": "Plan and engage in meaningful activities",
                "steps": ["activity_monitoring", "pleasure_mastery_rating", "scheduling", "review"],
                "contraindications": [],
                "evidence_level": "strong"
            }
        }

    def _initialize_safety_resources(self) -> Dict[str, Dict[str, Any]]:
        """Initialize safety and crisis resources"""
        return {
            "crisis_hotlines": {
                "national_suicide_prevention": {
                    "number": "988",
                    "description": "24/7 crisis support",
                    "languages": ["en", "es"],
                    "available": "24/7"
                },
                "crisis_text_line": {
                    "number": "Text HOME to 741741",
                    "description": "24/7 text-based crisis support",
                    "languages": ["en"],
                    "available": "24/7"
                }
            },
            
            "emergency_services": {
                "emergency": {
                    "number": "911",
                    "description": "Emergency medical and psychiatric services",
                    "when_to_use": "Immediate danger to self or others"
                }
            },
            
            "professional_resources": {
                "psychology_today": {
                    "url": "psychologytoday.com",
                    "description": "Find therapists and mental health professionals"
                },
                "nami": {
                    "url": "nami.org",
                    "description": "National Alliance on Mental Illness resources"
                }
            }
        }

    # ==================== MAIN INTERVENTION METHODS ====================

    async def assess_and_intervene(self, text: str, user_context: Optional[Dict[str, Any]] = None,
                                  emotion_analysis: Optional[EmotionAnalysis] = None) -> Tuple[CrisisAssessment, PersonalizedIntervention]:
        """
        Perform comprehensive crisis assessment and generate personalized intervention
        
        Args:
            text: User's journal entry or text to analyze
            user_context: Additional user context and preferences
            emotion_analysis: Pre-computed emotion analysis (optional)
            
        Returns:
            Tuple of (CrisisAssessment, PersonalizedIntervention)
        """
        try:
            # Step 1: Perform crisis assessment
            assessment = await self.assess_crisis_level(text, user_context, emotion_analysis)
            
            # Step 2: Generate personalized intervention
            intervention = await self.generate_intervention(assessment, text, user_context)
            
            # Update statistics
            self.intervention_stats["total_assessments"] += 1
            if assessment.crisis_level != CrisisLevel.NONE:
                self.intervention_stats["crisis_detections"] += 1
            if intervention:
                self.intervention_stats["interventions_generated"] += 1
            if assessment.professional_referral_urgent:
                self.intervention_stats["safety_referrals"] += 1
            
            logger.info(f"🆘 Crisis assessment completed: {assessment.crisis_level.value}")
            
            return assessment, intervention
            
        except Exception as e:
            logger.error(f"❌ Error in intervention assessment: {e}")
            return await self._fallback_assessment_and_intervention(text, user_context)

    async def assess_crisis_level(self, text: str, user_context: Optional[Dict[str, Any]] = None,
                                 emotion_analysis: Optional[EmotionAnalysis] = None) -> CrisisAssessment:
        """
        Assess crisis level and risk factors
        
        Args:
            text: Text to analyze for crisis indicators
            user_context: User context for personalized assessment
            emotion_analysis: Pre-computed emotion analysis
            
        Returns:
            CrisisAssessment with detailed risk analysis
        """
        try:
            # Check cache first
            cache_key = self._build_assessment_cache_key(text, user_context)
            cached_assessment = await unified_cache_service.get_ai_model_instance(cache_key)
            
            if cached_assessment:
                self.intervention_stats["cache_hits"] += 1
                return cached_assessment
            
            # Perform emotion analysis if not provided
            if not emotion_analysis:
                emotion_analysis = await ai_emotion_service.analyze_emotions(text)
            
            # Detect crisis indicators
            risk_factors = await self._detect_crisis_indicators(text, emotion_analysis)
            
            # Assess protective factors
            protective_factors = self._assess_protective_factors(text, user_context)
            
            # Calculate overall crisis level
            crisis_level = self._calculate_crisis_level(risk_factors, protective_factors)
            
            # Determine intervention needs
            immediate_interventions = self._select_immediate_interventions(crisis_level, risk_factors)
            followup_interventions = self._select_followup_interventions(crisis_level, risk_factors)
            
            # Safety planning and referral assessment
            safety_plan_needed = crisis_level in [CrisisLevel.MODERATE, CrisisLevel.HIGH, CrisisLevel.CRITICAL]
            professional_referral_urgent = crisis_level in [CrisisLevel.HIGH, CrisisLevel.CRITICAL]
            
            # Calculate confidence
            assessment_confidence = self._calculate_assessment_confidence(risk_factors, emotion_analysis)
            
            assessment = CrisisAssessment(
                crisis_level=crisis_level,
                risk_factors=risk_factors,
                protective_factors=protective_factors,
                immediate_interventions=immediate_interventions,
                followup_interventions=followup_interventions,
                safety_plan_needed=safety_plan_needed,
                professional_referral_urgent=professional_referral_urgent,
                assessment_confidence=assessment_confidence,
                assessment_metadata={
                    "text_length": len(text),
                    "emotion_primary": emotion_analysis.primary_emotion.emotion if emotion_analysis else "unknown",
                    "user_context_available": user_context is not None,
                    "assessment_method": "ai_powered"
                },
                created_at=datetime.utcnow()
            )
            
            # Cache assessment
            await unified_cache_service.set_ai_model_instance(
                assessment, cache_key, ttl=1800  # 30 minutes
            )
            
            return assessment
            
        except Exception as e:
            logger.error(f"❌ Error in crisis assessment: {e}")
            return await self._fallback_crisis_assessment(text)

    async def generate_intervention(self, assessment: CrisisAssessment, text: str,
                                  user_context: Optional[Dict[str, Any]] = None) -> PersonalizedIntervention:
        """
        Generate personalized therapeutic intervention
        
        Args:
            assessment: Crisis assessment results
            text: Original text for context
            user_context: User preferences and context
            
        Returns:
            PersonalizedIntervention with specific guidance
        """
        try:
            # Select primary intervention type
            if assessment.immediate_interventions:
                intervention_type = assessment.immediate_interventions[0].intervention_type
                therapeutic_approach = assessment.immediate_interventions[0].therapeutic_approach
            else:
                intervention_type = InterventionType.EMOTIONAL_REGULATION
                therapeutic_approach = TherapeuticApproach.MINDFULNESS
            
            # Generate intervention text using AI Prompt Service
            intervention_text = await self._generate_intervention_text(
                assessment, intervention_type, therapeutic_approach, user_context
            )
            
            # Determine personalization factors
            personalization_factors = self._identify_personalization_factors(user_context, assessment)
            
            # Expected outcomes
            expected_outcomes = self._determine_expected_outcomes(intervention_type, assessment.crisis_level)
            
            # Followup suggestions
            followup_suggestions = self._generate_followup_suggestions(assessment, intervention_type)
            
            intervention = PersonalizedIntervention(
                intervention_text=intervention_text,
                intervention_type=intervention_type,
                therapeutic_approach=therapeutic_approach,
                personalization_factors=personalization_factors,
                expected_outcomes=expected_outcomes,
                followup_suggestions=followup_suggestions,
                crisis_level=assessment.crisis_level,
                confidence_score=assessment.assessment_confidence,
                generation_metadata={
                    "generation_method": "ai_powered",
                    "template_base": intervention_type.value,
                    "approach": therapeutic_approach.value,
                    "personalized": len(personalization_factors) > 0
                },
                created_at=datetime.utcnow()
            )
            
            return intervention
            
        except Exception as e:
            logger.error(f"❌ Error generating intervention: {e}")
            return await self._fallback_intervention(assessment, text)

    # ==================== CRISIS DETECTION ====================

    async def _detect_crisis_indicators(self, text: str, emotion_analysis: EmotionAnalysis) -> List[CrisisIndicator]:
        """Detect crisis indicators in text"""
        indicators = []
        text_lower = text.lower()
        
        # Keyword-based detection
        for indicator_name, config in self.crisis_indicators.items():
            keyword_matches = sum(1 for keyword in config["keywords"] if keyword in text_lower)
            
            if keyword_matches > 0:
                # Calculate severity based on matches and context
                base_severity = config["severity_base"]
                match_factor = min(keyword_matches / len(config["keywords"]), 1.0)
                severity = base_severity * match_factor
                
                # Adjust based on emotion analysis
                if emotion_analysis:
                    if emotion_analysis.primary_emotion.emotion in ["sadness", "fear", "anger"]:
                        severity *= 1.2
                    if emotion_analysis.emotional_complexity > 0.7:
                        severity *= 1.1
                
                # Calculate confidence
                confidence = min(match_factor + 0.3, 1.0)
                
                indicator = CrisisIndicator(
                    indicator=indicator_name,
                    severity=min(severity, 1.0),
                    confidence=confidence,
                    description=config["description"],
                    immediate_risk=config["immediate_risk"]
                )
                indicators.append(indicator)
        
        # AI-enhanced detection using zero-shot classification
        ai_indicators = await self._ai_enhanced_crisis_detection(text)
        indicators.extend(ai_indicators)
        
        # Sort by severity (highest first)
        indicators.sort(key=lambda x: x.severity, reverse=True)
        
        return indicators[:5]  # Return top 5 indicators

    async def _ai_enhanced_crisis_detection(self, text: str) -> List[CrisisIndicator]:
        """Use AI models for enhanced crisis detection"""
        try:
            # Get zero-shot classification model
            model = await ai_model_manager.get_model("zero_shot_classifier")
            
            if not model:
                return []
            
            # Define crisis categories for classification
            crisis_categories = [
                "suicidal thoughts",
                "self-harm intentions", 
                "substance abuse crisis",
                "severe depression",
                "panic and anxiety",
                "emotional dysregulation",
                "trauma response"
            ]
            
            # Classify text
            results = model(text, crisis_categories)
            
            indicators = []
            if results and "scores" in results:
                for label, score in zip(results["labels"], results["scores"]):
                    if score > 0.5:  # Threshold for crisis indication
                        indicator = CrisisIndicator(
                            indicator=f"ai_detected_{label.replace(' ', '_')}",
                            severity=score,
                            confidence=score,
                            description=f"AI-detected: {label}",
                            immediate_risk=score > 0.8
                        )
                        indicators.append(indicator)
            
            return indicators
            
        except Exception as e:
            logger.error(f"❌ Error in AI crisis detection: {e}")
            return []

    def _assess_protective_factors(self, text: str, user_context: Optional[Dict[str, Any]]) -> List[str]:
        """Identify protective factors in text and context"""
        protective_factors = []
        text_lower = text.lower()
        
        # Keyword-based protective factors
        protective_keywords = {
            "social_support": ["friends", "family", "support", "loved ones", "people care"],
            "coping_skills": ["breathing", "meditation", "exercise", "therapy", "counseling"],
            "hope_future": ["tomorrow", "future", "hope", "looking forward", "goals"],
            "self_care": ["sleep", "eating", "shower", "rest", "taking care"],
            "professional_help": ["therapist", "doctor", "counselor", "medication", "treatment"],
            "meaning_purpose": ["meaning", "purpose", "important", "matters", "responsibility"],
            "positive_activities": ["hobbies", "work", "school", "volunteering", "creative"]
        }
        
        for factor_name, keywords in protective_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                protective_factors.append(factor_name)
        
        # Context-based protective factors
        if user_context:
            if user_context.get("has_therapist"):
                protective_factors.append("professional_support")
            if user_context.get("social_network_size", 0) > 2:
                protective_factors.append("strong_social_network")
            if user_context.get("coping_strategies"):
                protective_factors.append("learned_coping_strategies")
        
        return protective_factors

    def _calculate_crisis_level(self, risk_factors: List[CrisisIndicator], 
                               protective_factors: List[str]) -> CrisisLevel:
        """Calculate overall crisis level"""
        if not risk_factors:
            return CrisisLevel.NONE
        
        # Calculate risk score
        immediate_risk = any(indicator.immediate_risk for indicator in risk_factors)
        max_severity = max(indicator.severity for indicator in risk_factors)
        avg_severity = sum(indicator.severity for indicator in risk_factors) / len(risk_factors)
        
        # Calculate protective factor score
        protective_score = min(len(protective_factors) / 5.0, 1.0)  # Normalize to 0-1
        
        # Combine scores
        risk_score = (max_severity + avg_severity) / 2.0
        adjusted_risk = risk_score * (1.0 - protective_score * 0.3)  # Protective factors reduce risk
        
        # Determine crisis level
        if immediate_risk and adjusted_risk > 0.8:
            return CrisisLevel.CRITICAL
        elif immediate_risk or adjusted_risk > 0.7:
            return CrisisLevel.HIGH
        elif adjusted_risk > 0.5:
            return CrisisLevel.MODERATE
        elif adjusted_risk > 0.3:
            return CrisisLevel.LOW
        else:
            return CrisisLevel.NONE

    # ==================== INTERVENTION GENERATION ====================

    async def _generate_intervention_text(self, assessment: CrisisAssessment,
                                         intervention_type: InterventionType,
                                         therapeutic_approach: TherapeuticApproach,
                                         user_context: Optional[Dict[str, Any]]) -> str:
        """Generate personalized intervention text using AI Prompt Service"""
        try:
            # Create prompt request for intervention generation
            prompt_request = PromptRequest(
                prompt_type=PromptType.CRISIS_INTERVENTION,
                context=PromptContext.CRISIS_SITUATION if assessment.crisis_level in [CrisisLevel.HIGH, CrisisLevel.CRITICAL] else PromptContext.EMOTIONAL_SUPPORT,
                user_profile=user_context,
                specific_needs=[intervention_type.value, therapeutic_approach.value],
                emotional_state=assessment.risk_factors[0].indicator if assessment.risk_factors else "distressed",
                tone="supportive",
                length="medium"
            )
            
            # Generate intervention prompt
            generated_prompt = await ai_prompt_service.generate_prompt(prompt_request)
            
            if generated_prompt and generated_prompt.text:
                # Enhance with specific techniques
                enhanced_text = self._enhance_intervention_with_techniques(
                    generated_prompt.text, intervention_type, assessment.crisis_level
                )
                
                # Add safety resources if needed
                if assessment.professional_referral_urgent:
                    enhanced_text += self._add_safety_resources(assessment.crisis_level)
                
                return enhanced_text
            else:
                # Fallback to template-based generation
                return self._template_based_intervention(intervention_type, therapeutic_approach, assessment)
                
        except Exception as e:
            logger.error(f"❌ Error generating intervention text: {e}")
            return self._template_based_intervention(intervention_type, therapeutic_approach, assessment)

    def _enhance_intervention_with_techniques(self, base_text: str, 
                                            intervention_type: InterventionType,
                                            crisis_level: CrisisLevel) -> str:
        """Enhance intervention text with specific techniques"""
        template_config = self.intervention_templates.get(intervention_type, {})
        techniques = template_config.get("techniques", [])
        
        if not techniques:
            return base_text
        
        # Select appropriate techniques based on crisis level
        if crisis_level in [CrisisLevel.HIGH, CrisisLevel.CRITICAL]:
            # Focus on immediate techniques
            selected_techniques = techniques[:2]
        else:
            # Can include more comprehensive techniques
            selected_techniques = techniques[:3]
        
        technique_text = "\n\nSpecific techniques you can try:\n"
        
        for technique in selected_techniques:
            technique_info = self.therapeutic_techniques.get(technique, {})
            if technique_info:
                technique_text += f"• {technique_info.get('description', technique)}\n"
        
        return base_text + technique_text

    def _add_safety_resources(self, crisis_level: CrisisLevel) -> str:
        """Add safety resources to intervention text"""
        if crisis_level == CrisisLevel.CRITICAL:
            return "\n\n🚨 IMMEDIATE SAFETY RESOURCES:\n" \
                   "• National Suicide Prevention Lifeline: 988\n" \
                   "• Crisis Text Line: Text HOME to 741741\n" \
                   "• Emergency Services: 911\n" \
                   "Your safety is the top priority. Please reach out for immediate help."
        
        elif crisis_level == CrisisLevel.HIGH:
            return "\n\n🆘 CRISIS SUPPORT RESOURCES:\n" \
                   "• National Suicide Prevention Lifeline: 988 (24/7)\n" \
                   "• Crisis Text Line: Text HOME to 741741\n" \
                   "• Consider contacting a mental health professional"
        
        else:
            return "\n\n💙 SUPPORT RESOURCES:\n" \
                   "• If you need someone to talk to: 988\n" \
                   "• Mental health support: psychologytoday.com"

    def _template_based_intervention(self, intervention_type: InterventionType,
                                   therapeutic_approach: TherapeuticApproach,
                                   assessment: CrisisAssessment) -> str:
        """Generate intervention using templates when AI generation fails"""
        template_config = self.intervention_templates.get(intervention_type, {})
        base_template = template_config.get("base_template", "I understand you're going through a difficult time.")
        
        # Enhance based on crisis level
        if assessment.crisis_level == CrisisLevel.CRITICAL:
            enhanced = f"🚨 {base_template} Your immediate safety is what matters most right now."
        elif assessment.crisis_level == CrisisLevel.HIGH:
            enhanced = f"🆘 {base_template} Let's focus on what will help you feel safer and more stable."
        else:
            enhanced = f"💙 {base_template} Let's work through this together step by step."
        
        return enhanced

    # ==================== UTILITY METHODS ====================

    def _select_immediate_interventions(self, crisis_level: CrisisLevel, 
                                      risk_factors: List[CrisisIndicator]) -> List[InterventionRecommendation]:
        """Select immediate intervention recommendations"""
        interventions = []
        
        # Critical and high crisis levels need immediate safety interventions
        if crisis_level in [CrisisLevel.CRITICAL, CrisisLevel.HIGH]:
            interventions.append(InterventionRecommendation(
                intervention_type=InterventionType.IMMEDIATE_SAFETY,
                therapeutic_approach=TherapeuticApproach.TRAUMA_INFORMED,
                priority=1,
                description="Ensure immediate safety and crisis stabilization",
                specific_techniques=["safety_planning", "crisis_hotline_connection"],
                estimated_duration="immediate",
                prerequisites=[],
                contraindications=[]
            ))
        
        # Always add crisis stabilization for moderate and above
        if crisis_level in [CrisisLevel.MODERATE, CrisisLevel.HIGH, CrisisLevel.CRITICAL]:
            interventions.append(InterventionRecommendation(
                intervention_type=InterventionType.CRISIS_STABILIZATION,
                therapeutic_approach=TherapeuticApproach.DBT,
                priority=2,
                description="Stabilize emotional state and build coping capacity",
                specific_techniques=["distress_tolerance", "grounding_exercises"],
                estimated_duration="15-30 minutes",
                prerequisites=[],
                contraindications=[]
            ))
        
        # Add emotional regulation for all crisis levels
        if crisis_level != CrisisLevel.NONE:
            interventions.append(InterventionRecommendation(
                intervention_type=InterventionType.EMOTIONAL_REGULATION,
                therapeutic_approach=TherapeuticApproach.MINDFULNESS,
                priority=3,
                description="Help regulate emotional intensity",
                specific_techniques=["breathing_exercises", "mindful_awareness"],
                estimated_duration="10-15 minutes",
                prerequisites=[],
                contraindications=[]
            ))
        
        return interventions

    def _select_followup_interventions(self, crisis_level: CrisisLevel,
                                     risk_factors: List[CrisisIndicator]) -> List[InterventionRecommendation]:
        """Select follow-up intervention recommendations"""
        interventions = []
        
        # Add cognitive restructuring for negative thought patterns
        if any("depression" in indicator.indicator or "worthless" in indicator.indicator 
               for indicator in risk_factors):
            interventions.append(InterventionRecommendation(
                intervention_type=InterventionType.COGNITIVE_RESTRUCTURING,
                therapeutic_approach=TherapeuticApproach.CBT,
                priority=4,
                description="Address negative thought patterns",
                specific_techniques=["thought_challenging", "cognitive_defusion"],
                estimated_duration="20-30 minutes",
                prerequisites=["crisis_stabilized"],
                contraindications=["active_psychosis"]
            ))
        
        # Add behavioral activation for depression and isolation
        if any("depression" in indicator.indicator or "isolation" in indicator.indicator
               for indicator in risk_factors):
            interventions.append(InterventionRecommendation(
                intervention_type=InterventionType.BEHAVIORAL_ACTIVATION,
                therapeutic_approach=TherapeuticApproach.CBT,
                priority=5,
                description="Increase engagement in meaningful activities",
                specific_techniques=["activity_scheduling", "behavioral_experiments"],
                estimated_duration="ongoing",
                prerequisites=["basic_stability"],
                contraindications=[]
            ))
        
        return interventions

    def _identify_personalization_factors(self, user_context: Optional[Dict[str, Any]],
                                        assessment: CrisisAssessment) -> List[str]:
        """Identify factors for personalizing intervention"""
        factors = []
        
        if user_context:
            if user_context.get("therapy_experience"):
                factors.append("therapy_experienced")
            if user_context.get("preferred_approach"):
                factors.append(f"prefers_{user_context['preferred_approach']}")
            if user_context.get("cultural_background"):
                factors.append("culturally_adapted")
            if user_context.get("previous_crises"):
                factors.append("crisis_experienced")
        
        # Assessment-based factors
        if assessment.protective_factors:
            factors.append("has_protective_factors")
        if assessment.crisis_level == CrisisLevel.CRITICAL:
            factors.append("immediate_safety_focus")
        
        return factors

    def _determine_expected_outcomes(self, intervention_type: InterventionType,
                                   crisis_level: CrisisLevel) -> List[str]:
        """Determine expected outcomes for intervention"""
        base_outcomes = {
            InterventionType.IMMEDIATE_SAFETY: ["increased_safety", "crisis_stabilization"],
            InterventionType.CRISIS_STABILIZATION: ["emotional_stability", "reduced_distress"],
            InterventionType.EMOTIONAL_REGULATION: ["emotional_awareness", "coping_improvement"],
            InterventionType.COGNITIVE_RESTRUCTURING: ["thought_flexibility", "mood_improvement"],
            InterventionType.BEHAVIORAL_ACTIVATION: ["increased_activity", "mood_boost"],
            InterventionType.MINDFULNESS_GROUNDING: ["present_moment_awareness", "anxiety_reduction"],
            InterventionType.SOCIAL_CONNECTION: ["reduced_isolation", "support_activation"]
        }
        
        outcomes = base_outcomes.get(intervention_type, ["general_improvement"])
        
        # Adjust based on crisis level
        if crisis_level in [CrisisLevel.HIGH, CrisisLevel.CRITICAL]:
            outcomes.insert(0, "immediate_safety")
        
        return outcomes

    def _generate_followup_suggestions(self, assessment: CrisisAssessment,
                                     intervention_type: InterventionType) -> List[str]:
        """Generate follow-up suggestions"""
        suggestions = []
        
        # Crisis level specific suggestions
        if assessment.crisis_level in [CrisisLevel.HIGH, CrisisLevel.CRITICAL]:
            suggestions.extend([
                "Continue monitoring safety",
                "Consider professional crisis support",
                "Implement safety plan"
            ])
        
        # General follow-up suggestions
        suggestions.extend([
            "Practice techniques daily",
            "Track mood and progress",
            "Reach out for support when needed"
        ])
        
        # Professional referral suggestions
        if assessment.professional_referral_urgent:
            suggestions.append("Schedule appointment with mental health professional")
        elif assessment.safety_plan_needed:
            suggestions.append("Consider developing safety plan with therapist")
        
        return suggestions

    def _calculate_assessment_confidence(self, risk_factors: List[CrisisIndicator],
                                       emotion_analysis: EmotionAnalysis) -> float:
        """Calculate confidence in crisis assessment"""
        if not risk_factors:
            return 0.7  # Moderate confidence in no crisis
        
        # Base confidence on indicator confidence
        indicator_confidence = sum(indicator.confidence for indicator in risk_factors) / len(risk_factors)
        
        # Emotion analysis confidence
        emotion_confidence = emotion_analysis.primary_emotion.confidence if emotion_analysis else 0.5
        
        # Combine confidences
        combined_confidence = (indicator_confidence + emotion_confidence) / 2.0
        
        return min(combined_confidence, 1.0)

    def _build_assessment_cache_key(self, text: str, user_context: Optional[Dict[str, Any]]) -> str:
        """Build cache key for crisis assessment"""
        text_hash = hash(text)
        context_hash = hash(str(sorted(user_context.items()))) if user_context else 0
        return CachePatterns.ai_model_instance(f"crisis_assessment_{text_hash}_{context_hash}", "latest")

    # ==================== FALLBACK METHODS ====================

    async def _fallback_assessment_and_intervention(self, text: str, 
                                                   user_context: Optional[Dict[str, Any]]) -> Tuple[CrisisAssessment, PersonalizedIntervention]:
        """Provide fallback assessment and intervention when main methods fail"""
        # Simple fallback assessment
        assessment = await self._fallback_crisis_assessment(text)
        intervention = await self._fallback_intervention(assessment, text)
        
        return assessment, intervention

    async def _fallback_crisis_assessment(self, text: str) -> CrisisAssessment:
        """Provide fallback crisis assessment"""
        # Simple keyword-based fallback
        high_risk_keywords = ["suicide", "kill myself", "end it all", "not worth living"]
        moderate_risk_keywords = ["hopeless", "worthless", "can't go on", "overwhelmed"]
        
        text_lower = text.lower()
        
        # Check for high-risk indicators
        high_risk_count = sum(1 for keyword in high_risk_keywords if keyword in text_lower)
        moderate_risk_count = sum(1 for keyword in moderate_risk_keywords if keyword in text_lower)
        
        if high_risk_count > 0:
            crisis_level = CrisisLevel.HIGH
            risk_factors = [CrisisIndicator(
                indicator="fallback_high_risk",
                severity=0.8,
                confidence=0.6,
                description="High-risk language detected",
                immediate_risk=True
            )]
        elif moderate_risk_count > 0:
            crisis_level = CrisisLevel.MODERATE
            risk_factors = [CrisisIndicator(
                indicator="fallback_moderate_risk",
                severity=0.6,
                confidence=0.5,
                description="Moderate-risk language detected",
                immediate_risk=False
            )]
        else:
            crisis_level = CrisisLevel.LOW
            risk_factors = []
        
        return CrisisAssessment(
            crisis_level=crisis_level,
            risk_factors=risk_factors,
            protective_factors=[],
            immediate_interventions=[],
            followup_interventions=[],
            safety_plan_needed=crisis_level in [CrisisLevel.MODERATE, CrisisLevel.HIGH],
            professional_referral_urgent=crisis_level == CrisisLevel.HIGH,
            assessment_confidence=0.5,
            assessment_metadata={"fallback": True},
            created_at=datetime.utcnow()
        )

    async def _fallback_intervention(self, assessment: CrisisAssessment, text: str) -> PersonalizedIntervention:
        """Provide fallback intervention"""
        if assessment.crisis_level in [CrisisLevel.HIGH, CrisisLevel.CRITICAL]:
            intervention_text = ("I'm concerned about your safety and well-being. "
                               "Please reach out for immediate support: "
                               "National Suicide Prevention Lifeline: 988 or Emergency Services: 911")
            intervention_type = InterventionType.IMMEDIATE_SAFETY
        else:
            intervention_text = ("It sounds like you're going through a difficult time. "
                               "Remember that these feelings are temporary and there are ways to cope. "
                               "Consider reaching out to a trusted friend, family member, or mental health professional.")
            intervention_type = InterventionType.EMOTIONAL_REGULATION
        
        return PersonalizedIntervention(
            intervention_text=intervention_text,
            intervention_type=intervention_type,
            therapeutic_approach=TherapeuticApproach.PERSON_CENTERED,
            personalization_factors=["fallback"],
            expected_outcomes=["support_connection"],
            followup_suggestions=["seek_professional_help"],
            crisis_level=assessment.crisis_level,
            confidence_score=0.5,
            generation_metadata={"fallback": True},
            created_at=datetime.utcnow()
        )

    # ==================== MONITORING AND STATISTICS ====================

    def get_intervention_stats(self) -> Dict[str, Any]:
        """Get intervention service statistics"""
        total = max(self.intervention_stats["total_assessments"], 1)
        return {
            "total_assessments": self.intervention_stats["total_assessments"],
            "crisis_detection_rate": (self.intervention_stats["crisis_detections"] / total) * 100,
            "intervention_success_rate": (self.intervention_stats["interventions_generated"] / total) * 100,
            "safety_referral_rate": (self.intervention_stats["safety_referrals"] / total) * 100,
            "cache_hit_rate": (self.intervention_stats["cache_hits"] / total) * 100
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on intervention system"""
        health = {
            "status": "healthy",
            "ai_models_available": False,
            "emotion_service_available": False,
            "prompt_service_available": False,
            "cache_operational": False,
            "intervention_stats": self.get_intervention_stats()
        }
        
        try:
            # Check AI model availability
            zero_shot_model = await ai_model_manager.get_model("zero_shot_classifier")
            health["ai_models_available"] = zero_shot_model is not None
            
            # Check emotion service
            emotion_health = await ai_emotion_service.health_check()
            health["emotion_service_available"] = emotion_health["status"] == "healthy"
            
            # Check prompt service
            prompt_health = await ai_prompt_service.health_check()
            health["prompt_service_available"] = prompt_health["status"] == "healthy"
            
            # Check cache system
            test_key = "health_check_intervention"
            test_data = {"test": "intervention_health"}
            await unified_cache_service.set_ai_model_instance(test_data, test_key, ttl=60)
            cached_value = await unified_cache_service.get_ai_model_instance(test_key)
            health["cache_operational"] = cached_value is not None
            
            # Overall status
            critical_services = [
                health["emotion_service_available"],
                health["cache_operational"]
            ]
            
            if not any(critical_services):
                health["status"] = "error"
            elif not all(critical_services):
                health["status"] = "degraded"
            
        except Exception as e:
            health["status"] = "error"
            health["error"] = str(e)
        
        return health

# ==================== SERVICE INSTANCE ====================

# Global AI Intervention Service instance
ai_intervention_service = AIInterventionService()

# Integration with Phase 2 Service Registry
def register_ai_intervention_service():
    """Register AI Intervention Service in Phase 2 service registry"""
    try:
        from app.core.service_interfaces import service_registry
        service_registry.register_service("ai_intervention_service", ai_intervention_service)
        logger.info("✅ AI Intervention Service registered in service registry")
    except Exception as e:
        logger.error(f"❌ Failed to register AI Intervention Service: {e}")

# Auto-register when module is imported
register_ai_intervention_service()
