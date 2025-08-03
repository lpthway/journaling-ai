import React, { useState, useEffect } from 'react';
import { LightBulbIcon, ArrowPathIcon, HeartIcon, ArrowTrendingUpIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { insightsAPI } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';

const CoachingSuggestions = () => {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [basedOnEntries, setBasedOnEntries] = useState(0);

  useEffect(() => {
    loadSuggestions();
  }, []);

  const loadSuggestions = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      const response = await insightsAPI.getCoaching();
      setSuggestions(response.data.suggestions);
      setBasedOnEntries(response.data.based_on_entries);
    } catch (error) {
      console.error('Error loading coaching suggestions:', error);
      toast.error('Failed to load coaching suggestions');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    loadSuggestions(true);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <LightBulbIcon className="w-6 h-6 text-yellow-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                Personalized Coaching Suggestions
              </h2>
              <p className="text-sm text-gray-500">
                Based on your recent {basedOnEntries} journal entries
              </p>
            </div>
          </div>
          
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors"
          >
            <ArrowPathIcon className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Suggestions */}
      {suggestions.length > 0 ? (
        <div className="space-y-4">
          {suggestions.map((suggestion, index) => (
            <SuggestionCard
              key={index}
              suggestion={suggestion}
              index={index}
            />
          ))}
        </div>
      ) : (
        <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-200 text-center">
          <HeartIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No suggestions available
          </h3>
          <p className="text-gray-500 mb-4">
            Write more journal entries to get personalized coaching suggestions!
          </p>
          <button
            onClick={() => window.location.href = '/'}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            Start Journaling
          </button>
        </div>
      )}

      {/* Tips Section */}
      <div className="bg-blue-50 p-6 rounded-lg border border-blue-200">
        <div className="flex items-start space-x-3">
          <ArrowTrendingUpIcon className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <h3 className="text-sm font-medium text-blue-900 mb-2">
              How to get better suggestions:
            </h3>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Write regularly to help AI understand your patterns</li>
              <li>• Be honest about your feelings and experiences</li>
              <li>• Include specific details about challenges and victories</li>
              <li>• Reflect on your goals and aspirations</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

// Suggestion Card Component
const SuggestionCard = ({ suggestion, index }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isBookmarked, setIsBookmarked] = useState(false);

  const suggestionTypes = [
    { icon: LightBulbIcon, color: 'yellow', label: 'Insight' },
    { icon: HeartIcon, color: 'red', label: 'Wellbeing' },
    { icon: ArrowTrendingUpIcon, color: 'green', label: 'Growth' },
  ];

  const suggestionType = suggestionTypes[index % suggestionTypes.length];
  const Icon = suggestionType.icon;

  const colorClasses = {
    yellow: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    red: 'bg-red-100 text-red-700 border-red-200',
    green: 'bg-green-100 text-green-700 border-green-200',
  };

  const iconColorClasses = {
    yellow: 'text-yellow-600',
    red: 'text-red-600',
    green: 'text-green-600',
  };

  const handleBookmark = () => {
    setIsBookmarked(!isBookmarked);
    // Here you could save to localStorage or send to backend
    if (!isBookmarked) {
      toast.success('Suggestion bookmarked!');
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow duration-200">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg bg-${suggestionType.color}-100`}>
              <Icon className={`w-5 h-5 ${iconColorClasses[suggestionType.color]}`} />
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-900">
                {suggestionType.label} #{index + 1}
              </h3>
              <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${colorClasses[suggestionType.color]} mt-1`}>
                Personalized for you
              </div>
            </div>
          </div>
          
          <button
            onClick={handleBookmark}
            className={`p-2 rounded-md transition-colors ${
              isBookmarked 
                ? 'text-yellow-600 bg-yellow-50' 
                : 'text-gray-400 hover:text-yellow-600 hover:bg-yellow-50'
            }`}
            title={isBookmarked ? 'Remove bookmark' : 'Bookmark suggestion'}
          >
            <svg className="w-5 h-5" fill={isBookmarked ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="prose prose-sm max-w-none">
          <div className="text-gray-700 leading-relaxed">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{suggestion}</ReactMarkdown>
          </div>
        </div>

        {/* Actions */}
        <div className="mt-4 flex items-center space-x-3">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
          >
            {isExpanded ? 'Show less' : 'Learn more'}
          </button>
          <button className="text-sm text-gray-500 hover:text-gray-700 transition-colors">
            Share
          </button>
          <button className="text-sm text-gray-500 hover:text-gray-700 transition-colors">
            Not helpful
          </button>
        </div>

        {/* Expanded Content */}
        {isExpanded && (
          <div className="mt-4 pt-4 border-t border-gray-100 animate-slide-up">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="text-sm font-medium text-gray-900 mb-2">
                How to implement this:
              </h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Start small with just 5-10 minutes daily</li>
                <li>• Track your progress in your journal</li>
                <li>• Be patient with yourself as you build new habits</li>
                <li>• Celebrate small wins along the way</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CoachingSuggestions;