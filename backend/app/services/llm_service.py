### app/services/llm_service.py

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
    
    async def analyze_entries_for_insights(self, entries: List[Dict[str, Any]], 
                                         question: str) -> str:
        """Analyze entries to provide insights"""
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
        """Generate personalized coaching suggestions"""
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