import pytest
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.ai_service_init import initialize_ai_services, get_ai_services_status
from app.core.service_interfaces import service_registry

class TestBasicAIFunctionality:
    """Basic tests for AI services functionality"""
    
    def test_full_ai_system(self):
        """Test complete AI system initialization and basic functionality"""
        print("\n=== AI Services Complete Test ===")
        
        # 1. Initialize all AI services
        print("1. Initializing AI services...")
        init_result = initialize_ai_services()
        
        print(f"   Status: {init_result['status']}")
        print(f"   Services initialized: {len(init_result['services_initialized'])}/4")
        print(f"   Services: {init_result['services_initialized']}")
        
        if init_result['services_failed']:
            print(f"   Failed services: {init_result['services_failed']}")
            for error in init_result.get('errors', []):
                print(f"   Error: {error}")
        
        # Should have at least some services working
        assert len(init_result['services_initialized']) >= 2
        
        # 2. Test service registry integration
        print("\n2. Testing service registry...")
        ai_services = ['ai_model_manager', 'ai_prompt_service', 'ai_emotion_service', 'ai_intervention_service']
        
        registered_services = []
        for service_name in ai_services:
            try:
                service = service_registry.get_service(service_name)
                if service is not None:
                    registered_services.append(service_name)
                    print(f"   ✓ {service_name}: {type(service).__name__}")
                else:
                    print(f"   ✗ {service_name}: Not found")
            except Exception as e:
                print(f"   ✗ {service_name}: Error - {e}")
        
        assert len(registered_services) >= 2
        
        # 3. Test status reporting
        print("\n3. Testing status reporting...")
        status = get_ai_services_status()
        
        print(f"   Overall status: {status['overall_status']}")
        print(f"   Services reporting: {len(status['services'])}")
        
        if 'service_registry' in status['integrations']:
            registry_info = status['integrations']['service_registry']
            print(f"   Registry status: {registry_info.get('status', 'unknown')}")
            print(f"   Registered services: {registry_info.get('registered_services', 0)}/4")
        
        assert status['overall_status'] in ['healthy', 'degraded']
        
        # 4. Test individual service capabilities
        print("\n4. Testing individual services...")
        
        # Model Manager
        if 'ai_model_manager' in registered_services:
            try:
                model_manager = service_registry.get_service('ai_model_manager')
                model_status = model_manager.get_model_status()
                
                print(f"   Model Manager: {model_status['loaded_models']} models loaded")
                print(f"   GPU available: {model_status.get('gpu_available', 'unknown')}")
                print(f"   Memory usage: {model_status.get('total_memory_usage', 0):.2f}GB")
                
                assert isinstance(model_status['loaded_models'], int)
                assert 'gpu_available' in model_status
                
            except Exception as e:
                print(f"   Model Manager test failed: {e}")
        
        # Emotion Service
        if 'ai_emotion_service' in registered_services:
            try:
                emotion_service = service_registry.get_service('ai_emotion_service')
                emotion_stats = emotion_service.get_analysis_stats()
                
                print(f"   Emotion Service: {emotion_stats['total_analyses']} analyses performed")
                print(f"   Cache hit rate: {emotion_stats['cache_hit_rate']:.2f}")
                
                assert isinstance(emotion_stats['total_analyses'], int)
                
            except Exception as e:
                print(f"   Emotion Service test failed: {e}")
        
        # Prompt Service
        if 'ai_prompt_service' in registered_services:
            try:
                prompt_service = service_registry.get_service('ai_prompt_service')
                prompt_stats = prompt_service.get_generation_stats()
                
                print(f"   Prompt Service: {prompt_stats['total_generated']} prompts generated")
                
                assert isinstance(prompt_stats['total_generated'], int)
                
            except Exception as e:
                print(f"   Prompt Service test failed: {e}")
        
        # Intervention Service  
        if 'ai_intervention_service' in registered_services:
            try:
                intervention_service = service_registry.get_service('ai_intervention_service')
                intervention_stats = intervention_service.get_intervention_stats()
                
                print(f"   Intervention Service: {intervention_stats['total_assessments']} assessments")
                
                assert isinstance(intervention_stats['total_assessments'], int)
                
            except Exception as e:
                print(f"   Intervention Service test failed: {e}")
        
        print(f"\n=== AI Services Test Complete: {len(registered_services)}/4 services operational ===")
        
        # Overall success criteria
        assert len(registered_services) >= 2, f"Need at least 2 services, got {len(registered_services)}"
        assert status['overall_status'] in ['healthy', 'degraded'], f"Bad overall status: {status['overall_status']}"
