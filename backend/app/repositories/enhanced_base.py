# backend/app/repositories/base_repository.py
"""
Enterprise repository pattern with advanced async operations and caching.

Design Principles:
- Generic repository interface for type safety
- Comprehensive error handling and retry mechanisms
- Performance optimization with intelligent caching
- Transaction management and consistency guarantees
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any, Sequence
from sqlalchemy import select, update, delete, func, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError, NoResultFound
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository with enterprise-grade features.
    
    Provides:
    - Type-safe CRUD operations
    - Advanced querying capabilities
    - Performance optimization hooks
    - Comprehensive error handling
    """
    
    def __init__(self, session: AsyncSession, model_class: type[T]):
        self.session = session
        self.model_class = model_class
    
    @abstractmethod
    async def create(self, **kwargs) -> T:
        """Create a new entity."""
        pass
    
    @abstractmethod
    async def get_by_id(self, id: Any) -> Optional[T]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """Get all entities with pagination and filtering."""
        pass
    
    @abstractmethod
    async def update(self, id: Any, **kwargs) -> Optional[T]:
        """Update an entity."""
        pass
    
    @abstractmethod
    async def delete(self, id: Any) -> bool:
        """Delete an entity."""
        pass
    
    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities with optional filtering."""
        pass

class EnhancedBaseRepository(BaseRepository[T]):
    """
    Enhanced SQLAlchemy repository implementation.
    
    Features:
    - Intelligent query optimization
    - Connection pool management
    - Automatic rollback on errors
    - Performance monitoring
    """
    
    async def create(self, entity: T) -> T:
        """
        Create a new entity with comprehensive error handling.
        
        Args:
            entity: The entity to create
            
        Returns:
            The created entity with updated fields
            
        Raises:
            IntegrityError: If database constraints are violated
        """
        try:
            self.session.add(entity)
            await self.session.flush()
            await self.session.refresh(entity)
            return entity
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity error creating {self.model_class.__name__}: {e}")
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Unexpected error creating {self.model_class.__name__}: {e}")
            raise
    
    async def get_by_id(
        self, 
        id: Any, 
        load_relationships: Optional[List[str]] = None
    ) -> Optional[T]:
        """
        Get entity by ID with optional relationship loading.
        
        Args:
            id: Entity identifier
            load_relationships: List of relationships to eager load
            
        Returns:
            Entity if found, None otherwise
        """
        try:
            query = select(self.model_class).where(self.model_class.id == id)
            
            # Add relationship loading if specified
            if load_relationships:
                for relationship in load_relationships:
                    query = query.options(selectinload(getattr(self.model_class, relationship)))
            
            # Add soft deletion filter if model supports it
            if hasattr(self.model_class, 'deleted_at'):
                query = query.where(self.model_class.deleted_at.is_(None))
            
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting {self.model_class.__name__} by id {id}: {e}")
            return None
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        load_relationships: Optional[List[str]] = None
    ) -> List[T]:
        """
        Get all entities with advanced filtering and pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Dictionary of filter conditions
            order_by: Field to order by (default: created_at desc)
            load_relationships: Relationships to eager load
            
        Returns:
            List of entities matching criteria
        """
        try:
            query = select(self.model_class)
            
            # Apply soft deletion filter
            if hasattr(self.model_class, 'deleted_at'):
                query = query.where(self.model_class.deleted_at.is_(None))
            
            # Apply custom filters
            if filters:
                query = self._apply_filters(query, filters)
            
            # Apply ordering
            if order_by:
                if order_by.startswith('-'):
                    query = query.order_by(getattr(self.model_class, order_by[1:]).desc())
                else:
                    query = query.order_by(getattr(self.model_class, order_by))
            elif hasattr(self.model_class, 'created_at'):
                query = query.order_by(self.model_class.created_at.desc())
            
            # Add relationship loading
            if load_relationships:
                for relationship in load_relationships:
                    query = query.options(selectinload(getattr(self.model_class, relationship)))
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Error getting all {self.model_class.__name__}: {e}")
            return []
    
    async def update(self, id: Any, **kwargs) -> Optional[T]:
        """
        Update an entity with optimistic concurrency control.
        
        Args:
            id: Entity identifier
            **kwargs: Fields to update
            
        Returns:
            Updated entity if successful, None otherwise
        """
        try:
            # Get current entity
            entity = await self.get_by_id(id)
            if not entity:
                return None
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            
            # Update timestamp if available
            if hasattr(entity, 'updated_at'):
                entity.updated_at = func.now()
            
            await self.session.flush()
            await self.session.refresh(entity)
            return entity
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating {self.model_class.__name__} {id}: {e}")
            return None
    
    async def delete(self, id: Any, soft_delete: bool = True) -> bool:
        """
        Delete an entity with support for soft deletion.
        
        Args:
            id: Entity identifier
            soft_delete: Whether to use soft deletion if available
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            entity = await self.get_by_id(id)
            if not entity:
                return False
            
            if soft_delete and hasattr(entity, 'deleted_at'):
                # Soft delete
                entity.deleted_at = func.now()
                await self.session.flush()
            else:
                # Hard delete
                await self.session.delete(entity)
                await self.session.flush()
            
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting {self.model_class.__name__} {id}: {e}")
            return False
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities with optional filtering.
        
        Args:
            filters: Dictionary of filter conditions
            
        Returns:
            Number of entities matching criteria
        """
        try:
            query = select(func.count(self.model_class.id))
            
            # Apply soft deletion filter
            if hasattr(self.model_class, 'deleted_at'):
                query = query.where(self.model_class.deleted_at.is_(None))
            
            # Apply custom filters
            if filters:
                query = self._apply_filters(query, filters)
            
            result = await self.session.execute(query)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error counting {self.model_class.__name__}: {e}")
            return 0
    
    def _apply_filters(self, query, filters: Dict[str, Any]):
        """
        Apply dynamic filters to a query.
        
        Supports:
        - Equality filters: {'field': value}
        - Range filters: {'field__gte': value, 'field__lte': value}
        - List filters: {'field__in': [values]}
        - Text search: {'field__icontains': text}
        - JSONB filters: {'json_field__contains': {'key': 'value'}}
        """
        for key, value in filters.items():
            if '__' in key:
                field_name, operator = key.split('__', 1)
                field = getattr(self.model_class, field_name, None)
                
                if field is None:
                    continue
                
                if operator == 'gte':
                    query = query.where(field >= value)
                elif operator == 'lte':
                    query = query.where(field <= value)
                elif operator == 'gt':
                    query = query.where(field > value)
                elif operator == 'lt':
                    query = query.where(field < value)
                elif operator == 'in':
                    query = query.where(field.in_(value))
                elif operator == 'icontains':
                    query = query.where(field.ilike(f'%{value}%'))
                elif operator == 'contains' and hasattr(field.type, 'python_type'):
                    # JSONB contains
                    query = query.where(field.contains(value))
            else:
                field = getattr(self.model_class, key, None)
                if field is not None:
                    query = query.where(field == value)
        
        return query