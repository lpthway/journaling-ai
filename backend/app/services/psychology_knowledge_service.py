# backend/app/services/psychology_knowledge_service.py

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
import uuid
from typing import List, Dict, Any, Optional, Tuple
import logging
from pathlib import Path
import json
from dataclasses import dataclass
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)

class PsychologyDomain(Enum):
    """Psychology domains for knowledge categorization"""
    CBT = "cognitive_behavioral_therapy"
    GAMING_PSYCHOLOGY = "gaming_psychology"
    ADDICTION_RECOVERY = "addiction_recovery"
    MINDFULNESS = "mindfulness_practices"
    CRISIS_INTERVENTION = "crisis_intervention"
    EMOTIONAL_REGULATION = "emotional_regulation"
    STRESS_MANAGEMENT = "stress_management"
    HABIT_FORMATION = "habit_formation"
    SOCIAL_PSYCHOLOGY = "social_psychology"
    POSITIVE_PSYCHOLOGY = "positive_psychology"

@dataclass
class PsychologySource:
    """Structured psychology source information"""
    title: str
    authors: List[str]
    year: int
    source_type: str  # "book", "paper", "article", "guideline"
    doi: Optional[str] = None
    isbn: Optional[str] = None
    url: Optional[str] = None
    journal: Optional[str] = None
    publisher: Optional[str] = None
    credibility_score: float = 1.0  # 0-1 scale based on source quality

@dataclass
class PsychologyKnowledge:
    """Structured psychology knowledge entry"""
    content: str
    domain: PsychologyDomain
    source: PsychologySource
    techniques: List[str]  # Specific techniques/methods mentioned
    evidence_level: str  # "high", "medium", "low" based on research quality
    practical_applications: List[str]
    keywords: List[str]
    chunk_id: Optional[str] = None

class PsychologyKnowledgeService:
    """
    Professional psychology knowledge database with source attribution.
    
    Provides evidence-based psychological insights for AI conversations,
    maintaining separation from journal entries while enabling cross-referencing.
    """
    
    def __init__(self, persist_directory: str = "./data/psychology_db"):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB for psychology knowledge
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Use same embedding model for consistency
        self.embedding_model = SentenceTransformer("intfloat/multilingual-e5-large")
        
        # Create psychology knowledge collection
        self.collection = self.client.get_or_create_collection(
            name="psychology_knowledge",
            metadata={
                "hnsw:space": "cosine",
                "description": "Evidence-based psychology knowledge database"
            }
        )
        
        # Create domain-specific collections for specialized searches
        self.domain_collections = {}
        for domain in PsychologyDomain:
            self.domain_collections[domain] = self.client.get_or_create_collection(
                name=f"psychology_{domain.value}",
                metadata={"hnsw:space": "cosine", "domain": domain.value}
            )
        
        logger.info(f"Psychology Knowledge Service initialized with {len(PsychologyDomain)} specialized domains")
    
    def _generate_chunk_id(self, content: str, source_title: str) -> str:
        """Generate unique chunk identifier"""
        content_hash = hashlib.md5(f"{content}{source_title}".encode()).hexdigest()
        return f"psych_{content_hash[:12]}"
    
    def _prepare_metadata(self, knowledge: PsychologyKnowledge) -> Dict[str, Any]:
        """Prepare metadata for ChromaDB storage"""
        return {
            "domain": knowledge.domain.value,
            "source_title": knowledge.source.title,
            "authors": ",".join(knowledge.source.authors),
            "year": knowledge.source.year,
            "source_type": knowledge.source.source_type,
            "evidence_level": knowledge.evidence_level,
            "techniques": ",".join(knowledge.techniques),
            "applications": ",".join(knowledge.practical_applications),
            "keywords": ",".join(knowledge.keywords),
            "credibility_score": knowledge.source.credibility_score,
            "doi": knowledge.source.doi or "",
            "journal": knowledge.source.journal or "",
            "isbn": knowledge.source.isbn or "",
            "url": knowledge.source.url or ""
        }
    
    async def add_knowledge(self, knowledge: PsychologyKnowledge) -> str:
        """Add psychology knowledge to the database"""
        try:
            # Generate unique chunk ID
            chunk_id = self._generate_chunk_id(knowledge.content, knowledge.source.title)
            knowledge.chunk_id = chunk_id
            
            # Generate embedding
            embedding = self.embedding_model.encode(knowledge.content).tolist()
            
            # Prepare metadata
            metadata = self._prepare_metadata(knowledge)
            
            # Add to main collection
            self.collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[knowledge.content],
                metadatas=[metadata]
            )
            
            # Add to domain-specific collection
            domain_collection = self.domain_collections[knowledge.domain]
            domain_collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[knowledge.content],
                metadatas=[metadata]
            )
            
            logger.info(f"Added psychology knowledge: {chunk_id} (domain: {knowledge.domain.value})")
            return chunk_id
            
        except Exception as e:
            logger.error(f"Error adding psychology knowledge: {e}")
            raise
    
    async def search_knowledge(
        self,
        query: str,
        domain: Optional[PsychologyDomain] = None,
        evidence_level: Optional[str] = None,
        limit: int = 5,
        min_credibility: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Search psychology knowledge with domain and quality filtering"""
        try:
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Choose collection based on domain
            if domain:
                collection = self.domain_collections[domain]
            else:
                collection = self.collection
            
            # Build filters
            where_clause = {"credibility_score": {"$gte": min_credibility}}
            if evidence_level:
                where_clause["evidence_level"] = evidence_level
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause,
                include=["metadatas", "documents", "distances"]
            )
            
            # Format results with source attribution
            formatted_results = []
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i]
                
                # Reconstruct source information
                source_info = {
                    "title": metadata["source_title"],
                    "authors": metadata["authors"].split(",") if metadata["authors"] else [],
                    "year": metadata["year"],
                    "type": metadata["source_type"],
                    "evidence_level": metadata["evidence_level"],
                    "credibility_score": metadata["credibility_score"]
                }
                
                # Add optional source details
                if metadata.get("doi"):
                    source_info["doi"] = metadata["doi"]
                if metadata.get("journal"):
                    source_info["journal"] = metadata["journal"]
                if metadata.get("url"):
                    source_info["url"] = metadata["url"]
                
                formatted_results.append({
                    "id": results['ids'][0][i],
                    "content": results['documents'][0][i],
                    "domain": metadata["domain"],
                    "source": source_info,
                    "techniques": metadata["techniques"].split(",") if metadata["techniques"] else [],
                    "applications": metadata["applications"].split(",") if metadata["applications"] else [],
                    "keywords": metadata["keywords"].split(",") if metadata["keywords"] else [],
                    "relevance_score": 1 - results['distances'][0][i],
                    "similarity": round((1 - results['distances'][0][i]) * 100, 1)
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching psychology knowledge: {e}")
            return []
    
    async def get_knowledge_for_context(
        self,
        user_message: str,
        journal_context: Optional[str] = None,
        preferred_domains: Optional[List[PsychologyDomain]] = None,
        max_sources: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get relevant psychology knowledge for AI conversation context.
        
        This method intelligently selects psychology knowledge based on:
        - User's current message
        - Optional journal context
        - Preferred psychology domains
        - Source quality and relevance
        """
        try:
            # Combine user message with journal context for richer search
            search_query = user_message
            if journal_context:
                search_query = f"{user_message} {journal_context}"
            
            # If no preferred domains, search all
            if not preferred_domains:
                results = await self.search_knowledge(
                    query=search_query,
                    limit=max_sources * 2,  # Get more to filter
                    min_credibility=0.7  # Higher quality sources
                )
            else:
                # Search each preferred domain
                all_results = []
                for domain in preferred_domains:
                    domain_results = await self.search_knowledge(
                        query=search_query,
                        domain=domain,
                        limit=max_sources,
                        min_credibility=0.6
                    )
                    all_results.extend(domain_results)
                
                # Sort by relevance and take top results
                results = sorted(
                    all_results, 
                    key=lambda x: x['relevance_score'], 
                    reverse=True
                )[:max_sources]
            
            # Filter for minimum relevance threshold
            relevant_results = [
                result for result in results[:max_sources]
                if result['relevance_score'] > 0.6
            ]
            
            logger.info(f"Retrieved {len(relevant_results)} relevant psychology sources for context")
            return relevant_results
            
        except Exception as e:
            logger.error(f"Error getting psychology knowledge for context: {e}")
            return []
    
    async def get_techniques_for_issue(self, issue_type: str) -> List[Dict[str, Any]]:
        """Get specific psychological techniques for a given issue"""
        try:
            # Map common issues to domains
            issue_domain_mapping = {
                "anxiety": [PsychologyDomain.CBT, PsychologyDomain.MINDFULNESS],
                "depression": [PsychologyDomain.CBT, PsychologyDomain.POSITIVE_PSYCHOLOGY],
                "stress": [PsychologyDomain.STRESS_MANAGEMENT, PsychologyDomain.MINDFULNESS],
                "addiction": [PsychologyDomain.ADDICTION_RECOVERY, PsychologyDomain.CBT],
                "gaming": [PsychologyDomain.GAMING_PSYCHOLOGY, PsychologyDomain.ADDICTION_RECOVERY],
                "habits": [PsychologyDomain.HABIT_FORMATION, PsychologyDomain.CBT],
                "crisis": [PsychologyDomain.CRISIS_INTERVENTION],
                "emotions": [PsychologyDomain.EMOTIONAL_REGULATION, PsychologyDomain.MINDFULNESS]
            }
            
            # Find relevant domains
            relevant_domains = []
            for key, domains in issue_domain_mapping.items():
                if key in issue_type.lower():
                    relevant_domains.extend(domains)
            
            if not relevant_domains:
                relevant_domains = [PsychologyDomain.CBT]  # Default fallback
            
            # Search for techniques
            techniques = await self.get_knowledge_for_context(
                user_message=f"techniques for {issue_type}",
                preferred_domains=list(set(relevant_domains)),
                max_sources=5
            )
            
            return techniques
            
        except Exception as e:
            logger.error(f"Error getting techniques for issue: {e}")
            return []
    
    async def add_bulk_knowledge(self, knowledge_list: List[PsychologyKnowledge]) -> List[str]:
        """Add multiple psychology knowledge entries efficiently"""
        chunk_ids = []
        try:
            for knowledge in knowledge_list:
                chunk_id = await self.add_knowledge(knowledge)
                chunk_ids.append(chunk_id)
                
            logger.info(f"Added {len(chunk_ids)} psychology knowledge entries")
            return chunk_ids
            
        except Exception as e:
            logger.error(f"Error adding bulk psychology knowledge: {e}")
            raise
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the psychology knowledge database"""
        try:
            main_count = self.collection.count()
            
            domain_counts = {}
            for domain, collection in self.domain_collections.items():
                domain_counts[domain.value] = collection.count()
            
            return {
                "total_entries": main_count,
                "domain_breakdown": domain_counts,
                "domains_available": list(domain_counts.keys()),
                "database_path": str(self.persist_directory)
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
    
    def format_citation(self, source_info: Dict[str, Any]) -> str:
        """Format source information as a proper citation"""
        try:
            authors = ", ".join(source_info.get("authors", []))
            title = source_info.get("title", "Unknown Title")
            year = source_info.get("year", "Unknown Year")
            
            # Basic citation format
            citation = f"{authors} ({year}). {title}"
            
            # Add journal if available
            if source_info.get("journal"):
                citation += f". {source_info['journal']}"
            
            # Add DOI if available
            if source_info.get("doi"):
                citation += f". DOI: {source_info['doi']}"
            
            return citation
            
        except Exception as e:
            logger.error(f"Error formatting citation: {e}")
            return "Citation formatting error"

# Global instance
psychology_knowledge_service = PsychologyKnowledgeService()