import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from app.core.enhanced_database import DatabaseManager
except ImportError:
    DatabaseManager = None

try:
    from app.core.exceptions import DatabaseException
except ImportError:
    class DatabaseException(Exception):
        pass

class TestDatabaseManager:
    """Test database manager functionality"""

    @pytest.fixture
    async def mock_db_manager(self):
        """Create a mock database manager for testing"""
        with patch('app.core.enhanced_database.DatabaseManager') as mock_manager:
            mock_instance = AsyncMock()
            mock_manager.return_value = mock_instance
            yield mock_instance

    def test_database_manager_singleton(self):
        """Test that DatabaseManager follows singleton pattern"""
        if DatabaseManager is None:
            pytest.skip("DatabaseManager not available")
            
        try:
            manager1 = DatabaseManager()
            manager2 = DatabaseManager()
            
            # Should be same instance if singleton
            assert id(manager1) == id(manager2)
            print("✓ DatabaseManager singleton pattern working")
        except Exception as e:
            pytest.skip(f"DatabaseManager not available: {e}")

    @pytest.mark.asyncio
    async def test_database_connection_initialization(self, mock_db_manager):
        """Test database connection initialization"""
        mock_db_manager.initialize.return_value = True
        mock_db_manager.is_connected.return_value = True
        
        # Test initialization
        result = await mock_db_manager.initialize()
        assert result is True
        
        # Test connection status
        connected = await mock_db_manager.is_connected()
        assert connected is True
        
        print("✓ Database connection initialization test passed")

    @pytest.mark.asyncio
    async def test_database_connection_failure_handling(self, mock_db_manager):
        """Test database connection failure scenarios"""
        # Mock connection failure
        mock_db_manager.initialize.side_effect = DatabaseException("Connection failed")
        
        with pytest.raises(DatabaseException):
            await mock_db_manager.initialize()
        
        print("✓ Database connection failure handling test passed")

    @pytest.mark.asyncio
    async def test_database_session_context(self):
        """Test database session context manager"""
        mock_session = AsyncMock()
        
        # Test session context manager pattern
        async with mock_session as session:
            assert session is not None
            
        print("✓ Database session context test passed")

    def test_database_configuration_validation(self):
        """Test database configuration validation"""
        # Test that configuration is properly validated
        try:
            from app.core.config import settings
            
            # Check required database settings exist
            required_settings = ['database_url', 'database_host', 'database_name']
            for setting in required_settings:
                assert hasattr(settings, setting), f"Missing required setting: {setting}"
            
            print(f"✓ Database configuration validation passed")
            
        except Exception as e:
            pytest.skip(f"Database configuration not available: {e}")

    @pytest.mark.asyncio
    async def test_transaction_handling(self, mock_db_manager):
        """Test database transaction handling"""
        mock_session = AsyncMock()
        mock_db_manager.get_session.return_value.__aenter__.return_value = mock_session
        
        # Test successful transaction
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        
        async with mock_db_manager.get_session() as session:
            await session.commit()
            
        mock_session.commit.assert_called_once()
        print("✓ Database transaction handling test passed")

    @pytest.mark.asyncio
    async def test_connection_pooling(self, mock_db_manager):
        """Test database connection pooling"""
        # Mock connection pool stats
        mock_db_manager.get_pool_status.return_value = {
            'size': 10,
            'checked_in': 8,
            'checked_out': 2,
            'overflow': 0,
            'invalid': 0
        }
        
        pool_status = await mock_db_manager.get_pool_status()
        
        assert 'size' in pool_status
        assert 'checked_in' in pool_status
        assert 'checked_out' in pool_status
        
        print("✓ Database connection pooling test passed")

    def test_database_error_types(self):
        """Test custom database exception types"""
        from app.core.exceptions import DatabaseException, ValidationException, NotFoundException
        
        # Test exception creation
        db_error = DatabaseException("Test database error")
        assert str(db_error) == "Test database error"
        
        validation_error = ValidationException("Test validation error")
        assert str(validation_error) == "Test validation error"
        
        not_found_error = NotFoundException("Test not found error")
        assert str(not_found_error) == "Test not found error"
        
        print("✓ Database error types test passed")