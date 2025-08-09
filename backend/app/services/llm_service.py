# backend/app/services/llm_service.py - Enhanced with Psychology Knowledge Integration

import ollama
import json
from typing import List, Dict, Any, Optional, Tuple
import logging
from app.core.config import settings
from app.core.circuit_breaker import CircuitBreakerConfig, get_service_circuit_breaker
from app.services.psychology_knowledge_service import (
    psychology_knowledge_service, 
    PsychologyDomain
)

logger = logging.getLogger(__name__)

class EnhancedLLMService:
    """
    Enhanced LLM Service with integrated psychology knowledge database and proper resource management.
    
    Provides evidence-based, research-backed AI responses by combining:
    - User conversation context
    - Personal journal history 
    - Professional psychology knowledge
    - Source attribution and citations
    - Automatic memory cleanup
    """
    
    def __init__(self):
        self.client = ollama.Client(host=settings.OLLAMA_BASE_URL)
        self.model = settings.OLLAMA_MODEL
        self.psychology_service = psychology_knowledge_service
        self._active_requests = 0
        self._max_concurrent_requests = 5
        
        # Circuit breaker configuration for Ollama service
        ollama_config = CircuitBreakerConfig(
            failure_threshold=3,        # Open circuit after 3 failures
            recovery_timeout=30,        # Try recovery after 30 seconds
            success_threshold=2,        # Close circuit after 2 successes
            timeout=20.0,              # 20 second timeout for LLM calls
            expected_exceptions=(Exception,),  # All exceptions count as failures
            max_concurrent_calls=5     # Match our existing concurrency limit
        )
        self.circuit_breaker = get_service_circuit_breaker("ollama-llm", ollama_config)
    
    async def _circuit_breaker_generate(self, **generate_kwargs) -> Dict[str, Any]:
        """Circuit breaker protected Ollama generate call"""
        async def _make_ollama_call():
            # Convert to sync call since ollama client is synchronous
            import asyncio
            loop = asyncio.get_event_loop()
            
            def _sync_generate():
                return self.client.generate(**generate_kwargs)
                
            return await loop.run_in_executor(None, _sync_generate)
        
        return await self.circuit_breaker.call_async(_make_ollama_call)
        
    def __del__(self):
        """Destructor to ensure proper cleanup"""
        try:
            # Clean up any remaining resources
            if hasattr(self, 'client'):
                # Close any remaining connections
                del self.client
                
            # Force garbage collection
            import gc
            gc.collect()
        except Exception:
            # Ignore errors in destructor
            pass
    
    async def _resource_managed_request(self, request_func, *args, **kwargs):
        """Execute request with proper resource management"""
        if self._active_requests >= self._max_concurrent_requests:
            raise Exception("Too many concurrent requests - resource limit reached")
            
        self._active_requests += 1
        try:
            result = await request_func(*args, **kwargs)
            return result
        finally:
            self._active_requests -= 1
            # Force garbage collection after each request to prevent memory buildup
            import gc
            gc.collect()

    async def generate_evidence_based_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        journal_context: Optional[str] = None,
        session_type: str = "reflection_buddy"
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Generate AI response enhanced with psychology knowledge and source attribution.
        
        Returns:
            Tuple of (response_text, source_citations)
        """
        return await self._resource_managed_request(
            self._generate_evidence_based_response_impl,
            user_message, conversation_history, journal_context, session_type
        )
    
    async def _generate_evidence_based_response_impl(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        journal_context: Optional[str] = None,
        session_type: str = "reflection_buddy"
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Implementation of evidence-based response generation with resource management"""
        try:
            # Step 1: Get relevant psychology knowledge
            psychology_sources = await self._get_relevant_psychology_knowledge(
                user_message, journal_context, session_type
            )
            
            # Step 2: Build enhanced context with psychology insights
            enhanced_context = await self._build_enhanced_context(
                user_message, conversation_history, psychology_sources, journal_context
            )
            
            # Step 3: Generate response with professional psychology integration
            response = await self._generate_psychology_informed_response(
                enhanced_context, session_type
            )
            
            # Step 4: Format source citations
            citations = self._format_source_citations(psychology_sources)
            
            return response, citations
            
        except Exception as e:
            logger.error(f"Error generating evidence-based response: {e}")
            # Fallback to basic response
            return await self.generate_response(
                self._build_basic_prompt(user_message, conversation_history, session_type)
            ), []
    
    async def _get_relevant_psychology_knowledge(
        self,
        user_message: str,
        journal_context: Optional[str],
        session_type: str
    ) -> List[Dict[str, Any]]:
        """Intelligently select psychology knowledge based on conversation context"""
        
        # Map session types to preferred psychology domains
        session_domain_mapping = {
            "reflection_buddy": [PsychologyDomain.CBT, PsychologyDomain.EMOTIONAL_REGULATION],
            "inner_voice": [PsychologyDomain.MINDFULNESS, PsychologyDomain.POSITIVE_PSYCHOLOGY],
            "growth_challenge": [PsychologyDomain.HABIT_FORMATION, PsychologyDomain.POSITIVE_PSYCHOLOGY],
            "pattern_detective": [PsychologyDomain.CBT, PsychologyDomain.SOCIAL_PSYCHOLOGY],
            "crisis": [PsychologyDomain.CRISIS_INTERVENTION, PsychologyDomain.EMOTIONAL_REGULATION]
        }
        
        # Detect potential issues that need specific psychology domains
        issue_keywords = {
            "anxiety": [PsychologyDomain.CBT, PsychologyDomain.MINDFULNESS],
            "stress": [PsychologyDomain.STRESS_MANAGEMENT, PsychologyDomain.MINDFULNESS],
            "gaming": [PsychologyDomain.GAMING_PSYCHOLOGY, PsychologyDomain.ADDICTION_RECOVERY],
            "addiction": [PsychologyDomain.ADDICTION_RECOVERY, PsychologyDomain.CBT],
            "depression": [PsychologyDomain.CBT, PsychologyDomain.POSITIVE_PSYCHOLOGY],
            "habit": [PsychologyDomain.HABIT_FORMATION, PsychologyDomain.CBT]
        }
        
        # Start with session-based domains
        preferred_domains = session_domain_mapping.get(session_type, [PsychologyDomain.CBT])
        
        # Add issue-specific domains
        user_text = user_message.lower()
        if journal_context:
            user_text += " " + journal_context.lower()
        
        for issue, domains in issue_keywords.items():
            if issue in user_text:
                preferred_domains.extend(domains)
        
        # Remove duplicates while preserving order
        preferred_domains = list(dict.fromkeys(preferred_domains))
        
        # Get psychology knowledge
        psychology_sources = await self.psychology_service.get_knowledge_for_context(
            user_message=user_message,
            journal_context=journal_context,
            preferred_domains=preferred_domains,
            max_sources=3
        )
        
        logger.info(f"Retrieved {len(psychology_sources)} psychology sources for context")
        return psychology_sources
    
    async def _build_enhanced_context(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        psychology_sources: List[Dict[str, Any]],
        journal_context: Optional[str]
    ) -> str:
        """Build comprehensive context including psychology knowledge"""
        
        context_parts = []
        
        # Add psychology knowledge context
        if psychology_sources:
            context_parts.append("=== PROFESSIONAL PSYCHOLOGY KNOWLEDGE ===")
            for i, source in enumerate(psychology_sources, 1):
                context_parts.append(f"\nSource {i}: {source['source']['title']} ({source['source']['year']})")
                context_parts.append(f"Evidence Level: {source['source']['evidence_level']}")
                context_parts.append(f"Domain: {source['domain'].replace('_', ' ').title()}")
                context_parts.append(f"Key Techniques: {', '.join(source['techniques'][:3])}")
                context_parts.append(f"Content: {source['content']}")
                context_parts.append(f"Practical Applications: {', '.join(source['applications'][:2])}")
                context_parts.append("---")
        
        # Add conversation history
        if conversation_history:
            context_parts.append("\n=== CONVERSATION HISTORY ===")
            for msg in conversation_history[-6:]:  # Last 6 messages for context
                role_label = "User" if msg.get('role') == 'user' else "Assistant"
                context_parts.append(f"{role_label}: {msg.get('content', '')}")
        
        # Add journal context
        if journal_context:
            context_parts.append(f"\n=== JOURNAL CONTEXT ===")
            context_parts.append(journal_context)
        
        context_parts.append(f"\n=== CURRENT USER MESSAGE ===")
        context_parts.append(user_message)
        
        return "\n".join(context_parts)
    
    async def _generate_psychology_informed_response(
        self,
        enhanced_context: str,
        session_type: str
    ) -> str:
        """Generate response using psychology-informed prompting"""
        
        # Session-specific personality prompts
        session_prompts = {
            "reflection_buddy": """You are a warm, empathetic reflection buddy with professional psychology training. 
            Use evidence-based insights to guide thoughtful conversations.""",
            
            "inner_voice": """You are the user's wise inner voice, informed by psychological research. 
            Help them access their internal wisdom using proven therapeutic techniques.""",
            
            "growth_challenge": """You are a supportive growth coach with expertise in behavioral psychology. 
            Use research-backed strategies to motivate positive change.""",
            
            "pattern_detective": """You are an insightful pattern analyst with training in cognitive psychology. 
            Help identify behavioral patterns using established psychological frameworks.""",
            
            "crisis": """You are a crisis-informed support companion trained in evidence-based intervention techniques. 
            Prioritize safety and use proven de-escalation and coping strategies."""
        }
        
        base_prompt = session_prompts.get(session_type, session_prompts["reflection_buddy"])
        
        full_prompt = f"""{base_prompt}

IMPORTANT GUIDELINES:
- Integrate psychology knowledge naturally into your response
- Reference specific techniques or insights when relevant
- Maintain a conversational, non-clinical tone
- Cite sources when mentioning specific research or techniques
- Keep responses concise but substantive (2-4 sentences)
- Ask thoughtful follow-up questions
- If psychology sources mention specific techniques, explain them simply

CONTEXT:
{enhanced_context}

RESPONSE INSTRUCTIONS:
Respond as the {session_type.replace('_', ' ')} personality, incorporating relevant psychology insights naturally. 
When referencing psychology knowledge, format citations as: (Source Title, Year)

Your response:"""

        try:
            response = await self._circuit_breaker_generate(
                model=self.model,
                prompt=full_prompt,
                stream=False
            )
            
            return response['response'].strip()
            
        except Exception as e:
            logger.error(f"Error generating psychology-informed response: {e}")
            raise
    
    def _format_source_citations(self, psychology_sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format psychology sources for citation display"""
        citations = []
        
        for source in psychology_sources:
            source_info = source['source']
            citation = {
                "title": source_info['title'],
                "authors": source_info.get('authors', []),
                "year": source_info['year'],
                "type": source_info['type'],
                "evidence_level": source_info['evidence_level'],
                "credibility_score": source_info['credibility_score'],
                "relevance": source['similarity'],
                "domain": source['domain'].replace('_', ' ').title(),
                "key_techniques": source['techniques'][:3],
                "formatted_citation": self.psychology_service.format_citation(source_info)
            }
            
            # Add optional fields
            if source_info.get('doi'):
                citation['doi'] = source_info['doi']
            if source_info.get('journal'):
                citation['journal'] = source_info['journal']
            if source_info.get('url'):
                citation['url'] = source_info['url']
            
            citations.append(citation)
        
        return citations
    
    def _build_basic_prompt(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        session_type: str
    ) -> str:
        """Fallback basic prompt without psychology integration"""
        history_text = ""
        if conversation_history:
            for msg in conversation_history[-4:]:
                role = "You" if msg.get('role') == 'assistant' else "User"
                history_text += f"{role}: {msg.get('content', '')}\n"
        
        return f"""You are a {session_type.replace('_', ' ')} having a supportive conversation.

Conversation history:
{history_text}

User: {user_message}

Respond supportively and ask a thoughtful follow-up question:"""
    
    # Original methods maintained for backwards compatibility
    async def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        """Original response generation method (maintained for compatibility)"""
        try:
            full_prompt = prompt
            if context:
                full_prompt = f"Context:\n{context}\n\nQuestion: {prompt}\n\nAnswer:"
            
            response = await self._circuit_breaker_generate(
                model=self.model,
                prompt=full_prompt,
                stream=False
            )
            
            return response['response']
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return "I'm sorry, I couldn't generate a response at this time."
    
    async def analyze_combined_content(self, combined_content: List[Dict[str, Any]], question: str) -> str:
        """Enhanced analysis with potential psychology knowledge integration"""
        try:
            # Get relevant psychology knowledge for the analysis
            psychology_sources = await self.psychology_service.get_knowledge_for_context(
                user_message=question,
                max_sources=2
            )
            
            # Build context (existing logic)
            context_parts = []
            journal_count = 0
            chat_count = 0
            
            context_parts.append("Here's your personal content from both journal entries and conversations:\n")
            
            for i, content in enumerate(combined_content[:15], 1):
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
            
            # Add psychology context if available
            psychology_context = ""
            if psychology_sources:
                psychology_context = "\n\n=== RELEVANT PSYCHOLOGY RESEARCH ===\n"
                for source in psychology_sources:
                    psychology_context += f"• {source['source']['title']} ({source['source']['year']}): {source['content'][:200]}...\n"
            
            prompt = f"""Based on the personal content above (including {journal_count} journal entries and {chat_count} conversations), please answer this question: {question}

{psychology_context}

Please provide a thoughtful, personalized response using proper markdown formatting that:
1. References specific patterns or themes from BOTH journal entries and conversations
2. Offers insights about growth, changes, or trends across all your reflections
3. Is supportive and constructive
4. Acknowledges the different types of content (written journal vs. conversational)
5. Integrates relevant psychology research when applicable
6. Maintains privacy and confidentiality

FORMAT YOUR RESPONSE IN MARKDOWN:
- Use **bold** for emphasis on key insights
- Use ## headings for major sections (like "Key Patterns", "Growth Insights", "Recommendations")
- Use bullet points with - for lists
- Use numbered lists 1. 2. 3. for sequential points
- Use > blockquotes for important reflections
- Use *italics* for subtle emphasis

INLINE CITATIONS:
When referencing specific content, include inline citations like this:
- For journal entries: "In your journal entry about testing [📔1]..."
- For conversations: "During your conversation about work issues [💬2]..."
- For psychology research: "Research shows [🔬1]..." 

This helps readers jump directly to the source material you're referencing."""
            
            return await self.generate_response(prompt, context)
            
        except Exception as e:
            logger.error(f"Error analyzing combined content: {e}")
            return "I couldn't analyze your content at this time. Please try again later."
    
    async def generate_enhanced_coaching_suggestions(self, combined_content: List[Dict[str, Any]]) -> List[str]:
        """Generate coaching suggestions enhanced with psychology knowledge"""
        try:
            if not combined_content:
                return ["Keep writing in your journal and having conversations to track your progress and get personalized suggestions!"]
            
            # Analyze content to identify potential areas for psychology-informed coaching
            content_themes = self._extract_content_themes(combined_content)
            
            # Get relevant psychology knowledge for coaching
            psychology_sources = await self.psychology_service.get_knowledge_for_context(
                user_message=f"coaching suggestions for {', '.join(content_themes)}",
                max_sources=3
            )
            
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
            
            # Add psychology context
            if psychology_sources:
                context_parts.append("\nRelevant Psychology Research:")
                for source in psychology_sources:
                    context_parts.append(f"• {source['source']['title']}: {source['content'][:100]}...")
            
            context = "\n".join(context_parts)
            
            prompt = f"""Based on this personal content and psychology research, provide 4-5 brief, actionable coaching suggestions that could help with personal growth, wellbeing, or addressing any challenges mentioned.

Consider the different contexts:
- Journal entries show deliberate reflection and writing
- Conversations show interactive exploration and real-time thoughts
- Psychology research provides evidence-based strategies

Format as a simple list of suggestions, each on a new line starting with a dash (-).

Focus on practical, specific recommendations that acknowledge both the reflective and conversational aspects of personal growth, incorporating relevant psychological techniques when appropriate."""
            
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
    
    def _extract_content_themes(self, combined_content: List[Dict[str, Any]]) -> List[str]:
        """Extract main themes from combined content for psychology knowledge matching"""
        themes = []
        
        # Common theme keywords to look for
        theme_keywords = {
            'work': ['work', 'job', 'career', 'workplace', 'professional'],
            'relationships': ['family', 'friend', 'relationship', 'social', 'partner'],
            'stress': ['stress', 'anxiety', 'worried', 'overwhelmed', 'pressure'],
            'growth': ['learn', 'develop', 'improve', 'change', 'goal'],
            'health': ['health', 'exercise', 'sleep', 'energy', 'wellness'],
            'emotions': ['feel', 'emotion', 'sad', 'happy', 'angry', 'frustrated']
        }
        
        # Combine all content text
        all_text = ' '.join([content.get('content', '') for content in combined_content]).lower()
        
        # Find matching themes
        for theme, keywords in theme_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                themes.append(theme)
        
        return themes[:3] if themes else ['general wellbeing']
    
    async def cleanup_resources(self) -> None:
        """Clean up LLM service resources to prevent memory leaks"""
        try:
            logger.debug("🧹 Cleaning up LLM service resources")
            
            # Reset active requests counter
            self._active_requests = 0
            
            # Force garbage collection
            import gc
            gc.collect()
            gc.collect()  # Call twice for better cleanup
            
            logger.debug("✅ LLM service cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during LLM service cleanup: {e}")
    
    def get_resource_stats(self) -> Dict[str, Any]:
        """Get current resource usage statistics"""
        return {
            "active_requests": self._active_requests,
            "max_concurrent_requests": self._max_concurrent_requests,
            "client_connected": hasattr(self, 'client') and self.client is not None,
            "psychology_service_connected": hasattr(self, 'psychology_service') and self.psychology_service is not None
        }
    
    async def generate_automatic_tags(self, content: str, content_type: str = "journal") -> List[str]:
        """Enhanced automatic tagging with psychology knowledge integration"""
        try:
            if not content or len(content.strip()) < 10:
                return []
            
            # Get psychology knowledge that might be relevant for tagging
            psychology_sources = await self.psychology_service.search_knowledge(
                query=content[:200],  # First 200 chars for context
                limit=2,
                min_credibility=0.8
            )
            
            # Build enhanced prompt with psychology context
            content_description = "journal entry" if content_type == "journal" else "conversation"
            
            psychology_context = ""
            if psychology_sources:
                domains = [source['domain'].replace('_', ' ') for source in psychology_sources]
                techniques = []
                for source in psychology_sources:
                    techniques.extend(source['techniques'][:2])
                
                psychology_context = f"\n\nPsychology context detected: {', '.join(domains)}\nRelevant techniques: {', '.join(techniques[:4])}"
            
            prompt = f"""Analyze this {content_description} and generate 3-5 relevant tags that capture the main themes, emotions, topics, or categories.

Rules for tags:
- Use single words or short phrases (1-3 words max)
- Focus on themes, emotions, activities, relationships, goals, challenges, psychological concepts
- Be specific but not too niche
- Use lowercase
- Include psychology-related tags when relevant (e.g., 'cbt techniques', 'mindfulness', 'stress management')
- Separate tags with commas
- Examples: work, relationships, anxiety, gratitude, travel, health, goals, family, stress, creativity, learning, mindfulness, coping strategies

{content_description.title()}:
{content[:500]}...{psychology_context}

Generate only the tags as a comma-separated list, nothing else:"""
            
            response = await self.generate_response(prompt)
            
            # Parse the response to extract tags
            tags = []
            for line in response.split('\n'):
                line = line.strip()
                if line and not line.startswith('Tags:') and not line.startswith('Here are'):
                    # Split by comma and clean up
                    potential_tags = [tag.strip().lower() for tag in line.split(',')]
                    for tag in potential_tags:
                        # Clean tag: remove special characters, limit length
                        clean_tag = ''.join(c for c in tag if c.isalnum() or c in [' ', '-', '_']).strip()
                        if clean_tag and len(clean_tag) <= 25 and clean_tag not in tags:
                            tags.append(clean_tag)
                    break  # Only process the first valid line
            
            # Limit to 5 tags and ensure they're reasonable
            final_tags = []
            for tag in tags[:5]:
                if len(tag) >= 2 and len(tag.split()) <= 3:  # 2+ chars, max 3 words
                    final_tags.append(tag)
            
            return final_tags[:5] if final_tags else []
        
        except Exception as e:
            logger.error(f"Error generating automatic tags: {e}")
            return []
    
    async def extract_topics(self, text: str, max_topics: int = 5) -> List[str]:
        """Extract main topics from text using LLM"""
        try:
            prompt = f"""Extract the main topics from this text. Return only a simple list of topics, one per line, maximum {max_topics} topics.

Text: {text[:500]}...

Topics:"""

            response = await self._circuit_breaker_generate(
                model=self.model,
                prompt=prompt,
                stream=False
            )
            
            # Parse topics from response
            topics = []
            for line in response['response'].strip().split('\n'):
                topic = line.strip('- ').strip()
                if topic and len(topic) > 2:
                    topics.append(topic)
                    
            return topics[:max_topics]
            
        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
            return []
    
    async def answer_insights_question(self, context: Dict[str, Any]) -> str:
        """Answer insights questions using cached analytics and specific search results"""
        try:
            question = context['question']
            cached_analytics = context.get('cached_analytics', {})
            relevant_entries = context.get('relevant_entries', [])
            
            # Build context from cached analytics
            analytics_summary = ""
            if cached_analytics:
                mood_data = cached_analytics.get('mood_trends', {})
                entry_stats = cached_analytics.get('entry_stats', {})
                
                analytics_summary = f"""
Based on your recent data:
- Total entries: {entry_stats.get('total_entries', 0)}
- Average mood: {mood_data.get('average_mood', 'neutral')}
- Most common mood: {max(mood_data.get('mood_distribution', {}), key=mood_data.get('mood_distribution', {}).get, default='neutral')}
"""
            
            # Build context from relevant entries
            entries_context = ""
            if relevant_entries:
                entries_context = "\n".join([
                    f"Entry: {entry.get('content', '')[:200]}..."
                    for entry in relevant_entries[:3]
                ])
            
            prompt = f"""You are helping someone understand insights about their journaling patterns. Answer their question using the provided data and context.

Question: {question}

{analytics_summary}

Recent relevant entries:
{entries_context}

Provide a helpful, insightful answer that connects their question to their actual journaling data. Be specific and reference the data when possible."""

            response = await self._circuit_breaker_generate(
                model=self.model,
                prompt=prompt,
                stream=False
            )
            
            return response['response'].strip()
            
        except Exception as e:
            logger.error(f"Error answering insights question: {e}")
            return "I'm having trouble analyzing your data right now. Please try again later."


# Global instance - replace the existing llm_service
llm_service = EnhancedLLMService()