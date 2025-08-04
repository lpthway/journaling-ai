# backend/app/services/enhanced_database_adapter.py
"""
Enhanced Database Adapter for gradual transition from JSON to PostgreSQL.

This adapter maintains backward compatibility while introducing enhanced architecture.
Uses dual-write pattern during transition period.
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Enhanced architecture imports
from app.core.exceptions import DatabaseException, ValidationException, NotFoundException
from app.core.enhanced_database import DatabaseManager, DatabaseConfig
from app.repositories.enhanced_base import EnhancedBaseRepository
from app.repositories.entry_repository import EntryRepository
from app.repositories.session_repository import SessionRepository
from app.models.enhanced_models import Entry, ChatSession, User
from app.core.config import settings

# Legacy model imports for backward compatibility
from app.models.entry import Entry, EntryCreate, EntryUpdate, MoodType
from app.models.topic import Topic, TopicCreate, TopicUpdate

logger = logging.getLogger(__name__)

class EnhancedDatabaseAdapter:
    """
    Enhanced database adapter that provides:
    - Backward compatibility with existing JSON storage
    - Gradual transition to PostgreSQL with enhanced architecture
    - Dual-write pattern during migration
    - Enterprise-grade error handling and logging
    """
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.entries_file = self.data_dir / "entries.json"
        self.topics_file = self.data_dir / "topics.json"
        self.sessions_file = self.data_dir / "sessions.json"
        
        # Enhanced database manager with configuration
        db_config = DatabaseConfig(
            url=settings.DATABASE_URL,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=30,  # Default value since it's not in config
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_pre_ping=True,  # Default value since it's not in config
            echo=settings.DB_ECHO
        )
        self.db_manager = DatabaseManager(db_config)
        self._initialized = False
        
        # Legacy file initialization
        self.data_dir.mkdir(exist_ok=True)
        self._init_files()
    
    async def initialize(self):
        """Initialize enhanced database components."""
        if not self._initialized:
            try:
                await self.db_manager.initialize()
                self._initialized = True
                logger.info("Enhanced database adapter initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize enhanced database: {e}")
                raise DatabaseException(
                    "Database initialization failed",
                    context={"error": str(e)}
                )
    
    def _init_files(self):
        """Initialize JSON files if they don't exist (legacy support)."""
        for file_path in [self.entries_file, self.topics_file, self.sessions_file]:
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump([], f)
    
    # === ENHANCED ENTRY OPERATIONS ===
    
    async def create_entry(self, entry_data: EntryCreate) -> Entry:
        """Create entry with enhanced architecture and dual-write."""
        try:
            await self.initialize()
            
            # Use enhanced repository for PostgreSQL
            async with self.db_manager.get_session() as session:
                entry_repo = EntryRepository(session)
                
                # Convert legacy model to enhanced model
                enhanced_entry = Entry(
                    title=entry_data.title,
                    content=entry_data.content,
                    mood_score=entry_data.mood.value if entry_data.mood else None,
                    tags=entry_data.tags or [],
                    categories=entry_data.categories or [],
                    user_id="default_user"  # For single-user system
                )
                
                # Create in PostgreSQL with enhanced error handling
                created_entry = await entry_repo.create(enhanced_entry)
                
                # Dual-write to JSON (during transition)
                if settings.ENABLE_DUAL_WRITE:
                    await self._write_to_json(entry_data, "entries")
                
                # Convert back to legacy format for API compatibility
                return self._convert_to_legacy_entry(created_entry)
                
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Error creating entry: {e}")
            raise DatabaseException(
                "Failed to create entry",
                context={"entry_data": entry_data.dict(), "error": str(e)}
            )
    
    async def get_entry(self, entry_id: str) -> Optional[Entry]:
        """Get entry with enhanced error handling."""
        try:
            await self.initialize()
            
            async with self.db_manager.get_session() as session:
                entry_repo = EntryRepository(session)
                
                # Use enhanced repository with eager loading
                enhanced_entry = await entry_repo.get_by_id(
                    entry_id,
                    load_relationships=['user']
                )
                
                if not enhanced_entry:
                    return None
                
                return self._convert_to_legacy_entry(enhanced_entry)
                
        except Exception as e:
            logger.error(f"Error getting entry {entry_id}: {e}")
            raise DatabaseException(
                "Failed to retrieve entry",
                context={"entry_id": entry_id, "error": str(e)}
            )
    
    async def get_entries(
        self,
        skip: int = 0,
        limit: int = 100,
        topic_filter: Optional[str] = None,
        mood_filter: Optional[MoodType] = None
    ) -> List[Entry]:
        """Get entries with enhanced filtering and pagination."""
        try:
            await self.initialize()
            
            async with self.db_manager.get_session() as session:
                entry_repo = EntryRepository(session)
                
                # Build filters
                filters = {"user_id": "default_user"}
                if mood_filter:
                    filters["mood_score"] = mood_filter.value
                
                # Use enhanced repository with optimization
                enhanced_entries = await entry_repo.get_all(
                    skip=skip,
                    limit=limit,
                    filters=filters,
                    order_by="-created_at",
                    load_relationships=['user']
                )
                
                # Convert to legacy format
                return [
                    self._convert_to_legacy_entry(entry) 
                    for entry in enhanced_entries
                ]
                
        except Exception as e:
            logger.error(f"Error getting entries: {e}")
            raise DatabaseException(
                "Failed to retrieve entries",
                context={"filters": {"skip": skip, "limit": limit}, "error": str(e)}
            )
    
    # === ENHANCED SESSION OPERATIONS ===
    
    async def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create chat session with enhanced architecture."""
        try:
            await self.initialize()
            
            async with self.db_manager.get_session() as session:
                session_repo = SessionRepository(session)
                
                # Create enhanced session
                enhanced_session = ChatSession(
                    title=session_data.get("title", "New Session"),
                    session_type=session_data.get("session_type", "general"),
                    context=session_data.get("context", {}),
                    user_id="default_user"
                )
                
                created_session = await session_repo.create(enhanced_session)
                
                # Dual-write to JSON
                if settings.ENABLE_DUAL_WRITE:
                    await self._write_to_json(session_data, "sessions")
                
                return self._convert_to_legacy_session(created_session)
                
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise DatabaseException(
                "Failed to create session",
                context={"session_data": session_data, "error": str(e)}
            )
    
    # === CONVERSION UTILITIES ===
    
    def _convert_to_legacy_entry(self, enhanced_entry: Entry) -> Entry:
        """Convert enhanced model to legacy format for API compatibility."""
        return Entry(
            id=str(enhanced_entry.id),
            title=enhanced_entry.title or "",
            content=enhanced_entry.content,
            created_at=enhanced_entry.created_at,
            updated_at=enhanced_entry.updated_at,
            mood=MoodType(enhanced_entry.mood_score) if enhanced_entry.mood_score else None,
            tags=enhanced_entry.tags or [],
            categories=enhanced_entry.categories or [],
            word_count=enhanced_entry.word_count or 0,
            topic_id=None  # Legacy compatibility
        )
    
    def _convert_to_legacy_session(self, enhanced_session: ChatSession) -> Dict[str, Any]:
        """Convert enhanced session to legacy format."""
        return {
            "id": str(enhanced_session.id),
            "title": enhanced_session.title,
            "session_type": enhanced_session.session_type,
            "context": enhanced_session.context or {},
            "created_at": enhanced_session.created_at.isoformat(),
            "updated_at": enhanced_session.updated_at.isoformat(),
            "is_active": enhanced_session.is_active,
            "message_count": enhanced_session.message_count or 0
        }
    
    async def _write_to_json(self, data: Any, file_type: str):
        """Write to JSON file for dual-write pattern."""
        try:
            file_map = {
                "entries": self.entries_file,
                "sessions": self.sessions_file,
                "topics": self.topics_file
            }
            
            file_path = file_map.get(file_type)
            if not file_path:
                return
            
            # Read existing data
            existing_data = []
            if file_path.exists():
                with open(file_path, 'r') as f:
                    existing_data = json.load(f)
            
            # Add new data
            if hasattr(data, 'dict'):
                existing_data.append(data.dict())
            else:
                existing_data.append(data)
            
            # Write back
            with open(file_path, 'w') as f:
                json.dump(existing_data, f, indent=2, default=str)
                
        except Exception as e:
            logger.warning(f"Failed to write to JSON file {file_type}: {e}")
    
    # === HEALTH CHECK ===
    
    async def health_check(self) -> Dict[str, Any]:
        """Enhanced health check for both PostgreSQL and JSON systems."""
        health_status = {
            "status": "healthy",
            "components": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Check PostgreSQL
            await self.initialize()
            pg_health = await self.db_manager.health_check()
            health_status["components"]["postgresql"] = {
                "status": "healthy" if pg_health else "unhealthy",
                "enhanced_architecture": True
            }
        except Exception as e:
            health_status["components"]["postgresql"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Check JSON files
        try:
            json_healthy = all(
                file.exists() 
                for file in [self.entries_file, self.topics_file, self.sessions_file]
            )
            health_status["components"]["json_storage"] = {
                "status": "healthy" if json_healthy else "unhealthy",
                "dual_write_enabled": settings.ENABLE_DUAL_WRITE
            }
        except Exception as e:
            health_status["components"]["json_storage"] = {
                "status": "unhealthy", 
                "error": str(e)
            }
        
        return health_status

# Global enhanced adapter instance
enhanced_db_service = EnhancedDatabaseAdapter()
