# backend/app/tasks/crisis.py
"""
Crisis Detection and Intervention Tasks for Phase 0C
Real-time analysis for crisis patterns, risk assessment, and intervention triggers
CRITICAL PRIORITY tasks for user safety and wellbeing
"""

import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import re
from dataclasses import dataclass
from enum import Enum

# Celery and app imports
from app.services.celery_service import celery_app, monitored_task, TaskPriority, TaskCategory
from app.services.unified_database_service import unified_db_service
from app.services.redis_service_simple import simple_redis_service as redis_service
from app.core.config import settings
from app.core.performance_monitor import performance_monitor

logger = logging.getLogger(__name__)

class CrisisLevel(Enum):
    """Crisis severity levels for risk assessment"""
    LOW = "low"           # General monitoring
    MODERATE = "moderate" # Increased attention
    HIGH = "high"         # Intervention recommended
    CRITICAL = "critical" # Immediate intervention required

@dataclass
class CrisisIndicators:
    """Crisis detection indicators and patterns"""
    keywords: List[str]
    patterns: List[str]
    severity_weight: float
    category: str

# Crisis detection patterns - can be enhanced with AI later
CRISIS_PATTERNS = {
    "self_harm": CrisisIndicators(
        keywords=["hurt myself", "end it all", "can't take it", "want to die", "kill myself", "suicide"],
        patterns=[r"(?:want to|going to|plan to|thinking about).{0,20}(?:hurt|kill|end).{0,10}myself"],
        severity_weight=1.0,  # Highest severity
        category="self_harm"
    ),
    "hopelessness": CrisisIndicators(
        keywords=["no hope", "pointless", "nothing matters", "give up", "no way out"],
        patterns=[r"(?:no|don't see).{0,10}(?:point|hope|way out|future)"],
        severity_weight=0.8,
        category="emotional_distress"
    ),
    "isolation": CrisisIndicators(
        keywords=["alone", "nobody cares", "isolated", "no friends", "abandoned"],
        patterns=[r"(?:completely|totally|feel so).{0,10}(?:alone|isolated|abandoned)"],
        severity_weight=0.6,
        category="social_isolation"
    ),
}

# === CRISIS DETECTION TASKS ===

@monitored_task(priority=TaskPriority.CRITICAL, category=TaskCategory.CRISIS_DETECTION)
def detect_crisis_patterns(self, user_id: str, content: str, entry_id: str = None) -> Dict[str, Any]:
    """
    Analyze content for crisis indicators and risk assessment
    
    Args:
        user_id: User identifier
        content: Text content to analyze
        entry_id: Optional entry ID for tracking
    
    Returns:
        Crisis assessment with risk level and recommendations
    """
    try:
        start_time = time.time()
        
        logger.info(f"🚨 Analyzing content for crisis patterns - User: {user_id}")
        
        # Initialize assessment
        crisis_assessment = {
            "user_id": user_id,
            "entry_id": entry_id,
            "timestamp": datetime.utcnow().isoformat(),
            "risk_level": CrisisLevel.LOW.value,
            "risk_score": 0.0,
            "detected_indicators": [],
            "recommendations": [],
            "intervention_required": False,
            "analysis_time_ms": 0
        }
        
        # Normalize content for analysis
        content_lower = content.lower()
        
        # Analyze for each crisis pattern
        total_score = 0.0
        detected_patterns = []
        
        for pattern_name, indicators in CRISIS_PATTERNS.items():
            pattern_score = 0.0
            matches = []
            
            # Check keywords
            for keyword in indicators.keywords:
                if keyword in content_lower:
                    matches.append(f"keyword: {keyword}")
                    pattern_score += 0.2
            
            # Check regex patterns
            for pattern in indicators.patterns:
                regex_matches = re.findall(pattern, content_lower, re.IGNORECASE)
                if regex_matches:
                    matches.extend([f"pattern: {match}" for match in regex_matches])
                    pattern_score += 0.4
            
            # Apply severity weight
            if pattern_score > 0:
                weighted_score = pattern_score * indicators.severity_weight
                total_score += weighted_score
                
                detected_patterns.append({
                    "category": pattern_name,
                    "severity": indicators.category,
                    "score": weighted_score,
                    "matches": matches,
                    "weight": indicators.severity_weight
                })
        
        # Determine risk level based on total score
        if total_score >= 1.0:
            risk_level = CrisisLevel.CRITICAL
            intervention_required = True
        elif total_score >= 0.7:
            risk_level = CrisisLevel.HIGH
            intervention_required = True
        elif total_score >= 0.4:
            risk_level = CrisisLevel.MODERATE
            intervention_required = False
        else:
            risk_level = CrisisLevel.LOW
            intervention_required = False
        
        # Update assessment
        crisis_assessment.update({
            "risk_level": risk_level.value,
            "risk_score": round(total_score, 3),
            "detected_indicators": detected_patterns,
            "intervention_required": intervention_required,
            "analysis_time_ms": round((time.time() - start_time) * 1000, 2)
        })
        
        # Generate recommendations based on risk level
        crisis_assessment["recommendations"] = _generate_crisis_recommendations(risk_level, detected_patterns)
        
        logger.info(f"✅ Crisis analysis complete - Risk: {risk_level.value}, Score: {total_score}")
        
        return crisis_assessment
        
    except Exception as e:
        logger.error(f"❌ Crisis pattern detection failed: {e}")
        
        # Return safe fallback assessment
        return {
            "user_id": user_id,
            "entry_id": entry_id,
            "timestamp": datetime.utcnow().isoformat(),
            "risk_level": CrisisLevel.LOW.value,
            "risk_score": 0.0,
            "detected_indicators": [],
            "recommendations": ["Error in analysis - manual review recommended"],
            "intervention_required": False,
            "error": str(e),
            "analysis_time_ms": 0
        }

@monitored_task(priority=TaskPriority.CRITICAL, category=TaskCategory.CRISIS_DETECTION)
def evaluate_intervention_triggers(self, user_id: str, risk_score: float, user_context: Dict) -> Dict[str, Any]:
    """
    Determine if immediate intervention is required and what type
    
    Args:
        user_id: User identifier
        risk_score: Calculated risk score
        user_context: Additional context about the user and situation
    
    Returns:
        Intervention decision and action plan
    """
    try:
        start_time = time.time()
        
        logger.info(f"🚨 Evaluating intervention triggers - User: {user_id}, Risk: {risk_score}")
        
        # Initialize intervention plan
        intervention_plan = {
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "risk_score": risk_score,
            "intervention_type": "none",
            "urgency": "normal",
            "actions": [],
            "resources": [],
            "follow_up_required": False,
            "professional_referral": False
        }
        
        # Determine intervention type based on risk score
        if risk_score >= 1.0:
            # Critical risk - immediate intervention
            intervention_plan.update({
                "intervention_type": "immediate",
                "urgency": "critical",
                "actions": [
                    "Display immediate crisis resources",
                    "Provide crisis hotline information",
                    "Encourage immediate professional help",
                    "Log for manual review by support team"
                ],
                "resources": [
                    {"type": "crisis_hotline", "name": "National Suicide Prevention Lifeline", "contact": "988"},
                    {"type": "emergency", "name": "Emergency Services", "contact": "911"},
                    {"type": "crisis_text", "name": "Crisis Text Line", "contact": "Text HOME to 741741"}
                ],
                "follow_up_required": True,
                "professional_referral": True
            })
            
        elif risk_score >= 0.7:
            # High risk - strong intervention
            intervention_plan.update({
                "intervention_type": "strong",
                "urgency": "high",
                "actions": [
                    "Provide supportive response with resources",
                    "Suggest coping strategies",
                    "Recommend professional support",
                    "Schedule check-in within 24 hours"
                ],
                "resources": [
                    {"type": "support", "name": "Mental Health Resources", "contact": "Contact your healthcare provider"},
                    {"type": "coping", "name": "Coping Strategies", "contact": "Visit crisis support website"}
                ],
                "follow_up_required": True,
                "professional_referral": True
            })
            
        elif risk_score >= 0.4:
            # Moderate risk - supportive intervention
            intervention_plan.update({
                "intervention_type": "supportive",
                "urgency": "moderate",
                "actions": [
                    "Provide empathetic response",
                    "Suggest self-care activities",
                    "Offer additional resources if needed"
                ],
                "resources": [
                    {"type": "self_care", "name": "Self-Care Tips", "contact": "Built-in guidance"},
                    {"type": "support", "name": "Mental Health Information", "contact": "Educational resources"}
                ],
                "follow_up_required": False,
                "professional_referral": False
            })
        
        intervention_plan["evaluation_time_ms"] = round((time.time() - start_time) * 1000, 2)
        
        return intervention_plan
        
    except Exception as e:
        logger.error(f"❌ Intervention evaluation failed: {e}")
        
        # Return safe fallback - always err on side of caution
        return {
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "risk_score": risk_score,
            "intervention_type": "fallback",
            "urgency": "review_required",
            "actions": ["Manual review required due to system error"],
            "resources": [
                {"type": "emergency", "name": "Emergency Services", "contact": "911"},
                {"type": "crisis_hotline", "name": "Crisis Support", "contact": "988"}
            ],
            "follow_up_required": True,
            "professional_referral": True,
            "error": str(e),
            "evaluation_time_ms": 0
        }

# === HELPER FUNCTIONS ===

def _generate_crisis_recommendations(risk_level: CrisisLevel, detected_patterns: List[Dict]) -> List[str]:
    """Generate contextual recommendations based on crisis assessment"""
    
    recommendations = []
    
    if risk_level == CrisisLevel.CRITICAL:
        recommendations.extend([
            "🚨 IMMEDIATE ATTENTION REQUIRED",
            "Please reach out to a crisis hotline or emergency services",
            "Contact: National Suicide Prevention Lifeline - 988",
            "You are not alone - professional help is available"
        ])
        
    elif risk_level == CrisisLevel.HIGH:
        recommendations.extend([
            "Your wellbeing is important - consider reaching out for support",
            "Professional mental health resources can provide valuable assistance",
            "Crisis support is available 24/7 if you need immediate help"
        ])
        
    elif risk_level == CrisisLevel.MODERATE:
        recommendations.extend([
            "Thank you for sharing your feelings",
            "Consider talking to someone you trust about how you're feeling",
            "Self-care activities might help improve your mood"
        ])
        
    else:  # LOW
        recommendations.extend([
            "Your emotional wellbeing matters",
            "Continue using journaling as a healthy outlet"
        ])
    
    # Add pattern-specific recommendations
    for pattern in detected_patterns:
        if pattern["category"] == "isolation":
            recommendations.append("Consider connecting with friends, family, or support groups")
    
    return recommendations

# Export tasks for Celery discovery
__all__ = [
    'detect_crisis_patterns',
    'evaluate_intervention_triggers'
]