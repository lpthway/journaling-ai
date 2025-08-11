# backend/app/api/entries.py - Modernized with Unified Service Integration

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from typing import List, Optional, Dict, Any
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
from app.services.entry_analytics_processor import entry_analytics_processor
from app.decorators.cache_decorators import cached, cache_invalidate, timed_operation, CachePatterns
from app.core.performance_monitor import performance_monitor

logger = logging.getLogger(__name__)

router = APIRouter()

def _safe_get_entry_metadata(db_entry) -> dict:
    """Safely extract metadata from database entry object"""
    try:
        # Check for common metadata attribute names
        for attr_name in ['entry_metadata', 'metadata']:
            if hasattr(db_entry, attr_name):
                metadata = getattr(db_entry, attr_name)
                if metadata is None:
                    continue
                elif isinstance(metadata, dict):
                    return metadata
                elif hasattr(metadata, '__dict__'):
                    # Filter out SQLAlchemy internals
                    metadata_dict = {}
                    for key, value in metadata.__dict__.items():
                        if not key.startswith('_') and not hasattr(value, '__table__'):
                            try:
                                # Test if value is JSON serializable
                                import json
                                json.dumps(value)
                                metadata_dict[key] = value
                            except (TypeError, ValueError):
                                # Skip non-serializable values
                                continue
                    return metadata_dict
                else:
                    # If it's some other object, try to convert to dict safely
                    try:
                        result = dict(metadata)
                        # Filter out any SQLAlchemy objects
                        return {k: v for k, v in result.items() 
                               if not hasattr(v, '__table__') and not str(type(v)).startswith('<class \'sqlalchemy')}
                    except (TypeError, ValueError):
                        continue
        return {}
    except Exception:
        return {}

def _convert_entry_to_response(db_entry) -> Dict[str, Any]:
    """Helper function to convert database entry to response dict with proper UUID handling"""
    return {
        "id": str(db_entry.id),
        "title": db_entry.title,
        "content": db_entry.content,
        "entry_type": db_entry.entry_type,
        "user_id": str(db_entry.user_id) if db_entry.user_id else None,
        "topic_id": str(db_entry.topic_id) if db_entry.topic_id else None,
        "tags": db_entry.tags,
        "template_id": db_entry.template_id,
        "created_at": db_entry.created_at,
        "updated_at": db_entry.updated_at,
        "mood": db_entry.mood,
        "sentiment_score": db_entry.sentiment_score,
        "word_count": db_entry.word_count,
        "emotion_analysis": getattr(db_entry, 'emotion_analysis', None),
        "ai_analysis": getattr(db_entry, 'ai_analysis', None),
        "metadata": _safe_get_entry_metadata(db_entry),
        "is_favorite": getattr(db_entry, 'is_favorite', False),
        "version": getattr(db_entry, 'version', 1),
        "parent_entry_id": getattr(db_entry, 'parent_entry_id', None)
    }

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
            emotion_analysis = await ai_emotion_service.analyze_emotions(
                entry.content, 
                include_patterns=True
            )
            
            # Convert emotion analysis to mood for backward compatibility
            emotion_value = emotion_analysis.primary_emotion.emotion  # Already a string value
            sentiment_score = emotion_analysis.primary_emotion.confidence
            
            # Map emotion labels to mood types
            emotion_to_mood_mapping = {
                'label_0': 'neutral',
                'label_1': 'positive', 
                'label_2': 'negative',
                'joy': 'positive',
                'happiness': 'very_positive',
                'sadness': 'negative',
                'anger': 'negative',
                'fear': 'negative',
                'neutral': 'neutral',
                'positive': 'positive',
                'negative': 'negative'
            }
            mood = emotion_to_mood_mapping.get(emotion_value.lower(), 'neutral')
            
            # Check for crisis indicators using AI intervention service
            intervention_assessment = await ai_intervention_service.assess_crisis_level(
                entry.content, user_context={"user_id": "default_user"}
            )
            
            # Log crisis assessment results
            if intervention_assessment.crisis_level.name != "MINIMAL":
                logger.warning(f"🚨 Crisis detected: {intervention_assessment.crisis_level.name} - "
                             f"Risk factors: {len(intervention_assessment.risk_factors)} - "
                             f"Interventions: {len(intervention_assessment.immediate_interventions)}")
            else:
                logger.info(f"✅ No crisis detected - Level: {intervention_assessment.crisis_level.name}")
                
        except Exception as e:
            logger.warning(f"AI analysis failed: {e}")
            emotion_analysis = None
            intervention_assessment = None
        
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
        async with performance_monitor.timed_operation("unified_create_entry", {"user_id": entry.user_id or "default"}):
            db_entry = await unified_db_service.create_entry(
                title=entry.title,
                content=entry.content,
                user_id=entry.user_id or "default_user",  # Use user_id from request or default
                topic_id=entry.topic_id,
                mood=mood if mood else None,
                sentiment_score=sentiment_score,
                tags=final_tags
            )
        
        # Store detailed AI analysis results if available
        if emotion_analysis:
            try:
                # Convert emotion analysis to serializable format
                emotion_data = {
                    "primary_emotion": emotion_analysis.primary_emotion.emotion,
                    "confidence": emotion_analysis.primary_emotion.confidence,
                    "sentiment_polarity": emotion_analysis.sentiment_polarity,
                    "emotional_complexity": emotion_analysis.emotional_complexity,
                    "detected_patterns": emotion_analysis.detected_patterns,
                    "secondary_emotions": [
                        {"emotion": e.emotion, "score": e.confidence} 
                        for e in emotion_analysis.secondary_emotions
                    ],
                    "analysis_timestamp": datetime.utcnow().isoformat()
                }
                
                # Store emotion analysis in database by updating the db_entry object
                db_entry.emotion_analysis = emotion_data
                
                # Also store crisis assessment if available
                crisis_data = None
                if intervention_assessment:
                    # Convert InterventionRecommendation objects to dictionaries
                    immediate_interventions_dict = []
                    for intervention in intervention_assessment.immediate_interventions:
                        immediate_interventions_dict.append({
                            "intervention_type": intervention.intervention_type.value,
                            "therapeutic_approach": intervention.therapeutic_approach.value,
                            "priority": intervention.priority,
                            "description": intervention.description,
                            "specific_techniques": intervention.specific_techniques,
                            "estimated_duration": intervention.estimated_duration,
                            "prerequisites": intervention.prerequisites,
                            "contraindications": intervention.contraindications
                        })
                    
                    crisis_data = {
                        "crisis_level": intervention_assessment.crisis_level.name,
                        "risk_factors": [rf.indicator for rf in intervention_assessment.risk_factors],
                        "protective_factors": intervention_assessment.protective_factors,
                        "immediate_interventions": immediate_interventions_dict,
                        "professional_referral_urgent": intervention_assessment.professional_referral_urgent,
                        "assessment_timestamp": datetime.utcnow().isoformat()
                    }
                    db_entry.ai_analysis = crisis_data
                    logger.info(f"✅ Stored crisis assessment for entry {db_entry.id}: {intervention_assessment.crisis_level.name}")
                
                # Update the entry in database with emotion analysis data
                await unified_db_service.update_entry(
                    str(db_entry.id),
                    emotion_analysis=emotion_data,
                    ai_analysis=crisis_data
                )
                
                logger.info(f"✅ Added emotion analysis to entry {db_entry.id}")
                
            except Exception as e:
                logger.warning(f"Failed to store emotion analysis: {e}")
        
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
        
        # Invalidate analytics cache for fresh data
        try:
            await entry_analytics_processor.invalidate_analytics_cache(
                entry.user_id or "default_user"
            )
            logger.debug(f"Invalidated analytics cache for new entry {db_entry.id}")
        except Exception as e:
            # Don't let cache invalidation errors break entry creation
            logger.warning(f"Failed to invalidate analytics cache: {e}")
        
        return EntryResponse.model_validate(_convert_entry_to_response(db_entry))
        
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
    mood_filter: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None)
):
    """Get journal entries with unified service caching"""
    try:
        # Convert dates to datetime
        datetime_from = datetime.combine(date_from, datetime.min.time()) if date_from else None
        datetime_to = datetime.combine(date_to, datetime.max.time()) if date_to else None
        
        async with performance_monitor.timed_operation("unified_get_entries", {"limit": limit}):
            entries = await unified_db_service.get_entries(
                user_id=user_id or "default_user",
                skip=skip,
                limit=limit,
                topic_id=topic_id,
                mood_filter=mood_filter,
                date_from=datetime_from,
                date_to=datetime_to,
                use_cache=True
            )
        
        return [EntryResponse.model_validate(_convert_entry_to_response(entry)) for entry in entries]
        
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
        
        # Optimized: Bulk load entries to prevent N+1 queries
        entry_ids = [result['id'] for result in results]
        
        # Use bulk loading method from enhanced repository
        try:
            from app.repositories.enhanced_entry_repository import EnhancedEntryRepository
            from app.core.database import get_session
            
            async with get_session() as db_session:
                entry_repo = EnhancedEntryRepository(db_session)
                entries_dict = await entry_repo.get_entries_bulk_by_ids(entry_ids, include_topic=True)
            
            # Build enriched results with bulk-loaded data
            enriched_results = []
            for result in results:
                entry = entries_dict.get(result['id'])
                if entry:
                    enriched_results.append({
                        'entry': EntryResponse.model_validate(_convert_entry_to_response(entry)),
                        'similarity': result['similarity']
                    })
        except Exception as e:
            logger.warning(f"Bulk loading failed, falling back to individual loads: {e}")
            # Fallback to original method if bulk loading fails
            enriched_results = []
            for result in results:
                entry = await unified_db_service.get_entry(result['id'], use_cache=True)
                if entry:
                    enriched_results.append({
                        'entry': EntryResponse.model_validate(_convert_entry_to_response(entry)),
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
        
        return [EntryResponse.model_validate(entry) for entry in favorite_entries[:limit]]
        
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
        
        return EntryResponse.model_validate(_convert_entry_to_response(entry))
        
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
                emotion_analysis = await ai_emotion_service.analyze_emotions(
                    entry_update.content, 
                    include_patterns=True
                )
                emotion_value = emotion_analysis.primary_emotion.emotion
                sentiment_score = emotion_analysis.primary_emotion.confidence
                
                # Map emotion labels to mood types
                emotion_to_mood_mapping = {
                    'label_0': 'neutral',
                    'label_1': 'positive', 
                    'label_2': 'negative',
                    'joy': 'positive',
                    'happiness': 'very_positive',
                    'sadness': 'negative',
                    'anger': 'negative',
                    'fear': 'negative',
                    'neutral': 'neutral',
                    'positive': 'positive',
                    'negative': 'negative'
                }
                mood = emotion_to_mood_mapping.get(emotion_value.lower(), 'neutral')
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
                mood=mood if mood else None,
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
        
        # Invalidate analytics cache after entry update
        try:
            await entry_analytics_processor.invalidate_analytics_cache(
                str(existing_entry.user_id) if existing_entry.user_id else "default_user"
            )
            logger.debug(f"Invalidated analytics cache for updated entry {entry_id}")
        except Exception as e:
            # Don't let cache invalidation errors break entry update
            logger.warning(f"Failed to invalidate analytics cache: {e}")
        
        return EntryResponse.model_validate(updated_entry)
        
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
        
        return EntryResponse.model_validate(updated_entry)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling favorite: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle favorite")

@router.get("/analytics/mood")
@cached(ttl=1800, key_prefix="mood_analytics", monitor_performance=True)
async def get_mood_analytics(days: int = Query(30, ge=7, le=365), user_id: str = Query(..., description="User ID for analytics")):
    """Get mood analytics with unified service caching"""
    try:
        async with performance_monitor.timed_operation("mood_analytics", {"days": days}):
            analytics = await unified_db_service.get_mood_statistics(
                user_id=user_id,
                days=days,
                use_cache=True
            )
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting mood analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get mood analytics")

@router.get("/analytics/writing")
@cached(ttl=1800, key_prefix="writing_analytics", monitor_performance=True) 
async def get_writing_analytics(days: int = Query(30, ge=7, le=365), user_id: str = Query(..., description="User ID for analytics")):
    """Get writing statistics with unified service caching"""
    try:
        async with performance_monitor.timed_operation("writing_analytics", {"days": days}):
            analytics = await unified_db_service.get_writing_statistics(
                user_id=user_id,
                days=days,
                use_cache=True
            )
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting writing analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get writing analytics")