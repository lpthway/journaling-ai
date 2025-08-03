### app/api/entries.py

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime, date
from app.models.entry import Entry, EntryCreate, EntryUpdate, EntryResponse
from app.services.database_service import db_service
from app.services.vector_service import vector_service
from app.services.sentiment_service import sentiment_service
from app.services.llm_service import llm_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=EntryResponse)
async def create_entry(entry: EntryCreate):
    """Create a new journal entry with automatic tagging"""
    try:
        # Analyze sentiment
        mood, sentiment_score = sentiment_service.analyze_sentiment(entry.content)
        
        # Generate automatic tags if not provided
        auto_tags = []
        if len(entry.content.strip()) > 10:  # Only tag substantial content
            auto_tags = await llm_service.generate_automatic_tags(entry.content, "journal")
        
        # Combine manual tags with automatic tags, avoiding duplicates
        manual_tags = [tag.lower().strip() for tag in entry.tags] if entry.tags else []
        all_tags = manual_tags.copy()
        
        for auto_tag in auto_tags:
            if auto_tag not in all_tags:
                all_tags.append(auto_tag)
        
        # Limit to 8 tags total
        final_tags = all_tags[:8]
        
        # Update entry with final tags
        entry_with_tags = entry.model_copy()
        entry_with_tags.tags = final_tags
        
        # Create entry in database
        db_entry = await db_service.create_entry(entry_with_tags, mood, sentiment_score)
        
        # Prepare metadata for vector database
        metadata = {
            'entry_id': db_entry.id,
            'title': db_entry.title or '',
            'entry_type': db_entry.entry_type.value,
            'topic_id': db_entry.topic_id or '',
            'mood': db_entry.mood.value if db_entry.mood else 'neutral',
            'sentiment_score': db_entry.sentiment_score or 0.0,
            'created_at': db_entry.created_at.isoformat(),
            'tags': db_entry.tags or [],
            'word_count': db_entry.word_count or 0,
            'auto_tagged': len(auto_tags) > 0  # Track if entry was auto-tagged
        }
        
        await vector_service.add_entry(db_entry.id, db_entry.content, metadata)
        
        return EntryResponse(**db_entry.model_dump())
        
    except Exception as e:
        logger.error(f"Error creating entry: {e}")
        raise HTTPException(status_code=500, detail="Failed to create entry")

@router.get("/", response_model=List[EntryResponse])
async def get_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    topic_id: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None)
):
    """Get journal entries with optional filtering"""
    try:
        # Convert dates to datetime
        datetime_from = datetime.combine(date_from, datetime.min.time()) if date_from else None
        datetime_to = datetime.combine(date_to, datetime.max.time()) if date_to else None
        
        entries = await db_service.get_entries(
            skip=skip, 
            limit=limit, 
            topic_id=topic_id,
            date_from=datetime_from,
            date_to=datetime_to
        )
        
        return [EntryResponse(**entry.model_dump()) for entry in entries]
        
    except Exception as e:
        logger.error(f"Error getting entries: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve entries")

@router.get("/{entry_id}", response_model=EntryResponse)
async def get_entry(entry_id: str):
    """Get a specific journal entry"""
    try:
        entry = await db_service.get_entry(entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        return EntryResponse(**entry.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting entry {entry_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve entry")

@router.put("/{entry_id}", response_model=EntryResponse)
async def update_entry(entry_id: str, entry_update: EntryUpdate):
    """Update a journal entry"""
    try:
        # Check if entry exists
        existing_entry = await db_service.get_entry(entry_id)
        if not existing_entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        # Analyze sentiment if content is being updated
        mood = None
        sentiment_score = None
        if entry_update.content:
            mood, sentiment_score = sentiment_service.analyze_sentiment(entry_update.content)
        
        # Update entry in database
        updated_entry = await db_service.update_entry(entry_id, entry_update, mood, sentiment_score)
        
        # Update vector database
        content_to_index = entry_update.content or existing_entry.content
        metadata = {
            'entry_id': updated_entry.id,
            'title': updated_entry.title or '',
            'entry_type': updated_entry.entry_type.value,
            'topic_id': updated_entry.topic_id or '',
            'mood': updated_entry.mood.value if updated_entry.mood else 'neutral',
            'sentiment_score': updated_entry.sentiment_score or 0.0,
            'created_at': updated_entry.created_at.isoformat(),
            'tags': updated_entry.tags or [],
            'word_count': updated_entry.word_count or 0
        }
        
        await vector_service.update_entry(updated_entry.id, content_to_index, metadata)
        
        return EntryResponse(**updated_entry.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating entry {entry_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update entry")

@router.delete("/{entry_id}")
async def delete_entry(entry_id: str):
    """Delete a journal entry"""
    try:
        # Check if entry exists
        existing_entry = await db_service.get_entry(entry_id)
        if not existing_entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        # Delete from database
        success = await db_service.delete_entry(entry_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete entry")
        
        # Delete from vector database
        await vector_service.delete_entry(entry_id)
        
        return {"message": "Entry deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting entry {entry_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete entry")

@router.get("/search/semantic")
async def search_entries(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    topic_id: Optional[str] = Query(None)
):
    """Search entries using semantic similarity"""
    try:
        filters = {}
        if topic_id:
            filters['topic_id'] = topic_id
        
        results = await vector_service.search_entries(query, limit, filters)
        
        # Enrich results with full entry data
        enriched_results = []
        for result in results:
            entry = await db_service.get_entry(result['id'])
            if entry:
                enriched_results.append({
                    'entry': EntryResponse(**entry.model_dump()),
                    'similarity_score': 1 - result['distance'],  # Convert distance to similarity
                    'matched_content': result['content'][:200] + '...' if len(result['content']) > 200 else result['content']
                })
        
        return {
            'query': query,
            'results': enriched_results,
            'total_found': len(enriched_results)
        }
        
    except Exception as e:
        logger.error(f"Error searching entries: {e}")
        raise HTTPException(status_code=500, detail="Failed to search entries")

@router.get("/stats/mood")
async def get_mood_statistics(days: int = Query(30, ge=1, le=365)):
    """Get mood statistics for the specified period"""
    try:
        stats = await db_service.get_mood_statistics(days)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting mood statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve mood statistics")