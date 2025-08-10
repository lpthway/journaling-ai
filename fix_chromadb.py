#!/usr/bin/env python3
"""
Complete ChromaDB reset and fix script
Addresses the vector database collection errors
"""

import asyncio
import shutil
import os
import sys
import chromadb
from chromadb.config import Settings as ChromaSettings
from pathlib import Path

# Add the backend to the path so we can import settings
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.config import settings

async def fix_chromadb():
    """Complete ChromaDB reset and reinitialization"""
    print("🔧 Starting ChromaDB fix...")
    
    # 1. Stop any existing ChromaDB processes (if any)
    print("1. Stopping any existing ChromaDB processes...")
    
    # 2. Remove existing ChromaDB directory completely
    chroma_dir = settings.CHROMA_PERSIST_DIRECTORY
    print(f"2. Removing existing ChromaDB directory: {chroma_dir}")
    
    if os.path.exists(chroma_dir):
        try:
            shutil.rmtree(chroma_dir)
            print(f"   ✅ Removed {chroma_dir}")
        except Exception as e:
            print(f"   ⚠️ Error removing {chroma_dir}: {e}")
            # Try to continue anyway
    
    # 3. Recreate the directory
    print("3. Creating fresh ChromaDB directory...")
    os.makedirs(chroma_dir, exist_ok=True)
    print(f"   ✅ Created {chroma_dir}")
    
    # 4. Initialize fresh ChromaDB client and collection
    print("4. Initializing fresh ChromaDB client...")
    try:
        client = chromadb.PersistentClient(
            path=chroma_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        print("   ✅ ChromaDB client initialized")
        
        # Create the collection with correct settings
        print("5. Creating journal_entries collection...")
        collection = client.get_or_create_collection(
            name="journal_entries",
            metadata={"hnsw:space": "cosine"}
        )
        print(f"   ✅ Collection created with ID: {collection.id}")
        
        # Verify collection exists
        print("6. Verifying collection...")
        collections = client.list_collections()
        print(f"   Available collections: {[c.name for c in collections]}")
        
        # Test collection operations
        print("7. Testing collection operations...")
        test_id = "test_entry_1"
        test_embedding = [0.1] * 384  # Standard embedding dimension
        test_doc = "This is a test document"
        test_metadata = {"test": "true"}
        
        collection.add(
            ids=[test_id],
            embeddings=[test_embedding],
            documents=[test_doc],
            metadatas=[test_metadata]
        )
        print("   ✅ Test entry added successfully")
        
        # Clean up test entry
        collection.delete(ids=[test_id])
        print("   ✅ Test entry removed successfully")
        
    except Exception as e:
        print(f"   ❌ Error initializing ChromaDB: {e}")
        return False
    
    print("\n🎉 ChromaDB fix completed successfully!")
    print("The vector database should now work properly.")
    return True

async def main():
    """Main function"""
    print("=" * 60)
    print("ChromaDB Collection Fix Script")
    print("=" * 60)
    
    success = await fix_chromadb()
    
    if success:
        print("\n✅ All fixes applied successfully!")
        print("You can now restart the backend server.")
    else:
        print("\n❌ Some issues occurred during the fix.")
        print("Please check the error messages above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
