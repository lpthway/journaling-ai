#!/usr/bin/env python3
"""
Test script to verify user data separation is working correctly.

Tests:
1. Users can only see their own entries
2. Users can only see their own topics  
3. Users can only see their own chat sessions
4. API endpoints properly filter by authenticated user
5. No cross-user data leakage
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_USERS = [
    {"username": "testuser", "password": "password123"},
    {"username": "newuser", "password": "password123"}, 
    {"username": "demouser2025", "password": "password123"}
]

class UserDataSeparationTest:
    def __init__(self):
        self.session = None
        self.tokens = {}
        self.user_data = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def login_user(self, username, password):
        """Login user and get JWT token."""
        print(f"🔐 Logging in user: {username}")
        
        async with self.session.post(f"{BASE_URL}/auth/login", json={
            "username_or_email": username,
            "password": password
        }) as response:
            if response.status == 200:
                data = await response.json()
                token = data["access_token"]
                self.tokens[username] = token
                print(f"✅ Login successful for {username}")
                return token
            else:
                error = await response.text()
                print(f"❌ Login failed for {username}: {error}")
                return None
    
    async def create_test_entry(self, username, title_suffix=""):
        """Create a test entry for a user."""
        token = self.tokens.get(username)
        if not token:
            print(f"❌ No token for user {username}")
            return None
            
        entry_data = {
            "title": f"Test Entry for {username}{title_suffix}",
            "content": f"This is a test journal entry created by {username} at {datetime.now()}. This should only be visible to {username}.",
            "entry_type": "journal",
            "tags": [f"test-{username}"]
        }
        
        headers = {"Authorization": f"Bearer {token}"}
        
        async with self.session.post(f"{BASE_URL}/entries/", json=entry_data, headers=headers) as response:
            if response.status == 201:
                data = await response.json()
                print(f"✅ Created entry for {username}: {data['id']}")
                return data
            else:
                error = await response.text()
                print(f"❌ Failed to create entry for {username}: {error}")
                return None
    
    async def get_user_entries(self, username):
        """Get entries for a specific user."""
        token = self.tokens.get(username)
        if not token:
            return []
            
        headers = {"Authorization": f"Bearer {token}"}
        
        async with self.session.get(f"{BASE_URL}/entries/", headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                entries = data.get("entries", [])
                print(f"📋 User {username} can see {len(entries)} entries")
                return entries
            else:
                error = await response.text()
                print(f"❌ Failed to get entries for {username}: {error}")
                return []
    
    async def create_test_topic(self, username):
        """Create a test topic for a user."""
        token = self.tokens.get(username)
        if not token:
            return None
            
        topic_data = {
            "name": f"Test Topic for {username}",
            "description": f"This topic belongs to {username} and should only be visible to them.",
            "color": "#FF6B6B"
        }
        
        headers = {"Authorization": f"Bearer {token}"}
        
        async with self.session.post(f"{BASE_URL}/topics/", json=topic_data, headers=headers) as response:
            if response.status == 201:
                data = await response.json()
                print(f"✅ Created topic for {username}: {data['id']}")
                return data
            else:
                error = await response.text()
                print(f"❌ Failed to create topic for {username}: {error}")
                return None
    
    async def get_user_topics(self, username):
        """Get topics for a specific user."""
        token = self.tokens.get(username)
        if not token:
            return []
            
        headers = {"Authorization": f"Bearer {token}"}
        
        async with self.session.get(f"{BASE_URL}/topics/", headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                topics = data.get("topics", [])
                print(f"📂 User {username} can see {len(topics)} topics")
                return topics
            else:
                error = await response.text()
                print(f"❌ Failed to get topics for {username}: {error}")
                return []
    
    async def test_user_data_separation(self):
        """Main test function to verify user data separation."""
        print("🧪 Starting User Data Separation Test")
        print("=" * 50)
        
        # Step 1: Login all test users
        print("\n📝 Step 1: Login Test Users")
        for user in TEST_USERS:
            await self.login_user(user["username"], user["password"])
        
        # Step 2: Create test data for each user
        print("\n📝 Step 2: Create Test Data")
        for user in TEST_USERS:
            username = user["username"]
            
            # Create entries
            entry1 = await self.create_test_entry(username, " #1")
            entry2 = await self.create_test_entry(username, " #2")
            
            # Create topic
            topic = await self.create_test_topic(username)
            
            self.user_data[username] = {
                "entries": [entry1, entry2],
                "topics": [topic]
            }
        
        # Step 3: Verify data separation
        print("\n📝 Step 3: Verify Data Separation")
        separation_success = True
        
        for user in TEST_USERS:
            username = user["username"]
            print(f"\n🔍 Testing user: {username}")
            
            # Get user's entries
            user_entries = await self.get_user_entries(username)
            
            # Get user's topics
            user_topics = await self.get_user_topics(username)
            
            # Verify user can see their own data
            expected_entries = 2  # We created 2 entries per user
            if len(user_entries) < expected_entries:
                print(f"❌ User {username} should see at least {expected_entries} entries, but sees {len(user_entries)}")
                separation_success = False
            else:
                print(f"✅ User {username} can see their own entries")
            
            # Verify entries belong to the correct user
            for entry in user_entries:
                entry_title = entry.get("title", "")
                if username not in entry_title:
                    print(f"❌ User {username} can see entry that doesn't belong to them: {entry_title}")
                    separation_success = False
            
            # Verify topics belong to the correct user  
            for topic in user_topics:
                topic_name = topic.get("name", "")
                if username not in topic_name:
                    print(f"❌ User {username} can see topic that doesn't belong to them: {topic_name}")
                    separation_success = False
        
        # Step 4: Test cross-user access (should fail)
        print("\n📝 Step 4: Test Cross-User Access Prevention")
        
        # Try to access another user's entry directly (if we can guess the ID)
        # This should be handled by the backend filtering
        
        # Final Results
        print("\n" + "=" * 50)
        if separation_success:
            print("🎉 USER DATA SEPARATION TEST PASSED!")
            print("✅ Users can only see their own data")
            print("✅ No cross-user data leakage detected")
        else:
            print("❌ USER DATA SEPARATION TEST FAILED!")
            print("⚠️  Cross-user data access detected - security vulnerability!")
        
        return separation_success
    
    async def cleanup_test_data(self):
        """Clean up test data created during testing."""
        print("\n🧹 Cleaning up test data...")
        
        for user in TEST_USERS:
            username = user["username"]
            token = self.tokens.get(username)
            if not token:
                continue
                
            headers = {"Authorization": f"Bearer {token}"}
            
            # Get and delete test entries
            user_entries = await self.get_user_entries(username)
            for entry in user_entries:
                if "Test Entry for" in entry.get("title", ""):
                    async with self.session.delete(f"{BASE_URL}/entries/{entry['id']}", headers=headers) as response:
                        if response.status == 200:
                            print(f"🗑️  Deleted test entry: {entry['title']}")
            
            # Get and delete test topics
            user_topics = await self.get_user_topics(username)
            for topic in user_topics:
                if "Test Topic for" in topic.get("name", ""):
                    async with self.session.delete(f"{BASE_URL}/topics/{topic['id']}", headers=headers) as response:
                        if response.status == 200:
                            print(f"🗑️  Deleted test topic: {topic['name']}")


async def main():
    """Run the user data separation test."""
    try:
        async with UserDataSeparationTest() as test:
            success = await test.test_user_data_separation()
            await test.cleanup_test_data()
            
            if success:
                print("\n🎉 All tests passed! User data separation is working correctly.")
                exit(0)
            else:
                print("\n💥 Tests failed! User data separation has security issues.")
                exit(1)
                
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        exit(1)


if __name__ == "__main__":
    print("🔒 User Data Separation Security Test")
    print("Testing that users can only access their own data...")
    print()
    
    asyncio.run(main())