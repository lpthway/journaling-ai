### app/api/topics.py

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from app.models.topic import Topic, TopicCreate, TopicUpdate, TopicResponse
from app.services.unified_database_service import unified_db_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=TopicResponse)
async def create_topic(topic: TopicCreate):
    """Create a new topic"""
    try:
        db_topic = await unified_db_service.create_topic(topic)
        return TopicResponse(**db_topic.model_dump())
        
    except Exception as e:
        logger.error(f"Error creating topic: {e}")
        raise HTTPException(status_code=500, detail="Failed to create topic")

@router.get("/", response_model=List[TopicResponse])
async def get_topics():
    """Get all topics"""
    try:
        topics = await unified_db_service.get_topics()
        return [TopicResponse(**topic.model_dump()) for topic in topics]
        
    except Exception as e:
        logger.error(f"Error getting topics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve topics")

@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(topic_id: str):
    """Get a specific topic"""
    try:
        topic = await unified_db_service.get_topic(topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        
        return TopicResponse(**topic.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve topic")

@router.put("/{topic_id}", response_model=TopicResponse)
async def update_topic(topic_id: str, topic_update: TopicUpdate):
    """Update a topic"""
    try:
        updated_topic = await unified_db_service.update_topic(topic_id, topic_update)
        if not updated_topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        
        return TopicResponse(**updated_topic.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update topic")

@router.delete("/{topic_id}")
async def delete_topic(topic_id: str):
    """Delete a topic"""
    try:
        success = await unified_db_service.delete_topic(topic_id)
        if not success:
            raise HTTPException(status_code=404, detail="Topic not found")
        
        return {"message": "Topic deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete topic")

@router.get("/{topic_id}/entries")
async def get_topic_entries(
    topic_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get all entries for a specific topic"""
    try:
        # Verify topic exists
        topic = await unified_db_service.get_topic(topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        
        # Get entries for this topic
        entries = await unified_db_service.get_entries(skip=skip, limit=limit, topic_id=topic_id)
        
        from app.models.entry import EntryResponse
        return {
            'topic': TopicResponse(**topic.model_dump()),
            'entries': [EntryResponse(**entry.model_dump()) for entry in entries],
            'total_entries': topic.entry_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting entries for topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve topic entries")