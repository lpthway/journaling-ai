#!/usr/bin/env python3
"""
Simple test for the fixed populate script
"""

import asyncio
import aiohttp
from datetime import datetime

async def test_fixed_populate():
    """Test the fixed API calls"""
    test_user_id = "00000000-0000-0000-0000-000000000001"
    api_base = "http://localhost:8000/api/v1"
    
    print("🧪 Testing Fixed Populate Script APIs")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Create a topic
        print("📝 Test 1: Creating a topic...")
        topic_data = {
            "name": "Test Topic - Fixed Script",
            "description": "A test topic with proper schema",
            "user_id": test_user_id
        }
        
        async with session.post(
            f"{api_base}/topics/",
            json=topic_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status in [200, 201]:
                topic_result = await response.json()
                topic_id = topic_result['id']
                print(f"✅ Topic created: {topic_id}")
            else:
                error_text = await response.text()
                print(f"❌ Topic creation failed: {response.status} - {error_text}")
                return False
        
        # Test 2: Create an entry
        print("📝 Test 2: Creating an entry...")
        entry_data = {
            "user_id": test_user_id,
            "title": "Test Entry - Fixed Script",
            "content": "This is a test entry to verify the fixed populate script is working correctly with the proper schema.",
            "entry_type": "journal",
            "created_at": datetime.now().isoformat(),
            "tags": [],
            "topic_id": topic_id,
            "template_id": None
        }
        
        async with session.post(
            f"{api_base}/entries/",
            json=entry_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status in [200, 201]:
                entry_result = await response.json()
                entry_id = entry_result['id']
                print(f"✅ Entry created: {entry_id}")
            else:
                error_text = await response.text()
                print(f"❌ Entry creation failed: {response.status} - {error_text}")
                return False
        
        # Test 3: Retrieve the entry
        print("📝 Test 3: Retrieving the entry...")
        async with session.get(
            f"{api_base}/entries/{entry_id}",
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                retrieved_entry = await response.json()
                print(f"✅ Entry retrieved: {retrieved_entry['title']}")
            else:
                print(f"❌ Entry retrieval failed: {response.status}")
                return False
    
    print("\n🎉 All tests PASSED! Fixed populate script should work correctly.")
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_fixed_populate())
        if not success:
            exit(1)
    except Exception as e:
        print(f"❌ Test error: {e}")
        exit(1)
