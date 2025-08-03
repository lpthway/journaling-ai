#!/usr/bin/env python3
"""
Quick Data Population Script - Simple version for fast testing

Creates a small amount of sample data quickly for immediate testing.
"""

import asyncio
import aiohttp
import random
from datetime import datetime, timedelta

class QuickPopulator:
    def __init__(self):
        self.api_base = "http://localhost:8000/api/v1"
    
    # Simple predefined content for quick generation
    journal_entries = [
        {
            "title": "Productive Monday",
            "content": "Had a really productive day at work today. Finished the quarterly report and felt great about the presentation. The team responded well to my ideas. Feeling motivated and confident about the upcoming projects. Need to remember to maintain this momentum.",
            "entry_type": "journal"
        },
        {
            "title": "Weekend Reflection", 
            "content": "Spent the weekend hiking with friends. It was exactly what I needed after a stressful week. There's something about being in nature that helps me reset and gain perspective. Feeling grateful for good friends and outdoor adventures.",
            "entry_type": "journal"
        },
        {
            "title": "Challenging Day",
            "content": "Today was tough. Had a difficult conversation with my manager about the project timeline. Feeling anxious about whether I can meet all the expectations. Need to break things down into smaller tasks and focus on what I can control.",
            "entry_type": "journal"
        },
        {
            "title": "Creative Breakthrough",
            "content": "Finally made progress on that creative project I've been stuck on for weeks! The solution came to me while I was cooking dinner. Sometimes the best ideas come when you're not actively trying to solve the problem. Excited to keep building on this.",
            "entry_type": "journal"
        },
        {
            "title": "Family Time",
            "content": "Had dinner with my family tonight. My sister shared some exciting news about her job promotion. It made me reflect on my own career goals and what I want to achieve this year. Feeling inspired by her success and motivated to pursue my own ambitions.",
            "entry_type": "journal"
        }
    ]
    
    async def create_sample_data(self):
        """Create a small set of sample data quickly"""
        
        print("🚀 Quick population starting...")
        print("📝 Creating 5 journal entries...")
        
        # Create journal entries
        for i, entry in enumerate(self.journal_entries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.api_base}/entries/",
                        json=entry,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            print(f"✅ Created: '{entry['title']}'")
                            if result.get('tags'):
                                print(f"   Tags: {result['tags']}")
                        else:
                            print(f"❌ Failed to create: '{entry['title']}'")
            except Exception as e:
                print(f"❌ Error: {e}")
            
            await asyncio.sleep(0.5)  # Small delay
        
        print()
        print("💬 Creating 2 sample chat sessions...")
        
        # Create sample chat sessions
        sample_sessions = [
            {
                "session_type": "reflection_buddy",
                "title": "Work Stress Discussion",
                "description": "Talking through work-related stress",
                "messages": [
                    "I've been feeling really overwhelmed at work lately. There's so much on my plate and I don't know how to prioritize.",
                    "That sounds really challenging. When you think about everything on your plate, what feels most urgent or important right now?",
                    "I guess the quarterly report is due next week, but I also have three client meetings to prepare for. It all feels equally important.",
                    "It makes sense that it all feels important. Sometimes it helps to think about impact - which task, if done well, would have the biggest positive effect on your work or stress level?"
                ]
            },
            {
                "session_type": "growth_challenge", 
                "title": "Personal Goals Check-in",
                "description": "Reflecting on personal development goals",
                "messages": [
                    "I set some goals at the beginning of the year but I feel like I'm not making much progress.",
                    "Goal-setting can be tricky. What were some of the goals you set, and what does 'not much progress' look like to you?",
                    "I wanted to learn a new skill, exercise more regularly, and read more books. I've read maybe 2 books and my exercise routine is inconsistent.",
                    "Two books is still progress! And recognizing the inconsistency in exercise shows self-awareness. What's one small step you could take this week toward any of these goals?"
                ]
            }
        ]
        
        for session_data in sample_sessions:
            try:
                async with aiohttp.ClientSession() as session:
                    # Create session
                    session_payload = {
                        "session_type": session_data["session_type"],
                        "title": session_data["title"], 
                        "description": session_data["description"]
                    }
                    
                    async with session.post(
                        f"{self.api_base}/sessions/",
                        json=session_payload,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            session_id = result['id']
                            print(f"✅ Created session: '{session_data['title']}'")
                            
                            # Add user messages (every other message starting with first)
                            user_messages = session_data["messages"][::2]  # Get every other message starting with index 0
                            
                            for msg_content in user_messages:
                                async with session.post(
                                    f"{self.api_base}/sessions/{session_id}/messages",
                                    json={"content": msg_content},
                                    headers={"Content-Type": "application/json"}
                                ) as msg_response:
                                    if msg_response.status != 200:
                                        print(f"⚠️  Failed to add message")
                            
                            # Try auto-tagging
                            try:
                                async with session.post(
                                    f"{self.api_base}/sessions/{session_id}/auto-tag",
                                    headers={"Content-Type": "application/json"}
                                ) as tag_response:
                                    if tag_response.status == 200:
                                        tag_result = await tag_response.json()
                                        if tag_result.get('tags'):
                                            print(f"   Tags: {tag_result['tags']}")
                            except:
                                pass
                        else:
                            print(f"❌ Failed to create session: '{session_data['title']}'")
            except Exception as e:
                print(f"❌ Error creating session: {e}")
            
            await asyncio.sleep(1)
        
        print()
        print("✨ Quick population complete!")
        print("🎯 Created 5 journal entries + 2 chat sessions")
        print("🔍 Check the Insights tab to see your data!")

async def main():
    populator = QuickPopulator()
    await populator.create_sample_data()

if __name__ == "__main__":
    asyncio.run(main())
