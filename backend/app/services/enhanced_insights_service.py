# backend/app/services/enhanced_insights_service.py

import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from app.services.unified_database_service import unified_db_service
from app.services.session_service import session_service
from app.services.vector_service import vector_service
from app.services.sentiment_service import sentiment_service
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

class EnhancedInsightsService:
    """Enhanced insights service that includes both journal entries and chat conversations"""
    
    async def analyze_all_content(self, question: str, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Analyze both journal entries and chat conversations to answer a question"""
        try:
            # Get journal entries
            journal_entries = await self.get_journal_entries(user_id, days)
            
            # Get chat conversations
            chat_conversations = await self.get_chat_conversations(user_id, days)
            
            # Search for relevant content using vector search
            relevant_journal = await vector_service.search_entries(question, limit=10)
            relevant_chat = await self.search_chat_content(question, user_id, limit=10)
            
            # Combine and analyze all content
            all_content = self.combine_content(
                journal_entries, 
                chat_conversations, 
                relevant_journal, 
                relevant_chat
            )
            
            # Generate comprehensive insights
            answer = await llm_service.analyze_combined_content(all_content, question)
            
            return {
                'question': question,
                'answer': answer,
                'sources': {
                    'journal_entries': len(relevant_journal),
                    'chat_messages': len(relevant_chat),
                    'total_sources': len(relevant_journal) + len(relevant_chat)
                },
                'time_period': f"Last {days} days",
                'content_breakdown': {
                    'journal_entries': len(journal_entries),
                    'chat_conversations': len(chat_conversations),
                    'total_analyzed': len(all_content)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced insights analysis: {e}")
            raise
    
    async def get_comprehensive_mood_analysis(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get mood analysis from both journal entries and chat conversations"""
        try:
            # Analyze journal entry moods (existing functionality)
            journal_mood_stats = await unified_db_service.get_mood_statistics(user_id, days)
            
            # Analyze chat conversation sentiments
            chat_sentiments = await self.analyze_chat_sentiments(user_id, days)
            
            # Combine both analyses
            combined_analysis = await self.combine_mood_analyses(
                journal_mood_stats, 
                chat_sentiments
            )
            
            return combined_analysis
            
        except Exception as e:
            logger.error(f"Error in comprehensive mood analysis: {e}")
            raise
    
    async def generate_enhanced_coaching_suggestions(self, user_id: str, days: int = 7) -> List[str]:
        """Generate coaching suggestions based on both journal entries and chat conversations"""
        try:
            # Get recent journal entries
            journal_entries = await self.get_journal_entries(user_id, days)
            
            # Get recent chat conversations
            chat_conversations = await self.get_chat_conversations(user_id, days)
            
            # Convert to analysis format
            combined_content = []
            
            # Add journal entries
            for entry in journal_entries:
                combined_content.append({
                    'type': 'journal',
                    'content': entry.content,
                    'metadata': {
                        'created_at': entry.created_at.isoformat(),
                        'mood': entry.mood.value if entry.mood else 'Unknown',
                        'title': entry.title,
                        'sentiment_score': entry.sentiment_score
                    }
                })
            
            # Add chat conversations
            for conversation in chat_conversations:
                # Extract user messages for analysis (skip AI responses)
                user_messages = [msg for msg in conversation['messages'] if msg['role'] == 'user']
                if user_messages:
                    conversation_text = ' '.join([msg['content'] for msg in user_messages])
                    
                    # Analyze sentiment of the conversation
                    mood, sentiment_score = sentiment_service.analyze_sentiment(conversation_text)
                    
                    combined_content.append({
                        'type': 'chat',
                        'content': conversation_text,
                        'metadata': {
                            'created_at': conversation['created_at'],
                            'session_type': conversation['session_type'],
                            'message_count': len(user_messages),
                            'mood': mood.value,
                            'sentiment_score': sentiment_score
                        }
                    })
            
            # Generate enhanced suggestions
            suggestions = await llm_service.generate_enhanced_coaching_suggestions(combined_content)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating enhanced coaching suggestions: {e}")
            return ["Continue reflecting through both journaling and conversations to gain deeper insights."]
    
    async def analyze_conversation_patterns(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Analyze patterns in chat conversations"""
        try:
            conversations = await self.get_chat_conversations(user_id, days)
            
            if not conversations:
                return {
                    'message': 'No conversations found for analysis',
                    'patterns': {}
                }
            
            patterns = {
                'session_types': {},
                'conversation_length': [],
                'time_patterns': {},
                'engagement_trends': [],
                'common_themes': []
            }
            
            for conv in conversations:
                # Session type distribution
                session_type = conv['session_type']
                patterns['session_types'][session_type] = patterns['session_types'].get(session_type, 0) + 1
                
                # Conversation length
                user_message_count = len([m for m in conv['messages'] if m['role'] == 'user'])
                patterns['conversation_length'].append(user_message_count)
                
                # Time patterns (hour of day)
                created_time = datetime.fromisoformat(conv['created_at'].replace('Z', '+00:00'))
                hour = created_time.hour
                patterns['time_patterns'][hour] = patterns['time_patterns'].get(hour, 0) + 1
            
            # Calculate insights
            avg_length = sum(patterns['conversation_length']) / len(patterns['conversation_length'])
            most_used_type = max(patterns['session_types'].items(), key=lambda x: x[1])[0] if patterns['session_types'] else None
            peak_hour = max(patterns['time_patterns'].items(), key=lambda x: x[1])[0] if patterns['time_patterns'] else None
            
            return {
                'total_conversations': len(conversations),
                'average_length': round(avg_length, 1),
                'most_used_session_type': most_used_type,
                'peak_conversation_hour': peak_hour,
                'patterns': patterns,
                'insights': [
                    f"You've had {len(conversations)} conversations in the last {days} days",
                    f"Your favorite conversation type is {most_used_type.replace('_', ' ')}" if most_used_type else "No clear preference in conversation types yet",
                    f"You typically have conversations around {peak_hour}:00" if peak_hour else "No clear time pattern yet",
                    f"Your conversations average {avg_length:.1f} messages"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing conversation patterns: {e}")
            return {'error': 'Failed to analyze conversation patterns'}
    
    # Helper methods
    
    async def get_journal_entries(self, user_id: str, days: int) -> List:
        """Get journal entries from the last N days for a specific user"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return await unified_db_service.get_entries(user_id=user_id, date_from=start_date, date_to=end_date, limit=100)
    
    async def get_chat_conversations(self, user_id: str, days: int) -> List[Dict]:
        """Get chat conversations from the last N days"""
        try:
            # Get sessions from the last N days for this user
            sessions = await session_service.get_user_sessions(user_id=user_id, limit=50)
            
            conversations = []
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            for session in sessions:
                # Filter by date
                session_date = session.created_at
                if session_date >= start_date:
                    # Get messages for this session
                    messages = await session_service.get_session_messages(session.id)
                    
                    conversations.append({
                        'session_id': session.id,
                        'session_type': session.session_type,
                        'created_at': session.created_at.isoformat(),
                        'title': session.title,
                        'status': session.status,
                        'messages': [
                            {
                                'role': msg.role,
                                'content': msg.content,
                                'timestamp': msg.timestamp.isoformat()
                            }
                            for msg in messages
                        ]
                    })
            
            return conversations
            
        except Exception as e:
            logger.error(f"Error getting chat conversations: {e}")
            return []
    
    async def search_chat_content(self, query: str, user_id: str, limit: int = 10) -> List[Dict]:
        """Search through chat conversations for relevant content"""
        try:
            conversations = await self.get_chat_conversations(user_id, 30)  # Last 30 days
            relevant_chats = []
            
            for conv in conversations:
                # Combine user messages for this conversation
                user_messages = [msg for msg in conv['messages'] if msg['role'] == 'user']
                if user_messages:
                    combined_text = ' '.join([msg['content'] for msg in user_messages])
                    
                    # Simple relevance check (could be enhanced with vector search)
                    query_words = query.lower().split()
                    content_words = combined_text.lower().split()
                    
                    # Calculate simple relevance score
                    relevance = sum(1 for word in query_words if word in content_words) / len(query_words)
                    
                    if relevance > 0.1:  # Threshold for relevance
                        relevant_chats.append({
                            'type': 'chat',
                            'session_id': conv['session_id'],
                            'session_type': conv['session_type'],
                            'content': combined_text[:300] + '...' if len(combined_text) > 300 else combined_text,
                            'created_at': conv['created_at'],
                            'relevance_score': relevance,
                            'message_count': len(user_messages)
                        })
            
            # Sort by relevance and return top results
            relevant_chats.sort(key=lambda x: x['relevance_score'], reverse=True)
            return relevant_chats[:limit]
            
        except Exception as e:
            logger.error(f"Error searching chat content: {e}")
            return []
    
    async def analyze_chat_sentiments(self, user_id: str, days: int) -> Dict[str, Any]:
        """Analyze sentiments from chat conversations"""
        try:
            conversations = await self.get_chat_conversations(user_id, days)
            
            sentiment_data = {
                'mood_distribution': {},
                'daily_sentiments': {},
                'session_type_sentiments': {},
                'total_conversations': len(conversations)
            }
            
            for conv in conversations:
                # Get user messages only
                user_messages = [msg for msg in conv['messages'] if msg['role'] == 'user']
                
                if user_messages:
                    # Combine user messages for sentiment analysis
                    combined_text = ' '.join([msg['content'] for msg in user_messages])
                    
                    # Analyze sentiment
                    mood, sentiment_score = sentiment_service.analyze_sentiment(combined_text)
                    
                    # Update mood distribution
                    mood_str = mood.value
                    sentiment_data['mood_distribution'][mood_str] = sentiment_data['mood_distribution'].get(mood_str, 0) + 1
                    
                    # Update session type sentiments
                    session_type = conv['session_type']
                    if session_type not in sentiment_data['session_type_sentiments']:
                        sentiment_data['session_type_sentiments'][session_type] = []
                    sentiment_data['session_type_sentiments'][session_type].append(sentiment_score)
                    
                    # Update daily sentiments
                    date_str = conv['created_at'][:10]  # Get just the date part
                    if date_str not in sentiment_data['daily_sentiments']:
                        sentiment_data['daily_sentiments'][date_str] = []
                    sentiment_data['daily_sentiments'][date_str].append(sentiment_score)
            
            return sentiment_data
            
        except Exception as e:
            logger.error(f"Error analyzing chat sentiments: {e}")
            return {'error': 'Failed to analyze chat sentiments'}
    
    async def combine_mood_analyses(self, journal_moods: Dict, chat_sentiments: Dict) -> Dict[str, Any]:
        """Combine mood analysis from journal entries and chat conversations"""
        try:
            combined = {
                'sources': {
                    'journal_entries': journal_moods.get('total_entries', 0),
                    'chat_conversations': chat_sentiments.get('total_conversations', 0)
                },
                'combined_mood_distribution': {},
                'insights': [],
                'recommendations': []
            }
            
            # Combine mood distributions
            journal_dist = journal_moods.get('mood_distribution', {})
            chat_dist = chat_sentiments.get('mood_distribution', {})
            
            all_moods = set(list(journal_dist.keys()) + list(chat_dist.keys()))
            
            for mood in all_moods:
                journal_count = journal_dist.get(mood, 0)
                chat_count = chat_dist.get(mood, 0)
                combined['combined_mood_distribution'][mood] = {
                    'journal': journal_count,
                    'chat': chat_count,
                    'total': journal_count + chat_count
                }
            
            # Generate insights
            total_entries = combined['sources']['journal_entries'] + combined['sources']['chat_conversations']
            
            if total_entries > 0:
                combined['insights'].append(f"Analyzed {total_entries} total interactions ({combined['sources']['journal_entries']} journal entries, {combined['sources']['chat_conversations']} conversations)")
                
                # Find dominant mood across both sources
                total_mood_counts = {mood: data['total'] for mood, data in combined['combined_mood_distribution'].items()}
                if total_mood_counts:
                    dominant_mood = max(total_mood_counts.items(), key=lambda x: x[1])[0]
                    combined['insights'].append(f"Your dominant mood across all interactions is {dominant_mood.replace('_', ' ')}")
            
            return combined
            
        except Exception as e:
            logger.error(f"Error combining mood analyses: {e}")
            return {'error': 'Failed to combine mood analyses'}
    
    def combine_content(self, journal_entries, chat_conversations, relevant_journal, relevant_chat) -> List[Dict]:
        """Combine all content sources for analysis"""
        combined = []
        
        # Add relevant journal entries
        for entry in relevant_journal:
            combined.append({
                'type': 'journal',
                'content': entry['content'],
                'metadata': entry.get('metadata', {}),
                'relevance': 1 - entry.get('distance', 0)
            })
        
        # Add relevant chat content
        for chat in relevant_chat:
            combined.append({
                'type': 'chat',
                'content': chat['content'],
                'metadata': {
                    'session_type': chat['session_type'],
                    'created_at': chat['created_at'],
                    'message_count': chat['message_count']
                },
                'relevance': chat['relevance_score']
            })
        
        # Sort by relevance
        combined.sort(key=lambda x: x['relevance'], reverse=True)
        
        return combined

    async def get_detailed_sources(self, question: str, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get detailed source information for the insights response"""
        try:
            # Get relevant content
            relevant_journal = await vector_service.search_entries(question, limit=10)
            relevant_chat = await self.search_chat_content(question, user_id, limit=10)
            
            detailed_sources = {
                'journal_entries': [],
                'conversations': []
            }
            
            # Process journal entries
            for entry in relevant_journal:
                metadata = entry.get('metadata', {})
                detailed_sources['journal_entries'].append({
                    'id': entry['id'],
                    'date': metadata.get('created_at', 'Unknown'),
                    'title': metadata.get('title', 'Untitled'),
                    'snippet': entry['content'][:150] + '...' if len(entry['content']) > 150 else entry['content'],
                    'similarity': round((1 - entry.get('distance', 0)) * 100),
                    'type': 'journal'
                })
            
            # Process chat conversations
            for chat in relevant_chat:
                detailed_sources['conversations'].append({
                    'id': chat['session_id'],
                    'date': chat['created_at'],
                    'session_type': chat['session_type'].replace('_', ' ').title(),
                    'snippet': chat['content'],
                    'similarity': round(chat['relevance_score'] * 100),
                    'message_count': chat['message_count'],
                    'type': 'conversation'
                })
            
            return {
                'total_sources': len(detailed_sources['journal_entries']) + len(detailed_sources['conversations']),
                'detailed_sources': detailed_sources
            }
            
        except Exception as e:
            logger.error(f"Error getting detailed sources: {e}")
            return {
                'total_sources': 0,
                'detailed_sources': {'journal_entries': [], 'conversations': []}
            }

# Global instance
enhanced_insights_service = EnhancedInsightsService()