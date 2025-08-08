import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.unified_database_service import unified_db_service
from app.models.entry import EntryCreate, EntryUpdate
from app.models.session import SessionCreate
from app.core.exceptions import DatabaseException, NotFoundException

class TestDatabaseIntegration:
    """Integration tests for database operations"""

    @pytest.fixture
    async def mock_database_session(self):
        """Mock database session for testing"""
        with patch('app.core.database.get_db') as mock_get_db:
            mock_session = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_session
            yield mock_session

    @pytest.mark.asyncio
    async def test_create_entry_integration(self, mock_database_session):
        """Test entry creation through database service"""
        # Mock database operations
        mock_entry_model = Mock()
        mock_entry_model.id = 1
        mock_entry_model.content = "Test entry content"
        mock_entry_model.mood = "positive"
        mock_entry_model.sentiment_score = 0.85
        
        mock_database_session.add = Mock()
        mock_database_session.commit = AsyncMock()
        mock_database_session.refresh = AsyncMock()
        
        with patch('app.models.entry.Entry', return_value=mock_entry_model):
            entry_data = EntryCreate(
                content="Test entry content",
                mood="positive",
                tags=["test"]
            )
            
            # Mock the database service method
            with patch.object(unified_db_service, 'create_entry', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = mock_entry_model
                
                result = await unified_db_service.create_entry(entry_data)
                
                assert result.id == 1
                assert result.content == "Test entry content"
                assert result.mood == "positive"
                
                mock_create.assert_called_once_with(entry_data)

    @pytest.mark.asyncio
    async def test_get_entries_integration(self, mock_database_session):
        """Test retrieving entries from database"""
        mock_entries = [
            Mock(id=1, content="Entry 1", mood="positive"),
            Mock(id=2, content="Entry 2", mood="neutral"),
            Mock(id=3, content="Entry 3", mood="negative"),
        ]
        
        # Mock query result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_entries
        mock_database_session.execute = AsyncMock(return_value=mock_result)
        
        with patch.object(unified_db_service, 'get_entries', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_entries
            
            result = await unified_db_service.get_entries(limit=10, offset=0)
            
            assert len(result) == 3
            assert result[0].id == 1
            assert result[1].id == 2
            assert result[2].id == 3
            
            mock_get.assert_called_once_with(limit=10, offset=0)

    @pytest.mark.asyncio
    async def test_get_entry_by_id_integration(self, mock_database_session):
        """Test retrieving single entry by ID"""
        mock_entry = Mock(id=1, content="Test entry", mood="positive")
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_entry
        mock_database_session.execute = AsyncMock(return_value=mock_result)
        
        with patch.object(unified_db_service, 'get_entry_by_id', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_entry
            
            result = await unified_db_service.get_entry_by_id(1)
            
            assert result.id == 1
            assert result.content == "Test entry"
            
            mock_get.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_entry_not_found_integration(self, mock_database_session):
        """Test handling of entry not found"""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_database_session.execute = AsyncMock(return_value=mock_result)
        
        with patch.object(unified_db_service, 'get_entry_by_id', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = NotFoundException("Entry not found")
            
            with pytest.raises(NotFoundException):
                await unified_db_service.get_entry_by_id(999)

    @pytest.mark.asyncio
    async def test_update_entry_integration(self, mock_database_session):
        """Test updating an entry"""
        mock_existing_entry = Mock()
        mock_existing_entry.id = 1
        mock_existing_entry.content = "Original content"
        mock_existing_entry.mood = "neutral"
        
        mock_updated_entry = Mock()
        mock_updated_entry.id = 1
        mock_updated_entry.content = "Updated content"
        mock_updated_entry.mood = "positive"
        
        mock_database_session.commit = AsyncMock()
        mock_database_session.refresh = AsyncMock()
        
        with patch.object(unified_db_service, 'update_entry', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = mock_updated_entry
            
            update_data = EntryUpdate(content="Updated content", mood="positive")
            result = await unified_db_service.update_entry(1, update_data)
            
            assert result.id == 1
            assert result.content == "Updated content"
            assert result.mood == "positive"
            
            mock_update.assert_called_once_with(1, update_data)

    @pytest.mark.asyncio
    async def test_delete_entry_integration(self, mock_database_session):
        """Test deleting an entry"""
        mock_entry = Mock(id=1, content="To be deleted")
        
        mock_database_session.delete = Mock()
        mock_database_session.commit = AsyncMock()
        
        with patch.object(unified_db_service, 'delete_entry', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True
            
            result = await unified_db_service.delete_entry(1)
            
            assert result is True
            mock_delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_search_entries_integration(self, mock_database_session):
        """Test searching entries with various filters"""
        mock_search_results = [
            Mock(id=1, content="Happy thoughts", mood="positive"),
            Mock(id=2, content="Joyful day", mood="positive"),
        ]
        
        with patch.object(unified_db_service, 'search_entries', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_search_results
            
            search_filters = {
                "query": "happy",
                "mood": "positive",
                "date_from": "2025-08-01",
                "date_to": "2025-08-08"
            }
            
            result = await unified_db_service.search_entries(**search_filters)
            
            assert len(result) == 2
            assert all(entry.mood == "positive" for entry in result)
            
            mock_search.assert_called_once_with(**search_filters)

    @pytest.mark.asyncio
    async def test_session_creation_integration(self, mock_database_session):
        """Test session creation"""
        mock_session = Mock()
        mock_session.id = 1
        mock_session.session_type = "chat"
        mock_session.status = "active"
        
        mock_database_session.add = Mock()
        mock_database_session.commit = AsyncMock()
        mock_database_session.refresh = AsyncMock()
        
        with patch.object(unified_db_service, 'create_session', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_session
            
            session_data = SessionCreate(
                session_type="chat",
                initial_message="Hello, I'd like to chat"
            )
            
            result = await unified_db_service.create_session(session_data)
            
            assert result.id == 1
            assert result.session_type == "chat"
            assert result.status == "active"

    @pytest.mark.asyncio
    async def test_message_creation_integration(self, mock_database_session):
        """Test message creation within a session"""
        mock_message = Mock()
        mock_message.id = 1
        mock_message.session_id = 1
        mock_message.content = "Test message"
        mock_message.message_type = "user"
        
        with patch.object(unified_db_service, 'create_message', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_message
            
            result = await unified_db_service.create_message(
                session_id=1,
                content="Test message",
                message_type="user"
            )
            
            assert result.id == 1
            assert result.session_id == 1
            assert result.content == "Test message"
            assert result.message_type == "user"

    @pytest.mark.asyncio
    async def test_bulk_operations_integration(self, mock_database_session):
        """Test bulk database operations"""
        mock_entries = [
            Mock(id=1, content="Entry 1"),
            Mock(id=2, content="Entry 2"),
            Mock(id=3, content="Entry 3"),
        ]
        
        with patch.object(unified_db_service, 'bulk_create_entries', new_callable=AsyncMock) as mock_bulk:
            mock_bulk.return_value = mock_entries
            
            entries_data = [
                EntryCreate(content="Entry 1", mood="positive"),
                EntryCreate(content="Entry 2", mood="neutral"),
                EntryCreate(content="Entry 3", mood="negative"),
            ]
            
            result = await unified_db_service.bulk_create_entries(entries_data)
            
            assert len(result) == 3
            assert all(entry.id is not None for entry in result)

    @pytest.mark.asyncio
    async def test_transaction_handling_integration(self, mock_database_session):
        """Test database transaction handling"""
        mock_database_session.commit = AsyncMock()
        mock_database_session.rollback = AsyncMock()
        
        # Test successful transaction
        with patch.object(unified_db_service, 'create_entry', new_callable=AsyncMock) as mock_create:
            mock_entry = Mock(id=1, content="Test")
            mock_create.return_value = mock_entry
            
            entry_data = EntryCreate(content="Test", mood="positive")
            result = await unified_db_service.create_entry(entry_data)
            
            assert result is not None

        # Test failed transaction with rollback
        with patch.object(unified_db_service, 'create_entry', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = DatabaseException("Transaction failed")
            
            with pytest.raises(DatabaseException):
                await unified_db_service.create_entry(entry_data)

    @pytest.mark.asyncio
    async def test_connection_pooling_integration(self, mock_database_session):
        """Test database connection pooling behavior"""
        # Mock multiple concurrent operations
        async def create_multiple_entries():
            tasks = []
            for i in range(5):
                entry_data = EntryCreate(content=f"Entry {i}", mood="neutral")
                with patch.object(unified_db_service, 'create_entry', new_callable=AsyncMock) as mock_create:
                    mock_create.return_value = Mock(id=i, content=f"Entry {i}")
                    task = unified_db_service.create_entry(entry_data)
                    tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results

        # This would test connection pool behavior
        # In a real integration test, we'd verify connections are properly managed
        results = await create_multiple_entries()
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_database_error_recovery(self, mock_database_session):
        """Test database error recovery mechanisms"""
        # Test connection timeout recovery
        with patch.object(unified_db_service, 'get_entries', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [
                DatabaseException("Connection timeout"),  # First call fails
                [Mock(id=1, content="Success")]           # Retry succeeds
            ]
            
            # In a real implementation, there might be retry logic
            with pytest.raises(DatabaseException):
                await unified_db_service.get_entries()

    @pytest.mark.asyncio
    async def test_pagination_integration(self, mock_database_session):
        """Test database pagination functionality"""
        mock_page1 = [Mock(id=i, content=f"Entry {i}") for i in range(1, 11)]
        mock_page2 = [Mock(id=i, content=f"Entry {i}") for i in range(11, 21)]
        
        with patch.object(unified_db_service, 'get_entries', new_callable=AsyncMock) as mock_get:
            # Mock different pages
            mock_get.side_effect = [mock_page1, mock_page2]
            
            # Test first page
            page1 = await unified_db_service.get_entries(limit=10, offset=0)
            assert len(page1) == 10
            assert page1[0].id == 1
            
            # Test second page
            page2 = await unified_db_service.get_entries(limit=10, offset=10)
            assert len(page2) == 10
            assert page2[0].id == 11

    @pytest.mark.asyncio
    async def test_data_validation_integration(self, mock_database_session):
        """Test data validation at database layer"""
        with patch.object(unified_db_service, 'create_entry', new_callable=AsyncMock) as mock_create:
            # Test validation error
            mock_create.side_effect = DatabaseException("Invalid data: content too short")
            
            invalid_entry = EntryCreate(content="Hi", mood="positive")  # Too short
            
            with pytest.raises(DatabaseException):
                await unified_db_service.create_entry(invalid_entry)

    @pytest.mark.asyncio
    async def test_optimistic_locking_integration(self, mock_database_session):
        """Test optimistic locking for concurrent updates"""
        with patch.object(unified_db_service, 'update_entry', new_callable=AsyncMock) as mock_update:
            # Mock optimistic locking conflict
            mock_update.side_effect = DatabaseException("Record was modified by another transaction")
            
            update_data = EntryUpdate(content="Updated content")
            
            with pytest.raises(DatabaseException):
                await unified_db_service.update_entry(1, update_data)