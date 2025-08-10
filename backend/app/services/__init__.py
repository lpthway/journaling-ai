# backend/app/services/__init__.py
"""
Services module for Journaling AI

This module contains all service layer implementations including:
- AI Services (emotion analysis, prompt generation, crisis intervention)
- Database Services (unified database interface)
- Cache Services (Redis-based caching)
- Analytics Services (background processing and insights)
"""

# AI Services - Modern AI-powered capabilities
from .ai_service_init import initialize_ai_services, get_ai_services_status, run_ai_services_health_check
from .ai_model_manager import ai_model_manager
from .ai_emotion_service import ai_emotion_service, analyze_sentiment
from .ai_prompt_service import ai_prompt_service
from .ai_intervention_service import ai_intervention_service

# Core Services - Database and caching
from .unified_database_service import unified_db_service
from .cache_service import unified_cache_service
from .redis_service_simple import simple_redis_service as redis_service  # Use simple Redis service

# Analytics and Processing Services
from .analytics_service import analytics_cache_service
from .background_analytics import background_processor

# Psychology and Knowledge Services
from .psychology_knowledge_service import psychology_knowledge_service
from .vector_service import vector_service

# Session and Communication Services
from .session_service import session_service
from .llm_service import llm_service

# Celery and Task Services
from .celery_service import celery_service, celery_app
from .celery_monitoring import celery_monitoring_service

__all__ = [
    # AI Services
    'initialize_ai_services',
    'get_ai_services_status', 
    'run_ai_services_health_check',
    'ai_model_manager',
    'ai_emotion_service',
    'ai_prompt_service',
    'ai_intervention_service',
    'analyze_sentiment',  # Legacy compatibility
    
    # Core Services
    'unified_db_service',
    'unified_cache_service',
    'redis_service',
    
    # Analytics Services
    'analytics_cache_service',
    'background_processor',
    
    # Knowledge Services
    'psychology_knowledge_service',
    'vector_service',
    
    # Communication Services
    'session_service',
    'llm_service',
    
    # Task Services
    'celery_service',
    'celery_app',
    'celery_monitoring_service'
]
