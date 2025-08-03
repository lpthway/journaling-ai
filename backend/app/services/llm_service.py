# backend/app/services/llm_service.py - Enhanced version

import ollama
import json
from typing import List, Dict, Any, Optional
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.client = ollama.Client(host=settings.OLLAMA_BASE_URL)
        self.model = settings.OLLAMA_MODEL
    
    async def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate a response using the local LLM"""
        try:
            full_prompt = prompt
            if context:
                full_prompt = f"Context:\n{context}\n\nQuestion: {prompt}\n\nAnswer:"
            
            response = self.client.generate(
                model=self.model,
                prompt=full_prompt,
                stream=False
            )
            
            return response['response']
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return "I'm sorry, I couldn't generate a response at this time."
    
    async def analyze_combined_content(self, combined_content: List[Dict[str, Any]], question: str) -> str:
        """Analyze both journal entries and chat conversations to provide insights"""
        try:
            # Prepare context from both sources
            context_parts = []
            journal_count = 0
            chat_count = 0
            
            context_parts.append("Here's your personal content from both journal entries and conversations:\n")
            
            for i, content in enumerate(combined_content[:15], 1):  # Limit to most relevant
                content_type = content['type']
                metadata = content.get('metadata', {})
                
                if content_type == 'journal':
                    journal_count += 1
                    date = metadata.get('created_at', 'Unknown date')
                    mood = metadata.get('mood', 'Unknown mood')
                    title = metadata.get('title', 'Untitled')
                    
                    context_parts.append(f"\n--- Journal Entry {journal_count} ({date}) ---")
                    context_parts.append(f"Title: {title}")
                    context_parts.append(f"Mood: {mood}")
                    context_parts.append(f"Content: {content['content'][:300]}...")
                    
                elif content_type == 'chat':
                    chat_count += 1
                    date = metadata.get('created_at', 'Unknown date')
                    session_type = metadata.get('session_type', 'Unknown session')
                    message_count = metadata.get('message_count', 0)
                    
                    context_parts.append(f"\n--- Conversation {chat_count} ({date}) ---")
                    context_parts.append(f"Type: {session_type.replace('_', ' ').title()}")
                    context_parts.append(f"Messages: {message_count}")
                    context_parts.append(f"Your thoughts: {content['content'][:300]}...")
            
            context = "\n".join(context_parts)
            
            prompt = f"""Based on the personal content above (including {journal_count} journal entries and {chat_count} conversations), please answer this question: {question}

Please provide a thoughtful, personalized response using proper markdown formatting that:
1. References specific patterns or themes from BOTH journal entries and conversations
2. Offers insights about growth, changes, or trends across all your reflections
3. Is supportive and constructive
4. Acknowledges the different types of content (written journal vs. conversational)
5. Maintains privacy and confidentiality

FORMAT YOUR RESPONSE IN MARKDOWN:
- Use **bold** for emphasis on key insights
- Use ## headings for major sections (like "Key Patterns", "Growth Insights", "Recommendations")
- Use bullet points with - for lists
- Use numbered lists 1. 2. 3. for sequential points
- Use > blockquotes for important reflections
- Use *italics* for subtle emphasis

IMPORTANT - INLINE CITATIONS:
When referencing specific content, include inline citations like this:
- For journal entries: "In your journal entry about testing [📔1]..."
- For conversations: "During your conversation about work issues [💬2]..."
- Use [📔X] for journal entry citations (where X is the entry number)
- Use [💬X] for conversation citations (where X is the conversation number)

This helps readers jump directly to the source material you're referencing.

Your response should help with self-reflection and personal growth by drawing connections between your written thoughts and conversational insights."""
            
            return await self.generate_response(prompt, context)
            
        except Exception as e:
            logger.error(f"Error analyzing combined content: {e}")
            return "I couldn't analyze your content at this time. Please try again later."
    
    async def generate_enhanced_coaching_suggestions(self, combined_content: List[Dict[str, Any]]) -> List[str]:
        """Generate coaching suggestions based on both journal entries and chat conversations"""
        try:
            if not combined_content:
                return ["Keep writing in your journal and having conversations to track your progress and get personalized suggestions!"]
            
            # Prepare context
            context_parts = ["Recent personal content:\n"]
            journal_entries = [c for c in combined_content if c['type'] == 'journal']
            chat_entries = [c for c in combined_content if c['type'] == 'chat']
            
            # Add journal entries
            if journal_entries:
                context_parts.append("\nJournal Entries:")
                for i, entry in enumerate(journal_entries[:3], 1):
                    metadata = entry.get('metadata', {})
                    context_parts.append(f"{i}. Date: {metadata.get('created_at', 'Unknown')} - Mood: {metadata.get('mood', 'Unknown')}")
                    context_parts.append(f"   {entry['content'][:150]}...")
            
            # Add chat conversations
            if chat_entries:
                context_parts.append("\nConversation Insights:")
                for i, chat in enumerate(chat_entries[:3], 1):
                    metadata = chat.get('metadata', {})
                    context_parts.append(f"{i}. Session: {metadata.get('session_type', 'Unknown').replace('_', ' ').title()}")
                    context_parts.append(f"   {chat['content'][:150]}...")
            
            context = "\n".join(context_parts)
            
            prompt = f"""Based on this personal content from both journal writing and AI conversations, provide 4-5 brief, actionable coaching suggestions that could help with personal growth, wellbeing, or addressing any challenges mentioned.

Consider the different contexts:
- Journal entries show deliberate reflection and writing
- Conversations show interactive exploration and real-time thoughts

Format as a simple list of suggestions, each on a new line starting with a dash (-).

Focus on practical, specific recommendations that acknowledge both the reflective and conversational aspects of personal growth."""
            
            response = await self.generate_response(prompt, context)
            
            # Parse suggestions from response
            suggestions = []
            for line in response.split('\n'):
                line = line.strip()
                if line.startswith('-') or line.startswith('•'):
                    suggestions.append(line[1:].strip())
                elif line and not suggestions:  # First non-empty line if no bullet format
                    suggestions.append(line)
            
            return suggestions[:5] if suggestions else ["Continue both journaling and conversations to track your thoughts and feelings."]
        
        except Exception as e:
            logger.error(f"Error generating enhanced coaching suggestions: {e}")
            return ["Keep reflecting on your experiences through both writing and conversation."]
    
    async def analyze_entries_for_insights(self, entries: List[Dict[str, Any]], question: str) -> str:
        """Original method - analyze entries to provide insights (for backward compatibility)"""
        try:
            # Prepare context from entries
            context_entries = []
            for entry in entries[:10]:  # Limit to most relevant entries
                metadata = entry.get('metadata', {})
                context_entries.append({
                    'date': metadata.get('created_at', 'Unknown'),
                    'mood': metadata.get('mood', 'Unknown'),
                    'content': entry['content'][:200] + '...' if len(entry['content']) > 200 else entry['content']
                })
            
            context = "Here are some of your journal entries:\n\n"
            for i, entry in enumerate(context_entries, 1):
                context += f"Entry {i} ({entry['date']}) - Mood: {entry['mood']}\n"
                context += f"{entry['content']}\n\n"
            
            prompt = f"""Based on the journal entries provided, please answer this question: {question}

FORMAT YOUR RESPONSE IN MARKDOWN:
- Use **bold** for emphasis on key insights
- Use ## headings for major sections (like "Key Patterns", "Growth Insights", "Recommendations")
- Use bullet points with - for lists
- Use numbered lists 1. 2. 3. for sequential points
- Use > blockquotes for important reflections
- Use *italics* for subtle emphasis

IMPORTANT - INLINE CITATIONS:
When referencing specific entries, include inline citations like this:
- "In your entry about testing [📔1]..." or "Your reflection on growth [📔2]..."
- Use [📔X] for journal entry citations (where X is the entry number from 1-{len(context_entries)})

Please provide a thoughtful, personalized response that:
1. References specific patterns or themes from the entries
2. Offers insights about growth, changes, or trends
3. Is supportive and constructive
4. Maintains privacy and confidentiality

Your response should be helpful for self-reflection and personal growth."""
            
            return await self.generate_response(prompt, context)
        except Exception as e:
            logger.error(f"Error analyzing entries: {e}")
            return "I couldn't analyze your entries at this time. Please try again later."
    
    async def generate_coaching_suggestions(self, recent_entries: List[Dict[str, Any]]) -> List[str]:
        """Original method - generate coaching suggestions (for backward compatibility)"""
        try:
            if not recent_entries:
                return ["Keep writing in your journal to track your progress and get personalized suggestions!"]
            
            context = "Recent journal entries:\n\n"
            for entry in recent_entries[:5]:
                metadata = entry.get('metadata', {})
                context += f"Date: {metadata.get('created_at', 'Unknown')} - Mood: {metadata.get('mood', 'Unknown')}\n"
                context += f"{entry['content'][:150]}...\n\n"
            
            prompt = """Based on these recent journal entries, provide 3-5 brief, actionable coaching suggestions that could help with personal growth, wellbeing, or addressing any challenges mentioned. 

Format as a simple list of suggestions, each on a new line starting with a dash (-)."""
            
            response = await self.generate_response(prompt, context)
            
            # Parse suggestions from response
            suggestions = []
            for line in response.split('\n'):
                line = line.strip()
                if line.startswith('-') or line.startswith('•'):
                    suggestions.append(line[1:].strip())
                elif line and not suggestions:  # First non-empty line if no bullet format
                    suggestions.append(line)
            
            return suggestions[:5] if suggestions else ["Continue journaling to track your thoughts and feelings."]
        
        except Exception as e:
            logger.error(f"Error generating coaching suggestions: {e}")
            return ["Keep reflecting on your experiences and emotions through journaling."]

# Global instance
llm_service = LLMService()