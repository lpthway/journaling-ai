### app/services/vector_service.py

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
import uuid
from typing import List, Dict, Any, Optional
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIRECTORY,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.collection = self.client.get_or_create_collection(
            name="journal_entries",
            metadata={"hnsw:space": "cosine"}
        )
    
    def _prepare_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare metadata for ChromaDB by converting unsupported types"""
        clean_metadata = {}
        
        for key, value in metadata.items():
            if value is None:
                continue
            elif isinstance(value, (str, int, float, bool)):
                clean_metadata[key] = value
            elif isinstance(value, list):
                # Convert lists to comma-separated strings
                if value:  # Only if list is not empty
                    clean_metadata[key] = ','.join(str(item) for item in value)
                # Skip empty lists
            else:
                # Convert other types to string
                clean_metadata[key] = str(value)
        
        return clean_metadata
    
    async def add_entry(self, entry_id: str, content: str, metadata: Dict[str, Any]):
        """Add an entry to the vector database"""
        try:
            # Generate embedding
            embedding = self.embedding_model.encode(content).tolist()
            
            # Prepare metadata for ChromaDB
            clean_metadata = self._prepare_metadata(metadata)
            
            # Add to collection
            self.collection.add(
                ids=[entry_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[clean_metadata]
            )
            logger.info(f"Added entry {entry_id} to vector database")
        except Exception as e:
            logger.error(f"Error adding entry to vector database: {e}")
            raise
    
    async def update_entry(self, entry_id: str, content: str, metadata: Dict[str, Any]):
        """Update an entry in the vector database"""
        try:
            embedding = self.embedding_model.encode(content).tolist()
            
            # Prepare metadata for ChromaDB
            clean_metadata = self._prepare_metadata(metadata)
            
            self.collection.update(
                ids=[entry_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[clean_metadata]
            )
            logger.info(f"Updated entry {entry_id} in vector database")
        except Exception as e:
            logger.error(f"Error updating entry in vector database: {e}")
            raise
    
    async def delete_entry(self, entry_id: str):
        """Delete an entry from the vector database"""
        try:
            self.collection.delete(ids=[entry_id])
            logger.info(f"Deleted entry {entry_id} from vector database")
        except Exception as e:
            logger.error(f"Error deleting entry from vector database: {e}")
            raise
    
    async def search_entries(self, query: str, limit: int = 10, 
                           filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar entries"""
        try:
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Prepare filters for ChromaDB
            where_clause = None
            if filters:
                where_clause = self._prepare_metadata(filters)
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause
            )
            
            search_results = []
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i].copy()
                
                # Convert comma-separated strings back to lists for tags
                if 'tags' in metadata and metadata['tags']:
                    metadata['tags'] = metadata['tags'].split(',')
                
                search_results.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': metadata,
                    'distance': results['distances'][0][i]
                })
            
            return search_results
        except Exception as e:
            logger.error(f"Error searching entries: {e}")
            return []
    
    async def get_all_entries(self) -> List[Dict[str, Any]]:
        """Get all entries from the vector database"""
        try:
            results = self.collection.get()
            entries = []
            
            for i in range(len(results['ids'])):
                metadata = results['metadatas'][i].copy()
                
                # Convert comma-separated strings back to lists for tags
                if 'tags' in metadata and metadata['tags']:
                    metadata['tags'] = metadata['tags'].split(',')
                
                entries.append({
                    'id': results['ids'][i],
                    'content': results['documents'][i],
                    'metadata': metadata
                })
            
            return entries
        except Exception as e:
            logger.error(f"Error getting all entries: {e}")
            return []

# Global instance
vector_service = VectorService()