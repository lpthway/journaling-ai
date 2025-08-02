### app/api/insights.py

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from app.services.vector_service import vector_service
from app.services.llm_service import llm_service
from app.services.database_service import db_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/ask")
async def ask_question(question: str):
    """Ask a question about your journal entries"""
    try:
        if not question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Search for relevant entries
        relevant_entries = await vector_service.search_entries(question, limit=15)
        
        if not relevant_entries:
            return {
                'question': question,
                'answer': "I couldn't find any relevant entries to answer your question. Try writing more journal entries first!",
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
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail="Failed to process your question")

@router.get("/coaching")
async def get_coaching_suggestions():
    """Get personalized coaching suggestions based on recent entries"""
    try:
        # Get recent entries (last 7 days)
        from datetime import datetime, timedelta
        recent_date = datetime.now() - timedelta(days=7)
        recent_entries_db = await db_service.get_entries(
            limit=10, 
            date_from=recent_date
        )
        
        if not recent_entries_db:
            return {
                'suggestions': ["Start by writing your first journal entry to get personalized coaching suggestions!"],
                'based_on_entries': 0
            }
        
        # Convert to vector format for LLM service
        recent_entries = []
        for entry in recent_entries_db:
            recent_entries.append({
                'content': entry.content,
                'metadata': {
                    'created_at': entry.created_at.isoformat(),
                    'mood': entry.mood.value if entry.mood else 'Unknown',
                    'title': entry.title
                }
            })
        
        suggestions = await llm_service.generate_coaching_suggestions(recent_entries)
        
        return {
            'suggestions': suggestions,
            'based_on_entries': len(recent_entries_db),
            'period': 'Last 7 days'
        }
        
    except Exception as e:
        logger.error(f"Error generating coaching suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate coaching suggestions")

@router.get("/patterns")
async def analyze_patterns():
    """Analyze patterns in journal entries"""
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
        from collections import defaultdict
        from datetime import datetime, timedelta
        
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
            'patterns': patterns
        }
        
    except Exception as e:
        logger.error(f"Error analyzing patterns: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze patterns")

@router.get("/trends/mood")
async def get_mood_trends(days: int = Query(30, ge=7, le=365)):
    """Get detailed mood trends over time"""
    try:
        from datetime import datetime, timedelta
        
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
        from collections import defaultdict
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
            'daily_data': trend_data
        }
        
    except Exception as e:
        logger.error(f"Error getting mood trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze mood trends")