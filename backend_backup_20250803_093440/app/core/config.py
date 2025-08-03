# backend/app/core/config.py - Optimized for German/English

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Local Journaling Assistant"
    
    # Ollama Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"  # ⬆️ UPGRADED: Newer, better reasoning
    
    # Vector Database Settings
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma_db"
    
    # Embedding Model - KEEP THIS! Perfect for German/English
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-large"  # ✅ EXCELLENT choice
    
    # Sentiment Analysis - UPGRADED for multilingual emotion detection
    SENTIMENT_MODEL: str = "j-hartmann/emotion-english-distilroberta-base"  # ⬆️ 6 emotions instead of 3
    
    # Alternative multilingual sentiment (uncomment if you prefer):
    # SENTIMENT_MODEL: str = "nlptown/bert-base-multilingual-uncased-sentiment"  # German support
    
    class Config:
        case_sensitive = True

settings = Settings()

# Model Performance Info
MODEL_SPECS = {
    "embedding": {
        "model": "intfloat/multilingual-e5-large",
        "size": "2.24GB",
        "languages": "100+ including German & English",
        "quality": "⭐⭐⭐⭐⭐ Excellent",
        "best_for": "Multilingual semantic search",
        "why_chosen": "Best multilingual embedding model available"
    },
    "sentiment": {
        "model": "j-hartmann/emotion-english-distilroberta-base", 
        "size": "255MB",
        "emotions": ["joy", "sadness", "anger", "fear", "surprise", "disgust"],
        "languages": "English (primary)",
        "upgrade_from": "3 sentiments → 6 detailed emotions",
        "alternative": "nlptown/bert-base-multilingual-uncased-sentiment (for German)"
    },
    "llm": {
        "model": "llama3.2",
        "improvement": "Better reasoning, updated knowledge",
        "languages": "Multilingual including German"
    }
}