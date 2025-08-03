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
    
    # Simple predefined content for quick generation - English and German
    journal_entries = [
        {
            "title": "Productive Monday",
            "content": "Had a really productive day at work today. Finished the quarterly report and felt great about the presentation. The team responded well to my ideas. Feeling motivated and confident about the upcoming projects. Need to remember to maintain this momentum.",
            "entry_type": "journal",
            "language": "en"
        },
        {
            "title": "Arbeitsreiche Woche", 
            "content": "Diese Woche war besonders arbeitsreich. Ich habe viele neue Projekte übernommen und fühle mich etwas überfordert. Aber gleichzeitig bin ich stolz auf das, was ich geschafft habe. Ich muss lernen, besser Prioritäten zu setzen und auch mal Nein zu sagen.",
            "entry_type": "journal",
            "language": "de"
        },
        {
            "title": "Weekend Reflection", 
            "content": "Spent the weekend hiking with friends. It was exactly what I needed after a stressful week. There's something about being in nature that helps me reset and gain perspective. Feeling grateful for good friends and outdoor adventures.",
            "entry_type": "journal",
            "language": "en"
        },
        {
            "title": "Familienfest",
            "content": "Heute hatten wir ein großes Familienfest. Es war schön, alle wiederzusehen, aber auch anstrengend. Meine Großmutter hat viele Geschichten aus ihrer Jugend erzählt. Es hat mich daran erinnert, wie wichtig Familie ist und dass ich mehr Zeit mit ihnen verbringen sollte.",
            "entry_type": "journal",
            "language": "de"
        },
        {
            "title": "Challenging Day",
            "content": "Today was tough. Had a difficult conversation with my manager about the project timeline. Feeling anxious about whether I can meet all the expectations. Need to break things down into smaller tasks and focus on what I can control.",
            "entry_type": "journal",
            "language": "en"
        },
        {
            "title": "Kreative Inspiration",
            "content": "Heute hatte ich einen richtig kreativen Tag! Ich habe endlich eine Lösung für das Problem gefunden, das mich schon wochenlang beschäftigt hat. Manchmal kommen die besten Ideen, wenn man nicht aktiv darüber nachdenkt. Ich bin gespannt, wie es weitergeht.",
            "entry_type": "journal",
            "language": "de"
        },
        {
            "title": "Family Time",
            "content": "Had dinner with my family tonight. My sister shared some exciting news about her job promotion. It made me reflect on my own career goals and what I want to achieve this year. Feeling inspired by her success and motivated to pursue my own ambitions.",
            "entry_type": "journal",
            "language": "en"
        }
    ]
    
    # Topics to create for testing
    topics = [
        {
            "name": "Work & Career",
            "description": "Everything related to professional life, career development, and workplace experiences",
            "language": "en"
        },
        {
            "name": "Arbeit & Karriere",
            "description": "Alles rund um das Berufsleben, Karriereentwicklung und Erfahrungen am Arbeitsplatz",
            "language": "de"
        },
        {
            "name": "Personal Growth",
            "description": "Self-reflection, learning experiences, and personal development journey",
            "language": "en"
        },
        {
            "name": "Persönliche Entwicklung",
            "description": "Selbstreflexion, Lernerfahrungen und persönliche Weiterentwicklung",
            "language": "de"
        },
        {
            "name": "Family & Relationships",
            "description": "Connections with family, friends, and significant others",
            "language": "en"
        },
        {
            "name": "Familie & Beziehungen",
            "description": "Verbindungen zu Familie, Freunden und wichtigen Menschen",
            "language": "de"
        }
    ]
    
    async def create_sample_data(self):
        """Create a small set of sample data quickly"""
        
        print("🚀 Quick population starting...")
        
        # First create topics
        print("📚 Creating topics...")
        topic_ids = {}
        for topic in self.topics:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.api_base}/topics/",
                        json=topic,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            topic_ids[topic['name']] = result['id']
                            print(f"✅ Created topic: '{topic['name']}' ({topic['language']})")
                        else:
                            print(f"❌ Failed to create topic: '{topic['name']}'")
            except Exception as e:
                print(f"❌ Error creating topic: {e}")
        
        print()
        print(f"📝 Creating {len(self.journal_entries)} journal entries...")
        
        # Create journal entries with topic assignment
        for i, entry in enumerate(self.journal_entries):
            try:
                # Assign topic based on content and language
                topic_id = None
                if "work" in entry['content'].lower() or "arbeit" in entry['content'].lower():
                    if entry['language'] == 'en':
                        topic_id = topic_ids.get('Work & Career')
                    else:
                        topic_id = topic_ids.get('Arbeit & Karriere')
                elif "family" in entry['content'].lower() or "familie" in entry['content'].lower():
                    if entry['language'] == 'en':
                        topic_id = topic_ids.get('Family & Relationships')
                    else:
                        topic_id = topic_ids.get('Familie & Beziehungen')
                else:
                    if entry['language'] == 'en':
                        topic_id = topic_ids.get('Personal Growth')
                    else:
                        topic_id = topic_ids.get('Persönliche Entwicklung')
                
                entry_with_topic = entry.copy()
                if topic_id:
                    entry_with_topic['topic_id'] = topic_id
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.api_base}/entries/",
                        json=entry_with_topic,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            lang_flag = "🇺🇸" if entry['language'] == 'en' else "🇩🇪"
                            print(f"✅ Created: '{entry['title']}' {lang_flag}")
                            if result.get('tags'):
                                print(f"   Tags: {result['tags']}")
                        else:
                            print(f"❌ Failed to create: '{entry['title']}'")
            except Exception as e:
                print(f"❌ Error: {e}")
            
            await asyncio.sleep(0.5)  # Small delay
        
        print()
        print("💬 Creating 4 sample chat sessions...")
        
        # Create sample chat sessions - English and German
        sample_sessions = [
            {
                "session_type": "reflection_buddy",
                "title": "Work Stress Discussion",
                "description": "Talking through work-related stress",
                "language": "en",
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
                "language": "en",
                "messages": [
                    "I set some goals at the beginning of the year but I feel like I'm not making much progress.",
                    "Goal-setting can be tricky. What were some of the goals you set, and what does 'not much progress' look like to you?",
                    "I wanted to learn a new skill, exercise more regularly, and read more books. I've read maybe 2 books and my exercise routine is inconsistent.",
                    "Two books is still progress! And recognizing the inconsistency in exercise shows self-awareness. What's one small step you could take this week toward any of these goals?"
                ]
            },
            {
                "session_type": "inner_voice",
                "title": "Selbstreflexion über Beziehungen",
                "description": "Innere Stimme zur Reflexion über zwischenmenschliche Beziehungen",
                "language": "de",
                "messages": [
                    "Ich habe das Gefühl, dass ich in letzter Zeit nicht genug Zeit für meine Freunde habe. Die Arbeit nimmt so viel Raum ein.",
                    "Du spürst, dass das Gleichgewicht zwischen Arbeit und Freundschaften aus der Balance geraten ist. Was sagt dein Herz dazu?",
                    "Mein Herz sagt mir, dass Freundschaften wichtig sind und gepflegt werden müssen. Aber praktisch fällt es mir schwer, Zeit zu finden.",
                    "Deine innere Weisheit erkennt die Wichtigkeit von Verbindungen. Vielleicht geht es nicht um viel Zeit, sondern um bewusste, qualitätsvolle Momente?"
                ]
            },
            {
                "session_type": "pattern_detective",
                "title": "Analyse von Stressmustern",
                "description": "Untersuchung wiederkehrender Stressmuster im Alltag",
                "language": "de",
                "messages": [
                    "Mir fällt auf, dass ich immer montags besonders gestresst bin. Das passiert fast jede Woche.",
                    "Interessantes Muster! Lass uns das genauer betrachten. Was passiert typischerweise an Montagen, das sich von anderen Tagen unterscheidet?",
                    "Montags habe ich meist das Teammeetimg, viele E-Mails vom Wochenende und die Planung für die ganze Woche. Alles kommt zusammen.",
                    "Aha! Du hast ein klares Muster identifiziert: Montage = Meeting + E-Mail-Berg + Wochenplanung = Stress. Welche dieser drei Komponenten könntest du am ehesten verändern oder vorbereiten?"
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
                            lang_flag = "🇺🇸" if session_data['language'] == 'en' else "🇩🇪"
                            print(f"✅ Created session: '{session_data['title']}' {lang_flag}")
                            
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
        print(f"🎯 Created {len(self.topics)} topics + {len(self.journal_entries)} journal entries + 4 chat sessions")
        print("🌍 Multilingual data: English 🇺🇸 and German 🇩🇪")
        print("📚 Topics with categorized entries")
        print("🔍 Check the Insights tab to see your data!")

async def main():
    populator = QuickPopulator()
    await populator.create_sample_data()

if __name__ == "__main__":
    asyncio.run(main())
