#!/usr/bin/env python3
"""
Test script to verify user data separation is working correctly.
This will test both chat and analytics data isolation between users.
"""

import asyncio
import httpx
import json
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"

class UserDataSeparationTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.users = {
            "testuser": {"username": "testuser", "password": "password123", "token": None},
            "default_user": {"username": "default_user", "password": "admin123", "token": None}
        }
    
    async def login_user(self, username: str) -> str:
        """Login a user and return their token"""
        user_data = self.users[username]
        
        print(f"🔐 Logging in {username}...")
        response = await self.client.post(f"{API_BASE}/auth/login", json={
            "username_or_email": user_data["username"],
            "password": user_data["password"]
        })
        
        if response.status_code != 200:
            print(f"❌ Login failed for {username}: {response.status_code} - {response.text}")
            return None
            
        data = response.json()
        token = data.get("access_token")
        self.users[username]["token"] = token
        print(f"✅ Login successful for {username}")
        return token
    
    async def get_headers(self, username: str) -> dict:
        """Get authorization headers for a user"""
        token = self.users[username]["token"]
        if not token:
            token = await self.login_user(username)
        return {"Authorization": f"Bearer {token}"}
    
    async def test_analytics_separation(self):
        """Test that analytics data is separated between users"""
        print("\n📊 Testing Analytics Data Separation...")
        
        for username in self.users.keys():
            headers = await self.get_headers(username)
            if not headers.get("Authorization"):
                continue
                
            # Test analytics endpoints
            endpoints = [
                "/entries/analytics/mood?days=30",
                "/entries/analytics/writing?days=30"
            ]
            
            print(f"\n👤 Testing analytics for {username}:")
            for endpoint in endpoints:
                response = await self.client.get(f"{API_BASE}{endpoint}", headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✅ {endpoint}: {len(str(data))} chars of data")
                    if username == "testuser":
                        self.testuser_analytics = data
                    elif username == "default_user":
                        self.default_user_analytics = data
                else:
                    print(f"  ❌ {endpoint}: {response.status_code} - {response.text}")
    
    async def test_chat_separation(self):
        """Test that chat data is separated between users"""
        print("\n💬 Testing Chat Data Separation...")
        
        for username in self.users.keys():
            headers = await self.get_headers(username)
            if not headers.get("Authorization"):
                continue
                
            print(f"\n👤 Testing chat for {username}:")
            
            # Test chat endpoints
            response = await self.client.get(f"{API_BASE}/chat/conversations", headers=headers)
            if response.status_code == 200:
                conversations = response.json()
                print(f"  ✅ Conversations: {len(conversations.get('conversations', []))} found")
                if username == "testuser":
                    self.testuser_conversations = conversations
                elif username == "default_user":
                    self.default_user_conversations = conversations
            else:
                print(f"  ❌ Conversations: {response.status_code} - {response.text}")
    
    async def test_entries_separation(self):
        """Test that journal entries are separated between users"""
        print("\n📝 Testing Journal Entries Separation...")
        
        for username in self.users.keys():
            headers = await self.get_headers(username)
            if not headers.get("Authorization"):
                continue
                
            print(f"\n👤 Testing entries for {username}:")
            
            response = await self.client.get(f"{API_BASE}/entries/", headers=headers)
            if response.status_code == 200:
                entries = response.json()
                print(f"  ✅ Entries: {len(entries)} found")
                if username == "testuser":
                    self.testuser_entries = entries
                elif username == "default_user":
                    self.default_user_entries = entries
            else:
                print(f"  ❌ Entries: {response.status_code} - {response.text}")
    
    async def analyze_separation(self):
        """Analyze if data is properly separated"""
        print("\n🔍 Analyzing Data Separation Results...")
        
        # Check analytics separation
        if hasattr(self, 'testuser_analytics') and hasattr(self, 'default_user_analytics'):
            if self.testuser_analytics == self.default_user_analytics:
                print("❌ ANALYTICS DATA IS SHARED - Users see identical analytics!")
            else:
                print("✅ Analytics data appears to be separated")
        
        # Check chat separation  
        if hasattr(self, 'testuser_conversations') and hasattr(self, 'default_user_conversations'):
            testuser_conv = self.testuser_conversations.get('conversations', [])
            default_conv = self.default_user_conversations.get('conversations', [])
            if testuser_conv == default_conv and len(testuser_conv) > 0:
                print("❌ CHAT DATA IS SHARED - Users see identical conversations!")
            else:
                print("✅ Chat data appears to be separated")
        
        # Check entries separation
        if hasattr(self, 'testuser_entries') and hasattr(self, 'default_user_entries'):
            if self.testuser_entries == self.default_user_entries and len(self.testuser_entries) > 0:
                print("❌ ENTRIES DATA IS SHARED - Users see identical entries!")
            else:
                print("✅ Entries data appears to be separated")
    
    async def run_tests(self):
        """Run all separation tests"""
        print("🚀 Starting User Data Separation Tests")
        print("=" * 50)
        
        # Login all users first
        for username in self.users.keys():
            await self.login_user(username)
        
        # Run separation tests
        await self.test_analytics_separation()
        await self.test_chat_separation() 
        await self.test_entries_separation()
        
        # Analyze results
        await self.analyze_separation()
        
        print("\n" + "=" * 50)
        print("🏁 User Data Separation Tests Complete")
        
        await self.client.aclose()

async def main():
    tester = UserDataSeparationTester()
    await tester.run_tests()

if __name__ == "__main__":
    asyncio.run(main())
