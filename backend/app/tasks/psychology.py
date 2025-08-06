# backend/app/tasks/psychology.py
"""
Psychology Task Coordinators for Phase 0C
Lightweight task definitions that delegate to psychology services
Follows enterprise architecture: Tasks coordinate, Services contain business logic
"""

import logging
import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Celery and app imports
from app.services.celery_service import celery_app, monitored_task, TaskPriority, TaskCategory
from app.services.psychology_knowledge_service import psychology_knowledge_service
from app.services.enhanced_ai_service import get_enhanced_ai_service
from app.core.performance_monitor import performance_monitor

logger = logging.getLogger(__name__)

# === PSYCHOLOGY TASK COORDINATORS ===

@monitored_task(priority=TaskPriority.HIGH, category=TaskCategory.PSYCHOLOGY_PROCESSING)
def process_psychology_content(self, content_id: str, content_type: str = "research_paper") -> Dict[str, Any]:
    """
    Task coordinator for psychology content processing
    Delegates to psychology knowledge service for analysis
    
    Args:
        content_id: Identifier for the content to process
        content_type: Type of content (research_paper, clinical_guideline, etc.)
    
    Returns:
        Processing results with extracted knowledge
    """
    try:
        start_time = time.time()
        
        logger.info(f"🧠 Coordinating psychology content processing for {content_id}")
        
        # Delegate to psychology knowledge service
        processing_result = asyncio.run(
            psychology_knowledge_service.process_content(content_id, content_type)
        )
        
        # Add task coordination metadata
        processing_result.update({
            "task_coordination": {
                "task_id": self.request.id,
                "coordinator": "process_psychology_content",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        logger.info(f"✅ Psychology content processing complete in {processing_result['task_coordination']['processing_time_ms']}ms")
        
        return processing_result
        
    except Exception as e:
        logger.error(f"❌ Psychology content processing coordination failed: {e}")
        return {
            "error": str(e),
            "task_id": self.request.id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat()
        }

@monitored_task(priority=TaskPriority.NORMAL, category=TaskCategory.PSYCHOLOGY_PROCESSING)
def extract_psychology_knowledge(self, text_content: str, domain: str = None) -> Dict[str, Any]:
    """
    Task coordinator for extracting psychology knowledge from text
    
    Args:
        text_content: Text to analyze for psychology knowledge
        domain: Psychology domain for categorization
    
    Returns:
        Extracted knowledge with categorization
    """
    try:
        start_time = time.time()
        
        logger.info(f"🔍 Coordinating psychology knowledge extraction for domain: {domain}")
        
        # Delegate to psychology knowledge service
        extraction_result = asyncio.run(
            psychology_knowledge_service.extract_knowledge(text_content, domain)
        )
        
        extraction_result.update({
            "task_coordination": {
                "task_id": self.request.id,
                "coordinator": "extract_psychology_knowledge",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        return extraction_result
        
    except Exception as e:
        logger.error(f"❌ Psychology knowledge extraction coordination failed: {e}")
        return {
            "error": str(e),
            "task_id": self.request.id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat()
        }

@monitored_task(priority=TaskPriority.NORMAL, category=TaskCategory.PSYCHOLOGY_PROCESSING)
def analyze_user_psychology_profile(self, user_id: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
    """
    Task coordinator for analyzing user psychology patterns
    
    Args:
        user_id: User identifier
        analysis_type: Type of analysis (comprehensive, mood_focused, behavioral)
    
    Returns:
        Psychology profile analysis results
    """
    try:
        start_time = time.time()
        
        logger.info(f"🧠 Coordinating psychology profile analysis for user {user_id}")
        
        # Get AI service for analysis
        ai_service = get_enhanced_ai_service()
        
        # Delegate to AI service for user analysis
        analysis_result = asyncio.run(
            ai_service.analyze_user_psychology_profile(user_id, analysis_type)
        )
        
        analysis_result.update({
            "task_coordination": {
                "task_id": self.request.id,
                "coordinator": "analyze_user_psychology_profile",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"❌ Psychology profile analysis coordination failed: {e}")
        return {
            "error": str(e),
            "task_id": self.request.id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat()
        }

@monitored_task(priority=TaskPriority.HIGH, category=TaskCategory.PSYCHOLOGY_PROCESSING)
def generate_psychology_insights(self, user_id: str, time_range_days: int = 30) -> Dict[str, Any]:
    """
    Task coordinator for generating psychology-based insights
    
    Args:
        user_id: User identifier
        time_range_days: Number of days to analyze
    
    Returns:
        Psychology insights and recommendations
    """
    try:
        start_time = time.time()
        
        logger.info(f"💡 Coordinating psychology insights generation for user {user_id}")
        
        # Get AI service for insights
        ai_service = get_enhanced_ai_service()
        
        # Delegate to AI service for insights generation
        insights_result = asyncio.run(
            ai_service.generate_psychology_insights(user_id, time_range_days)
        )
        
        insights_result.update({
            "task_coordination": {
                "task_id": self.request.id,
                "coordinator": "generate_psychology_insights",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        return insights_result
        
    except Exception as e:
        logger.error(f"❌ Psychology insights generation coordination failed: {e}")
        return {
            "error": str(e),
            "task_id": self.request.id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat()
        }

@monitored_task(priority=TaskPriority.LOW, category=TaskCategory.PSYCHOLOGY_PROCESSING)
def update_psychology_knowledge_base(self, knowledge_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Task coordinator for updating psychology knowledge base
    
    Args:
        knowledge_updates: List of knowledge entries to add/update
    
    Returns:
        Update results
    """
    try:
        start_time = time.time()
        
        logger.info(f"📚 Coordinating psychology knowledge base update - {len(knowledge_updates)} entries")
        
        # Delegate to psychology knowledge service
        update_result = asyncio.run(
            psychology_knowledge_service.bulk_update_knowledge(knowledge_updates)
        )
        
        update_result.update({
            "task_coordination": {
                "task_id": self.request.id,
                "coordinator": "update_psychology_knowledge_base",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        return update_result
        
    except Exception as e:
        logger.error(f"❌ Psychology knowledge base update coordination failed: {e}")
        return {
            "error": str(e),
            "task_id": self.request.id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat()
        }

@monitored_task(priority=TaskPriority.NORMAL, category=TaskCategory.PSYCHOLOGY_PROCESSING)
def process_crisis_intervention_psychology(self, user_id: str, content: str, risk_level: str) -> Dict[str, Any]:
    """
    Task coordinator for psychology-informed crisis intervention
    Integrates with crisis detection for psychology-based responses
    
    Args:
        user_id: User identifier
        content: Content that triggered crisis detection
        risk_level: Risk level from crisis detection
    
    Returns:
        Psychology-informed intervention recommendations
    """
    try:
        start_time = time.time()
        
        logger.info(f"🚨 Coordinating psychology-informed crisis intervention for user {user_id}, risk: {risk_level}")
        
        # Get AI service for crisis psychology analysis
        ai_service = get_enhanced_ai_service()
        
        # Delegate to AI service for psychology-informed intervention
        intervention_result = asyncio.run(
            ai_service.generate_crisis_intervention_psychology(user_id, content, risk_level)
        )
        
        intervention_result.update({
            "task_coordination": {
                "task_id": self.request.id,
                "coordinator": "process_crisis_intervention_psychology",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        return intervention_result
        
    except Exception as e:
        logger.error(f"❌ Psychology-informed crisis intervention coordination failed: {e}")
        return {
            "error": str(e),
            "task_id": self.request.id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat()
        }

# Export tasks for Celery discovery
__all__ = [
    'process_psychology_content',
    'extract_psychology_knowledge',
    'analyze_user_psychology_profile',
    'generate_psychology_insights',
    'update_psychology_knowledge_base',
    'process_crisis_intervention_psychology'
]
