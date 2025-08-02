### app/core/config.py

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Local Journaling Assistant"
    
    # Ollama Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    
    # Vector Database Settings
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma_db"
    
    # Embedding Model
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-large"
    
    # Sentiment Analysis
    SENTIMENT_MODEL: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    
    class Config:
        case_sensitive = True

settings = Settings()
