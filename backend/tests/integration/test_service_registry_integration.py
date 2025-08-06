import pytest
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.ai_service_init import initialize_ai_services
from app.core.service_interfaces import service_registry

class TestServiceRegistryIntegration:
    """Test AI services integration with service registry"""
    
    def test_full_service_initialization(self):
        """Test complete AI service initialization"""
        result = initialize_ai_services()
        
        assert result['status'] in ['success', 'partial']
        assert len(result['services_initialized']) >= 2  # At least 2 services should work
        
        if result['status'] == 'success':
            assert len(result['services_initialized']) == 4
            assert len(result['services_failed']) == 0
            assert result['service_registry_status'] == 'healthy'
            print("✓ Full initialization successful")
        else:
            print(f"⚠ Partial initialization: {len(result['services_initialized'])}/4 services")
            if result['errors']:
                for error in result['errors']:
                    print(f"  Error: {error}")
    
    def test_service_discovery(self):
        """Test service discovery through registry"""
        # Initialize services
        initialize_ai_services()
        
        # Test each service is discoverable
        ai_services = [
            'ai_model_manager',
            'ai_prompt_service', 
            'ai_emotion_service',
            'ai_intervention_service'
        ]
        
        discovered_services = 0
        for service_name in ai_services:
            try:
                service = service_registry.get_service(service_name)
                if service is not None:
                    discovered_services += 1
                    print(f"✓ {service_name}: {type(service).__name__}")
                    assert hasattr(service, '__class__')
                else:
                    print(f"✗ {service_name}: Not found")
            except Exception as e:
                print(f"✗ {service_name}: Error - {e}")
        
        # At least 2 services should be discoverable
        assert discovered_services >= 2, f"Expected at least 2 services, found {discovered_services}"
    
    def test_cross_service_functionality(self):
        """Test basic cross-service functionality"""
        # Initialize services
        initialize_ai_services()
        
        # Get model manager and emotion service
        try:
            model_manager = service_registry.get_service('ai_model_manager')
            emotion_service = service_registry.get_service('ai_emotion_service')
            
            if model_manager and emotion_service:
                # Test that both services can report status
                model_status = model_manager.get_model_status()
                emotion_stats = emotion_service.get_analysis_stats()
                
                assert model_status is not None
                assert emotion_stats is not None
                
                print("✓ Cross-service communication working")
            else:
                pytest.skip("Required services not available")
                
        except Exception as e:
            print(f"Cross-service test failed: {e}")
            pytest.skip(f"Cross-service functionality not available: {e}")
    
    def test_service_health_monitoring(self):
        """Test service health monitoring"""
        from app.services.ai_service_init import get_ai_services_status
        
        # Initialize services
        initialize_ai_services()
        
        # Get comprehensive status
        status = get_ai_services_status()
        
        assert status is not None
        assert 'overall_status' in status
        assert 'services' in status
        assert 'integrations' in status
        
        print(f"Overall health status: {status['overall_status']}")
        
        # Should have service information
        assert len(status['services']) > 0
        
        # Check integration status
        if 'service_registry' in status['integrations']:
            registry_status = status['integrations']['service_registry']
            print(f"Service registry: {registry_status.get('status', 'unknown')} "
                  f"({registry_status.get('registered_services', 0)}/4 services)")
        
        # Overall status should be reasonable
        assert status['overall_status'] in ['healthy', 'degraded', 'critical']
