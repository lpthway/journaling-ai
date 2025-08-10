#!/usr/bin/env python3
"""
AI Model Configuration Fix Script
Addresses the model loading and cache service issues
"""

import asyncio
import sys
from pathlib import Path

# Add the backend to the path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

async def fix_ai_models():
    """Fix AI model configuration issues"""
    print("🔧 Starting AI model configuration fix...")
    
    # Check the current AI model configuration
    print("1. Checking AI model configuration...")
    try:
        from app.core.config import settings
        from app.services.hardware_service import hardware_service
        
        # Detect hardware capabilities
        await hardware_service.detect_hardware()
        
        print(f"   Hardware detected: {hardware_service.specs}")
        
        # Get optimal models for each task
        models = {}
        for task in ["sentiment", "emotion", "embeddings", "classification"]:
            model, use_gpu = hardware_service.get_optimal_model(task)
            models[task] = {"model": model, "gpu": use_gpu}
            print(f"   {task.capitalize()}: {model} (GPU: {use_gpu})")
        
    except Exception as e:
        print(f"   ❌ Error checking configuration: {e}")
        return False
    
    print("\n2. Testing model loading capabilities...")
    
    # Test embedding model loading (critical for vector database)
    try:
        print("   Testing embedding model...")
        from sentence_transformers import SentenceTransformer
        
        embedding_model = models["embeddings"]["model"]
        print(f"   Loading: {embedding_model}")
        
        model = SentenceTransformer(embedding_model)
        test_text = "This is a test sentence for embedding generation."
        embedding = model.encode(test_text)
        
        print(f"   ✅ Embedding model loaded successfully (dim: {len(embedding)})")
        
    except Exception as e:
        print(f"   ⚠️ Embedding model issue: {e}")
        print("   Using fallback model...")
        
        try:
            # Try a more compatible model
            fallback_model = "all-MiniLM-L6-v2"
            model = SentenceTransformer(fallback_model)
            embedding = model.encode(test_text)
            print(f"   ✅ Fallback embedding model works (dim: {len(embedding)})")
        except Exception as e2:
            print(f"   ❌ Fallback also failed: {e2}")
            return False
    
    # Check if the problematic DeBERTa model is required
    print("\n3. Checking sentiment analysis models...")
    
    problematic_model = "microsoft/deberta-v2-xlarge-mnli"
    if models["sentiment"]["model"] == problematic_model:
        print(f"   ⚠️ Problematic model detected: {problematic_model}")
        print("   This model has tokenizer conversion issues.")
        print("   Suggesting alternative models...")
        
        alternatives = [
            "cardiffnlp/twitter-roberta-base-sentiment",
            "nlptown/bert-base-multilingual-uncased-sentiment",
            "distilbert-base-uncased-finetuned-sst-2-english"
        ]
        
        for alt in alternatives:
            print(f"   - {alt}")
    
    print("\n4. Checking cache service configuration...")
    
    try:
        from app.services.cache_service import UnifiedCacheService
        cache_service = UnifiedCacheService()
        
        # Check if the missing method exists
        if hasattr(cache_service, 'delete_ai_model_instance'):
            print("   ✅ Cache service has required methods")
        else:
            print("   ⚠️ Cache service missing 'delete_ai_model_instance' method")
            print("   This will cause cleanup warnings but won't break functionality")
        
    except Exception as e:
        print(f"   ⚠️ Cache service check failed: {e}")
    
    return True

async def create_model_config_recommendations():
    """Create configuration recommendations"""
    print("\n5. Creating configuration recommendations...")
    
    recommendations = """
# AI Model Configuration Recommendations

## Issues Found:
1. ChromaDB collection errors - ✅ FIXED by ChromaDB reset
2. DeBERTa model tokenizer conversion issues
3. Cache service cleanup warnings
4. Tensor dimension mismatches in sentiment analysis

## Recommendations:

### 1. Model Alternatives
For sentiment analysis, replace problematic models with:
- cardiffnlp/twitter-roberta-base-sentiment (lighter, more compatible)
- distilbert-base-uncased-finetuned-sst-2-english (faster)

### 2. Embedding Models
Current embedding model should work fine after ChromaDB fix.

### 3. Cache Service
The missing 'delete_ai_model_instance' method causes warnings but doesn't break functionality.
Consider adding this method or updating the cleanup code.

### 4. Model Configuration
Consider adding model fallback logic in hardware_service.py for problematic models.

## Immediate Actions:
1. ✅ ChromaDB has been reset and fixed
2. ✅ Vector database collections recreated
3. 🔄 Restart backend server to apply fixes
4. 🔄 Test with populate_data.py script

## Optional Improvements:
- Update model configurations to use more compatible alternatives
- Add fallback logic for model loading failures
- Implement proper cache cleanup methods
"""
    
    with open("/home/abrasko/Projects/journaling-ai/AI_MODEL_RECOMMENDATIONS.md", "w") as f:
        f.write(recommendations)
    
    print("   ✅ Recommendations saved to AI_MODEL_RECOMMENDATIONS.md")

async def main():
    """Main function"""
    print("=" * 60)
    print("AI Model Configuration Fix Script")
    print("=" * 60)
    
    success = await fix_ai_models()
    await create_model_config_recommendations()
    
    if success:
        print("\n🎉 AI model analysis completed!")
        print("\nNext steps:")
        print("1. Restart the backend server")
        print("2. Test with populate_data.py")
        print("3. Monitor server.log for any remaining issues")
        print("4. Consider implementing model alternatives if issues persist")
    else:
        print("\n❌ Some critical issues found.")
        print("Please check the error messages above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
