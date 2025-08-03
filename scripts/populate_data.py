#!/usr/bin/env python3
"""
Data Population Script for Journaling AI

This script uses Ollama to generate realistic journal entries and chat conversations
to populate the application with test data for development and testing purposes.
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import aiohttp
import ollama
from pathlib import Path
import sys
from enum import Enum

# Define the enums we need locally to avoid import issues
class SessionType(Enum):
    REFLECTION_BUDDY = "reflection_buddy"
    INNER_VOICE = "inner_voice" 
    GROWTH_CHALLENGE = "growth_challenge"
    PATTERN_DETECTIVE = "pattern_detective"
    FREE_CHAT = "free_chat"

class DataPopulator:
    def __init__(self):
        self.ollama_client = ollama.Client(host="http://localhost:11434")
        self.api_base = "http://localhost:8000/api/v1"
        
        # Journal entry themes for variety
        self.journal_themes = [
            "work stress and productivity",
            "personal relationships and family",
            "health and wellness journey", 
            "creative projects and hobbies",
            "travel experiences and adventures",
            "learning and personal growth",
            "financial planning and goals",
            "daily routines and habits",
            "emotional challenges and breakthroughs",
            "career development and aspirations"
        ]
        
        # Chat session themes
        self.chat_themes = [
            "exploring feelings about work-life balance",
            "discussing relationship challenges",
            "reflecting on personal goals and motivation",
            "processing anxiety and stress management",
            "exploring creativity and passion projects",
            "working through decision-making challenges",
            "discussing self-improvement strategies",
            "reflecting on past experiences and lessons learned",
            "exploring future aspirations and dreams",
            "processing daily emotions and thoughts"
        ]

    async def generate_journal_entry(self, theme: str, days_ago: int) -> Dict[str, Any]:
        """Generate a realistic journal entry using Ollama"""
        
        # Create a date for the entry
        entry_date = datetime.now() - timedelta(days=days_ago)
        day_of_week = entry_date.strftime("%A")
        
        prompt = f"""Write a personal journal entry about {theme}. 

Guidelines:
- Write in first person as if you're reflecting on your day/week
- Make it feel authentic and personal (200-400 words)
- Include specific details and emotions
- Reference the fact that it's a {day_of_week}
- Make it feel like a real person's thoughts and experiences
- Include some concrete details or events
- Show genuine emotions and introspection

Write just the journal entry content, no title or formatting:"""

        try:
            response = self.ollama_client.generate(
                model="llama3.1",
                prompt=prompt,
                stream=False
            )
            
            content = response['response'].strip()
            
            # Generate a simple title based on the theme
            title_prompt = f"Create a short, personal title (3-6 words) for a journal entry about {theme}. Just return the title, nothing else:"
            
            title_response = self.ollama_client.generate(
                model="llama3.1", 
                prompt=title_prompt,
                stream=False
            )
            
            title = title_response['response'].strip().replace('"', '').replace("'", "")
            
            return {
                "title": title,
                "content": content,
                "entry_type": "journal",
                "tags": []  # Let auto-tagging handle this
            }
            
        except Exception as e:
            print(f"Error generating journal entry: {e}")
            return {
                "title": f"Reflection on {theme}",
                "content": f"Today I've been thinking about {theme}. There's a lot to process and reflect on.",
                "entry_type": "journal", 
                "tags": []
            }

    async def generate_chat_conversation(self, theme: str, session_type: SessionType) -> List[Dict[str, Any]]:
        """Generate a realistic chat conversation using Ollama"""
        
        # Define the AI assistant personality based on session type
        assistant_personalities = {
            SessionType.REFLECTION_BUDDY: "You are a warm, supportive reflection buddy. Ask thoughtful questions and provide gentle insights.",
            SessionType.INNER_VOICE: "You are the user's wise inner voice. Speak as their internal wisdom and intuition.",
            SessionType.GROWTH_CHALLENGE: "You are a motivational growth coach. Challenge the user to think bigger and take action.",
            SessionType.PATTERN_DETECTIVE: "You are an analytical pattern detective. Help the user identify patterns in their thoughts and behaviors.",
            SessionType.FREE_CHAT: "You are a friendly, open conversational partner. Be curious and engaging."
        }
        
        # Generate initial user message
        user_prompt = f"""You are a person starting a conversation with an AI assistant about {theme}. 
        Write a natural opening message (1-3 sentences) that someone might send when they want to talk about this topic.
        Be authentic and conversational. Just write the message, nothing else:"""
        
        try:
            user_response = self.ollama_client.generate(
                model="llama3.1",
                prompt=user_prompt, 
                stream=False
            )
            
            messages = []
            user_message = user_response['response'].strip()
            messages.append({
                "content": user_message,
                "role": "user"
            })
            
            # Generate 3-5 back-and-forth exchanges
            conversation_history = user_message
            num_exchanges = random.randint(3, 5)
            
            for i in range(num_exchanges):
                # Generate AI response
                ai_prompt = f"""{assistant_personalities[session_type]}

Conversation so far:
{conversation_history}

Respond to the user's message naturally and helpfully. Keep it conversational and supportive (1-3 sentences). 
Just write the response, nothing else:"""
                
                ai_response = self.ollama_client.generate(
                    model="llama3.1",
                    prompt=ai_prompt,
                    stream=False
                )
                
                ai_message = ai_response['response'].strip()
                messages.append({
                    "content": ai_message,
                    "role": "assistant"
                })
                
                conversation_history += f"\nAI: {ai_message}"
                
                # Generate user follow-up (except for last exchange)
                if i < num_exchanges - 1:
                    user_followup_prompt = f"""Based on this conversation so far:
{conversation_history}

Write a natural follow-up response from the user. Be authentic and continue the conversation meaningfully (1-2 sentences).
Just write the message, nothing else:"""
                    
                    user_followup = self.ollama_client.generate(
                        model="llama3.1",
                        prompt=user_followup_prompt,
                        stream=False
                    )
                    
                    user_message = user_followup['response'].strip()
                    messages.append({
                        "content": user_message,
                        "role": "user"
                    })
                    
                    conversation_history += f"\nUser: {user_message}"
            
            return messages
            
        except Exception as e:
            print(f"Error generating conversation: {e}")
            # Fallback simple conversation
            return [
                {"content": f"I've been thinking about {theme} lately and would love to explore it more.", "role": "user"},
                {"content": "That sounds like an important topic to explore. What specifically about it has been on your mind?", "role": "assistant"},
                {"content": "I guess I'm just trying to understand it better and figure out how to move forward.", "role": "user"},
                {"content": "Understanding is often the first step toward positive change. What feels most important to focus on right now?", "role": "assistant"}
            ]

    async def create_journal_entry(self, entry_data: Dict[str, Any]) -> bool:
        """Create a journal entry via API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/entries/",
                    json=entry_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Created journal entry: '{entry_data['title']}'")
                        if result.get('tags'):
                            print(f"   Auto-generated tags: {result['tags']}")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Failed to create journal entry: {response.status} - {error_text}")
                        return False
        except Exception as e:
            print(f"❌ Error creating journal entry: {e}")
            return False

    async def create_chat_session(self, session_type: SessionType, theme: str, messages: List[Dict]) -> bool:
        """Create a chat session with messages via API"""
        try:
            # Create session
            session_data = {
                "session_type": session_type.value,
                "title": f"Chat about {theme}",
                "description": f"Conversation exploring {theme}",
                "metadata": {"theme": theme}
            }
            
            async with aiohttp.ClientSession() as session:
                # Create the session
                async with session.post(
                    f"{self.api_base}/sessions/",
                    json=session_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"❌ Failed to create session: {response.status} - {error_text}")
                        return False
                    
                    session_result = await response.json()
                    session_id = session_result['id']
                    print(f"✅ Created chat session: '{session_data['title']}'")
                
                # Add messages (skip first user message as it will be sent via the message endpoint)
                user_messages = [msg for msg in messages if msg['role'] == 'user']
                
                for user_msg in user_messages:
                    async with session.post(
                        f"{self.api_base}/sessions/{session_id}/messages",
                        json={"content": user_msg['content']},
                        headers={"Content-Type": "application/json"}
                    ) as msg_response:
                        if msg_response.status != 200:
                            print(f"⚠️  Failed to add message to session {session_id}")
                
                # Trigger auto-tagging for the session
                try:
                    async with session.post(
                        f"{self.api_base}/sessions/{session_id}/auto-tag",
                        headers={"Content-Type": "application/json"}
                    ) as tag_response:
                        if tag_response.status == 200:
                            tag_result = await tag_response.json()
                            if tag_result.get('tags'):
                                print(f"   Auto-generated tags: {tag_result['tags']}")
                except:
                    pass  # Auto-tagging is optional
                
                return True
                
        except Exception as e:
            print(f"❌ Error creating chat session: {e}")
            return False

    async def populate_data(self, num_journal_entries: int = 10, num_chat_sessions: int = 5):
        """Populate the application with sample data"""
        
        print("🚀 Starting data population...")
        print(f"📝 Generating {num_journal_entries} journal entries")
        print(f"💬 Generating {num_chat_sessions} chat sessions")
        print()
        
        # Generate journal entries
        print("📝 Creating journal entries...")
        for i in range(num_journal_entries):
            theme = random.choice(self.journal_themes)
            days_ago = random.randint(1, 30)  # Spread across last 30 days
            
            print(f"   Generating entry {i+1}/{num_journal_entries}: {theme}")
            entry_data = await self.generate_journal_entry(theme, days_ago)
            await self.create_journal_entry(entry_data)
            
            # Small delay to avoid overwhelming the API
            await asyncio.sleep(1)
        
        print()
        
        # Generate chat sessions
        print("💬 Creating chat sessions...")
        session_types = list(SessionType)
        
        for i in range(num_chat_sessions):
            theme = random.choice(self.chat_themes)
            session_type = random.choice(session_types)
            
            print(f"   Generating session {i+1}/{num_chat_sessions}: {theme} ({session_type.value})")
            messages = await self.generate_chat_conversation(theme, session_type)
            await self.create_chat_session(session_type, theme, messages)
            
            # Small delay to avoid overwhelming the API
            await asyncio.sleep(2)
        
        print()
        print("✨ Data population complete!")
        print()
        print("🎯 What was created:")
        print(f"   • {num_journal_entries} journal entries with automatic tags")
        print(f"   • {num_chat_sessions} chat sessions with conversations")
        print(f"   • Automatic sentiment analysis for all content")
        print(f"   • AI-generated tags for better organization")
        print()
        print("🔍 You can now explore:")
        print("   • Insights & Analytics tab for patterns and trends")
        print("   • Coaching suggestions based on your 'content'")
        print("   • Ask AI questions about your 'experiences'")
        print("   • View comprehensive mood trends")

async def main():
    """Main function to run the data population"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Populate journaling AI with sample data")
    parser.add_argument("--journal-entries", type=int, default=15, help="Number of journal entries to create")
    parser.add_argument("--chat-sessions", type=int, default=8, help="Number of chat sessions to create")
    
    args = parser.parse_args()
    
    populator = DataPopulator()
    await populator.populate_data(args.journal_entries, args.chat_sessions)

if __name__ == "__main__":
    asyncio.run(main())
