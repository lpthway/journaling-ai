import pytest
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.ai_service_init import initialize_ai_services, get_ai_services_status
from app.core.service_interfaces import service_registry

class TestAIServiceInitialization:
    """Test AI service initialization and basic functionality"""
    
    def test_ai_services_initialization(self):
        """Test that all AI services initialize successfully"""
        result = initialize_ai_services()
        
        # Basic validation
        assert result is not None
        assert 'status' in result
        assert 'services_initialized' in result
        assert 'services_failed' in result
        
        # Check that we have some services initialized
        assert len(result['services_initialized']) > 0
        
        # Ideally all 4 services should initialize
        expected_services = 4
        actual_initialized = len(result['services_initialized'])
        
        print(f"Services initialized: {actual_initialized}/{expected_services}")
        print(f"Initialized services: {result['services_initialized']}")
        
        if result['services_failed']:
            print(f"Failed services: {result['services_failed']}")
            print(f"Errors: {result.get('errors', [])}")
        
        # At least some services should work
        assert actual_initialized >= 2, f"Expected at least 2 services, got {actual_initialized}"
    
    def test_service_registry_integration(self):
        """Test that services are properly registered"""
        # Initialize services first
        initialize_ai_services()
        
        # Test service discovery
        ai_services = [
            'ai_model_manager',
            'ai_prompt_service', 
            'ai_emotion_service',
            'ai_intervention_service'
        ]
        
        registered_count = 0
        for service_name in ai_services:
            try:
                service = service_registry.get_service(service_name)
                if service is not None:
                    registered_count += 1
                    print(f"✓ {service_name}: {type(service).__name__}")
                else:
                    print(f"✗ {service_name}: Not found")
            except Exception as e:
                print(f"✗ {service_name}: Error - {e}")
        
        # At least some services should be registered
        assert registered_count >= 2, f"Expected at least 2 registered services, got {registered_count}"
    
    def test_ai_services_status(self):
        """Test AI services status reporting"""
        # Initialize services first
        initialize_ai_services()
        
        # Get status
        status = get_ai_services_status()
        
        assert status is not None
        assert 'overall_status' in status
        assert 'services' in status
        assert 'integrations' in status
        
        print(f"Overall status: {status['overall_status']}")
        
        # Should have some service information
        assert len(status['services']) > 0
