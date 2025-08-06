# AI Service Initialization Module

"""
AI Service Initialization for Journaling AI
Ensures all AI services are properly loaded and registered at application startup
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def initialize_ai_services() -> Dict[str, Any]:
    """
    Initialize all AI services and register them in the service registry
    
    Returns:
        Initialization status and summary
    """
    initialization_results = {
        "status": "success",
        "services_initialized": [],
        "services_failed": [],
        "service_registry_status": "healthy",
        "errors": []
    }
    
    try:
        logger.info("🚀 Initializing AI Service Infrastructure...")
        
        # Import and initialize AI Model Manager
        try:
            from app.services.ai_model_manager import ai_model_manager
            initialization_results["services_initialized"].append("ai_model_manager")
            logger.info("✅ AI Model Manager initialized")
        except Exception as e:
            initialization_results["services_failed"].append("ai_model_manager")
            initialization_results["errors"].append(f"AI Model Manager: {str(e)}")
            logger.error(f"❌ AI Model Manager initialization failed: {e}")
        
        # Import and initialize AI Prompt Service
        try:
            from app.services.ai_prompt_service import ai_prompt_service
            initialization_results["services_initialized"].append("ai_prompt_service")
            logger.info("✅ AI Prompt Service initialized")
        except Exception as e:
            initialization_results["services_failed"].append("ai_prompt_service")
            initialization_results["errors"].append(f"AI Prompt Service: {str(e)}")
            logger.error(f"❌ AI Prompt Service initialization failed: {e}")
        
        # Import and initialize AI Emotion Service
        try:
            from app.services.ai_emotion_service import ai_emotion_service
            initialization_results["services_initialized"].append("ai_emotion_service")
            logger.info("✅ AI Emotion Service initialized")
        except Exception as e:
            initialization_results["services_failed"].append("ai_emotion_service")
            initialization_results["errors"].append(f"AI Emotion Service: {str(e)}")
            logger.error(f"❌ AI Emotion Service initialization failed: {e}")
        
        # Import and initialize AI Intervention Service
        try:
            from app.services.ai_intervention_service import ai_intervention_service
            initialization_results["services_initialized"].append("ai_intervention_service")
            logger.info("✅ AI Intervention Service initialized")
        except Exception as e:
            initialization_results["services_failed"].append("ai_intervention_service")
            initialization_results["errors"].append(f"AI Intervention Service: {str(e)}")
            logger.error(f"❌ AI Intervention Service initialization failed: {e}")
        
        # Verify service registry integration
        try:
            from app.core.service_interfaces import service_registry
            
            # Check if services are properly registered
            registered_services = []
            service_names = ["ai_model_manager", "ai_prompt_service", "ai_emotion_service", "ai_intervention_service"]
            
            for service_name in service_names:
                try:
                    service = service_registry.get_service(service_name)
                    if service:
                        registered_services.append(service_name)
                except ValueError:
                    # Service not registered
                    pass
            
            initialization_results["registered_services"] = registered_services
            
            if len(registered_services) == len(service_names):
                logger.info(f"✅ All {len(registered_services)} AI services registered in service registry")
            else:
                missing_services = set(service_names) - set(registered_services)
                logger.warning(f"⚠️ Some services not registered: {missing_services}")
                initialization_results["service_registry_status"] = "partial"
                
        except Exception as e:
            initialization_results["service_registry_status"] = "failed"
            initialization_results["errors"].append(f"Service Registry: {str(e)}")
            logger.error(f"❌ Service Registry check failed: {e}")
        
        # Update overall status
        if initialization_results["services_failed"]:
            initialization_results["status"] = "partial" if initialization_results["services_initialized"] else "failed"
        
        # Summary logging
        total_services = len(initialization_results["services_initialized"]) + len(initialization_results["services_failed"])
        successful_services = len(initialization_results["services_initialized"])
        
        if initialization_results["status"] == "success":
            logger.info(f"🎉 AI Service Infrastructure initialization completed successfully! ({successful_services}/{total_services} services)")
        else:
            logger.warning(f"⚠️ AI Service Infrastructure initialization completed with issues ({successful_services}/{total_services} services)")
        
        return initialization_results
        
    except Exception as e:
        error_result = {
            "status": "failed",
            "services_initialized": [],
            "services_failed": ["all"],
            "service_registry_status": "failed",
            "errors": [f"Critical initialization error: {str(e)}"],
            "exception": str(e)
        }
        
        logger.error(f"💥 Critical AI Service Infrastructure initialization failure: {e}")
        return error_result

def get_ai_services_status() -> Dict[str, Any]:
    """
    Get current status of all AI services
    
    Returns:
        Comprehensive status of AI service infrastructure
    """
    try:
        status_report = {
            "timestamp": "2025-08-06T12:00:00Z",  # Would use datetime.utcnow()
            "overall_status": "healthy",
            "services": {},
            "integrations": {},
            "performance": {}
        }
        
        # Check AI Model Manager
        try:
            from app.services.ai_model_manager import ai_model_manager
            model_status = ai_model_manager.get_model_status()
            status_report["services"]["ai_model_manager"] = {
                "status": "healthy",
                "loaded_models": model_status["loaded_models"],
                "memory_usage_gb": model_status["total_memory_usage"],
                "gpu_available": model_status["gpu_available"],
                "model_configs": len(ai_model_manager.model_configs)
            }
        except Exception as e:
            status_report["services"]["ai_model_manager"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check AI Prompt Service
        try:
            from app.services.ai_prompt_service import ai_prompt_service
            prompt_stats = ai_prompt_service.get_generation_stats()
            status_report["services"]["ai_prompt_service"] = {
                "status": "healthy",
                "total_generated": prompt_stats["total_generated"],
                "cache_hit_rate": prompt_stats["cache_hit_rate"],
                "generation_strategies": len(ai_prompt_service.generation_strategies)
            }
        except Exception as e:
            status_report["services"]["ai_prompt_service"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check AI Emotion Service
        try:
            from app.services.ai_emotion_service import ai_emotion_service
            emotion_stats = ai_emotion_service.get_analysis_stats()
            status_report["services"]["ai_emotion_service"] = {
                "status": "healthy",
                "total_analyses": emotion_stats["total_analyses"],
                "cache_hit_rate": emotion_stats["cache_hit_rate"],
                "pattern_detection_rate": emotion_stats["pattern_detection_rate"]
            }
        except Exception as e:
            status_report["services"]["ai_emotion_service"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check AI Intervention Service
        try:
            from app.services.ai_intervention_service import ai_intervention_service
            intervention_stats = ai_intervention_service.get_intervention_stats()
            status_report["services"]["ai_intervention_service"] = {
                "status": "healthy",
                "total_assessments": intervention_stats["total_assessments"],
                "crisis_detection_rate": intervention_stats["crisis_detection_rate"],
                "safety_referral_rate": intervention_stats["safety_referral_rate"]
            }
        except Exception as e:
            status_report["services"]["ai_intervention_service"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check service registry integration
        try:
            from app.core.service_interfaces import service_registry
            
            registered_count = 0
            service_names = ["ai_model_manager", "ai_prompt_service", "ai_emotion_service", "ai_intervention_service"]
            
            for service_name in service_names:
                try:
                    service = service_registry.get_service(service_name)
                    if service:
                        registered_count += 1
                except ValueError:
                    # Service not registered
                    pass
            
            status_report["integrations"]["service_registry"] = {
                "status": "healthy" if registered_count == len(service_names) else "degraded",
                "registered_services": registered_count,
                "total_services": len(service_names)
            }
            
        except Exception as e:
            status_report["integrations"]["service_registry"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Calculate overall status
        service_statuses = [service.get("status", "error") for service in status_report["services"].values()]
        integration_statuses = [integration.get("status", "error") for integration in status_report["integrations"].values()]
        
        all_statuses = service_statuses + integration_statuses
        
        if all(status == "healthy" for status in all_statuses):
            status_report["overall_status"] = "healthy"
        elif any(status == "healthy" for status in all_statuses):
            status_report["overall_status"] = "degraded"
        else:
            status_report["overall_status"] = "critical"
        
        return status_report
        
    except Exception as e:
        return {
            "timestamp": "2025-08-06T12:00:00Z",
            "overall_status": "critical",
            "error": str(e),
            "services": {},
            "integrations": {},
            "performance": {}
        }

async def run_ai_services_health_check() -> Dict[str, Any]:
    """
    Run comprehensive health check on all AI services
    
    Returns:
        Detailed health check results
    """
    health_check_results = {
        "overall_health": "healthy",
        "checks_performed": [],
        "checks_passed": [],
        "checks_failed": [],
        "recommendations": []
    }
    
    try:
        # AI Model Manager health check
        try:
            from app.services.ai_model_manager import ai_model_manager
            model_health = await ai_model_manager.health_check()
            health_check_results["checks_performed"].append("ai_model_manager")
            
            if model_health["status"] == "healthy":
                health_check_results["checks_passed"].append("ai_model_manager")
            else:
                health_check_results["checks_failed"].append("ai_model_manager")
                if "recommendations" in model_health:
                    health_check_results["recommendations"].extend(model_health["recommendations"])
                    
        except Exception as e:
            health_check_results["checks_failed"].append("ai_model_manager")
            health_check_results["recommendations"].append(f"Fix AI Model Manager: {str(e)}")
        
        # AI Prompt Service health check
        try:
            from app.services.ai_prompt_service import ai_prompt_service
            prompt_health = await ai_prompt_service.health_check()
            health_check_results["checks_performed"].append("ai_prompt_service")
            
            if prompt_health["status"] == "healthy":
                health_check_results["checks_passed"].append("ai_prompt_service")
            else:
                health_check_results["checks_failed"].append("ai_prompt_service")
                
        except Exception as e:
            health_check_results["checks_failed"].append("ai_prompt_service")
            health_check_results["recommendations"].append(f"Fix AI Prompt Service: {str(e)}")
        
        # AI Emotion Service health check
        try:
            from app.services.ai_emotion_service import ai_emotion_service
            emotion_health = await ai_emotion_service.health_check()
            health_check_results["checks_performed"].append("ai_emotion_service")
            
            if emotion_health["status"] == "healthy":
                health_check_results["checks_passed"].append("ai_emotion_service")
            else:
                health_check_results["checks_failed"].append("ai_emotion_service")
                
        except Exception as e:
            health_check_results["checks_failed"].append("ai_emotion_service")
            health_check_results["recommendations"].append(f"Fix AI Emotion Service: {str(e)}")
        
        # AI Intervention Service health check
        try:
            from app.services.ai_intervention_service import ai_intervention_service
            intervention_health = await ai_intervention_service.health_check()
            health_check_results["checks_performed"].append("ai_intervention_service")
            
            if intervention_health["status"] == "healthy":
                health_check_results["checks_passed"].append("ai_intervention_service")
            else:
                health_check_results["checks_failed"].append("ai_intervention_service")
                
        except Exception as e:
            health_check_results["checks_failed"].append("ai_intervention_service")
            health_check_results["recommendations"].append(f"Fix AI Intervention Service: {str(e)}")
        
        # Calculate overall health
        total_checks = len(health_check_results["checks_performed"])
        passed_checks = len(health_check_results["checks_passed"])
        
        if passed_checks == total_checks:
            health_check_results["overall_health"] = "healthy"
        elif passed_checks > total_checks // 2:
            health_check_results["overall_health"] = "degraded"
        else:
            health_check_results["overall_health"] = "critical"
        
        return health_check_results
        
    except Exception as e:
        return {
            "overall_health": "critical",
            "error": str(e),
            "checks_performed": [],
            "checks_passed": [],
            "checks_failed": ["initialization"],
            "recommendations": [f"Fix AI services initialization: {str(e)}"]
        }

# Export key functions
__all__ = [
    'initialize_ai_services',
    'get_ai_services_status', 
    'run_ai_services_health_check'
]
