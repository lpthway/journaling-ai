#!/usr/bin/env python3
"""
Database Cleanup Script for Journaling AI

This script cleans all user data from the database for testing purposes.
"""

import asyncio
import aiohttp
import sys

class DatabaseCleaner:
    def __init__(self):
        self.api_base = "http://localhost:8000/api/v1"
        self.test_user_id = "00000000-0000-0000-0000-000000000001"
    
    async def get_all_entries(self):
        """Get all journal entries for the test user"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base}/entries/") as response:
                    if response.status == 200:
                        entries = await response.json()
                        return entries if isinstance(entries, list) else []
                    else:
                        print(f"Failed to get entries: {response.status}")
                        return []
        except Exception as e:
            print(f"Error getting entries: {e}")
            return []
    
    async def get_all_sessions(self):
        """Get all chat sessions for the test user"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base}/sessions/") as response:
                    if response.status == 200:
                        sessions = await response.json()
                        return sessions if isinstance(sessions, list) else []
                    else:
                        print(f"Failed to get sessions: {response.status}")
                        return []
        except Exception as e:
            print(f"Error getting sessions: {e}")
            return []
    
    async def get_all_topics(self):
        """Get all topics"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base}/topics/") as response:
                    if response.status == 200:
                        topics = await response.json()
                        return topics if isinstance(topics, list) else []
                    else:
                        print(f"Failed to get topics: {response.status}")
                        return []
        except Exception as e:
            print(f"Error getting topics: {e}")
            return []
    
    async def delete_entry(self, entry_id):
        """Delete a journal entry"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(f"{self.api_base}/entries/{entry_id}") as response:
                    return response.status in [200, 204]
        except Exception as e:
            print(f"Error deleting entry {entry_id}: {e}")
            return False
    
    async def delete_session(self, session_id):
        """Delete a chat session"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(f"{self.api_base}/sessions/{session_id}") as response:
                    return response.status in [200, 204]
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False
    
    async def delete_topic(self, topic_id):
        """Delete a topic"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(f"{self.api_base}/topics/{topic_id}") as response:
                    return response.status in [200, 204]
        except Exception as e:
            print(f"Error deleting topic {topic_id}: {e}")
            return False
    
    async def cleanup_database(self):
        """Clean all data from the database"""
        print("🧹 Database Cleanup Starting...")
        print("=" * 50)
        print()
        
        # Get current data
        print("📊 Checking current database content...")
        entries = await self.get_all_entries()
        sessions = await self.get_all_sessions()
        topics = await self.get_all_topics()
        
        print(f"Found: {len(entries)} journal entries")
        print(f"Found: {len(sessions)} chat sessions")
        print(f"Found: {len(topics)} topics")
        print()
        
        if len(entries) == 0 and len(sessions) == 0 and len(topics) == 0:
            print("✅ Database is already clean!")
            return
        
        # Delete journal entries
        if entries:
            print("🗑️  Deleting journal entries...")
            deleted_entries = 0
            for entry in entries:
                entry_id = entry.get('id')
                if entry_id and await self.delete_entry(entry_id):
                    deleted_entries += 1
                    if deleted_entries % 10 == 0:
                        print(f"   Deleted {deleted_entries}/{len(entries)} entries...")
                await asyncio.sleep(0.1)
            print(f"✅ Deleted {deleted_entries}/{len(entries)} journal entries")
        
        # Delete chat sessions
        if sessions:
            print("🗑️  Deleting chat sessions...")
            deleted_sessions = 0
            for session in sessions:
                session_id = session.get('id')
                if session_id and await self.delete_session(session_id):
                    deleted_sessions += 1
                await asyncio.sleep(0.1)
            print(f"✅ Deleted {deleted_sessions}/{len(sessions)} chat sessions")
        
        # Delete topics
        if topics:
            print("🗑️  Deleting topics...")
            deleted_topics = 0
            for topic in topics:
                topic_id = topic.get('id')
                if topic_id and await self.delete_topic(topic_id):
                    deleted_topics += 1
                await asyncio.sleep(0.1)
            print(f"✅ Deleted {deleted_topics}/{len(topics)} topics")
        
        print()
        print("🎯 Database cleanup complete!")
        print("Ready for fresh data population.")
        print()

async def main():
    """Main cleanup function"""
    print("🤖 Journaling AI Database Cleanup Tool")
    print("⚠️  This will delete ALL data from the database!")
    print()
    
    # Safety confirmation
    try:
        confirm = input("Are you sure you want to proceed? (type 'yes' to confirm): ")
        if confirm.lower() != 'yes':
            print("❌ Cleanup cancelled.")
            return
    except KeyboardInterrupt:
        print("\n❌ Cleanup cancelled.")
        return
    
    cleaner = DatabaseCleaner()
    await cleaner.cleanup_database()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Cleanup interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        sys.exit(1)
