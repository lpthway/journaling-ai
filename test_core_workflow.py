#!/usr/bin/env python3
"""
Simplified Core Workflow Test Script

Tests the core API workflow without heavy AI features to validate our enhanced populate script approach.
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, Any

class CoreWorkflowTester:
    def __init__(self):
        self.api_base = "http://localhost:8000/api/v1"
        self.test_user_id = "00000000-0000-0000-0000-000000000001"
        self.stats = {
            'entries_created': 0,
            'entries_failed': 0,
            'topics_created': 0,
            'topics_failed': 0
        }
    
    async def test_simple_entry_creation(self) -> bool:
        """Test basic entry creation without heavy AI processing"""
        try:
            entry_data = {
                "user_id": self.test_user_id,
                "title": "Test Journal Entry - Core Workflow",
                "content": "This is a simple test entry to verify the core API workflow is working. No complex AI processing needed.",
                "language": "en",
                "entry_type": "journal",  # Required field
                "entry_date": datetime.now().isoformat(),
                "mood": "neutral",
                "weather": "clear"
            }
            
            async with aiohttp.ClientSession() as session:
                print("🧪 Testing basic entry creation...")
                async with session.post(
                    f"{self.api_base}/entries/",
                    json=entry_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Entry created successfully: {result.get('id', 'unknown')}")
                        self.stats['entries_created'] += 1
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Entry creation failed: {response.status} - {error_text}")
                        self.stats['entries_failed'] += 1
                        return False
        except Exception as e:
            print(f"❌ Error in entry creation test: {e}")
            self.stats['entries_failed'] += 1
            return False
    
    async def test_topic_creation(self) -> bool:
        """Test basic topic creation"""
        try:
            topic_data = {
                "name": "Test Topic - Core Workflow", 
                "description": "A test topic to verify topic creation API",
                "user_id": self.test_user_id
            }
            
            async with aiohttp.ClientSession() as session:
                print("🧪 Testing basic topic creation...")
                async with session.post(
                    f"{self.api_base}/topics/",
                    json=topic_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Topic created successfully: {result.get('id', 'unknown')}")
                        self.stats['topics_created'] += 1
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Topic creation failed: {response.status} - {error_text}")
                        self.stats['topics_failed'] += 1
                        return False
        except Exception as e:
            print(f"❌ Error in topic creation test: {e}")
            self.stats['topics_failed'] += 1
            return False
    
    async def test_entry_retrieval(self, entry_id: str) -> bool:
        """Test entry retrieval"""
        try:
            async with aiohttp.ClientSession() as session:
                print(f"🧪 Testing entry retrieval for ID: {entry_id}")
                async with session.get(
                    f"{self.api_base}/entries/{entry_id}",
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Entry retrieved successfully: {result.get('title', 'unknown')}")
                        return True
                    else:
                        print(f"❌ Entry retrieval failed: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Error in entry retrieval test: {e}")
            return False
    
    async def run_core_tests(self):
        """Run core workflow tests"""
        print("🚀 CORE WORKFLOW TESTING")
        print("=" * 50)
        print("🎯 Testing basic API functionality without heavy AI processing")
        print()
        
        # Test 1: Basic entry creation
        entry_success = await self.test_simple_entry_creation()
        await asyncio.sleep(1)
        
        # Test 2: Basic topic creation  
        topic_success = await self.test_topic_creation()
        await asyncio.sleep(1)
        
        # Test 3: Check if backend is responsive
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8000/health") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        print(f"✅ Backend health check: {health_data.get('status', 'unknown')}")
                    else:
                        print(f"⚠️  Backend health check failed: {response.status}")
        except Exception as e:
            print(f"❌ Backend not accessible: {e}")
        
        print()
        print("📊 CORE TEST RESULTS:")
        print(f"   Entries: {self.stats['entries_created']} created, {self.stats['entries_failed']} failed")
        print(f"   Topics: {self.stats['topics_created']} created, {self.stats['topics_failed']} failed")
        
        total_success = self.stats['entries_created'] + self.stats['topics_created']
        total_failed = self.stats['entries_failed'] + self.stats['topics_failed']
        
        if total_failed == 0:
            print("🎉 All core tests PASSED! Basic API workflow is functional.")
            print("💡 Issue is likely with heavy AI processing (embeddings, LLM, etc.)")
            return True
        else:
            print("⚠️  Some core tests FAILED. Basic API issues detected.")
            return False

async def main():
    """Main test function"""
    print("🤖 Core Workflow Test Tool")
    print("🎯 Testing basic API functionality to isolate issues")
    print()
    
    tester = CoreWorkflowTester()
    success = await tester.run_core_tests()
    
    if success:
        print()
        print("🚀 RECOMMENDATIONS:")
        print("   • Core APIs are working - issue is with AI processing")
        print("   • Consider running backend with AI features disabled")
        print("   • Or use CPU-only mode to avoid GPU memory issues")
        print("   • Enhanced populate script logic is sound")
    else:
        print()
        print("🔧 NEXT STEPS:")
        print("   • Check backend logs for detailed error messages")
        print("   • Verify database connection and schema")
        print("   • Ensure all required environment variables are set")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
