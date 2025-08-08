import React from 'react';
import { PaperAirplaneIcon } from '@heroicons/react/24/outline';
import LoadingSpinner from '../../Common/LoadingSpinner';

const QuestionForm = ({ 
  question, 
  setQuestion, 
  onSubmit, 
  loading, 
  suggestedQuestions, 
  onSuggestedQuestionClick,
  useEnhanced,
  setUseEnhanced 
}) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        Ask a Question About Your Reflections
      </h2>
      <p className="text-gray-600 mb-6">
        Get insights from both your journal entries and chat conversations. Ask questions about patterns, 
        growth, or specific topics across all your reflections.
      </p>

      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="What would you like to know about your reflections? Try asking about patterns, growth, or specific topics..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows="3"
            disabled={loading}
          />
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <label className="flex items-center space-x-2 text-sm text-gray-600">
              <input
                type="checkbox"
                checked={useEnhanced}
                onChange={(e) => setUseEnhanced(e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                disabled={loading}
              />
              <span>Use enhanced analysis (includes cross-platform insights)</span>
            </label>
          </div>
          
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="inline-flex items-center px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <>
                <LoadingSpinner className="w-4 h-4 mr-2" />
                Analyzing...
              </>
            ) : (
              <>
                <PaperAirplaneIcon className="w-4 h-4 mr-2" />
                Ask Question
              </>
            )}
          </button>
        </div>
      </form>

      {/* Suggested Questions */}
      <div className="mt-8">
        <h3 className="text-sm font-medium text-gray-900 mb-3">
          Suggested Questions
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {suggestedQuestions.map((suggestedQ, index) => (
            <button
              key={index}
              onClick={() => onSuggestedQuestionClick(suggestedQ)}
              disabled={loading}
              className="text-left p-3 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {suggestedQ}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default QuestionForm;