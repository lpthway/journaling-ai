"""
Admin API for Journaling AI
Provides administrative functions for database and cache management.
"""

import logging
from fastapi import APIRouter, HTTPException
from app.services.redis_service_simple import simple_redis_service
from app.services.vector_service import vector_service
import chromadb

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/cache/flush")
async def flush_redis_cache():
    """
    Flush all Redis cache data
    
    ⚠️ WARNING: This will delete ALL cached data!
    """
    try:
        logger.warning("🗑️ Admin request: Flushing Redis cache")
        success = await simple_redis_service.flush_db()
        
        if success:
            return {
                "success": True,
                "message": "Redis cache successfully flushed",
                "action": "cache_flush"
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail="Failed to flush Redis cache"
            )
            
    except Exception as e:
        logger.error(f"Error flushing Redis cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to flush cache: {str(e)}"
        )

@router.post("/vector/clear")
async def clear_vector_database():
    """
    Clear all vector database collections
    
    ⚠️ WARNING: This will delete ALL vector embeddings!
    """
    try:
        logger.warning("🗑️ Admin request: Clearing vector database")
        
        # Delete the journal entries collection if it exists
        try:
            vector_service.client.delete_collection("journal_entries")
            logger.info("Deleted 'journal_entries' collection")
        except Exception as e:
            logger.info(f"Collection 'journal_entries' not found or already deleted: {e}")
        
        # Recreate the collection to ensure clean state
        vector_service.collection = vector_service.client.get_or_create_collection(
            name="journal_entries",
            metadata={"hnsw:space": "cosine"}
        )
        
        return {
            "success": True,
            "message": "Vector database successfully cleared",
            "action": "vector_clear",
            "collections_reset": ["journal_entries"]
        }
        
    except Exception as e:
        logger.error(f"Error clearing vector database: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear vector database: {str(e)}"
        )

@router.post("/full-reset")
async def full_system_reset():
    """
    Perform a complete system reset
    
    ⚠️ WARNING: This will delete ALL data from:
    - Redis cache
    - Vector database
    Note: PostgreSQL data must be cleared separately via API endpoints
    """
    try:
        logger.warning("🚨 Admin request: Full system reset initiated")
        
        results = {
            "success": True,
            "actions_completed": [],
            "errors": []
        }
        
        # Clear Redis cache
        try:
            cache_success = await simple_redis_service.flush_db()
            if cache_success:
                results["actions_completed"].append("redis_cache_flushed")
            else:
                results["errors"].append("Failed to flush Redis cache")
        except Exception as e:
            results["errors"].append(f"Redis flush error: {str(e)}")
        
        # Clear vector database
        try:
            vector_service.client.delete_collection("journal_entries")
            vector_service.collection = vector_service.client.get_or_create_collection(
                name="journal_entries",
                metadata={"hnsw:space": "cosine"}
            )
            results["actions_completed"].append("vector_database_cleared")
        except Exception as e:
            results["errors"].append(f"Vector clear error: {str(e)}")
        
        if results["errors"]:
            results["success"] = False
            
        return results
        
    except Exception as e:
        logger.error(f"Error during full system reset: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to complete system reset: {str(e)}"
        )

@router.get("/status")
async def get_admin_status():
    """Get status of all data stores"""
    try:
        status = {
            "redis": {"status": "unknown", "details": {}},
            "vector": {"status": "unknown", "details": {}},
            "postgresql": {"status": "available", "details": "Use /entries/, /sessions/, /topics/ endpoints"}
        }
        
        # Check Redis
        try:
            await simple_redis_service.ping()
            status["redis"]["status"] = "connected"
            status["redis"]["details"] = {"connection": "active"}
        except Exception as e:
            status["redis"]["status"] = "error"
            status["redis"]["details"] = {"error": str(e)}
        
        # Check Vector database
        try:
            collections = vector_service.client.list_collections()
            status["vector"]["status"] = "connected"
            status["vector"]["details"] = {
                "collections": [col.name for col in collections],
                "count": len(collections)
            }
        except Exception as e:
            status["vector"]["status"] = "error"
            status["vector"]["details"] = {"error": str(e)}
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting admin status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )
