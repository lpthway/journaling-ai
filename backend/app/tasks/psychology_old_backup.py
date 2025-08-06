# backend/app/tasks/psychology.py
"""
Psychology Document Processing Tasks for Phase 0C
Heavy NLP workloads for research paper analysis, knowledge extraction, and content processing
COMPLETE AND FIXED VERSION - No Truncation
"""

import logging
import asyncio
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import re
from pathlib import Path
import hashlib
import time

# AI and NLP imports
import torch
from transformers import pipeline, AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import nltk
from textblob import TextBlob
import pandas as pd
import numpy as np

# Celery and app imports
from app.services.celery_service import celery_app, monitored_task, TaskPriority, TaskCategory
from app.services.unified_database_service import unified_db_service
from app.services.redis_service import redis_service
from app.core.config import settings
from app.core.performance_monitor import performance_monitor

logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('vader_lexicon', quiet=True)
except:
    logger.warning("Could not download NLTK data - some features may be limited")

class PsychologyProcessor:
    """
    Advanced psychology content processor with caching and performance optimization
    Handles research papers, clinical guidelines, and knowledge extraction
    """
    
    def __init__(self):
        self._embedding_model = None
        self._sentiment_pipeline = None
        self._summarization_pipeline = None
        self._chroma_client = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize AI models with caching and error handling"""
        if self._initialized:
            return
        
        try:
            # Check Redis cache for model availability
            cache_key = "psychology_models_initialized"
            if await redis_service.get(cache_key):
                logger.info("Psychology models already initialized")
                self._initialized = True
                return
            
            logger.info("🤖 Initializing psychology processing models...")
            
            # Initialize embedding model (cached in Redis)
            embedding_cache_key = "embedding_model_ready"
            if not await redis_service.get(embedding_cache_key):
                self._embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
                await redis_service.set(embedding_cache_key, True, ttl=86400)
                logger.info(f"✅ Loaded embedding model: {settings.EMBEDDING_MODEL}")
            
            # Initialize sentiment analysis pipeline
            sentiment_cache_key = "sentiment_model_ready"
            if not await redis_service.get(sentiment_cache_key):
                self._sentiment_pipeline = pipeline(
                    "text-classification",
                    model=settings.SENTIMENT_MODEL,
                    return_all_scores=True
                )
                await redis_service.set(sentiment_cache_key, True, ttl=86400)
                logger.info(f"✅ Loaded sentiment model: {settings.SENTIMENT_MODEL}")
            
            # Initialize summarization pipeline for research papers
            summarization_cache_key = "summarization_model_ready"
            if not await redis_service.get(summarization_cache_key):
                self._summarization_pipeline = pipeline(
                    "summarization",
                    model="facebook/bart-large-cnn",
                    max_length=150,
                    min_length=50,
                    do_sample=False
                )
                await redis_service.set(summarization_cache_key, True, ttl=86400)
                logger.info("✅ Loaded summarization model: facebook/bart-large-cnn")
            
            # Initialize ChromaDB for vector storage
            chroma_cache_key = "chroma_client_ready"
            if not await redis_service.get(chroma_cache_key):
                self._chroma_client = chromadb.PersistentClient(
                    path=settings.CHROMA_PERSIST_DIRECTORY,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                await redis_service.set(chroma_cache_key, True, ttl=86400)
                logger.info(f"✅ Initialized ChromaDB: {settings.CHROMA_PERSIST_DIRECTORY}")
            
            # Mark as initialized
            await redis_service.set(cache_key, True, ttl=86400)
            self._initialized = True
            
            logger.info("🎯 Psychology processing models fully initialized")
            
        except Exception as e:
            logger.error(f"❌ Error initializing psychology processor: {e}")
            raise
    
    def _ensure_models_loaded(self):
        """Lazy load models if not initialized"""
        if not self._initialized:
            # For synchronous task execution, initialize models synchronously
            if not self._embedding_model:
                self._embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            
            if not self._sentiment_pipeline:
                self._sentiment_pipeline = pipeline(
                    "text-classification",
                    model=settings.SENTIMENT_MODEL,
                    return_all_scores=True
                )
            
            if not self._summarization_pipeline:
                self._summarization_pipeline = pipeline(
                    "summarization",
                    model="facebook/bart-large-cnn",
                    max_length=150,
                    min_length=50
                )
            
            if not self._chroma_client:
                self._chroma_client = chromadb.PersistentClient(
                    path=settings.CHROMA_PERSIST_DIRECTORY
                )
            
            self._initialized = True
    
    def extract_research_paper_content(self, text: str) -> Dict[str, Any]:
        """
        Extract structured content from research paper text
        Identifies abstract, introduction, methodology, results, conclusion
        """
        try:
            # Common section headers in psychology papers
            section_patterns = {
                'abstract': r'(?i)(abstract|summary)\s*\n',
                'introduction': r'(?i)(introduction|background)\s*\n',
                'methodology': r'(?i)(method|methodology|procedure|participants)\s*\n',
                'results': r'(?i)(results|findings|analysis)\s*\n',
                'discussion': r'(?i)(discussion|interpretation)\s*\n',
                'conclusion': r'(?i)(conclusion|summary|implications)\s*\n',
                'references': r'(?i)(references|bibliography|citations)\s*\n'
            }
            
            # Extract sections
            sections = {}
            text_lower = text.lower()
            
            for section_name, pattern in section_patterns.items():
                matches = list(re.finditer(pattern, text, re.MULTILINE))
                if matches:
                    start_pos = matches[0].end()
                    
                    # Find end position (next section or end of text)
                    end_pos = len(text)
                    for other_section, other_pattern in section_patterns.items():
                        if other_section != section_name:
                            other_matches = list(re.finditer(other_pattern, text[start_pos:], re.MULTILINE))
                            if other_matches:
                                potential_end = start_pos + other_matches[0].start()
                                if potential_end > start_pos and potential_end < end_pos:
                                    end_pos = potential_end
                    
                    section_content = text[start_pos:end_pos].strip()
                    if section_content:
                        sections[section_name] = section_content[:2000]  # Limit length
            
            # Extract key metadata
            metadata = {
                'word_count': len(text.split()),
                'estimated_reading_time': max(1, len(text.split()) // 200),
                'sections_found': list(sections.keys()),
                'total_sections': len(sections),
                'content_type': 'research_paper'
            }
            
            # Extract potential citations (basic pattern matching)
            citation_pattern = r'\([A-Za-z]+(?:\s+(?:&|and)\s+[A-Za-z]+)*,\s+\d{4}\)'
            citations = re.findall(citation_pattern, text)
            metadata['citation_count'] = len(citations)
            metadata['citations_sample'] = citations[:10]  # First 10 citations
            
            return {
                'sections': sections,
                'metadata': metadata,
                'processing_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error extracting research paper content: {e}")
            return {
                'sections': {},
                'metadata': {'error': str(e)},
                'processing_timestamp': datetime.utcnow().isoformat()
            }
    
    def generate_embeddings(self, text_chunks: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks with batching"""
        try:
            self._ensure_models_loaded()
            
            # Process in batches to avoid memory issues
            batch_size = 32
            all_embeddings = []
            
            for i in range(0, len(text_chunks), batch_size):
                batch = text_chunks[i:i + batch_size]
                batch_embeddings = self._embedding_model.encode(
                    batch,
                    convert_to_tensor=False,
                    show_progress_bar=False
                )
                all_embeddings.extend(batch_embeddings.tolist())
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return []
    
    def analyze_psychological_content(self, text: str) -> Dict[str, Any]:
        """
        Analyze psychological themes, concepts, and emotional content
        """
        try:
            self._ensure_models_loaded()
            
            # Sentiment analysis with detailed emotions
            sentiment_results = self._sentiment_pipeline(text[:512])  # Limit for model
            sentiment_scores = {result['label']: result['score'] for result in sentiment_results[0]}
            
            # Extract psychological keywords and concepts
            psych_keywords = {
                'cognitive': ['cognitive', 'thinking', 'perception', 'memory', 'attention', 'reasoning'],
                'behavioral': ['behavior', 'behavioural', 'conditioning', 'reinforcement', 'habit'],
                'emotional': ['emotion', 'emotional', 'mood', 'feeling', 'affect', 'anxiety', 'depression'],
                'social': ['social', 'interpersonal', 'relationship', 'communication', 'group'],
                'developmental': ['development', 'developmental', 'childhood', 'adolescence', 'maturation'],
                'clinical': ['therapy', 'treatment', 'intervention', 'clinical', 'disorder', 'diagnosis']
            }
            
            keyword_counts = {}
            text_lower = text.lower()
            
            for category, keywords in psych_keywords.items():
                count = sum(text_lower.count(keyword) for keyword in keywords)
                keyword_counts[category] = count
            
            # Identify dominant psychological domain
            dominant_domain = max(keyword_counts, key=keyword_counts.get) if keyword_counts else 'general'
            
            # Extract key phrases (simplified approach)
            sentences = text.split('.')[:10]  # First 10 sentences
            key_phrases = [s.strip() for s in sentences if len(s.strip()) > 20]
            
            return {
                'sentiment_analysis': sentiment_scores,
                'psychological_domains': keyword_counts,
                'dominant_domain': dominant_domain,
                'key_phrases': key_phrases[:5],  # Top 5 phrases
                'content_complexity': 'high' if len(text.split()) > 1000 else 'medium' if len(text.split()) > 300 else 'low',
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing psychological content: {e}")
            return {
                'sentiment_analysis': {},
                'psychological_domains': {},
                'error': str(e),
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
    
    def store_knowledge_vectors(self, document_id: str, text_chunks: List[str], embeddings: List[List[float]], metadata: Dict[str, Any]) -> bool:
        """Store document embeddings in ChromaDB with metadata"""
        try:
            self._ensure_models_loaded()
            
            # Get or create collection
            collection_name = "psychology_knowledge"
            try:
                collection = self._chroma_client.get_collection(collection_name)
            except:
                collection = self._chroma_client.create_collection(
                    name=collection_name,
                    metadata={"description": "Psychology research paper knowledge base"}
                )
            
            # Prepare documents for storage
            chunk_ids = [f"{document_id}_chunk_{i}" for i in range(len(text_chunks))]
            chunk_metadata = [
                {
                    **metadata,
                    'document_id': document_id,
                    'chunk_index': i,
                    'chunk_text_length': len(chunk),
                    'storage_timestamp': datetime.utcnow().isoformat()
                }
                for i, chunk in enumerate(text_chunks)
            ]
            
            # Store in ChromaDB
            collection.add(
                documents=text_chunks,
                embeddings=embeddings,
                metadatas=chunk_metadata,
                ids=chunk_ids
            )
            
            logger.info(f"✅ Stored {len(text_chunks)} knowledge chunks for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing knowledge vectors: {e}")
            return False

# Global psychology processor instance
psychology_processor = PsychologyProcessor()

# === PSYCHOLOGY PROCESSING TASKS ===

@monitored_task(priority=TaskPriority.HIGH, category=TaskCategory.PSYCHOLOGY_PROCESSING)
def process_research_paper(self, document_id: str, document_text: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Process psychology research paper for knowledge extraction and storage
    
    Args:
        document_id: Unique document identifier
        document_text: Full text of the research paper
        metadata: Additional document metadata
    
    Returns:
        Processing results with extracted knowledge
    """
    try:
        start_time = time.time()
        
        logger.info(f"📄 Processing research paper: {document_id}")
        
        # Check if already processed (cache)
        cache_key = f"processed_paper:{document_id}"
        cached_result = asyncio.run(redis_service.get(cache_key))
        if cached_result:
            logger.info(f"🚀 Using cached result for document {document_id}")
            return cached_result
        
        # Initialize processor
        psychology_processor._ensure_models_loaded()
        
        # Extract structured content
        content_analysis = psychology_processor.extract_research_paper_content(document_text)
        
        # Generate summary if abstract not found
        if 'abstract' not in content_analysis['sections'] and psychology_processor._summarization_pipeline:
            try:
                # Summarize first 1000 words
                text_to_summarize = document_text[:1000]
                summary_result = psychology_processor._summarization_pipeline(text_to_summarize)
                content_analysis['sections']['generated_summary'] = summary_result[0]['summary_text']
            except Exception as e:
                logger.warning(f"Could not generate summary: {e}")
        
        # Analyze psychological content
        psych_analysis = psychology_processor.analyze_psychological_content(document_text)
        
        # Create text chunks for embeddings (sentences or paragraphs)
        text_chunks = []
        chunk_size = 500  # Words per chunk
        words = document_text.split()
        
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            if len(chunk.strip()) > 50:  # Only meaningful chunks
                text_chunks.append(chunk)
        
        # Generate embeddings
        logger.info(f"🧠 Generating embeddings for {len(text_chunks)} chunks")
        embeddings = psychology_processor.generate_embeddings(text_chunks)
        
        # Prepare metadata for storage
        storage_metadata = {
            **(metadata or {}),
            'processing_date': datetime.utcnow().isoformat(),
            'sections_extracted': content_analysis['metadata']['sections_found'],
            'dominant_psych_domain': psych_analysis['dominant_domain'],
            'content_complexity': psych_analysis['content_complexity'],
            'word_count': content_analysis['metadata']['word_count']
        }
        
        # Store knowledge vectors
        vector_storage_success = psychology_processor.store_knowledge_vectors(
            document_id, text_chunks, embeddings, storage_metadata
        )
        
        # Compile results
        processing_results = {
            'document_id': document_id,
            'processing_status': 'completed',
            'content_analysis': content_analysis,
            'psychological_analysis': psych_analysis,
            'knowledge_storage': {
                'success': vector_storage_success,
                'chunks_stored': len(text_chunks),
                'embeddings_generated': len(embeddings)
            },
            'processing_time_seconds': time.time() - start_time,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Cache results
        asyncio.run(redis_service.set(cache_key, processing_results, ttl=3600))  # 1 hour cache
        
        logger.info(f"✅ Research paper processing completed: {document_id} in {processing_results['processing_time_seconds']:.1f}s")
        
        return processing_results
        
    except Exception as e:
        error_result = {
            'document_id': document_id,
            'processing_status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.error(f"❌ Research paper processing failed: {document_id} - {e}")
        return error_result

@monitored_task(priority=TaskPriority.HIGH, category=TaskCategory.PSYCHOLOGY_PROCESSING)
def extract_clinical_guidelines(self, guideline_text: str, guideline_type: str = "general") -> Dict[str, Any]:
    """
    Extract actionable clinical guidelines and recommendations
    
    Args:
        guideline_text: Clinical guideline document text
        guideline_type: Type of guidelines (therapy, assessment, intervention)
    
    Returns:
        Extracted guidelines with structured recommendations
    """
    try:
        start_time = time.time()
        
        logger.info(f"📋 Extracting clinical guidelines: {guideline_type}")
        
        # Ensure models are loaded
        psychology_processor._ensure_models_loaded()
        
        # Extract recommendations (look for specific patterns)
        recommendation_patterns = [
            r'(?i)(?:recommend|suggest|advise|should|must|ought to)([^.]+)',
            r'(?i)(?:it is recommended|best practice|guidelines suggest)([^.]+)',
            r'(?i)(?:clinical guideline|treatment recommendation)([^.]+)'
        ]
        
        recommendations = []
        for pattern in recommendation_patterns:
            matches = re.findall(pattern, guideline_text)
            recommendations.extend([match.strip() for match in matches if len(match.strip()) > 10])
        
        # Remove duplicates and limit
        recommendations = list(set(recommendations))[:20]
        
        # Extract intervention strategies
        intervention_keywords = [
            'cognitive behavioral therapy', 'cbt', 'mindfulness', 'exposure therapy',
            'psychoeducation', 'skill building', 'behavioral activation',
            'acceptance and commitment therapy', 'dialectical behavior therapy'
        ]
        
        found_interventions = []
        text_lower = guideline_text.lower()
        for intervention in intervention_keywords:
            if intervention in text_lower:
                # Extract context around the intervention
                start_idx = text_lower.find(intervention)
                context = guideline_text[max(0, start_idx-100):start_idx+200]
                found_interventions.append({
                    'intervention': intervention,
                    'context': context.strip()
                })
        
        # Analyze psychological content
        psych_analysis = psychology_processor.analyze_psychological_content(guideline_text)
        
        # Extract key assessment criteria
        assessment_patterns = [
            r'(?i)(?:assess|evaluate|measure|screen for)([^.]+)',
            r'(?i)(?:diagnostic criteria|assessment tool|screening)([^.]+)'
        ]
        
        assessment_criteria = []
        for pattern in assessment_patterns:
            matches = re.findall(pattern, guideline_text)
            assessment_criteria.extend([match.strip() for match in matches if len(match.strip()) > 10])
        
        # Compile guideline extraction results
        guideline_results = {
            'guideline_type': guideline_type,
            'extraction_status': 'completed',
            'recommendations': {
                'total_found': len(recommendations),
                'items': recommendations[:10]  # Top 10 recommendations
            },
            'interventions': {
                'total_found': len(found_interventions),
                'items': found_interventions
            },
            'assessment_criteria': {
                'total_found': len(assessment_criteria),
                'items': assessment_criteria[:10]  # Top 10 criteria
            },
            'psychological_analysis': psych_analysis,
            'metadata': {
                'text_length': len(guideline_text),
                'word_count': len(guideline_text.split()),
                'processing_time_seconds': time.time() - start_time
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Clinical guidelines extracted: {len(recommendations)} recommendations, {len(found_interventions)} interventions")
        
        return guideline_results
        
    except Exception as e:
        error_result = {
            'guideline_type': guideline_type,
            'extraction_status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.error(f"❌ Clinical guideline extraction failed: {e}")
        return error_result

@monitored_task(priority=TaskPriority.NORMAL, category=TaskCategory.PSYCHOLOGY_PROCESSING)
def analyze_journal_entry_patterns(self, user_id: str, entry_texts: List[str], analyze_trends: bool = True) -> Dict[str, Any]:
    """
    Analyze psychological patterns in user journal entries
    
    Args:
        user_id: User identifier
        entry_texts: List of journal entry texts
        analyze_trends: Whether to analyze trends over time
    
    Returns:
        Pattern analysis results with insights
    """
    try:
        start_time = time.time()
        
        logger.info(f"🔍 Analyzing journal patterns for user {user_id}: {len(entry_texts)} entries")
        
        # Check cache first
        cache_key = f"journal_patterns:{user_id}:{len(entry_texts)}"
        cached_result = asyncio.run(redis_service.get(cache_key))
        if cached_result:
            logger.info(f"🚀 Using cached pattern analysis for user {user_id}")
            return cached_result
        
        # Initialize processor
        psychology_processor._ensure_models_loaded()
        
        # Analyze each entry
        entry_analyses = []
        for i, entry_text in enumerate(entry_texts):
            if len(entry_text.strip()) < 20:  # Skip very short entries
                continue
                
            analysis = psychology_processor.analyze_psychological_content(entry_text)
            analysis['entry_index'] = i
            analysis['entry_length'] = len(entry_text.split())
            entry_analyses.append(analysis)
        
        if not entry_analyses:
            return {
                'user_id': user_id,
                'analysis_status': 'no_content',
                'message': 'No substantial entries to analyze',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Aggregate psychological domains across entries
        domain_totals = {}
        sentiment_totals = {}
        complexity_counts = {'low': 0, 'medium': 0, 'high': 0}
        
        for analysis in entry_analyses:
            # Aggregate psychological domains
            for domain, count in analysis['psychological_domains'].items():
                domain_totals[domain] = domain_totals.get(domain, 0) + count
            
            # Aggregate sentiment scores
            for emotion, score in analysis['sentiment_analysis'].items():
                if emotion not in sentiment_totals:
                    sentiment_totals[emotion] = []
                sentiment_totals[emotion].append(score)
            
            # Count complexity levels
            complexity = analysis.get('content_complexity', 'medium')
            complexity_counts[complexity] += 1
        
        # Calculate averages and patterns
        avg_sentiments = {}
        for emotion, scores in sentiment_totals.items():
            avg_sentiments[emotion] = sum(scores) / len(scores) if scores else 0
        
        # Identify dominant patterns
        dominant_domain = max(domain_totals, key=domain_totals.get) if domain_totals else 'general'
        dominant_emotion = max(avg_sentiments, key=avg_sentiments.get) if avg_sentiments else 'neutral'
        
        # Generate insights
        insights = []
        
        # Domain insights
        if domain_totals.get('emotional', 0) > sum(domain_totals.values()) * 0.3:
            insights.append("High emotional content - focus on emotional processing and regulation")
        
        if domain_totals.get('cognitive', 0) > sum(domain_totals.values()) * 0.3:
            insights.append("Strong cognitive patterns - good for thought analysis and reframing")
        
        if domain_totals.get('social', 0) > sum(domain_totals.values()) * 0.3:
            insights.append("Social themes prominent - relationship and interpersonal focus")
        
        # Sentiment insights
        if avg_sentiments.get('sadness', 0) > 0.6:
            insights.append("Elevated sadness levels - consider mood tracking and support resources")
        
        if avg_sentiments.get('joy', 0) > 0.5:
            insights.append("Positive emotional tone - good mental health indicators")
        
        # Compile pattern analysis results
        pattern_results = {
            'user_id': user_id,
            'analysis_status': 'completed',
            'entries_analyzed': len(entry_analyses),
            'psychological_patterns': {
                'domain_distribution': domain_totals,
                'dominant_domain': dominant_domain,
                'sentiment_averages': avg_sentiments,
                'dominant_emotion': dominant_emotion,
                'complexity_distribution': complexity_counts
            },
            'insights': insights,
            'recommendations': {
                'focus_areas': [dominant_domain, 'emotional regulation'],
                'suggested_techniques': [
                    'mindfulness practice' if 'emotional' in dominant_domain else 'cognitive restructuring',
                    'journaling prompts for ' + dominant_domain,
                    'mood tracking'
                ]
            },
            'metadata': {
                'total_words_analyzed': sum(analysis['entry_length'] for analysis in entry_analyses),
                'avg_entry_length': sum(analysis['entry_length'] for analysis in entry_analyses) / len(entry_analyses),
                'processing_time_seconds': time.time() - start_time
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Cache results
        asyncio.run(redis_service.set(cache_key, pattern_results, ttl=1800))  # 30 minutes cache
        
        logger.info(f"✅ Journal pattern analysis completed for user {user_id}: {len(insights)} insights generated")
        
        return pattern_results
        
    except Exception as e:
        error_result = {
            'user_id': user_id,
            'analysis_status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.error(f"❌ Journal pattern analysis failed for user {user_id}: {e}")
        return error_result

@monitored_task(priority=TaskPriority.NORMAL, category=TaskCategory.PSYCHOLOGY_PROCESSING)
def generate_personalized_insights(self, user_id: str, recent_entries: List[Dict[str, Any]], user_preferences: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generate personalized psychological insights based on user's journal entries
    
    Args:
        user_id: User identifier
        recent_entries: Recent journal entries with metadata
        user_preferences: User preferences for insight generation
    
    Returns:
        Personalized insights and recommendations
    """
    try:
        start_time = time.time()
        
        logger.info(f"💡 Generating personalized insights for user {user_id}")
        
        # Ensure processor is initialized
        psychology_processor._ensure_models_loaded()
        
        # Extract texts for analysis
        entry_texts = [entry.get('content', '') for entry in recent_entries if entry.get('content')]
        
        if not entry_texts:
            return {
                'user_id': user_id,
                'insight_status': 'no_content',
                'message': 'No recent entries available for analysis',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Analyze patterns using existing task
        pattern_analysis = analyze_journal_entry_patterns.apply_async(
            args=[user_id, entry_texts, True]
        ).get()
        
        if pattern_analysis.get('analysis_status') != 'completed':
            return pattern_analysis  # Return error if pattern analysis failed
        
        # Generate personalized recommendations based on patterns
        patterns = pattern_analysis['psychological_patterns']
        dominant_domain = patterns['dominant_domain']
        sentiment_averages = patterns['sentiment_averages']
        
        # Personalized insights based on psychological domains
        personalized_insights = []
        
        if dominant_domain == 'emotional':
            personalized_insights.extend([
                "Your writing shows rich emotional awareness - a strength for mental health",
                "Consider exploring emotion regulation techniques like mindfulness or breathing exercises",
                "Your emotional vocabulary is developing - keep expressing feelings in detail"
            ])
        
        elif dominant_domain == 'cognitive':
            personalized_insights.extend([
                "You show strong analytical thinking in your reflections",
                "Your cognitive awareness is a valuable tool for problem-solving",
                "Consider cognitive restructuring techniques to challenge negative thought patterns"
            ])
        
        elif dominant_domain == 'social':
            personalized_insights.extend([
                "Relationships and social connections are important themes in your writing",
                "Your social awareness indicates good interpersonal intelligence",
                "Consider journaling about communication patterns and relationship goals"
            ])
        
        # Sentiment-based insights
        if sentiment_averages.get('joy', 0) > 0.5:
            personalized_insights.append("Your positive emotional tone suggests good psychological resilience")
        
        if sentiment_averages.get('sadness', 0) > 0.4:
            personalized_insights.append("Consider incorporating mood-lifting activities or reaching out for support")
        
        # Generate specific journal prompts
        journal_prompts = []
        
        if dominant_domain == 'emotional':
            journal_prompts.extend([
                "What emotions did I experience most strongly today, and what triggered them?",
                "How can I better support myself when I'm feeling overwhelmed?",
                "What are three things I'm grateful for right now?"
            ])
        
        elif dominant_domain == 'cognitive':
            journal_prompts.extend([
                "What thoughts kept coming back to me today? Are they helpful or unhelpful?",
                "What evidence supports or challenges my current concerns?",
                "What would I tell a friend facing the same situation?"
            ])
        
        elif dominant_domain == 'social':
            journal_prompts.extend([
                "How did my interactions with others make me feel today?",
                "What communication patterns do I notice in my relationships?",
                "Who are the people that bring out the best in me?"
            ])
        
        # Compile personalized insights
        insight_results = {
            'user_id': user_id,
            'insight_status': 'completed',
            'personalized_insights': personalized_insights,
            'journal_prompts': journal_prompts,
            'focus_recommendations': {
                'primary_focus': dominant_domain,
                'secondary_focuses': [domain for domain, count in patterns['domain_distribution'].items() 
                                    if domain != dominant_domain and count > 0][:2],
                'suggested_practices': [
                    'Daily emotional check-ins' if dominant_domain == 'emotional' else 'Thought pattern tracking',
                    'Mindfulness meditation',
                    'Regular reflection sessions'
                ]
            },
            'pattern_summary': pattern_analysis['psychological_patterns'],
            'metadata': {
                'entries_analyzed': len(entry_texts),
                'insight_generation_time': time.time() - start_time,
                'preferences_applied': bool(user_preferences)
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Personalized insights generated for user {user_id}: {len(personalized_insights)} insights")
        
        return insight_results
        
    except Exception as e:
        error_result = {
            'user_id': user_id,
            'insight_status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.error(f"❌ Personalized insight generation failed for user {user_id}: {e}")
        return error_result

@monitored_task(priority=TaskPriority.NORMAL, category=TaskCategory.PSYCHOLOGY_PROCESSING)
def process_pending_documents(self) -> Dict[str, Any]:
    """
    Scheduled task to process pending psychology documents in queue
    """
    try:
        start_time = time.time()
        
        logger.info("📚 Processing pending psychology documents")
        
        # Get pending documents from Redis queue
        pending_docs = asyncio.run(redis_service.get("pending_psychology_docs"))
        
        if not pending_docs:
            return {
                'task_status': 'completed',
                'documents_processed': 0,
                'message': 'No pending documents to process',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        processed_count = 0
        processing_results = []
        
        for doc_info in pending_docs[:5]:  # Process up to 5 documents per batch
            try:
                doc_id = doc_info.get('document_id')
                doc_text = doc_info.get('text')
                doc_metadata = doc_info.get('metadata', {})
                
                # Process the document
                result = process_research_paper.apply(
                    args=[doc_id, doc_text, doc_metadata]
                )
                
                processing_results.append({
                    'document_id': doc_id,
                    'status': result.get('processing_status', 'unknown'),
                    'processing_time': result.get('processing_time_seconds', 0)
                })
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing document {doc_info.get('document_id', 'unknown')}: {e}")
                processing_results.append({
                    'document_id': doc_info.get('document_id', 'unknown'),
                    'status': 'failed',
                    'error': str(e)
                })
        
        # Update pending queue (remove processed documents)
        remaining_docs = pending_docs[processed_count:]
        asyncio.run(redis_service.set("pending_psychology_docs", remaining_docs, ttl=86400))
        
        batch_results = {
            'task_status': 'completed',
            'documents_processed': processed_count,
            'processing_results': processing_results,
            'remaining_in_queue': len(remaining_docs),
            'total_processing_time': time.time() - start_time,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Batch processing completed: {processed_count} documents processed")
        
        return batch_results
        
    except Exception as e:
        error_result = {
            'task_status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.error(f"❌ Psychology document batch processing failed: {e}")
        return error_result

# === UTILITY FUNCTIONS FOR PSYCHOLOGY PROCESSING ===

async def queue_document_for_processing(
    document_id: str, 
    document_text: str, 
    metadata: Dict[str, Any] = None,
    priority: TaskPriority = TaskPriority.HIGH
) -> str:
    """
    Queue a psychology document for background processing
    
    Args:
        document_id: Unique document identifier
        document_text: Document content
        metadata: Additional metadata
        priority: Processing priority
    
    Returns:
        Task ID for tracking
    """
    try:
        # Dispatch processing task
        task_result = process_research_paper.apply_async(
            args=[document_id, document_text, metadata],
            priority=priority.value
        )
        
        logger.info(f"📄 Queued document for processing: {document_id} [Task: {task_result.id}]")
        
        # Store task reference for tracking
        await redis_service.set(
            f"doc_processing_task:{document_id}",
            {
                'task_id': task_result.id,
                'status': 'queued',
                'queued_at': datetime.utcnow().isoformat()
            },
            ttl=3600  # 1 hour
        )
        
        return task_result.id
        
    except Exception as e:
        logger.error(f"Error queuing document for processing: {e}")
        raise

async def get_knowledge_search_results(
    query: str, 
    limit: int = 10,
    similarity_threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Search psychology knowledge base using semantic similarity
    
    Args:
        query: Search query
        limit: Maximum results to return
        similarity_threshold: Minimum similarity score
    
    Returns:
        List of relevant knowledge chunks with metadata
    """
    try:
        # Initialize processor and ensure models are loaded
        psychology_processor._ensure_models_loaded()
        
        # Generate query embedding
        query_embedding = psychology_processor._embedding_model.encode([query])[0].tolist()
        
        # Search in ChromaDB
        collection = psychology_processor._chroma_client.get_collection("psychology_knowledge")
        
        search_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = []
        
        if search_results['documents'] and search_results['documents'][0]:
            for i, (doc, metadata, distance) in enumerate(zip(
                search_results['documents'][0],
                search_results['metadatas'][0],
                search_results['distances'][0]
            )):
                similarity_score = 1 - distance  # Convert distance to similarity
                
                if similarity_score >= similarity_threshold:
                    formatted_results.append({
                        'content': doc,
                        'metadata': metadata,
                        'similarity_score': similarity_score,
                        'relevance_rank': i + 1
                    })
        
        logger.info(f"🔍 Knowledge search returned {len(formatted_results)} results for query: {query[:50]}...")
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        return []

async def get_processing_status(document_id: str) -> Dict[str, Any]:
    """
    Get processing status for a queued document
    
    Args:
        document_id: Document identifier
    
    Returns:
        Processing status information
    """
    try:
        # Get task reference
        task_info = await redis_service.get(f"doc_processing_task:{document_id}")
        
        if not task_info:
            return {
                'document_id': document_id,
                'status': 'not_found',
                'message': 'No processing task found for this document'
            }
        
        task_id = task_info['task_id']
        
        # Get task status from Celery
        from app.services.celery_service import celery_service
        task_status = await celery_service.get_task_status(task_id)
        
        return {
            'document_id': document_id,
            'task_id': task_id,
            'status': task_status.get('state', 'unknown'),
            'queued_at': task_info.get('queued_at'),
            'result': task_status.get('result'),
            'error': task_status.get('error'),
            'ready': task_status.get('ready', False),
            'successful': task_status.get('successful', False),
            'failed': task_status.get('failed', False)
        }
        
    except Exception as e:
        logger.error(f"Error getting processing status for {document_id}: {e}")
        return {
            'document_id': document_id,
            'status': 'error',
            'error': str(e)
        }

# === PSYCHOLOGY KNOWLEDGE MANAGEMENT ===

async def initialize_psychology_knowledge_base():
    """Initialize psychology knowledge base with pre-loaded content"""
    try:
        logger.info("🧠 Initializing psychology knowledge base...")
        
        # Initialize processor
        await psychology_processor.initialize()
        
        # Check if already initialized
        init_status = await redis_service.get("psychology_kb_initialized")
        if init_status:
            logger.info("Psychology knowledge base already initialized")
            return True
        
        # Load sample psychology content (this would be replaced with actual content loading)
        sample_documents = [
            {
                'id': 'cbt_basics',
                'title': 'Cognitive Behavioral Therapy Fundamentals',
                'content': """
                Cognitive Behavioral Therapy (CBT) is a widely-used therapeutic approach that focuses on identifying and changing negative thought patterns and behaviors. The core principle of CBT is that our thoughts, feelings, and behaviors are interconnected. By changing our thoughts and behaviors, we can improve our emotional well-being.

                Key CBT techniques include:
                1. Cognitive restructuring - identifying and challenging negative thought patterns
                2. Behavioral activation - engaging in positive activities to improve mood
                3. Exposure therapy - gradually facing feared situations
                4. Mindfulness and grounding techniques
                5. Problem-solving skills training

                CBT has been extensively researched and proven effective for treating depression, anxiety, PTSD, and many other mental health conditions. The approach is typically short-term, goal-oriented, and focuses on practical skills that clients can use independently.
                """,
                'metadata': {
                    'category': 'therapy_approach',
                    'evidence_level': 'high',
                    'applications': ['depression', 'anxiety', 'PTSD']
                }
            },
            {
                'id': 'mindfulness_research',
                'title': 'Mindfulness-Based Interventions in Mental Health',
                'content': """
                Mindfulness-based interventions have gained significant attention in mental health treatment. Research shows that mindfulness practices can reduce symptoms of anxiety, depression, and chronic pain while improving overall well-being.

                Mindfulness involves paying attention to the present moment without judgment. Key components include:
                1. Awareness of thoughts and feelings without attachment
                2. Acceptance of current experience
                3. Non-judgmental observation
                4. Focus on breath and bodily sensations

                Mindfulness-Based Stress Reduction (MBSR) and Mindfulness-Based Cognitive Therapy (MBCT) are structured programs that combine mindfulness meditation with cognitive therapy techniques. Studies indicate significant improvements in emotional regulation, attention, and stress management.

                Neuroimaging research shows that regular mindfulness practice leads to structural changes in the brain, particularly in areas related to attention, emotional regulation, and self-awareness.
                """,
                'metadata': {
                    'category': 'mindfulness',
                    'evidence_level': 'high',
                    'applications': ['stress', 'anxiety', 'depression', 'chronic_pain']
                }
            }
        ]
        
        # Process sample documents
        for doc in sample_documents:
            try:
                # Queue document for processing
                task_result = process_research_paper.apply_async(
                    args=[doc['id'], doc['content'], doc['metadata']]
                )
                
                logger.info(f"✅ Queued sample document: {doc['title']}")
                
            except Exception as e:
                logger.error(f"Error processing sample document {doc['id']}: {e}")
        
        # Mark as initialized
        await redis_service.set("psychology_kb_initialized", True, ttl=86400)
        
        logger.info("✅ Psychology knowledge base initialization completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error initializing psychology knowledge base: {e}")
        return False

# === PSYCHOLOGY TASK MONITORING ===

async def get_psychology_processing_stats() -> Dict[str, Any]:
    """Get comprehensive statistics for psychology processing tasks"""
    try:
        # Get task counters from Redis
        total_processed = await redis_service.get("task_counter:psychology") or 0
        successful_processed = await redis_service.get("task_success:psychology") or 0
        failed_processed = await redis_service.get("task_failure:psychology") or 0
        
        # Calculate success rate
        success_rate = (successful_processed / max(total_processed, 1)) * 100
        
        # Get pending documents count
        pending_docs = await redis_service.get("pending_psychology_docs") or []
        pending_count = len(pending_docs)
        
        # Get processing queue status (would require Celery inspection)
        queue_stats = {
            'psychology_queue_size': 0,  # Would be populated with actual queue inspection
            'active_workers': 0,
            'average_processing_time': 0.0
        }
        
        stats = {
            'processing_statistics': {
                'total_documents_processed': total_processed,
                'successful_processing': successful_processed,
                'failed_processing': failed_processed,
                'success_rate_percentage': round(success_rate, 2),
                'pending_documents': pending_count
            },
            'queue_statistics': queue_stats,
            'knowledge_base': {
                'initialized': bool(await redis_service.get("psychology_kb_initialized")),
                'total_chunks_stored': 0,  # Would be populated with actual ChromaDB count
                'collections': ['psychology_knowledge']
            },
            'performance_metrics': {
                'average_processing_time_seconds': 0.0,
                'cache_hit_rate': 0.0,
                'model_initialization_status': bool(await redis_service.get("psychology_models_initialized"))
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting psychology processing stats: {e}")
        return {
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

# === ADVANCED PSYCHOLOGY ANALYSIS FEATURES ===

@monitored_task(priority=TaskPriority.NORMAL, category=TaskCategory.PSYCHOLOGY_PROCESSING)
def analyze_emotional_trajectory(self, user_id: str, days_back: int = 30) -> Dict[str, Any]:
    """
    Analyze emotional trajectory over time for psychological insights
    
    Args:
        user_id: User identifier
        days_back: Number of days to analyze
    
    Returns:
        Emotional trajectory analysis with trends and recommendations
    """
    try:
        start_time = time.time()
        
        logger.info(f"📈 Analyzing emotional trajectory for user {user_id}")
        
        # Get entries from the specified time period
        entries = asyncio.run(unified_db_service.get_entries(
            user_id=user_id,
            date_from=datetime.utcnow() - timedelta(days=days_back),
            limit=200
        ))
        
        if not entries:
            return {
                'user_id': user_id,
                'analysis_status': 'no_data',
                'message': f'No entries found for the last {days_back} days',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Ensure models are loaded
        psychology_processor._ensure_models_loaded()
        
        # Analyze emotional content over time
        emotional_timeline = []
        
        for entry in entries:
            if entry.content and len(entry.content.strip()) > 20:
                # Analyze psychological content
                analysis = psychology_processor.analyze_psychological_content(entry.content)
                
                emotional_timeline.append({
                    'date': entry.created_at.date().isoformat(),
                    'sentiment_scores': analysis['sentiment_analysis'],
                    'dominant_domain': analysis['dominant_domain'],
                    'emotional_keywords': analysis['psychological_domains'].get('emotional', 0),
                    'entry_id': str(entry.id),
                    'word_count': len(entry.content.split())
                })
        
        if not emotional_timeline:
            return {
                'user_id': user_id,
                'analysis_status': 'insufficient_content',
                'message': 'No substantial content found for analysis',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Calculate trajectory metrics
        sentiment_trend = []
        emotional_volatility = []
        
        for item in emotional_timeline:
            # Extract primary sentiment score
            sentiments = item['sentiment_scores']
            primary_sentiment = max(sentiments.items(), key=lambda x: x[1])[1] if sentiments else 0
            sentiment_trend.append(primary_sentiment)
        
        # Calculate volatility (standard deviation of sentiment changes)
        if len(sentiment_trend) > 1:
            sentiment_changes = [abs(sentiment_trend[i] - sentiment_trend[i-1]) for i in range(1, len(sentiment_trend))]
            volatility = np.std(sentiment_changes) if sentiment_changes else 0
        else:
            volatility = 0
        
        # Identify patterns
        trajectory_patterns = []
        
        # Trend analysis
        if len(sentiment_trend) >= 7:
            recent_avg = np.mean(sentiment_trend[-7:])  # Last 7 entries
            older_avg = np.mean(sentiment_trend[:-7])
            
            if recent_avg > older_avg * 1.1:
                trajectory_patterns.append("Improving emotional trend")
            elif recent_avg < older_avg * 0.9:
                trajectory_patterns.append("Declining emotional trend")
            else:
                trajectory_patterns.append("Stable emotional pattern")
        
        # Volatility assessment
        if volatility > 0.3:
            trajectory_patterns.append("High emotional volatility detected")
        elif volatility < 0.1:
            trajectory_patterns.append("Consistent emotional pattern")
        
        # Generate recommendations based on trajectory
        recommendations = []
        
        if "Declining emotional trend" in trajectory_patterns:
            recommendations.extend([
                "Consider implementing daily mood check-ins",
                "Explore mood-boosting activities and self-care practices",
                "Consider reaching out for professional support if the trend continues"
            ])
        
        if "High emotional volatility" in trajectory_patterns:
            recommendations.extend([
                "Practice emotional regulation techniques like deep breathing",
                "Consider mindfulness meditation to build emotional stability",
                "Track triggers that might cause emotional fluctuations"
            ])
        
        if "Improving emotional trend" in trajectory_patterns:
            recommendations.extend([
                "Continue current positive practices and routines",
                "Document what's working well for future reference",
                "Consider sharing insights to help maintain progress"
            ])
        
        # Compile trajectory analysis results
        trajectory_results = {
            'user_id': user_id,
            'analysis_status': 'completed',
            'analysis_period_days': days_back,
            'entries_analyzed': len(emotional_timeline),
            'trajectory_metrics': {
                'emotional_volatility': volatility,
                'average_sentiment': np.mean(sentiment_trend) if sentiment_trend else 0,
                'sentiment_range': max(sentiment_trend) - min(sentiment_trend) if sentiment_trend else 0,
                'trend_direction': trajectory_patterns[0] if trajectory_patterns else 'unknown'
            },
            'emotional_timeline': emotional_timeline[-30:],  # Last 30 entries for visualization
            'identified_patterns': trajectory_patterns,
            'recommendations': recommendations,
            'metadata': {
                'processing_time_seconds': time.time() - start_time,
                'total_words_analyzed': sum(item['word_count'] for item in emotional_timeline)
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Cache results
        cache_key = f"emotional_trajectory:{user_id}:{days_back}d"
        asyncio.run(redis_service.set(cache_key, trajectory_results, ttl=3600))  # 1 hour cache
        
        logger.info(f"✅ Emotional trajectory analysis completed for user {user_id}")
        
        return trajectory_results
        
    except Exception as e:
        error_result = {
            'user_id': user_id,
            'analysis_status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.error(f"❌ Emotional trajectory analysis failed for user {user_id}: {e}")
        return error_result