### app/services/vector_service.py

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
import uuid
import torch
from typing import List, Dict, Any, Optional
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self):
        # Initialize ChromaDB but delay model loading
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIRECTORY,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.embedding_model = None  # Load on demand
        self.model_loaded = False
        self.collection = self.client.get_or_create_collection(
            name="journal_entries",
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("🔧 Vector service initialized (embedding model will load on demand)")
        
    async def _ensure_model_loaded(self):
        """Load embedding model on first use"""
        if self.model_loaded:
            return
        
        try:
            # Import hardware service for optimal model selection
            from app.services.hardware_service import hardware_service
            
            # Get optimal embedding model based on hardware
            if not hardware_service.specs:
                await hardware_service.detect_hardware()
            
            embedding_model, use_gpu = hardware_service.get_optimal_model("embeddings")
            
            logger.info(f"🔄 Loading optimal embedding model: {embedding_model} (GPU: {use_gpu})")
            
            self.embedding_model = SentenceTransformer(embedding_model)
            
            # Move to GPU if available and recommended
            if use_gpu and torch.cuda.is_available():
                self.embedding_model = self.embedding_model.to('cuda')
                logger.info("🚀 Embedding model moved to GPU")
            
            self.model_loaded = True
            logger.info("✅ Loaded embedding model on demand")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            # Fallback to basic model
            try:
                self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
                self.model_loaded = True
                logger.info("✅ Loaded basic embedding model as fallback")
            except Exception as fallback_error:
                logger.error(f"Failed to load any embedding model: {fallback_error}")
                self.model_loaded = False

    def _intelligently_process_content(self, content: str, max_chars: int) -> str:
        """
        Intelligently process content for vector embedding while preserving semantic meaning
        """
        if len(content) <= max_chars:
            return content
        
        # For moderate overruns, preserve beginning and end
        if len(content) < max_chars * 1.5:
            first_part_size = int(max_chars * 0.6)
            remaining_size = max_chars - first_part_size - 10
            
            first_part = content[:first_part_size]
            last_part = content[-remaining_size:] if remaining_size > 0 else ""
            
            return f"{first_part}\n...\n{last_part}" if last_part else first_part
        
        # For large texts, extract key paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if not paragraphs:
            # Fallback to sentences
            sentences = [s.strip() for s in content.split('.') if s.strip()]
            if len(sentences) <= 6:
                result = '. '.join(sentences) + '.'
            else:
                result = '. '.join(sentences[:3] + ["..."] + sentences[-3:]) + '.'
            return result[:max_chars] if len(result) > max_chars else result
        
        # Select important paragraphs
        selected_paragraphs = []
        current_length = 0
        
        # Always include first paragraph (context)
        if paragraphs and len(paragraphs[0]) + 4 <= max_chars:
            selected_paragraphs.append(paragraphs[0])
            current_length += len(paragraphs[0]) + 4
        
        # Include last paragraph if space allows
        if len(paragraphs) > 1 and current_length + len(paragraphs[-1]) + 4 <= max_chars:
            selected_paragraphs.append(paragraphs[-1])
            current_length += len(paragraphs[-1]) + 4
        
        # Fill with middle paragraphs
        for para in paragraphs[1:-1]:
            if current_length + len(para) + 4 <= max_chars:
                insert_pos = len(selected_paragraphs) - (1 if len(paragraphs) > 1 and paragraphs[-1] in selected_paragraphs else 0)
                selected_paragraphs.insert(insert_pos, para)
                current_length += len(para) + 4
        
        if selected_paragraphs:
            result = '\n\n'.join(selected_paragraphs)
            return result[:max_chars] if len(result) > max_chars else result
        
        # Final fallback
        return content[:max_chars-3] + "..."
    
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
            # Validate input
            if not content or not content.strip():
                logger.warning(f"Empty content for entry {entry_id}, skipping vector database")
                return
            
            # Smart content processing to preserve important information
            processed_content = self._intelligently_process_content(content, max_chars=8000)
            if processed_content != content:
                logger.debug(f"Processed content for embedding: {len(processed_content)} chars (original: {len(content)})")
            
            # Ensure embedding model is loaded
            await self._ensure_model_loaded()
            
            # Generate embedding with CUDA error handling
            try:
                embedding = self.embedding_model.encode(processed_content).tolist()
            except RuntimeError as cuda_error:
                if "CUDA" in str(cuda_error) or "device-side assert" in str(cuda_error):
                    logger.warning(f"CUDA error in embedding generation, falling back to CPU: {cuda_error}")
                    # Try to move model to CPU and retry
                    self.embedding_model = self.embedding_model.to('cpu')
                    embedding = self.embedding_model.encode(content).tolist()
                else:
                    raise
            
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
            # Don't raise the exception to prevent breaking entry creation
            logger.warning(f"Vector database update failed for entry {entry_id}, but entry was still created")
    
    async def update_entry(self, entry_id: str, content: str, metadata: Dict[str, Any]):
        """Update an entry in the vector database"""
        try:
            # Ensure embedding model is loaded
            await self._ensure_model_loaded()
            
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
            # Ensure embedding model is loaded
            await self._ensure_model_loaded()
            
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