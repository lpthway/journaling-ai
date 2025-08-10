#!/usr/bin/env python3
"""Simple test script to verify basic API functionality"""

import asyncio
import aiohttp
import json

async def test_basic_api():
    api_base = "http://localhost:8000/api/v1"
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Create a topic
        print("🧪 Testing topic creation...")
        topic_data = {
            "name": "Test Topic",
            "description": "A simple test topic",
            "color": "#FF5733",
            "tags": ["test"]
        }
        
        async with session.post(
            f"{api_base}/topics/",
            json=topic_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status in [200, 201]:
                topic_result = await response.json()
                print(f"✅ Topic created: {topic_result['id']}")
                topic_id = topic_result['id']
            else:
                error_text = await response.text()
                print(f"❌ Topic creation failed: {response.status} - {error_text}")
                return
        
        # Test 2: Create an entry
        print("🧪 Testing entry creation...")
        entry_data = {
            "title": "Test Entry",
            "content": "This is a test journal entry with some content to analyze.",
            "entry_type": "journal",
            "topic_id": topic_id,
            "tags": ["test", "simple"]
        }
        
        async with session.post(
            f"{api_base}/entries/",
            json=entry_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status in [200, 201]:
                entry_result = await response.json()
                print(f"✅ Entry created: {entry_result['id']}")
                print(f"   Mood: {entry_result.get('mood', 'unknown')}")
                print(f"   Tags: {entry_result.get('tags', [])}")
            else:
                error_text = await response.text()
                print(f"❌ Entry creation failed: {response.status} - {error_text}")
                return
        
        # Test 3: List entries
        print("🧪 Testing entry listing...")
        async with session.get(
            f"{api_base}/entries/",
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                entries_result = await response.json()
                print(f"✅ Found {len(entries_result)} entries")
            else:
                error_text = await response.text()
                print(f"❌ Entry listing failed: {response.status} - {error_text}")
        
        print("\n🎉 Basic API tests completed!")

if __name__ == "__main__":
    asyncio.run(test_basic_api())