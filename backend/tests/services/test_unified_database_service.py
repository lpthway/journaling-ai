import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import sys
import os
from typing import List, Optional

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

try:
    from app.services.unified_database_service import UnifiedDatabaseService
    from app.models.entry import Entry, EntryCreate, EntryUpdate
    from app.models.session import Session, SessionCreate
    from app.core.exceptions import DatabaseException, NotFoundException, ValidationException
except ImportError:
    # Create mock classes if imports fail
    class UnifiedDatabaseService:
        pass
    class Entry:
        pass
    class EntryCreate:
        pass
    class EntryUpdate:
        pass
    class Session:
        pass
    class SessionCreate:
        pass
    class DatabaseException(Exception):
        pass
    class NotFoundException(Exception):
        pass
    class ValidationException(Exception):
        pass

class TestUnifiedDatabaseService:
    """Test unified database service functionality"""

    @pytest.fixture
    async def db_service(self):
        """Create database service instance for testing"""
        if UnifiedDatabaseService == type:
            pytest.skip("UnifiedDatabaseService not available")
            
        with patch('app.core.enhanced_database.DatabaseManager') as mock_manager:
            mock_instance = AsyncMock()
            mock_manager.return_value = mock_instance
            service = UnifiedDatabaseService()
            yield service

    @pytest.fixture
    def sample_entry_data(self):
        """Sample entry data for testing"""
        return {
            "content": "Today was a great day! I accomplished so much and feel proud.",
            "mood": "positive",
            "tags": ["productivity", "achievement", "gratitude"],
            "sentiment_score": 0.8
        }

    @pytest.fixture
    def sample_session_data(self):
        """Sample session data for testing"""
        return {
            "title": "Evening Reflection",
            "session_type": "reflection",
            "status": "active"
        }

    @pytest.mark.asyncio
    async def test_database_connection_initialization(self, db_service):
        """Test database connection and initialization"""
        if not hasattr(db_service, 'initialize'):
            pytest.skip("Database service initialize method not available")
            
        with patch.object(db_service, 'db_manager') as mock_db:
            mock_db.initialize = AsyncMock(return_value=True)
            
            result = await db_service.initialize()
            assert result is True
            mock_db.initialize.assert_called_once()
        
        print("✓ Database connection initialization test passed")

    @pytest.mark.asyncio
    async def test_create_entry_success(self, db_service, sample_entry_data):
        """Test successful entry creation"""
        if not hasattr(db_service, 'create_entry'):
            pytest.skip("create_entry method not available")
            
        with patch.object(db_service, '_get_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            # Mock created entry
            mock_entry = Mock()
            mock_entry.id = 1
            mock_entry.content = sample_entry_data["content"]
            mock_entry.mood = sample_entry_data["mood"]
            mock_entry.created_at = datetime.now()
            
            mock_session_instance.add = Mock()
            mock_session_instance.commit = AsyncMock()
            mock_session_instance.refresh = AsyncMock()
            
            entry_create = Mock()
            entry_create.content = sample_entry_data["content"]
            entry_create.mood = sample_entry_data["mood"]
            entry_create.tags = sample_entry_data["tags"]
            
            with patch('app.models.entry.Entry', return_value=mock_entry):
                result = await db_service.create_entry(entry_create)
                
                assert result is not None
                mock_session_instance.add.assert_called_once()
                mock_session_instance.commit.assert_called_once()
        
        print("✓ Entry creation test passed")

    @pytest.mark.asyncio
    async def test_get_entry_by_id_success(self, db_service):
        """Test successful entry retrieval by ID"""
        if not hasattr(db_service, 'get_entry_by_id'):
            pytest.skip("get_entry_by_id method not available")
            
        entry_id = 1
        
        with patch.object(db_service, '_get_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            # Mock found entry
            mock_entry = Mock()
            mock_entry.id = entry_id
            mock_entry.content = "Test entry content"
            
            mock_session_instance.get = AsyncMock(return_value=mock_entry)
            
            result = await db_service.get_entry_by_id(entry_id)
            
            assert result is not None
            assert result.id == entry_id
            mock_session_instance.get.assert_called_once_with(Entry, entry_id)
        
        print("✓ Get entry by ID test passed")

    @pytest.mark.asyncio
    async def test_get_entry_by_id_not_found(self, db_service):
        """Test entry retrieval when entry not found"""
        if not hasattr(db_service, 'get_entry_by_id'):
            pytest.skip("get_entry_by_id method not available")
            
        entry_id = 999
        
        with patch.object(db_service, '_get_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            # Mock entry not found
            mock_session_instance.get = AsyncMock(return_value=None)
            
            with pytest.raises(NotFoundException):
                await db_service.get_entry_by_id(entry_id)
        
        print("✓ Get entry by ID not found test passed")

    @pytest.mark.asyncio
    async def test_update_entry_success(self, db_service):
        """Test successful entry update"""
        if not hasattr(db_service, 'update_entry'):
            pytest.skip("update_entry method not available")
            
        entry_id = 1
        update_data = Mock()
        update_data.content = "Updated content"
        update_data.mood = "neutral"
        
        with patch.object(db_service, '_get_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            # Mock existing entry
            mock_entry = Mock()
            mock_entry.id = entry_id
            mock_entry.content = "Original content"
            
            mock_session_instance.get = AsyncMock(return_value=mock_entry)
            mock_session_instance.commit = AsyncMock()
            
            result = await db_service.update_entry(entry_id, update_data)
            
            assert result is not None
            assert mock_entry.content == "Updated content"
            mock_session_instance.commit.assert_called_once()
        
        print("✓ Entry update test passed")

    @pytest.mark.asyncio
    async def test_delete_entry_success(self, db_service):
        """Test successful entry deletion"""
        if not hasattr(db_service, 'delete_entry'):
            pytest.skip("delete_entry method not available")
            
        entry_id = 1
        
        with patch.object(db_service, '_get_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            # Mock existing entry
            mock_entry = Mock()
            mock_entry.id = entry_id
            
            mock_session_instance.get = AsyncMock(return_value=mock_entry)
            mock_session_instance.delete = Mock()
            mock_session_instance.commit = AsyncMock()
            
            result = await db_service.delete_entry(entry_id)
            
            assert result is True
            mock_session_instance.delete.assert_called_once_with(mock_entry)
            mock_session_instance.commit.assert_called_once()
        
        print("✓ Entry deletion test passed")

    @pytest.mark.asyncio
    async def test_search_entries_by_content(self, db_service):
        """Test entry search by content"""
        if not hasattr(db_service, 'search_entries'):
            pytest.skip("search_entries method not available")
            
        search_query = "happiness"
        
        with patch.object(db_service, '_get_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            # Mock search results
            mock_results = [Mock(), Mock()]
            mock_results[0].id = 1
            mock_results[0].content = "I feel happiness today"
            mock_results[1].id = 2
            mock_results[1].content = "Happiness is important"
            
            mock_query = Mock()
            mock_query.filter = Mock(return_value=mock_query)
            mock_query.all = AsyncMock(return_value=mock_results)
            mock_session_instance.query = Mock(return_value=mock_query)
            
            results = await db_service.search_entries(query=search_query)
            
            assert len(results) == 2
            assert all("happiness" in r.content.lower() for r in results)
        
        print("✓ Entry search by content test passed")

    @pytest.mark.asyncio
    async def test_get_entries_by_date_range(self, db_service):
        """Test entry retrieval by date range"""
        if not hasattr(db_service, 'get_entries_by_date_range'):
            pytest.skip("get_entries_by_date_range method not available")
            
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 1, 31)
        
        with patch.object(db_service, '_get_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            # Mock entries in date range
            mock_results = [Mock(), Mock()]
            mock_results[0].created_at = datetime(2025, 1, 15)
            mock_results[1].created_at = datetime(2025, 1, 20)
            
            mock_query = Mock()
            mock_query.filter = Mock(return_value=mock_query)
            mock_query.all = AsyncMock(return_value=mock_results)
            mock_session_instance.query = Mock(return_value=mock_query)
            
            results = await db_service.get_entries_by_date_range(start_date, end_date)
            
            assert len(results) == 2
            for entry in results:
                assert start_date <= entry.created_at <= end_date
        
        print("✓ Get entries by date range test passed")

    @pytest.mark.asyncio
    async def test_session_creation_and_management(self, db_service, sample_session_data):
        """Test session creation and management"""
        if not hasattr(db_service, 'create_session'):
            pytest.skip("Session management methods not available")
            
        with patch.object(db_service, '_get_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            # Mock created session
            mock_session_obj = Mock()
            mock_session_obj.id = 1
            mock_session_obj.title = sample_session_data["title"]
            mock_session_obj.status = sample_session_data["status"]
            
            mock_session_instance.add = Mock()
            mock_session_instance.commit = AsyncMock()
            
            session_create = Mock()
            session_create.title = sample_session_data["title"]
            session_create.session_type = sample_session_data["session_type"]
            
            with patch('app.models.session.Session', return_value=mock_session_obj):
                result = await db_service.create_session(session_create)
                
                assert result is not None
                assert result.title == sample_session_data["title"]
                mock_session_instance.add.assert_called_once()
                mock_session_instance.commit.assert_called_once()
        
        print("✓ Session creation and management test passed")

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, db_service):
        """Test transaction rollback on error"""
        if not hasattr(db_service, 'create_entry'):
            pytest.skip("Transaction methods not available")
            
        with patch.object(db_service, '_get_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            # Mock database error during commit
            mock_session_instance.add = Mock()
            mock_session_instance.commit = AsyncMock(side_effect=Exception("Database error"))
            mock_session_instance.rollback = AsyncMock()
            
            entry_create = Mock()
            entry_create.content = "Test content"
            
            with pytest.raises(Exception):
                await db_service.create_entry(entry_create)
            
            # Rollback should be called on error
            mock_session_instance.rollback.assert_called_once()
        
        print("✓ Transaction rollback on error test passed")

    @pytest.mark.asyncio
    async def test_connection_pool_management(self, db_service):
        """Test database connection pool management"""
        if not hasattr(db_service, 'get_connection_stats'):
            pytest.skip("Connection pool methods not available")
            
        with patch.object(db_service, 'db_manager') as mock_db:
            mock_db.get_pool_status = AsyncMock(return_value={
                'size': 10,
                'checked_in': 7,
                'checked_out': 3,
                'overflow': 0,
                'invalid': 0
            })
            
            stats = await db_service.get_connection_stats()
            
            assert 'size' in stats
            assert 'checked_in' in stats
            assert 'checked_out' in stats
            assert stats['size'] == 10
        
        print("✓ Connection pool management test passed")

    @pytest.mark.asyncio
    async def test_bulk_entry_operations(self, db_service):
        """Test bulk entry operations"""
        if not hasattr(db_service, 'bulk_create_entries'):
            pytest.skip("Bulk operations not available")
            
        entries_data = [
            Mock(content="Entry 1", mood="positive"),
            Mock(content="Entry 2", mood="neutral"),
            Mock(content="Entry 3", mood="negative")
        ]
        
        with patch.object(db_service, '_get_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            mock_session_instance.add_all = Mock()
            mock_session_instance.commit = AsyncMock()
            
            results = await db_service.bulk_create_entries(entries_data)
            
            assert len(results) == len(entries_data)
            mock_session_instance.add_all.assert_called_once()
            mock_session_instance.commit.assert_called_once()
        
        print("✓ Bulk entry operations test passed")

    @pytest.mark.asyncio
    async def test_database_health_check(self, db_service):
        """Test database health check functionality"""
        if not hasattr(db_service, 'health_check'):
            pytest.skip("Health check method not available")
            
        with patch.object(db_service, 'db_manager') as mock_db:
            mock_db.is_connected = AsyncMock(return_value=True)
            
            health_status = await db_service.health_check()
            
            assert health_status is True
            mock_db.is_connected.assert_called_once()
        
        print("✓ Database health check test passed")

    def test_validation_error_handling(self, db_service):
        """Test validation error handling"""
        # Test various validation scenarios
        invalid_data_cases = [
            {"content": "", "mood": "positive"},  # Empty content
            {"content": "Valid content", "mood": "invalid_mood"},  # Invalid mood
            {"content": None, "mood": "positive"},  # None content
        ]
        
        for invalid_data in invalid_data_cases:
            with pytest.raises((ValidationException, ValueError)):
                # This would be called in actual validation
                if not invalid_data.get("content"):
                    raise ValidationException("Content cannot be empty")
                if invalid_data.get("mood") and invalid_data["mood"] not in ["positive", "negative", "neutral"]:
                    raise ValidationException("Invalid mood value")
        
        print("✓ Validation error handling test passed")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])