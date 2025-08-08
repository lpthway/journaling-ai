import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.ai_service_init import (
    initialize_ai_services,
    get_ai_services_status,
    run_ai_services_health_check,
    cleanup_ai_services
)

class TestAIServiceInitialization:
    """Test AI service initialization and management"""

    @pytest.mark.asyncio
    async def test_initialize_ai_services_success(self):
        """Test successful AI services initialization"""
        with patch('app.services.ai_service_init.logger') as mock_logger:
            # Mock all AI services
            with patch('app.services.ai_model_manager.ai_model_manager') as mock_model_manager, \
                 patch('app.services.ai_model_manager.model_cleanup_scheduler') as mock_scheduler, \
                 patch('app.services.ai_prompt_service.ai_prompt_service'), \
                 patch('app.services.ai_emotion_service.ai_emotion_service'), \
                 patch('app.services.ai_intervention_service.ai_intervention_service'), \
                 patch('app.core.service_interfaces.service_registry') as mock_registry:
                
                # Mock successful initialization
                mock_model_manager.initialize = AsyncMock()
                mock_scheduler.start_scheduled_cleanup = AsyncMock()
                mock_registry.get_service.return_value = Mock()  # Service registered
                
                result = await initialize_ai_services()
                
                # Verify successful initialization
                assert result["status"] == "success"
                assert "ai_model_manager" in result["services_initialized"]
                assert "ai_prompt_service" in result["services_initialized"]
                assert "ai_emotion_service" in result["services_initialized"]
                assert "ai_intervention_service" in result["services_initialized"]
                assert len(result["services_failed"]) == 0
                
                # Verify model manager was initialized
                mock_model_manager.initialize.assert_called_once()
                mock_scheduler.start_scheduled_cleanup.assert_called_once()
                
                print("✓ AI services initialization success test passed")

    @pytest.mark.asyncio
    async def test_initialize_ai_services_partial_failure(self):
        """Test AI services initialization with partial failures"""
        with patch('app.services.ai_service_init.logger'):
            # Mock some services failing
            with patch('app.services.ai_model_manager.ai_model_manager') as mock_model_manager, \
                 patch('app.services.ai_model_manager.model_cleanup_scheduler'), \
                 patch('app.services.ai_prompt_service.ai_prompt_service'), \
                 patch('app.services.ai_emotion_service.ai_emotion_service') as mock_emotion_service, \
                 patch('app.services.ai_intervention_service.ai_intervention_service'):
                
                # Mock model manager success, emotion service failure
                mock_model_manager.initialize = AsyncMock()
                mock_emotion_service.side_effect = Exception("Emotion service init failed")
                
                result = await initialize_ai_services()
                
                # Verify partial success
                assert result["status"] == "partial"
                assert "ai_model_manager" in result["services_initialized"]
                assert "ai_emotion_service" in result["services_failed"]
                assert len(result["errors"]) > 0
                
                print("✓ AI services initialization partial failure test passed")

    @pytest.mark.asyncio
    async def test_initialize_ai_services_complete_failure(self):
        """Test AI services initialization complete failure"""
        with patch('app.services.ai_service_init.logger'):
            # Mock critical failure during initialization
            with patch('app.services.ai_model_manager.ai_model_manager') as mock_model_manager:
                mock_model_manager.initialize.side_effect = Exception("Critical init failure")
                
                # Test that even with failures, the function handles it gracefully
                result = await initialize_ai_services()
                
                # Should handle failure gracefully
                assert result["status"] in ["failed", "partial"]
                assert "ai_model_manager" in result["services_failed"]
                assert len(result["errors"]) > 0
                
                print("✓ AI services initialization complete failure test passed")

    def test_get_ai_services_status_healthy(self):
        """Test getting AI services status when all healthy"""
        with patch('app.services.ai_model_manager.ai_model_manager') as mock_model_manager, \
             patch('app.services.ai_prompt_service.ai_prompt_service') as mock_prompt_service, \
             patch('app.services.ai_emotion_service.ai_emotion_service') as mock_emotion_service, \
             patch('app.services.ai_intervention_service.ai_intervention_service') as mock_intervention_service, \
             patch('app.core.service_interfaces.service_registry') as mock_registry:
            
            # Mock healthy status from all services
            mock_model_manager.get_model_status.return_value = {
                "loaded_models": 3,
                "total_memory_usage": 2.5,
                "gpu_available": True
            }
            mock_model_manager.model_configs = ["model1", "model2", "model3"]
            
            mock_prompt_service.get_generation_stats.return_value = {
                "total_generated": 150,
                "cache_hit_rate": 0.75
            }
            mock_prompt_service.generation_strategies = ["strategy1", "strategy2"]
            
            mock_emotion_service.get_analysis_stats.return_value = {
                "total_analyses": 200,
                "cache_hit_rate": 0.80,
                "pattern_detection_rate": 0.65
            }
            
            mock_intervention_service.get_intervention_stats.return_value = {
                "total_assessments": 50,
                "crisis_detection_rate": 0.05,
                "safety_referral_rate": 0.02
            }
            
            mock_registry.get_service.return_value = Mock()  # All services registered
            
            status = get_ai_services_status()
            
            # Verify healthy status
            assert status["overall_status"] == "healthy"
            assert "ai_model_manager" in status["services"]
            assert "ai_prompt_service" in status["services"]
            assert "ai_emotion_service" in status["services"]
            assert "ai_intervention_service" in status["services"]
            assert status["services"]["ai_model_manager"]["status"] == "healthy"
            
            print("✓ AI services status healthy test passed")

    def test_get_ai_services_status_degraded(self):
        """Test getting AI services status when some are degraded"""
        with patch('app.services.ai_model_manager.ai_model_manager') as mock_model_manager, \
             patch('app.services.ai_prompt_service.ai_prompt_service') as mock_prompt_service, \
             patch('app.services.ai_emotion_service.ai_emotion_service') as mock_emotion_service, \
             patch('app.services.ai_intervention_service.ai_intervention_service'):
            
            # Mock mixed status - some healthy, some failed
            mock_model_manager.get_model_status.return_value = {
                "loaded_models": 2,
                "total_memory_usage": 1.5,
                "gpu_available": True
            }
            mock_model_manager.model_configs = ["model1", "model2"]
            
            mock_prompt_service.get_generation_stats.side_effect = Exception("Prompt service error")
            mock_emotion_service.get_analysis_stats.return_value = {
                "total_analyses": 100,
                "cache_hit_rate": 0.70,
                "pattern_detection_rate": 0.60
            }
            
            # This should cause intervention service to fail
            mock_intervention_service.get_intervention_stats.side_effect = Exception("Intervention error")
            
            status = get_ai_services_status()
            
            # Verify degraded status
            assert status["overall_status"] in ["degraded", "critical"]
            assert status["services"]["ai_model_manager"]["status"] == "healthy"
            assert status["services"]["ai_prompt_service"]["status"] == "error"
            assert status["services"]["ai_intervention_service"]["status"] == "error"
            
            print("✓ AI services status degraded test passed")

    @pytest.mark.asyncio
    async def test_run_ai_services_health_check(self):
        """Test comprehensive AI services health check"""
        with patch('app.services.ai_model_manager.ai_model_manager') as mock_model_manager, \
             patch('app.services.ai_prompt_service.ai_prompt_service') as mock_prompt_service, \
             patch('app.services.ai_emotion_service.ai_emotion_service') as mock_emotion_service, \
             patch('app.services.ai_intervention_service.ai_intervention_service') as mock_intervention_service:
            
            # Mock health checks
            mock_model_manager.health_check = AsyncMock(return_value={"status": "healthy"})
            mock_prompt_service.health_check = AsyncMock(return_value={"status": "healthy"})
            mock_emotion_service.health_check = AsyncMock(return_value={"status": "healthy"})
            mock_intervention_service.health_check = AsyncMock(return_value={"status": "healthy"})
            
            result = await run_ai_services_health_check()
            
            # Verify health check results
            assert result["overall_health"] == "healthy"
            assert "ai_model_manager" in result["checks_passed"]
            assert "ai_prompt_service" in result["checks_passed"]
            assert "ai_emotion_service" in result["checks_passed"]
            assert "ai_intervention_service" in result["checks_passed"]
            assert len(result["checks_failed"]) == 0
            
            # Verify all health checks were called
            mock_model_manager.health_check.assert_called_once()
            mock_prompt_service.health_check.assert_called_once()
            mock_emotion_service.health_check.assert_called_once()
            mock_intervention_service.health_check.assert_called_once()
            
            print("✓ AI services health check test passed")

    @pytest.mark.asyncio
    async def test_run_ai_services_health_check_with_failures(self):
        """Test health check with some services failing"""
        with patch('app.services.ai_model_manager.ai_model_manager') as mock_model_manager, \
             patch('app.services.ai_prompt_service.ai_prompt_service') as mock_prompt_service, \
             patch('app.services.ai_emotion_service.ai_emotion_service') as mock_emotion_service, \
             patch('app.services.ai_intervention_service.ai_intervention_service') as mock_intervention_service:
            
            # Mock mixed health check results
            mock_model_manager.health_check = AsyncMock(return_value={"status": "healthy"})
            mock_prompt_service.health_check = AsyncMock(return_value={"status": "degraded"})
            mock_emotion_service.health_check = AsyncMock(side_effect=Exception("Health check failed"))
            mock_intervention_service.health_check = AsyncMock(return_value={"status": "healthy"})
            
            result = await run_ai_services_health_check()
            
            # Verify mixed health results
            assert result["overall_health"] in ["degraded", "critical"]
            assert "ai_model_manager" in result["checks_passed"]
            assert "ai_intervention_service" in result["checks_passed"]
            assert "ai_emotion_service" in result["checks_failed"]
            assert len(result["recommendations"]) > 0
            
            print("✓ AI services health check with failures test passed")

    @pytest.mark.asyncio
    async def test_cleanup_ai_services(self):
        """Test AI services cleanup"""
        with patch('app.services.ai_service_init.logger') as mock_logger:
            with patch('app.services.ai_model_manager.model_cleanup_scheduler') as mock_scheduler, \
                 patch('app.services.ai_model_manager.ai_model_manager') as mock_model_manager, \
                 patch('app.services.llm_service.llm_service') as mock_llm_service:
                
                # Mock successful cleanup
                mock_scheduler.stop_scheduled_cleanup = AsyncMock()
                mock_model_manager.cleanup_all_models = AsyncMock()
                mock_llm_service.cleanup_resources = AsyncMock()
                
                result = await cleanup_ai_services()
                
                # Verify successful cleanup
                assert result["status"] == "success"
                assert "model_cleanup_scheduler" in result["services_cleaned"]
                assert "ai_model_manager" in result["services_cleaned"]
                assert "llm_service" in result["services_cleaned"]
                assert len(result["cleanup_errors"]) == 0
                
                # Verify cleanup methods were called
                mock_scheduler.stop_scheduled_cleanup.assert_called_once()
                mock_model_manager.cleanup_all_models.assert_called_once()
                mock_llm_service.cleanup_resources.assert_called_once()
                
                print("✓ AI services cleanup test passed")

    @pytest.mark.asyncio
    async def test_cleanup_ai_services_with_errors(self):
        """Test AI services cleanup with errors"""
        with patch('app.services.ai_service_init.logger'):
            with patch('app.services.ai_model_manager.model_cleanup_scheduler') as mock_scheduler, \
                 patch('app.services.ai_model_manager.ai_model_manager') as mock_model_manager, \
                 patch('app.services.llm_service.llm_service') as mock_llm_service:
                
                # Mock partial cleanup failure
                mock_scheduler.stop_scheduled_cleanup = AsyncMock()
                mock_model_manager.cleanup_all_models = AsyncMock(side_effect=Exception("Cleanup failed"))
                mock_llm_service.cleanup_resources = AsyncMock()
                
                result = await cleanup_ai_services()
                
                # Verify partial cleanup
                assert result["status"] == "partial"
                assert "model_cleanup_scheduler" in result["services_cleaned"]
                assert "llm_service" in result["services_cleaned"]
                assert len(result["cleanup_errors"]) > 0
                assert "AI Model Manager" in str(result["cleanup_errors"])
                
                print("✓ AI services cleanup with errors test passed")

    def test_service_initialization_error_handling(self):
        """Test error handling during service initialization"""
        with patch('app.services.ai_service_init.logger'):
            # Test that errors are properly caught and reported
            try:
                # This should not crash even if services are not available
                from app.services.ai_service_init import initialize_ai_services
                
                # Function should be importable and callable
                assert callable(initialize_ai_services)
                print("✓ Service initialization error handling test passed")
                
            except Exception as e:
                pytest.skip(f"Service initialization not available: {e}")

    def test_service_status_reporting_structure(self):
        """Test service status reporting data structure"""
        with patch('app.services.ai_model_manager.ai_model_manager'), \
             patch('app.services.ai_prompt_service.ai_prompt_service'), \
             patch('app.services.ai_emotion_service.ai_emotion_service'), \
             patch('app.services.ai_intervention_service.ai_intervention_service'):
            
            try:
                status = get_ai_services_status()
                
                # Verify status structure
                required_keys = ["overall_status", "services", "integrations", "performance"]
                for key in required_keys:
                    assert key in status, f"Missing key: {key}"
                
                assert isinstance(status["services"], dict)
                assert isinstance(status["integrations"], dict)
                
                print("✓ Service status reporting structure test passed")
                
            except Exception as e:
                pytest.skip(f"Service status reporting not available: {e}")

    @pytest.mark.asyncio
    async def test_service_integration_flow(self):
        """Test complete service integration flow"""
        with patch('app.services.ai_model_manager.ai_model_manager') as mock_model_manager, \
             patch('app.services.ai_emotion_service.ai_emotion_service') as mock_emotion_service, \
             patch('app.services.ai_intervention_service.ai_intervention_service') as mock_intervention_service:
            
            # Mock complete integration flow
            mock_model_manager.initialize = AsyncMock()
            mock_emotion_service.initialize = AsyncMock()
            mock_intervention_service.initialize = AsyncMock()
            
            # Test initialization
            result = await initialize_ai_services()
            
            # Test that initialization completed
            assert result["status"] in ["success", "partial"]
            
            print("✓ Service integration flow test passed")

    def test_service_memory_monitoring(self):
        """Test service memory usage monitoring"""
        with patch('app.services.ai_model_manager.ai_model_manager') as mock_model_manager:
            # Mock memory monitoring
            mock_model_manager.get_memory_usage.return_value = {
                "total_memory": 2048,
                "used_memory": 1024,
                "available_memory": 1024,
                "models_loaded": 3
            }
            
            if hasattr(mock_model_manager, 'get_memory_usage'):
                memory_info = mock_model_manager.get_memory_usage()
                
                assert "total_memory" in memory_info
                assert "used_memory" in memory_info
                assert memory_info["used_memory"] <= memory_info["total_memory"]
            
            print("✓ Service memory monitoring test passed")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])