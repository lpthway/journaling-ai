#!/usr/bin/env python3
"""
Data Population Script for Journaling AI

This script uses Ollama to generate realistic journal entries and chat conversations
to populate the application with test data for development and testing purposes.
"""

import asyncio
import json
import random
import argparse
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
        
        # Core topics for better organization (limited set to encourage reuse)
        self.core_topics = [
            {"name": "Work & Career", "description": "Professional life, career development, and workplace experiences", "language": "en"},
            {"name": "Arbeit & Karriere", "description": "Berufsleben, Karriereentwicklung und Erfahrungen am Arbeitsplatz", "language": "de"},
            {"name": "Personal Growth", "description": "Self-reflection, learning experiences, and personal development", "language": "en"},
            {"name": "Persönliche Entwicklung", "description": "Selbstreflexion, Lernerfahrungen und persönliche Weiterentwicklung", "language": "de"},
            {"name": "Family & Relationships", "description": "Connections with family, friends, and significant others", "language": "en"},
            {"name": "Familie & Beziehungen", "description": "Verbindungen zu Familie, Freunden und wichtigen Menschen", "language": "de"},
            {"name": "Health & Wellness", "description": "Physical and mental health, fitness, nutrition, and wellbeing", "language": "en"},
            {"name": "Gesundheit & Wohlbefinden", "description": "Körperliche und geistige Gesundheit, Fitness, Ernährung", "language": "de"},
            {"name": "Daily Life", "description": "Everyday experiences, routines, and observations", "language": "en"},
            {"name": "Alltag", "description": "Alltägliche Erfahrungen, Routinen und Beobachtungen", "language": "de"}
        ]
        
        # Seasonal topics (created occasionally based on time of year)
        self.seasonal_topics = [
            {"name": "Travel & Adventures", "description": "Travel experiences and explorations", "language": "en", "seasons": ["spring", "summer"]},
            {"name": "Reisen & Abenteuer", "description": "Reiseerfahrungen und Entdeckungen", "language": "de", "seasons": ["spring", "summer"]},
            {"name": "Holiday Reflections", "description": "Holiday experiences and family gatherings", "language": "en", "seasons": ["winter"]},
            {"name": "Feiertagsreflexionen", "description": "Feiertags-Erfahrungen und Familientreffen", "language": "de", "seasons": ["winter"]},
            {"name": "New Year Goals", "description": "Resolutions, planning, and fresh starts", "language": "en", "seasons": ["winter"]},
            {"name": "Neujahrsziele", "description": "Vorsätze, Planung und Neuanfänge", "language": "de", "seasons": ["winter"]}
        ]
        
        # Diverse journal themes for realistic variety
        self.journal_themes = [
            # Work & Career themes
            {"theme": "work stress and productivity challenges", "language": "en", "topic_category": "work"},
            {"theme": "team collaboration and workplace dynamics", "language": "en", "topic_category": "work"},
            {"theme": "career goals and professional development", "language": "en", "topic_category": "work"},
            {"theme": "work-life balance struggles", "language": "en", "topic_category": "work"},
            {"theme": "Arbeitsstress und Produktivitätsherausforderungen", "language": "de", "topic_category": "work"},
            {"theme": "Teamarbeit und Arbeitsplatz-Dynamik", "language": "de", "topic_category": "work"},
            {"theme": "Karriereziele und berufliche Entwicklung", "language": "de", "topic_category": "work"},
            
            # Personal Growth themes
            {"theme": "self-reflection and personal insights", "language": "en", "topic_category": "growth"},
            {"theme": "learning new skills and knowledge", "language": "en", "topic_category": "growth"},
            {"theme": "overcoming personal challenges", "language": "en", "topic_category": "growth"},
            {"theme": "meditation and mindfulness practice", "language": "en", "topic_category": "growth"},
            {"theme": "Selbstreflexion und persönliche Einsichten", "language": "de", "topic_category": "growth"},
            {"theme": "neue Fähigkeiten und Wissen erlernen", "language": "de", "topic_category": "growth"},
            {"theme": "persönliche Herausforderungen überwinden", "language": "de", "topic_category": "growth"},
            
            # Family & Relationships themes
            {"theme": "family time and bonding experiences", "language": "en", "topic_category": "relationships"},
            {"theme": "friendship dynamics and social connections", "language": "en", "topic_category": "relationships"},
            {"theme": "romantic relationship reflections", "language": "en", "topic_category": "relationships"},
            {"theme": "communication challenges with loved ones", "language": "en", "topic_category": "relationships"},
            {"theme": "Familienzeit und verbindende Erfahrungen", "language": "de", "topic_category": "relationships"},
            {"theme": "Freundschaftsdynamik und soziale Verbindungen", "language": "de", "topic_category": "relationships"},
            {"theme": "romantische Beziehungsreflexionen", "language": "de", "topic_category": "relationships"},
            
            # Health & Wellness themes
            {"theme": "fitness journey and exercise routines", "language": "en", "topic_category": "health"},
            {"theme": "mental health and emotional wellbeing", "language": "en", "topic_category": "health"},
            {"theme": "nutrition and healthy eating habits", "language": "en", "topic_category": "health"},
            {"theme": "sleep patterns and rest quality", "language": "en", "topic_category": "health"},
            {"theme": "Fitness-Reise und Trainingsroutinen", "language": "de", "topic_category": "health"},
            {"theme": "mentale Gesundheit und emotionales Wohlbefinden", "language": "de", "topic_category": "health"},
            {"theme": "Ernährung und gesunde Essgewohnheiten", "language": "de", "topic_category": "health"},
            
            # Daily Life themes
            {"theme": "morning routines and daily habits", "language": "en", "topic_category": "daily"},
            {"theme": "evening reflections and gratitude", "language": "en", "topic_category": "daily"},
            {"theme": "weekend activities and leisure time", "language": "en", "topic_category": "daily"},
            {"theme": "weather and seasonal observations", "language": "en", "topic_category": "daily"},
            {"theme": "cooking and meal experiences", "language": "en", "topic_category": "daily"},
            {"theme": "Morgenroutinen und tägliche Gewohnheiten", "language": "de", "topic_category": "daily"},
            {"theme": "Abendreflexionen und Dankbarkeit", "language": "de", "topic_category": "daily"},
            {"theme": "Wochenendaktivitäten und Freizeit", "language": "de", "topic_category": "daily"},
            
            # Seasonal themes
            {"theme": "travel planning and adventure dreams", "language": "en", "topic_category": "seasonal", "seasons": ["spring", "summer"]},
            {"theme": "holiday preparations and celebrations", "language": "en", "topic_category": "seasonal", "seasons": ["winter"]},
            {"theme": "new year resolutions and goal setting", "language": "en", "topic_category": "seasonal", "seasons": ["winter"]},
            {"theme": "Reiseplanung und Abenteuerträume", "language": "de", "topic_category": "seasonal", "seasons": ["spring", "summer"]},
            {"theme": "Feiertagsvorbereitungen und Feiern", "language": "de", "topic_category": "seasonal", "seasons": ["winter"]}
        ]
        
        # Chat session themes for variety
        self.chat_themes = [
            # English themes
            {"theme": "exploring feelings about work-life balance", "language": "en"},
            {"theme": "discussing relationship challenges", "language": "en"},
            {"theme": "reflecting on personal goals and motivation", "language": "en"},
            {"theme": "processing anxiety and stress management", "language": "en"},
            {"theme": "exploring creativity and passion projects", "language": "en"},
            {"theme": "working through decision-making challenges", "language": "en"},
            {"theme": "discussing self-improvement strategies", "language": "en"},
            {"theme": "reflecting on past experiences and lessons learned", "language": "en"},
            {"theme": "exploring future aspirations and dreams", "language": "en"},
            {"theme": "processing daily emotions and thoughts", "language": "en"},
            # German themes
            {"theme": "Gefühle zur Work-Life-Balance erkunden", "language": "de"},
            {"theme": "Beziehungsherausforderungen besprechen", "language": "de"},
            {"theme": "persönliche Ziele und Motivation reflektieren", "language": "de"},
            {"theme": "Angst und Stressmanagement verarbeiten", "language": "de"},
            {"theme": "Kreativität und Leidenschaftsprojekte erkunden", "language": "de"},
            {"theme": "Entscheidungsfindung durcharbeiten", "language": "de"},
            {"theme": "Selbstverbesserungsstrategien diskutieren", "language": "de"},
            {"theme": "vergangene Erfahrungen und Lektionen reflektieren", "language": "de"},
            {"theme": "zukünftige Bestrebungen und Träume erkunden", "language": "de"},
            {"theme": "tägliche Emotionen und Gedanken verarbeiten", "language": "de"}
        ]
        
        # Store created topic IDs for reuse
        self.created_topic_ids = {}
    
    def get_season(self, date: datetime) -> str:
        """Get season based on date"""
        month = date.month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "autumn"
    
    def select_theme_for_date(self, date: datetime, language_preference: str = None) -> Dict[str, str]:
        """Select appropriate theme based on date and season"""
        season = self.get_season(date)
        
        # 70% chance for language preference if specified, 30% chance for other language
        if language_preference and random.random() < 0.7:
            language = language_preference
        else:
            language = random.choice(['en', 'de'])
        
        # Filter themes by language and appropriate season
        available_themes = [
            theme for theme in self.journal_themes 
            if theme['language'] == language and (
                'seasons' not in theme or season in theme.get('seasons', [])
            )
        ]
        
        return random.choice(available_themes)
    
    def should_create_seasonal_topic(self, date: datetime) -> Dict[str, str]:
        """Determine if a seasonal topic should be created"""
        season = self.get_season(date)
        
        # Only create seasonal topics during relevant seasons
        relevant_topics = [
            topic for topic in self.seasonal_topics 
            if season in topic.get('seasons', [])
        ]
        
        # 20% chance to create a seasonal topic during relevant season
        if relevant_topics and random.random() < 0.2:
            return random.choice(relevant_topics)
        
        return None
    
    def get_topic_for_theme(self, theme_data: Dict[str, str]) -> str:
        """Get appropriate topic ID for a theme"""
        category = theme_data.get('topic_category', 'daily')
        language = theme_data['language']
        
        # Map categories to topic names
        topic_mapping = {
            'work': 'Work & Career' if language == 'en' else 'Arbeit & Karriere',
            'growth': 'Personal Growth' if language == 'en' else 'Persönliche Entwicklung',
            'relationships': 'Family & Relationships' if language == 'en' else 'Familie & Beziehungen',
            'health': 'Health & Wellness' if language == 'en' else 'Gesundheit & Wohlbefinden',
            'daily': 'Daily Life' if language == 'en' else 'Alltag',
            'seasonal': None  # Will be handled separately
        }
        
        topic_name = topic_mapping.get(category)
        return self.created_topic_ids.get(topic_name)

    async def generate_journal_entry(self, theme_data: Dict[str, str], days_ago: int) -> Dict[str, Any]:
        """Generate a realistic journal entry using Ollama"""
        
        theme = theme_data["theme"]
        language = theme_data["language"]
        
        # Create a date for the entry
        entry_date = datetime.now() - timedelta(days=days_ago)
        day_of_week = entry_date.strftime("%A") if language == "en" else {
            "Monday": "Montag", "Tuesday": "Dienstag", "Wednesday": "Mittwoch", 
            "Thursday": "Donnerstag", "Friday": "Freitag", "Saturday": "Samstag", "Sunday": "Sonntag"
        }.get(entry_date.strftime("%A"), entry_date.strftime("%A"))
        
        if language == "en":
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
        else:
            prompt = f"""Schreibe einen persönlichen Tagebucheintrag über {theme}.

Richtlinien:
- Schreibe in der ersten Person, als würdest du über deinen Tag/deine Woche reflektieren
- Mache es authentisch und persönlich (200-400 Wörter)
- Füge spezifische Details und Emotionen hinzu
- Erwähne, dass es ein {day_of_week} ist
- Lass es wie die echten Gedanken und Erfahrungen einer Person wirken
- Füge konkrete Details oder Ereignisse hinzu
- Zeige echte Emotionen und Selbstreflexion

Schreibe nur den Tagebuchinhalt, keinen Titel oder Formatierung:"""

        try:
            response = self.ollama_client.generate(
                model="llama3.1",
                prompt=prompt,
                stream=False
            )
            
            content = response['response'].strip()
            
            # Generate a simple title based on the theme
            if language == "en":
                title_prompt = f"Create a short, personal title (3-6 words) for a journal entry about {theme}. Just return the title, nothing else:"
            else:
                title_prompt = f"Erstelle einen kurzen, persönlichen Titel (3-6 Wörter) für einen Tagebucheintrag über {theme}. Gib nur den Titel zurück, nichts anderes:"
            
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
                "tags": [],  # Let auto-tagging handle this
                "language": language
            }
            
        except Exception as e:
            print(f"Error generating journal entry: {e}")
            fallback_title = "Reflection" if language == "en" else "Reflexion"
            fallback_content = f"Today I've been thinking about {theme}." if language == "en" else f"Heute habe ich über {theme} nachgedacht."
            return {
                "title": fallback_title,
                "content": fallback_content,
                "entry_type": "journal", 
                "tags": [],
                "language": language
            }

    async def generate_chat_conversation(self, theme_data: Dict[str, str], session_type: SessionType) -> List[Dict[str, Any]]:
        """Generate a realistic chat conversation using Ollama"""
        
        theme = theme_data["theme"]
        language = theme_data["language"]
        
        # Define the AI assistant personality based on session type and language
        if language == "en":
            assistant_personalities = {
                SessionType.REFLECTION_BUDDY: "You are a warm, supportive reflection buddy. Ask thoughtful questions and provide gentle insights.",
                SessionType.INNER_VOICE: "You are the user's wise inner voice. Speak as their internal wisdom and intuition.",
                SessionType.GROWTH_CHALLENGE: "You are a motivational growth coach. Challenge the user to think bigger and take action.",
                SessionType.PATTERN_DETECTIVE: "You are an analytical pattern detective. Help the user identify patterns in their thoughts and behaviors.",
                SessionType.FREE_CHAT: "You are a friendly, open conversational partner. Be curious and engaging."
            }
            user_prompt = f"""You are a person starting a conversation with an AI assistant about {theme}. 
            Write a natural opening message (1-3 sentences) that someone might send when they want to talk about this topic.
            Be authentic and conversational. Just write the message, nothing else:"""
        else:
            assistant_personalities = {
                SessionType.REFLECTION_BUDDY: "Du bist ein warmer, unterstützender Reflexionspartner. Stelle durchdachte Fragen und biete sanfte Einsichten.",
                SessionType.INNER_VOICE: "Du bist die weise innere Stimme des Nutzers. Sprich als ihre interne Weisheit und Intuition.",
                SessionType.GROWTH_CHALLENGE: "Du bist ein motivierender Wachstumscoach. Fordere den Nutzer heraus, größer zu denken und zu handeln.",
                SessionType.PATTERN_DETECTIVE: "Du bist ein analytischer Musterdetektiv. Hilf dem Nutzer, Muster in Gedanken und Verhaltensweisen zu erkennen.",
                SessionType.FREE_CHAT: "Du bist ein freundlicher, offener Gesprächspartner. Sei neugierig und einnehmend."
            }
            user_prompt = f"""Du bist eine Person, die ein Gespräch mit einem KI-Assistenten über {theme} beginnt.
            Schreibe eine natürliche Eröffnungsnachricht (1-3 Sätze), die jemand senden könnte, wenn er über dieses Thema sprechen möchte.
            Sei authentisch und gesprächig. Schreibe nur die Nachricht, nichts anderes:"""
        
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
                if language == "en":
                    ai_prompt = f"""{assistant_personalities[session_type]}

Conversation so far:
{conversation_history}

Respond to the user's message naturally and helpfully. Keep it conversational and supportive (1-3 sentences). 
Just write the response, nothing else:"""
                else:
                    ai_prompt = f"""{assistant_personalities[session_type]}

Gespräch bisher:
{conversation_history}

Antworte auf die Nachricht des Nutzers natürlich und hilfreich. Halte es gesprächig und unterstützend (1-3 Sätze).
Schreibe nur die Antwort, nichts anderes:"""
                
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
                    if language == "en":
                        user_followup_prompt = f"""Based on this conversation so far:
{conversation_history}

Write a natural follow-up response from the user. Be authentic and continue the conversation meaningfully (1-2 sentences).
Just write the message, nothing else:"""
                    else:
                        user_followup_prompt = f"""Basierend auf diesem Gespräch bisher:
{conversation_history}

Schreibe eine natürliche Antwort des Nutzers. Sei authentisch und führe das Gespräch sinnvoll weiter (1-2 Sätze).
Schreibe nur die Nachricht, nichts anderes:"""
                    
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
            if language == "en":
                return [
                    {"content": f"I've been thinking about {theme} lately and would love to explore it more.", "role": "user"},
                    {"content": "That sounds like an important topic to explore. What specifically about it has been on your mind?", "role": "assistant"},
                    {"content": "I guess I'm just trying to understand it better and figure out how to move forward.", "role": "user"},
                    {"content": "Understanding is often the first step toward positive change. What feels most important to focus on right now?", "role": "assistant"}
                ]
            else:
                return [
                    {"content": f"Ich habe in letzter Zeit über {theme} nachgedacht und würde es gerne weiter erkunden.", "role": "user"},
                    {"content": "Das klingt nach einem wichtigen Thema zum Erkunden. Was beschäftigt dich speziell daran?", "role": "assistant"},
                    {"content": "Ich versuche es wohl einfach besser zu verstehen und herauszufinden, wie ich weitermachen soll.", "role": "user"},
                    {"content": "Verstehen ist oft der erste Schritt zu positiver Veränderung. Worauf sich zu konzentrieren fühlt sich jetzt am wichtigsten an?", "role": "assistant"}
                ]

    async def create_topic(self, topic_data: Dict[str, str]) -> str:
        """Create a topic via API and return its ID"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/topics/",
                    json=topic_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        lang_flag = "🇺🇸" if topic_data['language'] == 'en' else "🇩🇪"
                        print(f"✅ Created topic: '{topic_data['name']}' {lang_flag}")
                        return result['id']
                    else:
                        error_text = await response.text()
                        print(f"❌ Failed to create topic: {response.status} - {error_text}")
                        return None
        except Exception as e:
            print(f"❌ Error creating topic: {e}")
            return None

    async def create_journal_entry(self, entry_data: Dict[str, Any], topic_id: str = None) -> bool:
        """Create a journal entry via API"""
        try:
            # Add topic_id if provided
            if topic_id:
                entry_data['topic_id'] = topic_id
                
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/entries/",
                    json=entry_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        lang_flag = "🇺🇸" if entry_data.get('language') == 'en' else "🇩🇪"
                        print(f"✅ Created journal entry: '{entry_data['title']}' {lang_flag}")
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

    async def create_chat_session(self, session_type: SessionType, theme_data: Dict[str, str], messages: List[Dict]) -> bool:
        """Create a chat session with messages via API"""
        try:
            # Create session
            lang_flag = "🇺🇸" if theme_data['language'] == 'en' else "🇩🇪"
            session_data = {
                "session_type": session_type.value,
                "title": f"Chat about {theme_data['theme']}",
                "description": f"Conversation exploring {theme_data['theme']}",
                "metadata": {"theme": theme_data['theme'], "language": theme_data['language']}
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
                    print(f"✅ Created chat session: '{session_data['title']}' {lang_flag}")
                
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

    async def populate_year_data(self, language_preference: str = None):
        """Populate the application with a full year of realistic data (1-3 entries per day)"""
        
        print("🚀 Starting FULL YEAR data population...")
        print("📅 Generating entries from one year ago to today")
        print("� 1-3 entries per day (journal entries + chat sessions)")
        print("🌍 Languages: English 🇺🇸 and German 🇩🇪")
        if language_preference:
            lang_flag = "🇺🇸" if language_preference == 'en' else "🇩🇪"
            print(f"🎯 Preference: {language_preference} {lang_flag} (70% of content)")
        print()
        
        # Create core topics first
        print("📚 Creating core topics...")
        for topic in self.core_topics:
            topic_id = await self.create_topic(topic)
            if topic_id:
                self.created_topic_ids[topic['name']] = topic_id
            await asyncio.sleep(0.3)
        
        print()
        
        # Generate daily entries for the past year
        start_date = datetime.now() - timedelta(days=365)
        end_date = datetime.now()
        current_date = start_date
        
        total_entries = 0
        total_chats = 0
        seasonal_topics_created = set()
        
        print("📝 Generating year-long daily entries...")
        print(f"📅 From {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print()
        
        while current_date <= end_date:
            # Determine number of entries for this day (1-3, weighted toward 1-2)
            num_entries = random.choices([1, 2, 3], weights=[50, 35, 15])[0]
            
            # Reduce entries on some days to simulate realistic patterns
            if random.random() < 0.15:  # 15% chance of no entries (busy days)
                num_entries = 0
            elif current_date.weekday() in [5, 6]:  # Weekends - slightly different pattern
                num_entries = random.choices([1, 2, 3], weights=[40, 40, 20])[0]
            
            days_ago = (end_date - current_date).days
            
            # Create seasonal topic if appropriate
            seasonal_topic = self.should_create_seasonal_topic(current_date)
            if seasonal_topic and seasonal_topic['name'] not in seasonal_topics_created:
                topic_id = await self.create_topic(seasonal_topic)
                if topic_id:
                    self.created_topic_ids[seasonal_topic['name']] = topic_id
                    seasonal_topics_created.add(seasonal_topic['name'])
                await asyncio.sleep(0.3)
            
            for entry_num in range(num_entries):
                entry_type = random.choices(['journal', 'chat'], weights=[70, 30])[0]
                
                if entry_type == 'journal':
                    # Generate journal entry
                    theme_data = self.select_theme_for_date(current_date, language_preference)
                    
                    if total_entries % 50 == 0:
                        lang_flag = "🇺🇸" if theme_data['language'] == 'en' else "🇩🇪"
                        print(f"   📝 Day {365 - days_ago}/365: {current_date.strftime('%Y-%m-%d')} - Entry {total_entries + 1} {lang_flag}")
                    
                    entry_data = await self.generate_journal_entry(theme_data, days_ago)
                    topic_id = self.get_topic_for_theme(theme_data)
                    
                    await self.create_journal_entry(entry_data, topic_id)
                    total_entries += 1
                    
                else:
                    # Generate chat session
                    theme_data = random.choice([t for t in self.chat_themes if t['language'] == (language_preference or random.choice(['en', 'de']))])
                    session_type = random.choice(list(SessionType))
                    
                    if total_chats % 20 == 0:
                        lang_flag = "🇺🇸" if theme_data['language'] == 'en' else "🇩🇪"
                        print(f"   💬 Day {365 - days_ago}/365: {current_date.strftime('%Y-%m-%d')} - Chat {total_chats + 1} {lang_flag}")
                    
                    messages = await self.generate_chat_conversation(theme_data, session_type)
                    await self.create_chat_session(session_type, theme_data, messages)
                    total_chats += 1
                
                # Small delay between entries
                await asyncio.sleep(0.5)
            
            # Move to next day
            current_date += timedelta(days=1)
            
            # Longer delay every 10 days to avoid overwhelming the API
            if (end_date - current_date).days % 10 == 0:
                await asyncio.sleep(2)
        
        print()
        print("✨ FULL YEAR data population complete!")
        print()
        print("🎯 What was created:")
        print(f"   • {len(self.created_topic_ids)} topics (core + seasonal)")
        print(f"   • {total_entries} journal entries across 365 days")
        print(f"   • {total_chats} chat sessions with conversations")
        print(f"   • Realistic daily patterns (1-3 entries per day)")
        print(f"   • Seasonal content variation")
        print(f"   • Multilingual content (English 🇺🇸 and German 🇩🇪)")
        print(f"   • Automatic sentiment analysis and AI-generated tags")
        print()
        print("📊 Data distribution:")
        print(f"   • Average {total_entries/365:.1f} journal entries per day")
        print(f"   • Average {total_chats/365:.1f} chat sessions per day")
        print(f"   • Total: {total_entries + total_chats} content pieces")
        print()
        print("🔍 Perfect for testing:")
        print("   • Mood prediction patterns over time")
        print("   • Long-term emotional trends and insights")
        print("   • Seasonal variation in content and mood")
        print("   • Hardware-adaptive AI performance with large datasets")
        print("   • Auto-tagging accuracy across diverse content")

    async def populate_data(self, num_journal_entries: int = 15, num_chat_sessions: int = 8):
        """Populate the application with sample data (original method for smaller datasets)"""
        
        print("🚀 Starting data population...")
        print(f"📚 Creating {len(self.core_topics)} core topics")
        print(f"📝 Generating {num_journal_entries} journal entries")
        print(f"💬 Generating {num_chat_sessions} chat sessions")
        print("🌍 Languages: English 🇺🇸 and German 🇩🇪")
        print()
        
        # Create core topics first
        print("📚 Creating core topics...")
        for topic in self.core_topics:
            topic_id = await self.create_topic(topic)
            if topic_id:
                self.created_topic_ids[topic['name']] = topic_id
            await asyncio.sleep(0.5)
        
        print()
        
        # Generate journal entries
        print("📝 Creating journal entries...")
        for i in range(num_journal_entries):
            theme_data = random.choice(self.journal_themes)
            days_ago = random.randint(1, 30)  # Spread across last 30 days
            
            print(f"   Generating entry {i+1}/{num_journal_entries}: {theme_data['theme']} ({theme_data['language']})")
            entry_data = await self.generate_journal_entry(theme_data, days_ago)
            topic_id = self.get_topic_for_theme(theme_data)
            
            await self.create_journal_entry(entry_data, topic_id)
            await asyncio.sleep(1)
        
        print()
        
        # Generate chat sessions
        print("💬 Creating chat sessions...")
        session_types = list(SessionType)
        
        for i in range(num_chat_sessions):
            theme_data = random.choice(self.chat_themes)
            session_type = random.choice(session_types)
            
            print(f"   Generating session {i+1}/{num_chat_sessions}: {theme_data['theme']} ({theme_data['language']}, {session_type.value})")
            messages = await self.generate_chat_conversation(theme_data, session_type)
            await self.create_chat_session(session_type, theme_data, messages)
            
            # Small delay to avoid overwhelming the API
            await asyncio.sleep(2)
        
        print()
        print("✨ Data population complete!")
        print()
        print("🎯 What was created:")
        print(f"   • {len(self.created_topic_ids)} topics in English and German")
        print(f"   • {num_journal_entries} journal entries with automatic tags")
        print(f"   • {num_chat_sessions} chat sessions with conversations")
        print(f"   • Automatic sentiment analysis for all content")
        print(f"   • AI-generated tags for better organization")
        print(f"   • Multilingual content testing (English 🇺🇸 and German 🇩🇪)")

async def main():
    """Main function to run the data population"""
    
    parser = argparse.ArgumentParser(description="Populate journaling AI with sample data")
    parser.add_argument("--year", action="store_true", help="Generate a full year of data (365 days)")
    parser.add_argument("--language", choices=['en', 'de'], help="Language preference (en/de, 70 percent of content)")
    parser.add_argument("--journal-entries", type=int, default=15, help="Number of journal entries for regular mode")
    parser.add_argument("--chat-sessions", type=int, default=8, help="Number of chat sessions for regular mode")
    
    args = parser.parse_args()
    
    populator = DataPopulator()
    
    if args.year:
        await populator.populate_year_data(args.language)
    else:
        await populator.populate_data(args.journal_entries, args.chat_sessions)

if __name__ == "__main__":
    asyncio.run(main())
