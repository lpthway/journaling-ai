#!/usr/bin/env python3
"""
Simple user data separation test that bypasses rate limiting by using database directly for auth tokens.
"""

import asyncio
import aiohttp
import json
import uuid
from datetime import datetime, timezone, timedelta

# Database imports
import sys
import os
sys.path.append('./backend')
from app.core.database import database
from app.auth.models import AuthUser
from app.auth.security import jwt_manager
from sqlalchemy import select

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"

async def create_jwt_token(user_id: str, username: str, email: str) -> str:
    """Create a JWT token for testing purposes."""
    token_data = {
        "sub": user_id,
        "username": username,
        "email": email
    }
    access_token_expires = timedelta(hours=1)
    return jwt_manager.create_access_token(data=token_data, expires_delta=access_token_expires)

async def get_test_tokens():
    """Get JWT tokens for test users directly from database."""
    await database.initialize()
    
    tokens = {}
    try:
        async with database.get_session() as session:
            # Get test users
            result = await session.execute(
                select(AuthUser).where(AuthUser.username.in_(["testuser", "newuser", "demouser2025"]))
            )
            users = result.scalars().all()
            
            for user in users:
                token = await create_jwt_token(str(user.id), user.username, user.email)
                tokens[user.username] = {
                    "token": token,
                    "user_id": str(user.id)
                }
                print(f"✅ Created token for {user.username} ({user.id})")
                
    finally:
        await database.close()
    
    return tokens

async def test_user_data_separation():
    """Test that users can only access their own data."""
    print("🔒 Simple User Data Separation Test")
    print("=" * 50)
    
    # Get tokens for test users
    print("📝 Getting authentication tokens...")
    tokens = await get_test_tokens()
    
    if len(tokens) < 2:
        print("❌ Not enough test users found. Need at least 2 users for separation test.")
        return False
    
    async with aiohttp.ClientSession() as session:
        # Create test entries for each user
        print("\n📝 Creating test entries...")
        user_entries = {}
        
        for username, auth_info in tokens.items():
            headers = {"Authorization": f"Bearer {auth_info['token']}"}
            
            # Create a test entry
            entry_data = {
                "title": f"Test Entry for {username}",
                "content": f"This is a private entry created by {username} at {datetime.now()}. Only {username} should see this.",
                "entry_type": "journal",
                "tags": [f"test-{username}", "separation-test"]
            }
            
            async with session.post(f"{BASE_URL}/entries/", json=entry_data, headers=headers) as response:
                if response.status == 201:
                    entry = await response.json()
                    user_entries[username] = entry
                    print(f"✅ Created entry for {username}: {entry.get('id', 'unknown')}")
                else:
                    error = await response.text()
                    print(f"❌ Failed to create entry for {username}: {error}")
        
        # Test data separation
        print("\n📝 Testing data separation...")
        separation_success = True
        
        for username, auth_info in tokens.items():
            headers = {"Authorization": f"Bearer {auth_info['token']}"}
            
            # Get user's entries
            async with session.get(f"{BASE_URL}/entries/", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    entries = data.get("entries", [])
                    print(f"🔍 User {username} can see {len(entries)} entries")
                    
                    # Verify entries belong to the correct user
                    for entry in entries:
                        entry_title = entry.get("title", "")
                        if f"Test Entry for {username}" not in entry_title and username not in entry_title:
                            # Check if this entry belongs to another test user
                            for other_user in tokens.keys():
                                if other_user != username and other_user in entry_title:
                                    print(f"❌ SECURITY VIOLATION: User {username} can see entry from {other_user}: {entry_title}")
                                    separation_success = False
                                    break
                else:
                    error = await response.text()
                    print(f"❌ Failed to get entries for {username}: {error}")
                    separation_success = False
        
        # Create test topics
        print("\n📝 Creating test topics...")
        user_topics = {}
        
        for username, auth_info in tokens.items():
            headers = {"Authorization": f"Bearer {auth_info['token']}"}
            
            topic_data = {
                "name": f"Test Topic for {username}",
                "description": f"This topic belongs to {username}",
                "color": "#FF6B6B"
            }
            
            async with session.post(f"{BASE_URL}/topics/", json=topic_data, headers=headers) as response:
                if response.status == 201:
                    topic = await response.json()
                    user_topics[username] = topic
                    print(f"✅ Created topic for {username}: {topic.get('id', 'unknown')}")
                else:
                    error = await response.text()
                    print(f"❌ Failed to create topic for {username}: {error}")
        
        # Test topic separation
        print("\n📝 Testing topic separation...")
        
        for username, auth_info in tokens.items():
            headers = {"Authorization": f"Bearer {auth_info['token']}"}
            
            # Get user's topics
            async with session.get(f"{BASE_URL}/topics/", headers=headers) as response:
                if response.status == 200:
                    topics = await response.json()
                    print(f"📂 User {username} can see {len(topics)} topics")
                    
                    # Verify topics belong to the correct user
                    for topic in topics:
                        topic_name = topic.get("name", "")
                        if f"Test Topic for {username}" not in topic_name and username not in topic_name:
                            # Check if this topic belongs to another test user
                            for other_user in tokens.keys():
                                if other_user != username and other_user in topic_name:
                                    print(f"❌ SECURITY VIOLATION: User {username} can see topic from {other_user}: {topic_name}")
                                    separation_success = False
                                    break
                else:
                    error = await response.text()
                    print(f"❌ Failed to get topics for {username}: {error}")
                    separation_success = False
        
        # Results
        print("\n" + "=" * 50)
        if separation_success:
            print("🎉 USER DATA SEPARATION TEST PASSED!")
            print("✅ Users can only see their own data")
            print("✅ No cross-user data leakage detected")
        else:
            print("❌ USER DATA SEPARATION TEST FAILED!")
            print("⚠️  Cross-user data access detected - SECURITY VULNERABILITY!")
        
        return separation_success

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_user_data_separation())
    exit(0 if success else 1)