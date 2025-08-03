#!/bin/bash

echo "🔄 Integrating Chat Conversations into Insights System"
echo "===================================================="
echo ""
echo "This will enhance your insights to include both:"
echo "✓ Journal entries (existing)"
echo "✓ Chat conversations (new)"
echo ""

# Check if we're in the right directory
if [ ! -d "backend/app/services" ]; then
    echo "❌ Please run this from the project root directory"
    exit 1
fi

# Create backup
BACKUP_DIR="backend_backup_$(date +%Y%m%d_%H%M%S)"
echo "📦 Creating backup at: $BACKUP_DIR"
cp -r backend "$BACKUP_DIR"

echo ""
echo "🔧 Adding enhanced insights service..."

# 1. Create the enhanced insights service
cat > backend/app/services/enhanced_insights_service.py << 'EOF'
# backend/app/services/enhanced_insights_service.py

import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from app.services.database_service import db_service
from app.services.session_service import session_service
from app.services.vector_service import vector_service
from app.services.sentiment_service import sentiment_service
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

class EnhancedInsightsService:
    """Enhanced insights service that includes both journal entries and chat conversations"""
    
    async def analyze_all_content(self, question: str, days: int = 30) -> Dict[str, Any]:
        """Analyze both journal entries and chat conversations to answer a question"""
        try:
            # Get journal entries
            journal_entries = await self._get_journal_entries(days)
            
            # Get chat conversations
            chat_conversations = await self._get_chat_conversations(days)
            
            # Search for relevant content using vector search
            relevant_journal = await vector_service.search_entries(question, limit=10)
            relevant_chat = await self._search_chat_content(question, limit=10)
            
            # Combine and analyze all content
            all_content = self._combine_content(
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
    
    async def get_comprehensive_mood_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Get mood analysis from both journal entries and chat conversations"""
        try:
            # Analyze journal entry moods (existing functionality)
            journal_mood_stats = await db_service.get_mood_statistics(days)
            
            # Analyze chat conversation sentiments
            chat_sentiments = await self._analyze_chat_sentiments(days)
            
            # Combine both analyses
            combined_analysis = await self._combine_mood_analyses(
                journal_mood_stats, 
                chat_sentiments
            )
            
            return combined_analysis
            
        except Exception as e:
            logger.error(f"Error in comprehensive mood analysis: {e}")
            raise
    
    async def generate_enhanced_coaching_suggestions(self, days: int = 7) -> List[str]:
        """Generate coaching suggestions based on both journal entries and chat conversations"""
        try:
            # Get recent journal entries
            journal_entries = await self._get_journal_entries(days)
            
            # Get recent chat conversations
            chat_conversations = await self._get_chat_conversations(days)
            
            # Convert to analysis format
            combined_content = []
            
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
EOF

echo "✅ LLM service enhanced"

# 3. Update the insights API with new endpoints
echo ""
echo "🔧 Updating insights API with enhanced endpoints..."

# Backup the original insights API
cp backend/app/api/insights.py backend/app/api/insights_original.py

# Update the insights API to include enhanced functionality
cat > backend/app/api/insights.py << 'EOF'
### app/api/insights.py - Enhanced version

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from app.services.vector_service import vector_service
from app.services.llm_service import llm_service
from app.services.database_service import db_service
from app.services.enhanced_insights_service import enhanced_insights_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/ask")
async def ask_question(question: str):
    """Ask a question about your journal entries AND chat conversations"""
    try:
        if not question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Use enhanced insights service that includes both journals and chats
        result = await enhanced_insights_service.analyze_all_content(question, days=30)
        
        return {
            'question': question,
            'answer': result['answer'],
            'sources': result['sources'],
            'content_breakdown': result['content_breakdown'],
            'time_period': result['time_period']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail="Failed to process your question")

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

@router.get("/coaching")
async def get_coaching_suggestions():
    """Get personalized coaching suggestions based on recent entries AND conversations"""
    try:
        suggestions = await enhanced_insights_service.generate_enhanced_coaching_suggestions(days=7)
        
        return {
            'suggestions': suggestions,
            'source': 'journal_and_chat',
            'period': 'Last 7 days',
            'note': 'Based on both your journal entries and chat conversations'
        }
        
    except Exception as e:
        logger.error(f"Error generating coaching suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate coaching suggestions")

@router.get("/coaching-journal-only")
async def get_coaching_suggestions_journal_only():
    """Get coaching suggestions based on journal entries only (original functionality)"""
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
                'based_on_entries': 0,
                'source': 'journal_only'
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
            'period': 'Last 7 days',
            'source': 'journal_only'
        }
        
    except Exception as e:
        logger.error(f"Error generating journal-only coaching suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate coaching suggestions")

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
            'patterns': patterns,
            'source': 'journal_only'
        }
        
    except Exception as e:
        logger.error(f"Error analyzing patterns: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze patterns")

@router.get("/patterns-enhanced")
async def analyze_enhanced_patterns():
    """Analyze patterns across both journal entries and chat conversations"""
    try:
        # Get comprehensive mood analysis
        mood_analysis = await enhanced_insights_service.get_comprehensive_mood_analysis(days=30)
        
        # Get conversation patterns
        conversation_patterns = await enhanced_insights_service.analyze_conversation_patterns(days=30)
        
        # Get journal patterns (existing functionality)
        journal_patterns_response = await analyze_patterns()
        journal_patterns = journal_patterns_response.get('patterns', {})
        
        # Combine all patterns
        enhanced_patterns = {
            'mood_analysis': mood_analysis,
            'conversation_patterns': conversation_patterns,
            'journal_patterns': journal_patterns,
            'summary': {
                'total_journal_entries': journal_patterns.get('writing_frequency', {}).get('total_entries', 0),
                'total_conversations': conversation_patterns.get('total_conversations', 0),
                'analysis_period': '30 days',
                'sources': ['journal_entries', 'chat_conversations']
            }
        }
        
        return enhanced_patterns
        
    except Exception as e:
        logger.error(f"Error analyzing enhanced patterns: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze enhanced patterns")

@router.get("/chat-insights")
async def get_chat_insights(days: int = Query(30, ge=7, le=365)):
    """Get insights specifically from chat conversations"""
    try:
        conversation_patterns = await enhanced_insights_service.analyze_conversation_patterns(days)
        return conversation_patterns
        
    except Exception as e:
        logger.error(f"Error getting chat insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze chat insights")

@router.get("/mood-analysis-comprehensive")
async def get_comprehensive_mood_analysis(days: int = Query(30, ge=7, le=365)):
    """Get comprehensive mood analysis from all sources"""
    try:
        analysis = await enhanced_insights_service.get_comprehensive_mood_analysis(days)
        return analysis
        
    except Exception as e:
        logger.error(f"Error getting comprehensive mood analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform comprehensive mood analysis")

# Keep original endpoints for backward compatibility
@router.get("/trends/mood")
async def get_mood_trends(days: int = Query(30, ge=7, le=365)):
    """Get detailed mood trends over time from journal entries only"""
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
            'daily_data': trend_data,
            'source': 'journal_only'
        }
        
    except Exception as e:
        logger.error(f"Error getting mood trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze mood trends")
EOF

echo "✅ Insights API updated with enhanced endpoints"

# 4. Update the frontend to use enhanced insights
echo ""
echo "🔧 Updating frontend to use enhanced insights..."

# Create a new frontend component for enhanced insights
cat > frontend/src/components/Insights/EnhancedAskQuestion.jsx << 'EOF'
import React, { useState } from 'react';
import { PaperAirplaneIcon, SparklesIcon, SwitchHorizontalIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { insightsAPI } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';

const EnhancedAskQuestion = () => {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [useEnhanced, setUseEnhanced] = useState(true); // Default to enhanced

  const suggestedQuestions = [
    "How have my thoughts evolved in both my writing and conversations?",
    "What themes appear across my journals and chats?",
    "How does my mood differ between writing and talking?",
    "What insights can you draw from all my reflections?",
    "Have I improved over time across all interactions?",
    "What patterns do you notice in how I express myself?",
    "How do my conversations complement my journal writing?",
    "What growth do you see in my overall reflection journey?"
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    const currentQuestion = question.trim();
    setQuestion('');
    setLoading(true);

    try {
      // Use enhanced or journal-only endpoint based on toggle
      const endpoint = useEnhanced ? 'ask' : 'ask-journal-only';
      const response = await insightsAPI[endpoint](currentQuestion);
      
      const newEntry = {
        id: Date.now(),
        question: currentQuestion,
        answer: response.data.answer,
        sources: response.data.sources || { sources_used: response.data.sources_used },
        contentBreakdown: response.data.content_breakdown,
        timePeriod: response.data.time_period,
        relevantEntries: response.data.relevant_entries || [],
        timestamp: new Date(),
        enhanced: useEnhanced
      };

      setConversationHistory(prev => [newEntry, ...prev]);
      setAnswer(newEntry);
    } catch (error) {
      console.error('Error asking question:', error);
      toast.error('Failed to get an answer. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestedQuestion = (suggestedQ) => {
    setQuestion(suggestedQ);
  };

  return (
    <div className="space-y-6">
      {/* Enhanced vs Journal-only Toggle */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <SparklesIcon className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">Ask AI About Your Reflections</h2>
          </div>
          
          <div className="flex items-center space-x-3">
            <span className="text-sm text-gray-600">Analysis mode:</span>
            <button
              onClick={() => setUseEnhanced(!useEnhanced)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${
                useEnhanced ? 'bg-blue-600' : 'bg-gray-300'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  useEnhanced ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
            <span className="text-sm font-medium text-gray-900">
              {useEnhanced ? 'Enhanced (Journal + Chat)' : 'Journal Only'}
            </span>
          </div>
        </div>
        
        <div className="mb-4 p-3 bg-blue-50 rounded-md">
          <p className="text-sm text-blue-800">
            {useEnhanced 
              ? '🌟 Enhanced mode analyzes both your journal entries AND chat conversations for deeper insights'
              : '📔 Journal-only mode analyzes just your written journal entries (original functionality)'
            }
          </p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="question" className="block text-sm font-medium text-gray-700 mb-2">
              {useEnhanced 
                ? "What would you like to know about your complete reflection journey?"
                : "What would you like to know about your journal entries?"
              }
            </label>
            <div className="flex space-x-3">
              <input
                type="text"
                id="question"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder={useEnhanced 
                  ? "e.g., How do my thoughts in conversations differ from my journal writing?"
                  : "e.g., How has my mood changed over the last month?"
                }
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !question.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
              >
                {loading ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  <PaperAirplaneIcon className="w-4 h-4" />
                )}
                <span>Ask</span>
              </button>
            </div>
          </div>
        </form>

        {/* Suggested Questions */}
        <div className="mt-4">
          <p className="text-sm text-gray-600 mb-3">Suggested questions:</p>
          <div className="flex flex-wrap gap-2">
            {(useEnhanced ? suggestedQuestions : [
              "Have I improved over time?",
              "What do I write about most?",
              "How has my mood changed recently?",
              "What patterns do you notice in my entries?"
            ]).map((q, index) => (
              <button
                key={index}
                onClick={() => handleSuggestedQuestion(q)}
                className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
                disabled={loading}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Conversation History */}
      {conversationHistory.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Conversation History</h3>
          {conversationHistory.map((entry) => (
            <ConversationEntry key={entry.id} entry={entry} />
          ))}
        </div>
      )}
    </div>
  );
};

// Enhanced Conversation Entry Component
const ConversationEntry = ({ entry }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Question */}
      <div className={`px-6 py-4 border-b border-gray-200 ${
        entry.enhanced ? 'bg-blue-50' : 'bg-gray-50'
      }`}>
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3 flex-1">
            <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
              entry.enhanced ? 'bg-blue-600' : 'bg-gray-600'
            }`}>
              <span className="text-white text-sm font-medium">Q</span>
            </div>
            <div className="flex-1">
              <p className="text-gray-900 font-medium">{entry.question}</p>
              <div className="flex items-center space-x-4 mt-1">
                <p className="text-xs text-gray-500">
                  {entry.timestamp.toLocaleString()}
                </p>
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                  entry.enhanced 
                    ? 'bg-blue-100 text-blue-800' 
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {entry.enhanced ? '🌟 Enhanced Analysis' : '📔 Journal Only'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Answer */}
      <div className="px-6 py-4">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0 w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">
            <SparklesIcon className="w-4 h-4 text-white" />
          </div>
          <div className="flex-1">
            <div className="prose prose-sm max-w-none">
              <p className="text-gray-900 whitespace-pre-wrap">{entry.answer}</p>
            </div>
            
            {/* Enhanced Sources Info */}
            <div className="mt-4 pt-4 border-t border-gray-100">
              {entry.enhanced && entry.sources ? (
                <div className="space-y-2">
                  <p className="text-xs text-gray-500">
                    Enhanced analysis based on {entry.sources.total_sources} sources:
                  </p>
                  <div className="flex space-x-4 text-xs">
                    <span className="text-blue-600">
                      📔 {entry.sources.journal_entries} journal entries
                    </span>
                    <span className="text-purple-600">
                      💬 {entry.sources.chat_messages} conversations
                    </span>
                  </div>
                  {entry.timePeriod && (
                    <p className="text-xs text-gray-500">
                      Time period: {entry.timePeriod}
                    </p>
                  )}
                </div>
              ) : (
                <p className="text-xs text-gray-500">
                  Based on {entry.sources?.sources_used || 0} journal entries
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedAskQuestion;
EOF

echo "✅ Enhanced frontend component created"

# 5. Update the frontend API service
echo ""
echo "🔧 Updating frontend API service..."

# Add enhanced endpoints to the API service
cat >> frontend/src/services/api.js << 'EOF'

// Enhanced Insights API - includes chat conversations
export const enhancedInsightsAPI = {
  askQuestion: (question) => api.post('/insights/ask', null, { params: { question } }),
  askJournalOnly: (question) => api.post('/insights/ask-journal-only', null, { params: { question } }),
  getEnhancedCoaching: () => api.get('/insights/coaching'),
  getJournalOnlyCoaching: () => api.get('/insights/coaching-journal-only'),
  getEnhancedPatterns: () => api.get('/insights/patterns-enhanced'),
  getChatInsights: (days = 30) => api.get('/insights/chat-insights', { params: { days } }),
  getComprehensiveMoodAnalysis: (days = 30) => api.get('/insights/mood-analysis-comprehensive', { params: { days } }),
};

// Update existing insightsAPI to include new methods
insightsAPI.ask = enhancedInsightsAPI.askQuestion;
insightsAPI.askJournalOnly = enhancedInsightsAPI.askJournalOnly;
insightsAPI.getEnhancedCoaching = enhancedInsightsAPI.getEnhancedCoaching;
insightsAPI.getEnhancedPatterns = enhancedInsightsAPI.getEnhancedPatterns;
insightsAPI.getChatInsights = enhancedInsightsAPI.getChatInsights;
insightsAPI.getComprehensiveMoodAnalysis = enhancedInsightsAPI.getComprehensiveMoodAnalysis;
EOF

echo "✅ Frontend API service updated"

# 6. Summary and next steps
echo ""
echo "🎉 INTEGRATION COMPLETE!"
echo "========================"
echo ""
echo "✅ Enhanced insights service created"
echo "✅ LLM service enhanced with combined analysis"
echo "✅ API endpoints updated with chat integration"
echo "✅ Frontend component created for enhanced insights"
echo "✅ API service updated with new endpoints"
echo ""
echo "📊 NEW CAPABILITIES:"
echo "   🌟 Combined analysis of journal entries + chat conversations"
echo "   💬 Chat conversation sentiment analysis"
echo "   📈 Enhanced mood trends across all interactions"
echo "   🎯 Comprehensive coaching suggestions"
echo "   🔍 Pattern analysis across all content types"
echo ""
echo "🚀 TO USE THE ENHANCED FEATURES:"
echo "================================"
echo "1. Restart your backend:"
echo "   cd backend && source venv/bin/activate && python run.py"
echo ""
echo "2. In your frontend, the Ask AI feature now includes both:"
echo "   - Enhanced mode (journal + chat)"
echo "   - Journal-only mode (original)"
echo ""
echo "3. NEW API ENDPOINTS AVAILABLE:"
echo "   POST /api/v1/insights/ask (enhanced)"
echo "   POST /api/v1/insights/ask-journal-only"
echo "   GET  /api/v1/insights/coaching (enhanced)"
echo "   GET  /api/v1/insights/patterns-enhanced"
echo "   GET  /api/v1/insights/chat-insights"
echo "   GET  /api/v1/insights/mood-analysis-comprehensive"
echo ""
echo "💾 BACKUP LOCATION:"
echo "   $BACKUP_DIR"
echo ""
echo "🧪 TEST THE INTEGRATION:"
echo "========================"
echo "1. Have some chat conversations"
echo "2. Write some journal entries"
echo "3. Go to Insights → Ask AI"
echo "4. Try questions like:"
echo "   - 'How do my thoughts in conversations differ from my writing?'"
echo "   - 'What themes appear across all my reflections?'"
echo "   - 'How has my communication style evolved?'"
echo ""
echo "🎯 The enhanced system now provides much richer insights!"for entry in journal_entries:
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
    
    async def analyze_conversation_patterns(self, days: int = 30) -> Dict[str, Any]:
        """Analyze patterns in chat conversations"""
        try:
            conversations = await self._get_chat_conversations(days)
            
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
    
    async def _get_journal_entries(self, days: int) -> List:
        """Get journal entries from the last N days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return await db_service.get_entries(date_from=start_date, date_to=end_date, limit=100)
    
    async def _get_chat_conversations(self, days: int) -> List[Dict]:
        """Get chat conversations from the last N days"""
        try:
            # Get sessions from the last N days
            sessions = await session_service.get_sessions(limit=50)
            
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
    
    async def _search_chat_content(self, query: str, limit: int = 10) -> List[Dict]:
        """Search through chat conversations for relevant content"""
        try:
            conversations = await self._get_chat_conversations(30)  # Last 30 days
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
    
    async def _analyze_chat_sentiments(self, days: int) -> Dict[str, Any]:
        """Analyze sentiments from chat conversations"""
        try:
            conversations = await self._get_chat_conversations(days)
            
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
    
    async def _combine_mood_analyses(self, journal_moods: Dict, chat_sentiments: Dict) -> Dict[str, Any]:
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
    
    def _combine_content(self, journal_entries, chat_conversations, relevant_journal, relevant_chat) -> List[Dict]:
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

# Global instance
enhanced_insights_service = EnhancedInsightsService()
EOF

echo "✅ Enhanced insights service created"

# 2. Update the LLM service with enhanced methods
echo ""
echo "🔧 Updating LLM service with enhanced analysis methods..."

# Add the enhanced methods to the existing LLM service
cat >> backend/app/services/llm_service.py << 'EOF'

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

Please provide a thoughtful, personalized response that:
1. References specific patterns or themes from BOTH journal entries and conversations
2. Offers insights about growth, changes, or trends across all your reflections
3. Is supportive and constructive
4. Acknowledges the different types of content (written journal vs. conversational)
5. Maintains privacy and confidentiality

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