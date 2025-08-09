# backend/app/repositories/base_cached_repository.py
"""
Enhanced Repository Pattern with Redis Caching Integration
Provides consistent data access with automatic caching layer
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from contextlib import asynccontextmanager
import json
import logging
import hashlib
from datetime import timedelta

from app.core.service_interfaces import CacheableServiceInterface, CacheStrategy, service_registry
from app.core.exceptions import RepositoryException, NotFoundException
from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T')

class CachedRepositoryMixin(Generic[T]):
    """
    Mixin providing caching capabilities to repositories
    Integrates seamlessly with Redis without tight coupling
    """
    
    def __init__(self, session: AsyncSession, model_class: type[T], cache_prefix: str):
        self.session = session
        self.model_class = model_class
        self.cache_prefix = cache_prefix
        self._cache_strategy = service_registry.get_cache_strategy()
    
    def _get_cache_key(self, key: str) -> str:
        """Generate cache key with prefix"""
        return f"{self.cache_prefix}:{key}"
    
    def _get_list_cache_key(self, filters: Dict[str, Any]) -> str:
        """Generate cache key for list queries"""
        from datetime import datetime
        import uuid
        
        # Convert filters to JSON-serializable format
        serializable_filters = {}
        for key, value in filters.items():
            if isinstance(value, datetime):
                serializable_filters[key] = value.isoformat()
            elif isinstance(value, uuid.UUID):
                serializable_filters[key] = str(value)
            else:
                serializable_filters[key] = value
        
        filter_hash = hashlib.md5(json.dumps(serializable_filters, sort_keys=True).encode()).hexdigest()
        return f"{self.cache_prefix}:list:{filter_hash}"
    
    async def _get_from_cache(self, key: str) -> Optional[T]:
        """Get entity from cache"""
        if not self._cache_strategy:
            return None
        
        try:
            cache_key = self._get_cache_key(key)
            cached_data = await self._cache_strategy.get(cache_key)
            
            if cached_data:
                # Deserialize cached entity
                return self._deserialize_entity(cached_data)
            
            return None
            
        except Exception as e:
            logger.warning(f"Cache get error for {key}: {e}")
            return None
    
    async def _set_cache(self, key: str, entity: T, ttl: Optional[int] = None) -> None:
        """Set entity in cache"""
        if not self._cache_strategy:
            return
        
        try:
            cache_key = self._get_cache_key(key)
            serialized_data = self._serialize_entity(entity)
            await self._cache_strategy.set(cache_key, serialized_data, ttl)
            
        except Exception as e:
            logger.warning(f"Cache set error for {key}: {e}")
    
    async def _invalidate_cache(self, key: str) -> None:
        """Invalidate specific cache key"""
        if not self._cache_strategy:
            return
        
        try:
            cache_key = self._get_cache_key(key)
            await self._cache_strategy.delete(cache_key)
            
        except Exception as e:
            logger.warning(f"Cache invalidation error for {key}: {e}")
    
    async def _invalidate_cache_pattern(self, pattern: str) -> None:
        """Invalidate cache keys matching pattern"""
        if not self._cache_strategy:
            return
        
        try:
            cache_pattern = f"{self.cache_prefix}:{pattern}"
            await self._cache_strategy.invalidate_pattern(cache_pattern)
            
        except Exception as e:
            logger.warning(f"Cache pattern invalidation error for {pattern}: {e}")
    
    def _serialize_entity(self, entity: T) -> Dict[str, Any]:
        """Serialize entity for caching"""
        from datetime import datetime, date
        import uuid
        
        # Convert SQLAlchemy model to dictionary with JSON-serializable values
        if hasattr(entity, '__table__'):
            result = {}
            for c in entity.__table__.columns:
                value = getattr(entity, c.name)
                # Handle different data types for JSON serialization
                if value is None:
                    result[c.name] = None
                elif isinstance(value, (datetime, date)):
                    result[c.name] = value.isoformat()
                elif isinstance(value, uuid.UUID):
                    result[c.name] = str(value)
                elif isinstance(value, (dict, list)):
                    result[c.name] = value  # Already JSON serializable
                else:
                    result[c.name] = value
            return result
        return entity.__dict__
    
    def _deserialize_entity(self, data: Dict[str, Any]) -> T:
        """Deserialize entity from cache"""
        from datetime import datetime
        import uuid
        
        # Convert data back to proper types
        processed_data = {}
        for key, value in data.items():
            if value is None:
                processed_data[key] = None
            elif isinstance(value, str):
                # Try to convert ISO datetime strings back to datetime objects
                if 'T' in value and len(value) > 10:  # Likely datetime ISO string
                    try:
                        processed_data[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except ValueError:
                        # If it's not a datetime, treat as regular string
                        # Also try to convert UUID strings back to UUID
                        try:
                            processed_data[key] = uuid.UUID(value)
                        except ValueError:
                            processed_data[key] = value
                else:
                    processed_data[key] = value
            else:
                processed_data[key] = value
        
        # Create entity instance from processed data
        return self.model_class(**processed_data)

class EnhancedBaseRepository(CachedRepositoryMixin[T], CacheableServiceInterface[T]):
    """
    Enhanced base repository with caching and consistent interface
    Ready for Redis integration in Phase 0B
    """
    
    def __init__(self, session: AsyncSession, model_class: type[T], cache_prefix: str):
        super().__init__(session, model_class, cache_prefix)
        
        # Cache configuration
        self.default_ttl = getattr(settings, 'CACHE_DEFAULT_TTL', 3600)  # 1 hour
        self.list_cache_ttl = getattr(settings, 'CACHE_LIST_TTL', 300)   # 5 minutes
    
    async def get_by_id(self, id: str, use_cache: bool = True) -> Optional[T]:
        """Get entity by ID with optional caching"""
        try:
            # Try cache first
            if use_cache:
                cached_entity = await self._get_from_cache(str(id))
                if cached_entity:
                    logger.debug(f"Cache hit for {self.model_class.__name__}:{id}")
                    return cached_entity
            
            # Query database
            stmt = select(self.model_class).where(getattr(self.model_class, 'id') == id)
            result = await self.session.execute(stmt)
            entity = result.scalar_one_or_none()
            
            # Cache the result
            if entity and use_cache:
                await self._set_cache(str(id), entity, self.default_ttl)
                logger.debug(f"Cached {self.model_class.__name__}:{id}")
            
            return entity
            
        except Exception as e:
            logger.error(f"Error getting {self.model_class.__name__} by ID {id}: {e}")
            raise RepositoryException(f"Failed to get entity by ID", context={"id": id, "error": str(e)})
    
    async def create(self, data: Dict[str, Any], invalidate_cache: bool = True) -> T:
        """Create entity with cache invalidation"""
        try:
            # Create entity
            entity = self.model_class(**data)
            self.session.add(entity)
            await self.session.flush()
            await self.session.refresh(entity)
            
            # Cache the new entity
            entity_id = getattr(entity, 'id', None)
            if entity_id:
                await self._set_cache(str(entity_id), entity, self.default_ttl)
            
            # Invalidate list caches
            if invalidate_cache:
                await self._invalidate_cache_pattern("list:*")
            
            logger.info(f"Created {self.model_class.__name__}:{entity_id}")
            return entity
            
        except Exception as e:
            logger.error(f"Error creating {self.model_class.__name__}: {e}")
            raise RepositoryException(f"Failed to create entity", context={"data": data, "error": str(e)})
    
    async def update(self, id: str, data: Dict[str, Any], invalidate_cache: bool = True) -> Optional[T]:
        """Update entity with cache invalidation"""
        try:
            # Get existing entity
            entity = await self.get_by_id(id, use_cache=False)  # Skip cache for update
            if not entity:
                return None
            
            # Update entity
            for key, value in data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            
            await self.session.flush()
            await self.session.refresh(entity)
            
            # Update cache
            await self._set_cache(str(id), entity, self.default_ttl)
            
            # Invalidate related caches
            if invalidate_cache:
                await self._invalidate_cache_pattern("list:*")
            
            logger.info(f"Updated {self.model_class.__name__}:{id}")
            return entity
            
        except Exception as e:
            logger.error(f"Error updating {self.model_class.__name__} {id}: {e}")
            raise RepositoryException(f"Failed to update entity", context={"id": id, "data": data, "error": str(e)})
    
    async def delete(self, id: str, invalidate_cache: bool = True) -> bool:
        """Delete entity with cache invalidation"""
        try:
            # Check if entity exists
            entity = await self.get_by_id(id, use_cache=False)
            if not entity:
                return False
            
            # Soft delete if supported
            if hasattr(entity, 'deleted_at'):
                entity.deleted_at = func.now()
                await self.session.flush()
            else:
                # Hard delete
                await self.session.delete(entity)
                await self.session.flush()
            
            # Remove from cache
            await self._invalidate_cache(str(id))
            
            # Invalidate related caches
            if invalidate_cache:
                await self._invalidate_cache_pattern("list:*")
            
            logger.info(f"Deleted {self.model_class.__name__}:{id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting {self.model_class.__name__} {id}: {e}")
            raise RepositoryException(f"Failed to delete entity", context={"id": id, "error": str(e)})
    
    async def search(self, filters: Dict[str, Any], use_cache: bool = True) -> List[T]:
        """Search entities with optional caching"""
        try:
            # Try cache first
            cache_key = None
            if use_cache:
                cache_key = self._get_list_cache_key(filters)
                cached_results = await self._cache_strategy.get(cache_key) if self._cache_strategy else None
                
                if cached_results:
                    logger.debug(f"Cache hit for {self.model_class.__name__} search")
                    return [self._deserialize_entity(data) for data in cached_results]
            
            # Build query
            stmt = select(self.model_class)
            
            # Apply filters, skipping special keys
            skip_value = 0
            limit_value = None
            
            for key, value in filters.items():
                # Handle special keys
                if key.startswith('_'):
                    if key == '_skip':
                        skip_value = value
                    elif key == '_limit':
                        limit_value = value
                    continue
                
                # Handle comparison operators
                if '__' in key:
                    field_name, operator = key.split('__', 1)
                    if hasattr(self.model_class, field_name):
                        column = getattr(self.model_class, field_name)
                        if operator == 'gte':
                            stmt = stmt.where(column >= value)
                        elif operator == 'lte':
                            stmt = stmt.where(column <= value)
                        elif operator == 'gt':
                            stmt = stmt.where(column > value)
                        elif operator == 'lt':
                            stmt = stmt.where(column < value)
                        elif operator == 'like':
                            stmt = stmt.where(column.like(f"%{value}%"))
                        elif operator == 'ilike':
                            stmt = stmt.where(column.ilike(f"%{value}%"))
                    continue
                
                # Handle direct column matches
                if hasattr(self.model_class, key):
                    column = getattr(self.model_class, key)
                    if isinstance(value, list):
                        stmt = stmt.where(column.in_(value))
                    else:
                        stmt = stmt.where(column == value)
            
            # Apply pagination
            if skip_value:
                stmt = stmt.offset(skip_value)
            if limit_value:
                stmt = stmt.limit(limit_value)
            
            # Execute query
            result = await self.session.execute(stmt)
            entities = list(result.scalars().all())
            
            # Cache results
            if use_cache and cache_key and self._cache_strategy:
                serialized_results = [self._serialize_entity(entity) for entity in entities]
                await self._cache_strategy.set(cache_key, serialized_results, self.list_cache_ttl)
                logger.debug(f"Cached {self.model_class.__name__} search results")
            
            return entities
            
        except Exception as e:
            logger.error(f"Error searching {self.model_class.__name__}: {e}")
            raise RepositoryException(f"Failed to search entities", context={"filters": filters, "error": str(e)})

class RepositoryFactory:
    """
    Factory for creating repository instances with consistent caching
    """
    
    @staticmethod
    def create_repository(session: AsyncSession, model_class: type[T], cache_prefix: str) -> EnhancedBaseRepository[T]:
        """Create repository instance with caching capabilities"""
        return EnhancedBaseRepository(session, model_class, cache_prefix)
    
    @staticmethod
    def create_entry_repository(session: AsyncSession) -> 'EnhancedEntryRepository':
        """Create entry repository with specialized methods"""
        from app.repositories.enhanced_entry_repository import EnhancedEntryRepository
        return EnhancedEntryRepository(session)
    
    @staticmethod
    def create_session_repository(session: AsyncSession) -> 'EnhancedSessionRepository':
        """Create session repository with specialized methods"""
        from app.repositories.enhanced_session_repository import EnhancedSessionRepository
        return EnhancedSessionRepository(session)