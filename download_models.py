#!/usr/bin/env python3
"""
Model Download Script

Pre-downloads and caches all AI models to avoid rate limiting during operation.
Run this once to download all models for offline use.
"""

import sys
import os
import logging
from pathlib import Path
from typing import List, Dict

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def download_model(model_name: str, cache_dir: Path) -> bool:
    """Download and cache a single model"""
    try:
        from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification
        
        # Create model-specific directory
        model_dir = cache_dir / model_name.replace("/", "--")
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if model is already downloaded properly
        if model_dir.exists() and any(f.name in ['config.json', 'tokenizer.json', 'pytorch_model.bin', 'model.safetensors'] for f in model_dir.rglob('*') if f.is_file()):
            logger.info(f"✅ Model already cached: {model_name}")
            return True
        
        logger.info(f"⬇️ Downloading model: {model_name}")
        
        # Download tokenizer directly to the model directory
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        tokenizer.save_pretrained(str(model_dir))
        
        # Try sequence classification model first, then fall back to base model
        try:
            model = AutoModelForSequenceClassification.from_pretrained(model_name)
            model.save_pretrained(str(model_dir))
        except:
            model = AutoModel.from_pretrained(model_name)
            model.save_pretrained(str(model_dir))
        
        logger.info(f"✅ Successfully downloaded: {model_name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to download {model_name}: {e}")
        return False

def main():
    """Download all required models"""
    print("🚀 Journaling AI - Model Download Script")
    print("=" * 50)
    
    # Create models directory in backend
    models_dir = Path(__file__).parent / "backend" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Define all models used by the system
    models_to_download = [
        # Enhanced AI Service models
        "j-hartmann/emotion-english-distilroberta-base",
        "facebook/bart-large-mnli",
        "cardiffnlp/twitter-roberta-base-sentiment-latest",
        "sentence-transformers/all-mpnet-base-v2",
        # "cardiffnlp/twitter-xlm-roberta-base-sentiment",  # SKIP: SentencePiece tokenizer issue
        "facebook/bart-base",
        "sentence-transformers/all-MiniLM-L6-v2",
        "distilbert-base-uncased-finetuned-sst-2-english",
        
        # Sentiment Service models
        "nlptown/bert-base-multilingual-uncased-sentiment",  # ✅ FIXES rate limiting!
    ]
    
    print(f"📦 Downloading {len(models_to_download)} models...")
    print()
    
    successful_downloads = 0
    failed_downloads = 0
    
    for i, model_name in enumerate(models_to_download, 1):
        print(f"[{i}/{len(models_to_download)}] {model_name}")
        
        if download_model(model_name, models_dir):
            successful_downloads += 1
        else:
            failed_downloads += 1
        
        print()
    
    # Summary
    print("=" * 50)
    print("📊 Download Summary:")
    print(f"✅ Successful: {successful_downloads}")
    print(f"❌ Failed: {failed_downloads}")
    print(f"📁 Models stored in: {models_dir.absolute()}")
    
    if failed_downloads == 0:
        print()
        print("🎉 All models downloaded successfully!")
        print("You can now use the journaling AI system offline without rate limiting.")
    else:
        print()
        print("⚠️ Some models failed to download.")
        print("The system will fall back to online loading for failed models.")
    
    # Display disk usage
    try:
        total_size = sum(f.stat().st_size for f in models_dir.rglob('*') if f.is_file())
        total_size_mb = total_size / (1024 * 1024)
        print(f"💾 Total disk space used: {total_size_mb:.1f}MB")
    except:
        pass

if __name__ == "__main__":
    main()
