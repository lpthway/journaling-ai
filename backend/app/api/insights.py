# backend/app/api/insights.py - Enhanced with Chat Integration

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from app.services.vector_service import vector_service
from app.services.llm_service import llm_service
from app.services.database_service import db_service
from app.services.session_service import session_service
from app.services.sentiment_service import sentiment_service
import logging
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/ask")
async def ask_question(question: str):
    """Ask a question about your journal entries AND chat conversations"""
    try:
        if not question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        logger.info(f"Enhanced insights request: {question}")
        
        # Search journal entries
        relevant_journal = await vector_service.search_entries(question, limit=10)
        
        # Search chat conversations
        relevant_chat = await search_chat_content(question, limit=10)
        
        # Combine and analyze
        all_content = combine_content_sources(relevant_journal, relevant_chat)
        
        # Generate comprehensive answer
        answer = await llm_service.analyze_combined_content(all_content, question)
        
        # Prepare detailed sources
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
        
        total_sources = len(detailed_sources['journal_entries']) + len(detailed_sources['conversations'])
        
        return {
            'question': question,
            'answer': answer,
            'sources': {
                'journal_entries': len(relevant_journal),
                'chat_messages': len(relevant_chat),
                'total_sources': total_sources
            },
            'content_breakdown': {
                'journal_entries': len(relevant_journal),
                'chat_conversations': len(relevant_chat),
                'total_analyzed': len(all_content)
            },
            'time_period': 'Last 30 days',
            'sources_used': total_sources,
            'detailed_sources': detailed_sources
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail="Failed to process your question")

@router.get("/chat-insights")
async def get_chat_insights(days: int = Query(30, ge=7, le=365)):
    """Get insights specifically from chat conversations"""
    try:
        conversations = await get_chat_conversations(days)
        
        if not conversations:
            return {
                'message': 'No conversations found for analysis',
                'total_conversations': 0,
                'patterns': {}
            }
        
        # Analyze conversation patterns
        patterns = {
            'session_types': {},
            'conversation_length': [],
            'time_patterns': {},
            'daily_activity': {}
        }
        
        total_messages = 0
        for conv in conversations:
            # Session type distribution
            session_type = conv['session_type']
            patterns['session_types'][session_type] = patterns['session_types'].get(session_type, 0) + 1
            
            # Conversation length
            user_message_count = len([m for m in conv['messages'] if m['role'] == 'user'])
            patterns['conversation_length'].append(user_message_count)
            total_messages += user_message_count
            
            # Time patterns (hour of day)
            try:
                created_time = datetime.fromisoformat(conv['created_at'].replace('Z', '+00:00'))
                hour = created_time.hour
                patterns['time_patterns'][hour] = patterns['time_patterns'].get(hour, 0) + 1
                
                # Daily activity
                date_str = created_time.strftime('%Y-%m-%d')
                patterns['daily_activity'][date_str] = patterns['daily_activity'].get(date_str, 0) + 1
            except:
                pass
        
        # Calculate insights
        avg_length = sum(patterns['conversation_length']) / len(patterns['conversation_length']) if patterns['conversation_length'] else 0
        most_used_type = max(patterns['session_types'].items(), key=lambda x: x[1])[0] if patterns['session_types'] else None
        peak_hour = max(patterns['time_patterns'].items(), key=lambda x: x[1])[0] if patterns['time_patterns'] else None
        
        return {
            'total_conversations': len(conversations),
            'average_length': round(avg_length, 1),
            'total_messages': total_messages,
            'most_used_session_type': most_used_type,
            'peak_conversation_hour': peak_hour,
            'patterns': patterns,
            'insights': [
                f"You've had {len(conversations)} conversations in the last {days} days",
                f"Your favorite conversation type is {most_used_type.replace('_', ' ')}" if most_used_type else "No clear preference in conversation types yet",
                f"You typically have conversations around {peak_hour}:00" if peak_hour else "No clear time pattern yet",
                f"Your conversations average {avg_length:.1f} messages each"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting chat insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze chat insights")

@router.get("/mood-analysis-comprehensive")
async def get_comprehensive_mood_analysis(days: int = Query(30, ge=7, le=365)):
    """Get comprehensive mood analysis from all sources"""
    try:
        # Get journal mood statistics
        journal_mood_stats = await db_service.get_mood_statistics(days)
        
        # Get chat sentiment analysis
        chat_sentiments = await analyze_chat_sentiments(days)
        
        # Combine both analyses
        combined_analysis = {
            'sources': {
                'journal_entries': journal_mood_stats.get('total_entries', 0),
                'chat_conversations': chat_sentiments.get('total_conversations', 0)
            },
            'combined_mood_distribution': {},
            'insights': [],
            'recommendations': []
        }
        
        # Combine mood distributions
        journal_dist = journal_mood_stats.get('mood_distribution', {})
        chat_dist = chat_sentiments.get('mood_distribution', {})
        
        all_moods = set(list(journal_dist.keys()) + list(chat_dist.keys()))
        
        for mood in all_moods:
            journal_count = journal_dist.get(mood, 0)
            chat_count = chat_dist.get(mood, 0)
            combined_analysis['combined_mood_distribution'][mood] = {
                'journal': journal_count,
                'chat': chat_count,
                'total': journal_count + chat_count
            }
        
        # Generate insights
        total_entries = combined_analysis['sources']['journal_entries'] + combined_analysis['sources']['chat_conversations']
        
        if total_entries > 0:
            combined_analysis['insights'].append(
                f"Analyzed {total_entries} total interactions ({combined_analysis['sources']['journal_entries']} journal entries, {combined_analysis['sources']['chat_conversations']} conversations)"
            )
            
            # Find dominant mood across both sources
            total_mood_counts = {mood: data['total'] for mood, data in combined_analysis['combined_mood_distribution'].items()}
            if total_mood_counts:
                dominant_mood = max(total_mood_counts.items(), key=lambda x: x[1])[0]
                combined_analysis['insights'].append(
                    f"Your dominant mood across all interactions is {dominant_mood.replace('_', ' ')}"
                )
        
        return combined_analysis
        
    except Exception as e:
        logger.error(f"Error getting comprehensive mood analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform comprehensive mood analysis")

@router.get("/coaching")
async def get_coaching_suggestions():
    """Get personalized coaching suggestions based on recent entries AND conversations"""
    try:
        # Get recent journal entries
        recent_date = datetime.now() - timedelta(days=7)
        recent_entries_db = await db_service.get_entries(limit=10, date_from=recent_date)
        
        # Get recent chat conversations
        recent_conversations = await get_chat_conversations(7)
        
        # Combine content for analysis
        combined_content = []
        
        # Add journal entries
        for entry in recent_entries_db:
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
        for conversation in recent_conversations:
            # Extract user messages for analysis
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
        
        if not combined_content:
            return {
                'suggestions': ["Start by writing journal entries and having conversations to get personalized coaching suggestions!"],
                'source': 'enhanced',
                'period': 'Last 7 days'
            }
        
        # Generate enhanced suggestions
        suggestions = await llm_service.generate_enhanced_coaching_suggestions(combined_content)
        
        return {
            'suggestions': suggestions,
            'source': 'journal_and_chat',
            'period': 'Last 7 days',
            'note': 'Based on both your journal entries and chat conversations',
            'content_breakdown': {
                'journal_entries': len([c for c in combined_content if c['type'] == 'journal']),
                'conversations': len([c for c in combined_content if c['type'] == 'chat'])
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating coaching suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate coaching suggestions")

# Original endpoints for backward compatibility
@router.post("/ask-journal-only")
async def ask_question_journal_only(question: str):
    """Ask a question about your journal entries only (original functionality)"""
    try:
        if not question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Search for relevant entries
        relevant_entries = await vector_service.search_entries(question, limit=15)
        
        if not relevant_entries:
            return {
                'question': question,
                'answer': "I couldn't find any relevant journal entries to answer your question. Try writing more journal entries first!",
                'sources_used': 0
            }
        
        # Generate insight using LLM
        answer = await llm_service.analyze_entries_for_insights(relevant_entries, question)
        
        return {
            'question': question,
            'answer': answer,
            'sources_used': len(relevant_entries),
            'relevant_entries': [
                {
                    'id': entry['id'],
                    'snippet': entry['content'][:150] + '...' if len(entry['content']) > 150 else entry['content'],
                    'date': entry['metadata'].get('created_at', 'Unknown'),
                    'similarity': 1 - entry['distance']
                }
                for entry in relevant_entries[:5]  # Show top 5 sources
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing journal question: {e}")
        raise HTTPException(status_code=500, detail="Failed to process your question")

@router.get("/patterns")
async def analyze_patterns():
    """Analyze patterns in journal entries (original functionality)"""
    try:
        # Get mood statistics
        mood_stats = await db_service.get_mood_statistics(30)
        
        # Get recent entries for trend analysis
        recent_entries = await db_service.get_entries(limit=50)
        
        if not recent_entries:
            return {
                'message': "Not enough data for pattern analysis. Keep journaling!",
                'patterns': {}
            }
        
        # Analyze writing frequency
        daily_counts = defaultdict(int)
        word_counts = []
        topic_usage = defaultdict(int)
        
        for entry in recent_entries:
            date_str = entry.created_at.strftime('%Y-%m-%d')
            daily_counts[date_str] += 1
            word_counts.append(entry.word_count)
            
            if entry.topic_id:
                topic_usage[entry.topic_id] += 1
        
        # Calculate averages and trends
        avg_word_count = sum(word_counts) / len(word_counts) if word_counts else 0
        writing_frequency = len(daily_counts) / 30  # entries per day over last 30 days
        
        patterns = {
            'mood_distribution': mood_stats['mood_distribution'],
            'writing_frequency': {
                'entries_per_day': round(writing_frequency, 2),
                'total_entries': len(recent_entries),
                'avg_word_count': round(avg_word_count, 1)
            },
            'topic_usage': dict(topic_usage),
            'recent_trend': 'improving' if len(recent_entries[:10]) > len(recent_entries[10:20]) else 'stable'
        }
        
        return {
            'analysis_period': '30 days',
            'total_entries_analyzed': len(recent_entries),
            'patterns': patterns,
            'source': 'journal_only'
        }
        
    except Exception as e:
        logger.error(f"Error analyzing patterns: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze patterns")

@router.get("/trends/mood")
async def get_mood_trends(days: int = Query(30, ge=7, le=365)):
    """Get detailed mood trends over time from journal entries only"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        entries = await db_service.get_entries(
            limit=1000,
            date_from=start_date,
            date_to=end_date
        )
        
        if not entries:
            return {
                'message': "No entries found for the specified period",
                'trends': {}
            }
        
        # Group by day and calculate daily mood averages
        daily_moods = defaultdict(list)
        mood_values = {
            'very_negative': -2,
            'negative': -1,
            'neutral': 0,
            'positive': 1,
            'very_positive': 2
        }
        
        for entry in entries:
            if entry.mood:
                date_str = entry.created_at.strftime('%Y-%m-%d')
                daily_moods[date_str].append(mood_values[entry.mood.value])
        
        # Calculate daily averages
        daily_averages = {}
        for date_str, moods in daily_moods.items():
            daily_averages[date_str] = sum(moods) / len(moods)
        
        # Sort by date
        sorted_dates = sorted(daily_averages.keys())
        trend_data = [
            {
                'date': date_str,
                'mood_score': round(daily_averages[date_str], 2),
                'entry_count': len(daily_moods[date_str])
            }
            for date_str in sorted_dates
        ]
        
        # Calculate overall trend
        if len(trend_data) >= 2:
            recent_avg = sum(d['mood_score'] for d in trend_data[-7:]) / min(7, len(trend_data))
            earlier_avg = sum(d['mood_score'] for d in trend_data[:7]) / min(7, len(trend_data))
            trend_direction = 'improving' if recent_avg > earlier_avg else 'declining' if recent_avg < earlier_avg else 'stable'
        else:
            trend_direction = 'insufficient_data'
        
        return {
            'period_days': days,
            'total_entries': len(entries),
            'trend_direction': trend_direction,
            'daily_data': trend_data,
            'source': 'journal_only'
        }
        
    except Exception as e:
        logger.error(f"Error getting mood trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze mood trends")

# Helper functions
async def get_chat_conversations(days: int) -> List[Dict]:
    """Get chat conversations from the last N days"""
    try:
        # Get sessions from the last N days
        sessions = await session_service.get_sessions(limit=50)
        
        conversations = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        for session in sessions:
            # Filter by date
            if session.created_at >= start_date:
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

async def search_chat_content(query: str, limit: int = 10) -> List[Dict]:
    """Search through chat conversations for relevant content"""
    try:
        conversations = await get_chat_conversations(30)  # Last 30 days
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

async def analyze_chat_sentiments(days: int) -> Dict[str, Any]:
    """Analyze sentiments from chat conversations"""
    try:
        conversations = await get_chat_conversations(days)
        
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
        return {'total_conversations': 0, 'mood_distribution': {}}

def combine_content_sources(journal_entries, chat_entries):
    """Combine journal entries and chat content for analysis"""
    combined = []
    
    # Add journal entries
    for entry in journal_entries:
        combined.append({
            'type': 'journal',
            'content': entry['content'],
            'metadata': entry.get('metadata', {}),
            'relevance': 1 - entry.get('distance', 0)
        })
    
    # Add chat entries
    for chat in chat_entries:
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