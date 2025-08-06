# backend/app/api/insights.py - Enhanced with Chat Integration

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from app.services.vector_service import vector_service
from app.services.llm_service import llm_service
from app.services.unified_database_service import unified_db_service
from app.services.ai_emotion_service import ai_emotion_service
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
        journal_mood_stats = await unified_db_service.get_mood_statistics(days)
        
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
        recent_entries_db = await unified_db_service.get_entries(limit=10, date_from=recent_date)
        
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
                
                # Analyze emotions using modern AI emotion service
                try:
                    emotion_analysis = await ai_emotion_service.analyze_emotions(conversation_text)
                    mood = emotion_analysis.primary_emotion.emotion.value
                    sentiment_score = emotion_analysis.primary_emotion.confidence
                except Exception as e:
                    logger.warning(f"AI emotion analysis failed: {e}")
                    mood = "neutral"
                    sentiment_score = 0.5
                
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

@router.get("/trends/comprehensive")
async def get_comprehensive_trends(days: int = Query(30, ge=7, le=365)):
    """Get comprehensive mood trends including journal entries AND chat conversations with all days filled"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get journal entries
        journal_entries = await unified_db_service.get_entries(
            limit=1000,
            date_from=start_date,
            date_to=end_date
        )
        
        # Get chat conversations
        chat_conversations = await get_chat_conversations(days)
        
        # Create a complete date range
        all_dates = []
        current_date = start_date
        while current_date <= end_date:
            all_dates.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        
        # Initialize daily data structure
        daily_data = {}
        for date_str in all_dates:
            daily_data[date_str] = {
                'date': date_str,
                'journal_entries': [],
                'chat_conversations': [],
                'journal_mood_scores': [],
                'chat_mood_scores': [],
                'combined_mood_scores': []
            }
        
        # Process journal entries
        mood_values = {
            'very_negative': -2,
            'negative': -1,
            'neutral': 0,
            'positive': 1,
            'very_positive': 2
        }
        
        total_journal_entries = 0
        for entry in journal_entries:
            date_str = entry.created_at.strftime('%Y-%m-%d')
            if date_str in daily_data and entry.mood:
                mood_score = mood_values[entry.mood.value]
                daily_data[date_str]['journal_entries'].append({
                    'id': entry.id,
                    'title': entry.title,
                    'mood': entry.mood.value,
                    'mood_score': mood_score
                })
                daily_data[date_str]['journal_mood_scores'].append(mood_score)
                daily_data[date_str]['combined_mood_scores'].append(mood_score)
                total_journal_entries += 1
        
        # Process chat conversations
        total_chat_conversations = 0
        for conv in chat_conversations:
            try:
                conv_date = datetime.fromisoformat(conv['created_at'].replace('Z', '+00:00'))
                date_str = conv_date.strftime('%Y-%m-%d')
                
                if date_str in daily_data:
                    # Get user messages for emotion analysis
                    user_messages = [msg for msg in conv['messages'] if msg['role'] == 'user']
                    if user_messages:
                        combined_text = ' '.join([msg['content'] for msg in user_messages])
                        try:
                            emotion_analysis = await ai_emotion_service.analyze_emotions(combined_text)
                            mood = emotion_analysis.primary_emotion.emotion
                            sentiment_score = emotion_analysis.primary_emotion.confidence
                        except Exception as e:
                            logger.warning(f"AI emotion analysis failed: {e}")
                            from app.models.entry import MoodType
                            mood = MoodType.NEUTRAL
                            sentiment_score = 0.5
                        mood_score = mood_values.get(mood.value, 0)
                        
                        daily_data[date_str]['chat_conversations'].append({
                            'id': conv['session_id'],
                            'session_type': conv['session_type'],
                            'message_count': len(user_messages),
                            'mood': mood.value,
                            'mood_score': mood_score
                        })
                        daily_data[date_str]['chat_mood_scores'].append(mood_score)
                        daily_data[date_str]['combined_mood_scores'].append(mood_score)
                        total_chat_conversations += 1
            except Exception as e:
                logger.warning(f"Error processing conversation date: {e}")
                continue
        
        # Calculate daily averages and create trend data
        trend_data = []
        for date_str in sorted(all_dates):
            day_data = daily_data[date_str]
            
            # Calculate averages
            journal_avg = sum(day_data['journal_mood_scores']) / len(day_data['journal_mood_scores']) if day_data['journal_mood_scores'] else None
            chat_avg = sum(day_data['chat_mood_scores']) / len(day_data['chat_mood_scores']) if day_data['chat_mood_scores'] else None
            combined_avg = sum(day_data['combined_mood_scores']) / len(day_data['combined_mood_scores']) if day_data['combined_mood_scores'] else None
            
            trend_data.append({
                'date': date_str,
                'journal_mood_score': round(journal_avg, 2) if journal_avg is not None else None,
                'chat_mood_score': round(chat_avg, 2) if chat_avg is not None else None,
                'combined_mood_score': round(combined_avg, 2) if combined_avg is not None else None,
                'journal_entry_count': len(day_data['journal_entries']),
                'chat_conversation_count': len(day_data['chat_conversations']),
                'total_activity_count': len(day_data['journal_entries']) + len(day_data['chat_conversations']),
                'has_data': len(day_data['combined_mood_scores']) > 0
            })
        
        # Calculate overall trends
        def calculate_trend(scores):
            valid_scores = [s for s in scores if s is not None]
            if len(valid_scores) >= 2:
                recent_scores = valid_scores[-7:] if len(valid_scores) >= 7 else valid_scores[len(valid_scores)//2:]
                earlier_scores = valid_scores[:7] if len(valid_scores) >= 7 else valid_scores[:len(valid_scores)//2]
                
                if recent_scores and earlier_scores:
                    recent_avg = sum(recent_scores) / len(recent_scores)
                    earlier_avg = sum(earlier_scores) / len(earlier_scores)
                    
                    if recent_avg > earlier_avg + 0.1:
                        return 'improving'
                    elif recent_avg < earlier_avg - 0.1:
                        return 'declining'
                    else:
                        return 'stable'
            return 'insufficient_data'
        
        journal_scores = [d['journal_mood_score'] for d in trend_data if d['journal_mood_score'] is not None]
        chat_scores = [d['chat_mood_score'] for d in trend_data if d['chat_mood_score'] is not None]
        combined_scores = [d['combined_mood_score'] for d in trend_data if d['combined_mood_score'] is not None]
        
        return {
            'period_days': days,
            'total_journal_entries': total_journal_entries,
            'total_chat_conversations': total_chat_conversations,
            'total_activities': total_journal_entries + total_chat_conversations,
            'journal_trend_direction': calculate_trend(journal_scores),
            'chat_trend_direction': calculate_trend(chat_scores),
            'combined_trend_direction': calculate_trend(combined_scores),
            'daily_data': trend_data,
            'source': 'comprehensive',
            'data_summary': {
                'days_with_journal_entries': len([d for d in trend_data if d['journal_entry_count'] > 0]),
                'days_with_chat_conversations': len([d for d in trend_data if d['chat_conversation_count'] > 0]),
                'days_with_any_activity': len([d for d in trend_data if d['has_data']]),
                'total_days_in_period': len(trend_data)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting comprehensive trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze comprehensive trends")

@router.get("/trends/mood")
async def get_mood_trends(days: int = Query(30, ge=7, le=365)):
    """Get detailed mood trends over time from journal entries only"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        entries = await unified_db_service.get_entries(
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
        # TODO: Implement get_sessions and get_session_messages in unified_db_service
        # For now, return empty list to unblock imports
        return []
        
        # # Get sessions from the last N days
        # sessions = await session_service.get_sessions(limit=50)
        # 
        # conversations = []
        # end_date = datetime.now()
        # start_date = end_date - timedelta(days=days)
        # 
        # for session in sessions:
        #     # Filter by date
        #     if session.created_at >= start_date:
        #         # Get messages for this session
        #         messages = await session_service.get_session_messages(session.id)
        #         
        #         conversations.append({
        #             'session_id': session.id,
        #             'session_type': session.session_type,
        #             'created_at': session.created_at.isoformat(),
        #             'title': session.title,
        #             'status': session.status,
        #             'messages': [
        #                 {
        #                     'role': msg.role,
        #                     'content': msg.content,
        #                     'timestamp': msg.timestamp.isoformat()
        #                 }
        #                 for msg in messages
        #             ]
        #         })
        # 
        # return conversations
        
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
                # Combine user messages for emotion analysis
                combined_text = ' '.join([msg['content'] for msg in user_messages])
                
                # Analyze emotions using modern AI emotion service
                try:
                    emotion_analysis = await ai_emotion_service.analyze_emotions(combined_text)
                    mood = emotion_analysis.primary_emotion.emotion
                    sentiment_score = emotion_analysis.primary_emotion.confidence
                except Exception as e:
                    logger.warning(f"AI emotion analysis failed: {e}")
                    from app.models.entry import MoodType
                    mood = MoodType.NEUTRAL
                    sentiment_score = 0.5
                
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