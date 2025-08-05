"""
Enhanced search repository with trigram (gin_trgm_ops) support
Provides fuzzy search capabilities for better user experience
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import selectinload

from app.models.enhanced_models import Entry, Topic
from app.repositories.enhanced_base import EnhancedBaseRepository

import logging
logger = logging.getLogger(__name__)

class TrigramSearchRepository(EnhancedBaseRepository):
    """Enhanced search capabilities using PostgreSQL trigram indexes"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
    
    async def fuzzy_search_entries(
        self,
        user_id: str,
        query: str,
        min_similarity: float = 0.1,
        limit: int = 20,
        offset: int = 0,
        search_fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fuzzy search entries using trigram similarity
        
        Args:
            user_id: User identifier
            query: Search query
            min_similarity: Minimum similarity threshold (0.0-1.0)
            limit: Maximum results to return
            offset: Results offset for pagination
            search_fields: Fields to search in ['title', 'content'] (default: both)
        
        Returns:
            List of entries with similarity scores
        """
        try:
            search_fields = search_fields or ['title', 'content']
            similarity_conditions = []
            
            # Build similarity conditions for each field
            for field in search_fields:
                if field == 'title':
                    similarity_conditions.append(
                        func.similarity(Entry.title, query).label(f'{field}_similarity')
                    )
                elif field == 'content':
                    similarity_conditions.append(
                        func.similarity(Entry.content, query).label(f'{field}_similarity')
                    )
            
            # Combine similarities (use maximum similarity across fields)
            if len(similarity_conditions) > 1:
                max_similarity = func.greatest(*[cond for cond in similarity_conditions])
            else:
                max_similarity = similarity_conditions[0]
            
            # Build the main query
            search_query = select(
                Entry,
                max_similarity.label('similarity_score')
            ).options(
                selectinload(Entry.topic)
            ).where(
                and_(
                    Entry.user_id == user_id,
                    Entry.deleted_at.is_(None),
                    max_similarity >= min_similarity
                )
            ).order_by(
                max_similarity.desc(),
                Entry.created_at.desc()
            ).offset(offset).limit(limit)
            
            result = await self.session.execute(search_query)
            entries_with_scores = result.all()
            
            # Format results
            results = []
            for entry, similarity in entries_with_scores:
                results.append({
                    'entry': entry,
                    'similarity_score': float(similarity),
                    'match_type': 'fuzzy'
                })
            
            logger.info(f"Trigram search for '{query[:50]}...' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in trigram entry search: {e}")
            raise
    
    async def fuzzy_search_topics(
        self,
        user_id: str,
        query: str,
        min_similarity: float = 0.1,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Fuzzy search topics using trigram similarity
        
        Args:
            user_id: User identifier
            query: Search query
            min_similarity: Minimum similarity threshold
            limit: Maximum results to return
            offset: Results offset for pagination
        
        Returns:
            List of topics with similarity scores
        """
        try:
            # Calculate similarity for both name and description
            name_similarity = func.similarity(Topic.name, query)
            desc_similarity = func.similarity(Topic.description, query)
            max_similarity = func.greatest(name_similarity, desc_similarity)
            
            search_query = select(
                Topic,
                max_similarity.label('similarity_score'),
                name_similarity.label('name_similarity'),
                desc_similarity.label('description_similarity')
            ).where(
                and_(
                    Topic.user_id == user_id,
                    Topic.deleted_at.is_(None),
                    max_similarity >= min_similarity
                )
            ).order_by(
                max_similarity.desc(),
                Topic.name
            ).offset(offset).limit(limit)
            
            result = await self.session.execute(search_query)
            topics_with_scores = result.all()
            
            # Format results
            results = []
            for topic, similarity, name_sim, desc_sim in topics_with_scores:
                results.append({
                    'topic': topic,
                    'similarity_score': float(similarity),
                    'name_similarity': float(name_sim),
                    'description_similarity': float(desc_sim),
                    'match_type': 'fuzzy'
                })
            
            logger.info(f"Trigram topic search for '{query[:50]}...' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in trigram topic search: {e}")
            raise
    
    async def combined_fuzzy_search(
        self,
        user_id: str,
        query: str,
        min_similarity: float = 0.1,
        entry_limit: int = 15,
        topic_limit: int = 5
    ) -> Dict[str, Any]:
        """
        Combined fuzzy search across entries and topics
        
        Args:
            user_id: User identifier
            query: Search query
            min_similarity: Minimum similarity threshold
            entry_limit: Maximum entry results
            topic_limit: Maximum topic results
        
        Returns:
            Combined search results with relevance ranking
        """
        try:
            # Search entries and topics in parallel
            entry_results = await self.fuzzy_search_entries(
                user_id=user_id,
                query=query,
                min_similarity=min_similarity,
                limit=entry_limit
            )
            
            topic_results = await self.fuzzy_search_topics(
                user_id=user_id,
                query=query,
                min_similarity=min_similarity,
                limit=topic_limit
            )
            
            # Calculate overall search quality metrics
            total_results = len(entry_results) + len(topic_results)
            avg_similarity = 0.0
            
            if total_results > 0:
                all_scores = [r['similarity_score'] for r in entry_results] + \
                           [r['similarity_score'] for r in topic_results]
                avg_similarity = sum(all_scores) / len(all_scores)
            
            return {
                'entries': entry_results,
                'topics': topic_results,
                'metadata': {
                    'query': query,
                    'total_results': total_results,
                    'avg_similarity': avg_similarity,
                    'search_type': 'fuzzy_trigram',
                    'min_similarity_threshold': min_similarity
                }
            }
            
        except Exception as e:
            logger.error(f"Error in combined fuzzy search: {e}")
            raise
    
    async def suggest_similar_entries(
        self,
        entry_id: str,
        user_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find entries similar to a given entry using title/content similarity
        
        Args:
            entry_id: Source entry ID
            user_id: User identifier  
            limit: Maximum suggestions to return
        
        Returns:
            List of similar entries with similarity scores
        """
        try:
            # Get the source entry
            source_entry = await self.session.get(Entry, entry_id)
            if not source_entry:
                return []
            
            # Use title for similarity matching
            search_text = source_entry.title
            
            # Find similar entries (excluding the source entry)
            similarity_score = func.similarity(Entry.title, search_text)
            
            similar_query = select(
                Entry,
                similarity_score.label('similarity_score')
            ).options(
                selectinload(Entry.topic)
            ).where(
                and_(
                    Entry.user_id == user_id,
                    Entry.id != entry_id,
                    Entry.deleted_at.is_(None),
                    similarity_score > 0.1
                )
            ).order_by(
                similarity_score.desc()
            ).limit(limit)
            
            result = await self.session.execute(similar_query)
            similar_entries = result.all()
            
            # Format results
            suggestions = []
            for entry, similarity in similar_entries:
                suggestions.append({
                    'entry': entry,
                    'similarity_score': float(similarity),
                    'match_type': 'content_similarity'
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error finding similar entries: {e}")
            return []
    
    async def advanced_fuzzy_search(
        self,
        user_id: str,
        query: str,
        filters: Dict[str, Any] = None,
        min_similarity: float = 0.1,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Advanced fuzzy search with filters and ranking
        
        Args:
            user_id: User identifier
            query: Search query
            filters: Additional filters (mood, date_range, topic_id, etc.)
            min_similarity: Minimum similarity threshold
            limit: Maximum results to return
            offset: Results offset for pagination
        
        Returns:
            Advanced search results with multiple ranking factors
        """
        try:
            filters = filters or {}
            
            # Base similarity conditions
            title_similarity = func.similarity(Entry.title, query)
            content_similarity = func.similarity(Entry.content, query)
            max_similarity = func.greatest(title_similarity, content_similarity)
            
            # Build base conditions
            conditions = [
                Entry.user_id == user_id,
                Entry.deleted_at.is_(None),
                max_similarity >= min_similarity
            ]
            
            # Apply additional filters
            if filters.get('mood'):
                conditions.append(Entry.mood == filters['mood'])
            
            if filters.get('topic_id'):
                conditions.append(Entry.topic_id == filters['topic_id'])
            
            if filters.get('date_from'):
                conditions.append(Entry.created_at >= filters['date_from'])
            
            if filters.get('date_to'):
                conditions.append(Entry.created_at <= filters['date_to'])
            
            if filters.get('tags'):
                for tag in filters['tags']:
                    conditions.append(Entry.tags.contains([tag]))
            
            # Enhanced ranking with multiple factors
            # 1. Text similarity (primary)
            # 2. Recency boost
            # 3. Favorite entries boost
            recency_factor = func.extract('epoch', func.now() - Entry.created_at) / 86400.0  # Days ago
            favorite_boost = func.case((Entry.is_favorite == True, 0.1), else_=0.0)
            
            composite_score = (
                max_similarity + 
                favorite_boost +
                func.case((recency_factor < 7, 0.05), else_=0.0)  # Recent entries boost
            )
            
            search_query = select(
                Entry,
                max_similarity.label('similarity_score'),
                title_similarity.label('title_similarity'),
                content_similarity.label('content_similarity'),
                composite_score.label('composite_score')
            ).options(
                selectinload(Entry.topic)
            ).where(
                and_(*conditions)
            ).order_by(
                composite_score.desc(),
                Entry.created_at.desc()
            ).offset(offset).limit(limit)
            
            result = await self.session.execute(search_query)
            entries_with_scores = result.all()
            
            # Format results with detailed scoring
            results = []
            for entry, similarity, title_sim, content_sim, composite in entries_with_scores:
                results.append({
                    'entry': entry,
                    'similarity_score': float(similarity),
                    'title_similarity': float(title_sim),
                    'content_similarity': float(content_sim),
                    'composite_score': float(composite),
                    'match_type': 'advanced_fuzzy',
                    'is_recent': (entry.created_at and 
                                 (entry.created_at.date() - entry.created_at.today().date()).days < 7),
                    'is_favorite': entry.is_favorite
                })
            
            return {
                'results': results,
                'metadata': {
                    'query': query,
                    'total_results': len(results),
                    'applied_filters': filters,
                    'search_type': 'advanced_fuzzy_trigram',
                    'min_similarity_threshold': min_similarity
                }
            }
            
        except Exception as e:
            logger.error(f"Error in advanced fuzzy search: {e}")
            raise
