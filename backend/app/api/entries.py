# backend/app/api/entries.py - Modernized with Unified Service Integration

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from typing import List, Optional
from datetime import datetime, date
import logging

# Enhanced architecture imports
from app.core.exceptions import ValidationException, NotFoundException, DatabaseException
from app.models.entry import Entry, EntryCreate, EntryUpdate, EntryResponse, MoodType
from app.services.unified_database_service import unified_db_service
from app.services.vector_service import vector_service
from app.services.ai_emotion_service import ai_emotion_service
from app.services.ai_intervention_service import ai_intervention_service  
from app.services.llm_service import llm_service
from app.decorators.cache_decorators import cached, cache_invalidate, timed_operation, CachePatterns
from app.core.performance_monitor import performance_monitor

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=EntryResponse)
@timed_operation("create_entry_api", track_errors=True)
async def create_entry(entry: EntryCreate, request: Request):
    """Create a new journal entry with unified service and caching"""
    correlation_id = getattr(request.state, 'correlation_id', None)
    
    try:
        # Input validation
        if not entry.content or len(entry.content.strip()) < 3:
            raise ValidationException(
                "Entry content must be at least 3 characters long",
                context={"content_length": len(entry.content) if entry.content else 0},
                correlation_id=correlation_id
            )
        
        # Analyze sentiment with enhanced error handling
        mood = None
        sentiment_score = 0.0
        
        try:
            # Use modern AI emotion analysis instead of legacy sentiment analysis
            emotion_analysis = await ai_emotion_service.analyze_emotions(entry.content)
            
            # Convert emotion analysis to mood for backward compatibility
            mood = emotion_analysis.primary_emotion.emotion.value  # Gets the EmotionCategory value
            sentiment_score = emotion_analysis.primary_emotion.confidence
            
            # Check for crisis indicators using AI intervention service
            intervention_assessment = await ai_intervention_service.assess_crisis_risk(
                entry.content, user_context={"user_id": str(entry.user_id)}
            )
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
        
        # Generate automatic tags
        auto_tags = []
        if len(entry.content.strip()) > 10:
            try:
                auto_tags = await llm_service.generate_automatic_tags(entry.content, "journal")
            except Exception as e:
                logger.warning(f"Auto-tagging failed: {e}")
        
        # Combine manual and automatic tags
        manual_tags = [tag.lower().strip() for tag in entry.tags] if entry.tags else []
        all_tags = manual_tags.copy()
        
        for auto_tag in auto_tags:
            if auto_tag not in all_tags:
                all_tags.append(auto_tag)
        
        final_tags = all_tags[:8]  # Limit to 8 tags
        
        # Create entry using unified service
        async with performance_monitor.timed_operation("unified_create_entry", {"user_id": "default"}):
            db_entry = await unified_db_service.create_entry(
                title=entry.title,
                content=entry.content,
                topic_id=entry.topic_id,
                mood=mood.value if mood else None,
                sentiment_score=sentiment_score,
                tags=final_tags
            )
        
        # Add to vector database for search
        try:
            metadata = {
                'entry_id': str(db_entry.id),
                'title': db_entry.title or '',
                'mood': db_entry.mood or 'neutral',
                'sentiment_score': db_entry.sentiment_score or 0.0,
                'created_at': db_entry.created_at.isoformat(),
                'tags': db_entry.tags or [],
                'word_count': db_entry.word_count or 0,
                'auto_tagged': len(auto_tags) > 0
            }
            
            await vector_service.add_entry(str(db_entry.id), db_entry.content, metadata)
        except Exception as e:
            logger.warning(f"Vector database update failed: {e}")
        
        return EntryResponse(**db_entry.__dict__)
        
    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"Error creating entry: {e}")
        raise HTTPException(status_code=500, detail="Failed to create entry")

@router.get("/", response_model=List[EntryResponse])
@CachePatterns.ENTRY_READ
async def get_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    topic_id: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    mood_filter: Optional[str] = Query(None)
):
    """Get journal entries with unified service caching"""
    try:
        # Convert dates to datetime
        datetime_from = datetime.combine(date_from, datetime.min.time()) if date_from else None
        datetime_to = datetime.combine(date_to, datetime.max.time()) if date_to else None
        
        async with performance_monitor.timed_operation("unified_get_entries", {"limit": limit}):
            entries = await unified_db_service.get_entries(
                skip=skip,
                limit=limit,
                topic_id=topic_id,
                mood_filter=mood_filter,
                date_from=datetime_from,
                date_to=datetime_to,
                use_cache=True
            )
        
        return [EntryResponse(**entry.__dict__) for entry in entries]
        
    except Exception as e:
        logger.error(f"Error getting entries: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve entries")

@router.get("/search/semantic")
@cached(ttl=900, key_prefix="semantic_search", monitor_performance=True)
async def search_entries(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    topic_id: Optional[str] = Query(None)
):
    """Search entries using semantic similarity with caching"""
    try:
        filters = {}
        if topic_id:
            filters['topic_id'] = topic_id
        
        async with performance_monitor.timed_operation("semantic_search", {"query_length": len(query)}):
            results = await vector_service.search_entries(query, limit, filters)
        
        # Enrich results with full entry data from unified service
        enriched_results = []
        for result in results:
            entry = await unified_db_service.get_entry(result['id'], use_cache=True)
            if entry:
                enriched_results.append({
                    'entry': EntryResponse(**entry.__dict__),
                    'similarity': result['similarity']
                })
        
        return {
            'results': enriched_results,
            'total_found': len(enriched_results),
            'query': query
        }
        
    except Exception as e:
        logger.error(f"Error searching entries: {e}")
        raise HTTPException(status_code=500, detail="Failed to search entries")

@router.get("/favorites")
@CachePatterns.ENTRY_READ
async def get_favorite_entries(limit: int = Query(50, ge=1, le=100)):
    """Get all favorite entries with unified service caching"""
    try:
        async with performance_monitor.timed_operation("get_favorites", {"limit": limit}):
            entries = await unified_db_service.get_entries(
                skip=0,
                limit=limit,
                mood_filter=None,
                use_cache=True
            )
        
        # Filter favorites (this will be optimized in the service later)
        favorite_entries = [entry for entry in entries if getattr(entry, 'is_favorite', False)]
        
        return [EntryResponse(**entry.__dict__) for entry in favorite_entries[:limit]]
        
    except Exception as e:
        logger.error(f"Error getting favorite entries: {e}")
        raise HTTPException(status_code=500, detail="Failed to get favorite entries")

@router.get("/{entry_id}", response_model=EntryResponse)
@CachePatterns.ENTRY_READ
async def get_entry(entry_id: str):
    """Get a specific journal entry with caching"""
    try:
        async with performance_monitor.timed_operation("get_single_entry", {"entry_id": entry_id}):
            entry = await unified_db_service.get_entry(entry_id, use_cache=True)
        
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        return EntryResponse(**entry.__dict__)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting entry {entry_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve entry")

@router.put("/{entry_id}", response_model=EntryResponse)
@CachePatterns.INVALIDATE_ENTRIES
@timed_operation("update_entry_api", track_errors=True)
async def update_entry(entry_id: str, entry_update: EntryUpdate):
    """Update a journal entry with unified service and cache invalidation"""
    try:
        # Check if entry exists
        existing_entry = await unified_db_service.get_entry(entry_id, use_cache=False)
        if not existing_entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        # Analyze sentiment if content is being updated
        mood = None
        sentiment_score = None
        
        if entry_update.content:
            try:
                # Use modern AI emotion analysis for content updates
                emotion_analysis = await ai_emotion_service.analyze_emotions(entry_update.content)
                mood = emotion_analysis.primary_emotion.emotion.value
                sentiment_score = emotion_analysis.primary_emotion.confidence
            except Exception as e:
                logger.warning(f"AI emotion analysis failed: {e}")
                # Fallback to basic mood if AI analysis fails
                mood = "neutral"
                sentiment_score = 0.5
        
        # Update entry using unified service
        async with performance_monitor.timed_operation("unified_update_entry", {"entry_id": entry_id}):
            updated_entry = await unified_db_service.update_entry(
                entry_id=entry_id,
                title=entry_update.title,
                content=entry_update.content,
                mood=mood.value if mood else None,
                sentiment_score=sentiment_score,
                tags=entry_update.tags
            )
        
        if not updated_entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        # Update vector database
        try:
            content_to_index = entry_update.content or existing_entry.content
            metadata = {
                'entry_id': str(updated_entry.id),
                'title': updated_entry.title or '',
                'mood': updated_entry.mood or 'neutral',
                'sentiment_score': updated_entry.sentiment_score or 0.0,
                'created_at': updated_entry.created_at.isoformat(),
                'tags': updated_entry.tags or [],
                'word_count': updated_entry.word_count or 0
            }
            
            await vector_service.update_entry(str(updated_entry.id), content_to_index, metadata)
        except Exception as e:
            logger.warning(f"Vector database update failed: {e}")
        
        return EntryResponse(**updated_entry.__dict__)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating entry {entry_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update entry")

@router.delete("/{entry_id}")
@CachePatterns.INVALIDATE_ENTRIES
@timed_operation("delete_entry_api", track_errors=True)
async def delete_entry(entry_id: str):
    """Delete a journal entry with unified service and cache invalidation"""
    try:
        # Check if entry exists
        existing_entry = await unified_db_service.get_entry(entry_id, use_cache=False)
        if not existing_entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        # Delete from unified service
        async with performance_monitor.timed_operation("unified_delete_entry", {"entry_id": entry_id}):
            success = await unified_db_service.delete_entry(entry_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete entry")
        
        # Delete from vector database
        try:
            await vector_service.delete_entry(entry_id)
        except Exception as e:
            logger.warning(f"Vector database deletion failed: {e}")
        
        return {"message": "Entry deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting entry {entry_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete entry")

@router.patch("/{entry_id}/favorite")
@CachePatterns.INVALIDATE_ENTRIES
async def toggle_favorite(entry_id: str):
    """Toggle favorite status with cache invalidation"""
    try:
        entry = await unified_db_service.get_entry(entry_id, use_cache=False)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        # This would need to be implemented in unified_db_service
        # For now, we'll use a simple update
        current_favorite = getattr(entry, 'is_favorite', False)
        
        updated_entry = await unified_db_service.update_entry(
            entry_id=entry_id,
            # This would need is_favorite parameter in unified service
        )
        
        return EntryResponse(**updated_entry.__dict__)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling favorite: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle favorite")

@router.get("/analytics/mood")
@cached(ttl=1800, key_prefix="mood_analytics", monitor_performance=True)
async def get_mood_analytics(days: int = Query(30, ge=7, le=365)):
    """Get mood analytics with unified service caching"""
    try:
        async with performance_monitor.timed_operation("mood_analytics", {"days": days}):
            analytics = await unified_db_service.get_mood_statistics(
                days=days,
                use_cache=True
            )
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting mood analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get mood analytics")

@router.get("/analytics/writing")
@cached(ttl=1800, key_prefix="writing_analytics", monitor_performance=True) 
async def get_writing_analytics(days: int = Query(30, ge=7, le=365)):
    """Get writing statistics with unified service caching"""
    try:
        async with performance_monitor.timed_operation("writing_analytics", {"days": days}):
            analytics = await unified_db_service.get_writing_statistics(
                days=days,
                use_cache=True
            )
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting writing analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get writing analytics")