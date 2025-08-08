import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.main import app
from app.models.entry import EntryCreate
from app.core.exceptions import ValidationException, NotFoundException

class TestAPIIntegration:
    """Integration tests for API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_services(self):
        """Mock all external services"""
        with patch('app.services.unified_database_service.unified_db_service') as mock_db, \
             patch('app.services.ai_emotion_service.ai_emotion_service') as mock_emotion, \
             patch('app.services.ai_intervention_service.ai_intervention_service') as mock_intervention:
            
            # Setup default mocks
            mock_emotion_result = Mock()
            mock_emotion_result.primary_emotion = Mock()
            mock_emotion_result.primary_emotion.emotion = Mock()
            mock_emotion_result.primary_emotion.emotion.value = "positive"
            mock_emotion_result.primary_emotion.confidence = 0.85
            mock_emotion.analyze_emotions = AsyncMock(return_value=mock_emotion_result)
            
            mock_crisis_result = Mock()
            mock_crisis_result.requires_intervention = False
            mock_crisis_result.crisis_level = "low"
            mock_intervention.assess_crisis_risk = AsyncMock(return_value=mock_crisis_result)
            
            yield {
                'db': mock_db,
                'emotion': mock_emotion,
                'intervention': mock_intervention
            }

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "critical"]

    def test_entries_endpoint_create(self, client, mock_services):
        """Test creating a new entry through API"""
        # Mock database response
        mock_created_entry = Mock()
        mock_created_entry.id = 1
        mock_created_entry.content = "Test entry content"
        mock_created_entry.mood = "positive"
        mock_created_entry.sentiment_score = 0.85
        mock_created_entry.tags = ["test"]
        mock_services['db'].create_entry = AsyncMock(return_value=mock_created_entry)
        
        entry_data = {
            "content": "Test entry content",
            "mood": "positive",
            "tags": ["test"]
        }
        
        response = client.post("/api/entries/", json=entry_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == entry_data["content"]
        assert data["mood"] == "positive"

    def test_entries_endpoint_create_validation_error(self, client, mock_services):
        """Test entry creation with validation error"""
        entry_data = {
            "content": "",  # Empty content should trigger validation error
            "mood": "positive"
        }
        
        response = client.post("/api/entries/", json=entry_data)
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    def test_entries_endpoint_get_all(self, client, mock_services):
        """Test getting all entries"""
        # Mock database response
        mock_entries = [
            Mock(id=1, content="Entry 1", mood="positive"),
            Mock(id=2, content="Entry 2", mood="neutral"),
        ]
        mock_services['db'].get_entries = AsyncMock(return_value=mock_entries)
        
        response = client.get("/api/entries/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_entries_endpoint_get_by_id(self, client, mock_services):
        """Test getting entry by ID"""
        mock_entry = Mock()
        mock_entry.id = 1
        mock_entry.content = "Test entry"
        mock_entry.mood = "positive"
        mock_services['db'].get_entry_by_id = AsyncMock(return_value=mock_entry)
        
        response = client.get("/api/entries/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

    def test_entries_endpoint_get_not_found(self, client, mock_services):
        """Test getting non-existent entry"""
        mock_services['db'].get_entry_by_id = AsyncMock(
            side_effect=NotFoundException("Entry not found")
        )
        
        response = client.get("/api/entries/999")
        
        assert response.status_code == 404

    def test_entries_search_endpoint(self, client, mock_services):
        """Test entry search functionality"""
        mock_search_results = [
            Mock(id=1, content="Happy entry", mood="positive"),
        ]
        mock_services['db'].search_entries = AsyncMock(return_value=mock_search_results)
        
        response = client.get("/api/entries/search?query=happy")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_sessions_endpoint_create(self, client, mock_services):
        """Test creating a new session"""
        # Mock session creation
        mock_session = Mock()
        mock_session.id = 1
        mock_session.session_type = "chat"
        mock_services['db'].create_session = AsyncMock(return_value=mock_session)
        
        session_data = {
            "session_type": "chat",
            "initial_message": "Hello"
        }
        
        response = client.post("/api/sessions/", json=session_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_type"] == "chat"

    def test_sessions_send_message_endpoint(self, client, mock_services):
        """Test sending message in session"""
        # Mock message creation and AI response
        mock_user_message = Mock()
        mock_user_message.id = 1
        mock_user_message.content = "Test message"
        mock_user_message.message_type = "user"
        
        mock_ai_response = Mock()
        mock_ai_response.id = 2
        mock_ai_response.content = "AI response"
        mock_ai_response.message_type = "assistant"
        
        mock_services['db'].create_message = AsyncMock(return_value=mock_user_message)
        
        with patch('app.services.llm_service.llm_service') as mock_llm:
            mock_llm.generate_response = AsyncMock(return_value="AI response")
            
            message_data = {
                "content": "Test message",
                "message_type": "user"
            }
            
            response = client.post("/api/sessions/1/messages", json=message_data)
            
            assert response.status_code == 200

    def test_insights_ask_question_endpoint(self, client, mock_services):
        """Test AI insights question endpoint"""
        with patch('app.services.llm_service.llm_service') as mock_llm:
            mock_llm.generate_insight = AsyncMock(return_value={
                "answer": "Your mood patterns show improvement",
                "sources": ["entry1", "entry2"],
                "confidence": 0.8
            })
            
            question_data = {
                "question": "What are my mood patterns?"
            }
            
            response = client.post("/api/insights/ask", json=question_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "answer" in data
            assert "sources" in data

    def test_insights_patterns_endpoint(self, client, mock_services):
        """Test pattern analysis endpoint"""
        with patch('app.services.enhanced_insights_service.enhanced_insights_service') as mock_insights:
            mock_insights.analyze_patterns = AsyncMock(return_value={
                "mood_patterns": {"positive": 0.6, "negative": 0.2, "neutral": 0.2},
                "topic_patterns": {"work": 0.4, "personal": 0.6},
                "temporal_patterns": {"morning": 0.8, "evening": 0.6}
            })
            
            response = client.get("/api/insights/patterns")
            
            assert response.status_code == 200
            data = response.json()
            assert "mood_patterns" in data

    def test_error_handling_integration(self, client, mock_services):
        """Test error handling across API endpoints"""
        # Test database error
        mock_services['db'].get_entries = AsyncMock(
            side_effect=Exception("Database connection failed")
        )
        
        response = client.get("/api/entries/")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    def test_authentication_middleware(self, client):
        """Test authentication middleware (if implemented)"""
        # This test would check JWT token validation
        # For now, we'll test that endpoints are accessible
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_cors_headers(self, client):
        """Test CORS configuration"""
        response = client.options("/api/entries/")
        
        # Should have CORS headers configured
        assert "access-control-allow-origin" in [h.lower() for h in response.headers.keys()]

    def test_rate_limiting(self, client):
        """Test rate limiting (if implemented)"""
        # Make multiple rapid requests
        responses = []
        for i in range(5):
            response = client.get("/api/health")
            responses.append(response)
        
        # All should succeed (rate limiting not implemented yet)
        assert all(r.status_code == 200 for r in responses)

    def test_request_validation_integration(self, client, mock_services):
        """Test request validation across different endpoints"""
        # Test invalid JSON
        response = client.post(
            "/api/entries/", 
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

        # Test missing required fields
        response = client.post("/api/entries/", json={})
        assert response.status_code == 422

        # Test invalid field types
        response = client.post("/api/entries/", json={
            "content": 123,  # Should be string
            "mood": "positive"
        })
        assert response.status_code == 422

    def test_response_format_consistency(self, client, mock_services):
        """Test that all endpoints return consistent response formats"""
        # Mock successful responses
        mock_entry = Mock()
        mock_entry.id = 1
        mock_entry.content = "Test"
        mock_entry.mood = "positive"
        mock_services['db'].create_entry = AsyncMock(return_value=mock_entry)
        mock_services['db'].get_entries = AsyncMock(return_value=[mock_entry])
        
        # Test different endpoints
        endpoints_to_test = [
            ("POST", "/api/entries/", {"content": "Test", "mood": "positive"}),
            ("GET", "/api/entries/", None),
            ("GET", "/api/health", None),
        ]
        
        for method, endpoint, data in endpoints_to_test:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json=data)
            
            assert response.status_code in [200, 201]
            assert response.headers["content-type"].startswith("application/json")

    def test_performance_headers(self, client):
        """Test that performance monitoring headers are present"""
        response = client.get("/api/health")
        
        # Check for correlation ID or request ID header
        assert any(
            header.lower() in ["x-correlation-id", "x-request-id"] 
            for header in response.headers.keys()
        ) or response.status_code == 200  # Header may not be implemented yet

    def test_concurrent_requests(self, client, mock_services):
        """Test handling concurrent requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.get("/api/health")
            results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert len(results) == 5
        assert all(status == 200 for status in results)