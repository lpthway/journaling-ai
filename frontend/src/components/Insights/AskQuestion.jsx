import React, { useState } from 'react';
import { PaperAirplaneIcon, SparklesIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { insightsAPI } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';

const AskQuestion = () => {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);

  const suggestedQuestions = [
    "Have I improved over time?",
    "What do I write about most?",
    "How has my mood changed recently?",
    "What patterns do you notice in my entries?",
    "What am I most grateful for?",
    "What challenges do I face most often?",
    "How do I handle stress?",
    "What makes me happiest?"
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    const currentQuestion = question.trim();
    setQuestion('');
    setLoading(true);

    try {
      const response = await insightsAPI.askQuestion(currentQuestion);
      
      const newEntry = {
        id: Date.now(),
        question: currentQuestion,
        answer: response.data.answer,
        sourcesUsed: response.data.sources_used,
        relevantEntries: response.data.relevant_entries || [],
        timestamp: new Date()
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
      {/* Question Input */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div className="flex items-center space-x-2 mb-4">
          <SparklesIcon className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">Ask AI About Your Journal</h2>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="question" className="block text-sm font-medium text-gray-700 mb-2">
              What would you like to know about your journaling journey?
            </label>
            <div className="flex space-x-3">
              <input
                type="text"
                id="question"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="e.g., How has my mood changed over the last month?"
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
            {suggestedQuestions.map((q, index) => (
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

// Conversation Entry Component
const ConversationEntry = ({ entry }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Question */}
      <div className="bg-blue-50 px-6 py-4 border-b border-gray-200">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
              <span className="text-white text-sm font-medium">Q</span>
            </div>
          </div>
          <div className="flex-1">
            <p className="text-gray-900 font-medium">{entry.question}</p>
            <p className="text-xs text-gray-500 mt-1">
              {entry.timestamp.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Answer */}
      <div className="px-6 py-4">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">
              <SparklesIcon className="w-4 h-4 text-white" />
            </div>
          </div>
          <div className="flex-1">
            <div className="prose prose-sm max-w-none">
              <p className="text-gray-900 whitespace-pre-wrap">{entry.answer}</p>
            </div>
            
            {/* Sources Info */}
            <div className="mt-4 pt-4 border-t border-gray-100">
              <p className="text-xs text-gray-500 mb-2">
                Based on {entry.sourcesUsed} journal entries
              </p>
              
              {/* Relevant Entries Preview */}
              {entry.relevantEntries && entry.relevantEntries.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-medium text-gray-600">Most relevant entries:</p>
                  <div className="space-y-1">
                    {entry.relevantEntries.slice(0, 3).map((relevantEntry, index) => (
                      <div key={index} className="text-xs bg-gray-50 p-2 rounded">
                        <div className="flex justify-between items-start mb-1">
                          <span className="font-medium text-gray-700">
                            {relevantEntry.date}
                          </span>
                          <span className="text-gray-500">
                            {Math.round(relevantEntry.similarity * 100)}% match
                          </span>
                        </div>
                        <p className="text-gray-600">{relevantEntry.snippet}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AskQuestion;