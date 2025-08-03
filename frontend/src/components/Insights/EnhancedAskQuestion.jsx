// frontend/src/components/Insights/EnhancedAskQuestion.jsx
// Enhanced version with clickable citation links - FIXED

import React, { useState } from 'react';
import { PaperAirplaneIcon, SparklesIcon, ArrowTopRightOnSquareIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { insightsAPI } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';

const EnhancedAskQuestion = () => {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [useEnhanced, setUseEnhanced] = useState(true);

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
      const endpoint = useEnhanced ? 'ask' : 'askJournalOnly';
      const response = await insightsAPI[endpoint](currentQuestion);
      
      const newEntry = {
        id: Date.now(),
        question: currentQuestion,
        answer: response.data.answer,
        sources: response.data.sources || { sources_used: response.data.sources_used },
        contentBreakdown: response.data.content_breakdown,
        timePeriod: response.data.time_period,
        relevantEntries: response.data.relevant_entries || [],
        detailedSources: response.data.detailed_sources || { journal_entries: [], conversations: [] },
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
              ? '🌟 Enhanced mode analyzes both your journal entries AND chat conversations with clickable citations'
              : '📔 Journal-only mode analyzes just your written journal entries with source links'
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
            <ConversationEntryWithCitations key={entry.id} entry={entry} />
          ))}
        </div>
      )}
    </div>
  );
};

// Enhanced Conversation Entry with Citation Links
const ConversationEntryWithCitations = ({ entry }) => {
  const [showCitations, setShowCitations] = useState(false);

  // Function to add citation links to the answer text
  const formatAnswerWithCitations = (text, sources) => {
    if (!sources || (!sources.journal_entries?.length && !sources.conversations?.length)) {
      return text;
    }

    // Create a map of all sources with citation numbers
    const allSources = [];
    
    // Add journal entries
    sources.journal_entries?.forEach((source, index) => {
      allSources.push({
        ...source,
        citationNumber: allSources.length + 1,
        sourceType: 'journal'
      });
    });

    // Add conversations
    sources.conversations?.forEach((source, index) => {
      allSources.push({
        ...source,
        citationNumber: allSources.length + 1,
        sourceType: 'conversation'
      });
    });

    // For now, return the text with citation indicators
    // In a real implementation, you'd want to parse the text and add citations where appropriate
    return (
      <div>
        <p className="text-gray-900 whitespace-pre-wrap">{text}</p>
        
        {/* Citation Numbers */}
        {allSources.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1">
            <span className="text-xs text-gray-500 mr-2">Sources:</span>
            {allSources.map((source) => (
              <CitationLink key={source.citationNumber} source={source} />
            ))}
          </div>
        )}
      </div>
    );
  };

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

      {/* Answer with Citations */}
      <div className="px-6 py-4">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0 w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">
            <SparklesIcon className="w-4 h-4 text-white" />
          </div>
          <div className="flex-1">
            <div className="prose prose-sm max-w-none">
              {formatAnswerWithCitations(entry.answer, entry.detailedSources)}
            </div>
            
            {/* Sources Summary */}
            <div className="mt-4 pt-4 border-t border-gray-100">
              {entry.enhanced && entry.sources ? (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-gray-500">
                      Enhanced analysis based on {entry.sources.total_sources || 0} sources:
                    </p>
                    <button
                      onClick={() => setShowCitations(!showCitations)}
                      className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                    >
                      {showCitations ? 'Hide' : 'Show'} detailed sources
                    </button>
                  </div>
                  <div className="flex space-x-4 text-xs">
                    <span className="text-blue-600">
                      📔 {entry.sources.journal_entries || 0} journal entries
                    </span>
                    <span className="text-purple-600">
                      💬 {entry.sources.chat_messages || 0} conversations
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

            {/* Detailed Sources (collapsible) */}
            {showCitations && entry.detailedSources && (
              <DetailedSourcesList sources={entry.detailedSources} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Citation Link Component
const CitationLink = ({ source }) => {
  const handleCitationClick = () => {
    if (source.sourceType === 'journal') {
      // Navigate to journal entry
      window.location.href = `/journal#entry-${source.id}`;
    } else if (source.sourceType === 'conversation') {
      // Navigate to chat conversation
      window.location.href = `/chat/${source.id}`;
    }
  };

  return (
    <button
      onClick={handleCitationClick}
      className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 hover:bg-blue-200 transition-colors"
      title={`${source.sourceType === 'journal' ? 'Journal' : 'Chat'}: ${source.snippet?.substring(0, 50)}...`}
    >
      [{source.citationNumber}]
      <ArrowTopRightOnSquareIcon className="w-3 h-3 ml-1" />
    </button>
  );
};

// Detailed Sources List Component
const DetailedSourcesList = ({ sources }) => {
  return (
    <div className="mt-4 p-4 bg-gray-50 rounded-lg">
      <h4 className="text-sm font-medium text-gray-900 mb-3">Detailed Sources</h4>
      
      {/* Journal Entries */}
      {sources.journal_entries?.length > 0 && (
        <div className="mb-4">
          <h5 className="text-xs font-medium text-gray-700 mb-2">📔 Journal Entries</h5>
          <div className="space-y-2">
            {sources.journal_entries.map((entry, index) => (
              <SourceItem key={entry.id || index} source={entry} type="journal" />
            ))}
          </div>
        </div>
      )}

      {/* Conversations */}
      {sources.conversations?.length > 0 && (
        <div>
          <h5 className="text-xs font-medium text-gray-700 mb-2">💬 Conversations</h5>
          <div className="space-y-2">
            {sources.conversations.map((conversation, index) => (
              <SourceItem key={conversation.id || index} source={conversation} type="conversation" />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Individual Source Item
const SourceItem = ({ source, type }) => {
  const handleSourceClick = () => {
    if (type === 'journal') {
      window.location.href = `/journal#entry-${source.id}`;
    } else {
      window.location.href = `/chat/${source.id}`;
    }
  };

  return (
    <div className="p-3 bg-white rounded border border-gray-200 hover:border-gray-300 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-1">
            <span className="text-xs font-medium text-gray-600">
              {type === 'journal' ? source.title || 'Untitled Entry' : source.session_type}
            </span>
            <span className="text-xs text-gray-500">
              {source.similarity}% match
            </span>
          </div>
          <p className="text-xs text-gray-600 mb-2 line-clamp-2">
            {source.snippet}
          </p>
          <p className="text-xs text-gray-500">
            {source.date} {type === 'conversation' && `• ${source.message_count} messages`}
          </p>
        </div>
        <button
          onClick={handleSourceClick}
          className="ml-3 p-1 text-gray-400 hover:text-blue-600 transition-colors"
          title={`Go to ${type}`}
        >
          <ArrowTopRightOnSquareIcon className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default EnhancedAskQuestion;