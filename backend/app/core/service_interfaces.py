# backend/app/core/service_interfaces.py
"""
Unified Service Interface Pattern for Redis Integration
Provides clean abstraction layer for all data operations
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, TypeVar, Generic
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

T = TypeVar('T')

class CacheableServiceInterface(ABC, Generic[T]):
    """
    Abstract interface for cacheable services
    Enables Redis integration without tight coupling
    """
    
    @abstractmethod
    async def get_by_id(self, id: str, use_cache: bool = True) -> Optional[T]:
        """Get entity by ID with optional caching"""
        pass
    
    @abstractmethod
    async def create(self, data: Dict[str, Any], invalidate_cache: bool = True) -> T:
        """Create entity with cache invalidation"""
        pass
    
    @abstractmethod
    async def update(self, id: str, data: Dict[str, Any], invalidate_cache: bool = True) -> Optional[T]:
        """Update entity with cache invalidation"""
        pass
    
    @abstractmethod
    async def delete(self, id: str, invalidate_cache: bool = True) -> bool:
        """Delete entity with cache invalidation"""
        pass
    
    @abstractmethod
    async def search(self, filters: Dict[str, Any], use_cache: bool = True) -> List[T]:
        """Search entities with optional caching"""
        pass

class CacheStrategy(ABC):
    """
    Abstract caching strategy for Redis integration
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cached value with optional TTL"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete cached value"""
        pass
    
    @abstractmethod
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        pass

class ServiceRegistry:
    """
    Service registry for dependency injection and Redis integration
    """
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._cache_strategy: Optional[CacheStrategy] = None
    
    def register_service(self, name: str, service: Any):
        """Register a service for dependency injection"""
        self._services[name] = service
    
    def get_service(self, name: str) -> Any:
        """Get registered service"""
        if name not in self._services:
            raise ValueError(f"Service '{name}' not registered")
        return self._services[name]
    
    def set_cache_strategy(self, strategy: CacheStrategy):
        """Set global caching strategy for Redis integration"""
        self._cache_strategy = strategy
    
    def get_cache_strategy(self) -> Optional[CacheStrategy]:
        """Get current caching strategy"""
        return self._cache_strategy

# Global service registry for Redis integration
service_registry = ServiceRegistry()