// frontend/src/components/Insights/EnhancedAskQuestion.jsx
// Enhanced version with clickable citation links and markdown support

import React, { useState } from 'react';
import { SparklesIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

// Import decomposed components
import QuestionForm from './QuestionForm/QuestionForm';
import ConversationEntryWithCitations from './ConversationEntry/ConversationEntryWithCitations';

// Use the legacy API endpoints that have full citation functionality
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const callLegacyAPI = async (endpoint, question) => {
  const url = `${API_BASE_URL}/insights-legacy/${endpoint}?question=${encodeURIComponent(question)}`;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    }
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API call failed: ${response.status} - ${errorText}`);
  }
  
  return response.json();
};

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
    if (!question.trim() || loading) return;

    setLoading(true);
    const currentQuestion = question;
    
    try {
      // Choose endpoint based on enhanced mode
      const endpoint = useEnhanced ? 'cross-platform-insights' : 'journal-insights';
      const result = await callLegacyAPI(endpoint, currentQuestion);
      
      // Create conversation entry with timestamp
      const conversationEntry = {
        id: Date.now(),
        question: currentQuestion,
        answer: result.answer || result.insight || 'No answer received',
        sources: result.sources || {},
        detailedSources: result.detailed_sources || result.sources || {},
        timestamp: new Date().toLocaleString(),
        timePeriod: result.time_period,
        useEnhanced
      };
      
      setConversationHistory(prev => [conversationEntry, ...prev]);
      setAnswer(result);
      setQuestion('');
      
    } catch (error) {
      console.error('Error asking question:', error);
      toast.error('Failed to get insights. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestedQuestion = (suggestedQ) => {
    setQuestion(suggestedQ);
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center space-x-3 mb-4">
          <SparklesIcon className="w-8 h-8 text-blue-600" />
          <h1 className="text-2xl font-bold text-gray-900">
            Enhanced Insights
          </h1>
        </div>
        <p className="text-gray-600">
          Ask questions about your journal entries and conversations to uncover patterns and insights.
        </p>
      </div>

      {/* Question Form */}
      <QuestionForm
        question={question}
        setQuestion={setQuestion}
        onSubmit={handleSubmit}
        loading={loading}
        suggestedQuestions={suggestedQuestions}
        onSuggestedQuestionClick={handleSuggestedQuestion}
        useEnhanced={useEnhanced}
        setUseEnhanced={setUseEnhanced}
      />

      {/* Conversation History */}
      {conversationHistory.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-6">
            Your Questions & Insights
          </h3>
          {conversationHistory.map((entry) => (
            <ConversationEntryWithCitations 
              key={entry.id} 
              entry={entry} 
            />
          ))}
        </div>
      )}

      {/* Empty State */}
      {conversationHistory.length === 0 && !loading && (
        <div className="text-center py-12">
          <SparklesIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Ready for Insights
          </h3>
          <p className="text-gray-500">
            Ask your first question to start exploring patterns in your reflections.
          </p>
        </div>
      )}
    </div>
  );
};

export default EnhancedAskQuestion;