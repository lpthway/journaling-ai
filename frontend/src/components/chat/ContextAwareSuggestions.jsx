// frontend/src/components/chat/ContextAwareSuggestions.jsx
import React, { useState, useEffect } from 'react';
import { 
  LightBulbIcon, 
  BookOpenIcon, 
  HeartIcon,
  SparklesIcon,
  ChatBubbleLeftRightIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { entryAPI } from '../../services/api';

const ContextAwareSuggestions = ({ recentEntries = [], currentMood, onSuggestionClick, isLoading = false }) => {
  const [suggestions, setSuggestions] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    generateContextAwareSuggestions();
  }, [recentEntries, currentMood]);

  const generateContextAwareSuggestions = () => {
    const contextSuggestions = [];

    // Mood-based suggestions
    if (currentMood) {
      const moodSuggestions = getMoodBasedSuggestions(currentMood);
      contextSuggestions.push(...moodSuggestions);
    }

    // Entry-based suggestions
    if (recentEntries.length > 0) {
      const entrySuggestions = getEntryBasedSuggestions(recentEntries);
      contextSuggestions.push(...entrySuggestions);
    }

    // General helpful suggestions
    const generalSuggestions = getGeneralSuggestions();
    contextSuggestions.push(...generalSuggestions);

    // Shuffle and limit suggestions
    const shuffled = contextSuggestions.sort(() => 0.5 - Math.random());
    setSuggestions(shuffled.slice(0, 6));
  };

  const getMoodBasedSuggestions = (mood) => {
    const moodSuggestionMap = {
      'positive': [
        {
          text: "What's contributing to your positive feelings today?",
          icon: HeartIcon,
          category: 'reflection',
          color: 'text-green-600 bg-green-50 border-green-200'
        },
        {
          text: "How can you carry this positive energy into tomorrow?",
          icon: SparklesIcon,
          category: 'planning',
          color: 'text-green-600 bg-green-50 border-green-200'
        }
      ],
      'negative': [
        {
          text: "What would help you feel a bit better right now?",
          icon: HeartIcon,
          category: 'support',
          color: 'text-blue-600 bg-blue-50 border-blue-200'
        },
        {
          text: "Can you tell me more about what's troubling you?",
          icon: ChatBubbleLeftRightIcon,
          category: 'exploration',
          color: 'text-blue-600 bg-blue-50 border-blue-200'
        }
      ],
      'neutral': [
        {
          text: "What's on your mind today?",
          icon: LightBulbIcon,
          category: 'open',
          color: 'text-purple-600 bg-purple-50 border-purple-200'
        },
        {
          text: "Is there anything you'd like to explore or discuss?",
          icon: ChatBubbleLeftRightIcon,
          category: 'open',
          color: 'text-purple-600 bg-purple-50 border-purple-200'
        }
      ]
    };

    return moodSuggestionMap[mood] || moodSuggestionMap['neutral'];
  };

  const getEntryBasedSuggestions = (entries) => {
    const suggestions = [];
    const latestEntry = entries[0];

    if (latestEntry) {
      // Check for common themes/tags
      const tags = latestEntry.tags || [];
      
      if (tags.includes('work') || tags.includes('stress')) {
        suggestions.push({
          text: "Would you like to talk about managing work stress?",
          icon: BookOpenIcon,
          category: 'coping',
          color: 'text-orange-600 bg-orange-50 border-orange-200',
          context: 'work_stress'
        });
      }

      if (tags.includes('relationships') || tags.includes('family')) {
        suggestions.push({
          text: "How are your relationships affecting you lately?",
          icon: HeartIcon,
          category: 'relationships',
          color: 'text-pink-600 bg-pink-50 border-pink-200',
          context: 'relationships'
        });
      }

      if (tags.includes('goals') || tags.includes('planning')) {
        suggestions.push({
          text: "What steps can you take toward your goals?",
          icon: SparklesIcon,
          category: 'goal_setting',
          color: 'text-indigo-600 bg-indigo-50 border-indigo-200',
          context: 'goals'
        });
      }

      // Time-based suggestions
      const entryAge = new Date() - new Date(latestEntry.created_at);
      const hoursAgo = entryAge / (1000 * 60 * 60);

      if (hoursAgo < 2) {
        suggestions.push({
          text: `You mentioned "${latestEntry.title.toLowerCase()}" earlier. How are you feeling about it now?`,
          icon: ArrowPathIcon,
          category: 'follow_up',
          color: 'text-blue-600 bg-blue-50 border-blue-200',
          context: 'recent_entry'
        });
      }
    }

    // Pattern-based suggestions
    if (entries.length >= 3) {
      const recentMoods = entries.slice(0, 3).map(e => e.mood).filter(Boolean);
      const predominantMood = getMostFrequent(recentMoods);

      if (predominantMood === 'negative') {
        suggestions.push({
          text: "I've noticed some challenging themes in your recent entries. Want to talk about coping strategies?",
          icon: HeartIcon,
          category: 'pattern_support',
          color: 'text-red-600 bg-red-50 border-red-200',
          context: 'pattern_negative'
        });
      } else if (predominantMood === 'positive') {
        suggestions.push({
          text: "You seem to be in a good space lately! What's been working well for you?",
          icon: SparklesIcon,
          category: 'pattern_positive',
          color: 'text-green-600 bg-green-50 border-green-200',
          context: 'pattern_positive'
        });
      }
    }

    return suggestions;
  };

  const getGeneralSuggestions = () => [
    {
      text: "How was your day today?",
      icon: ChatBubbleLeftRightIcon,
      category: 'general',
      color: 'text-gray-600 bg-gray-50 border-gray-200'
    },
    {
      text: "What are you grateful for right now?",
      icon: HeartIcon,
      category: 'gratitude',
      color: 'text-green-600 bg-green-50 border-green-200'
    },
    {
      text: "Is there something you'd like to work through?",
      icon: LightBulbIcon,
      category: 'problem_solving',
      color: 'text-blue-600 bg-blue-50 border-blue-200'
    },
    {
      text: "What's one thing you learned about yourself recently?",
      icon: SparklesIcon,
      category: 'self_reflection',
      color: 'text-purple-600 bg-purple-50 border-purple-200'
    }
  ];

  const getMostFrequent = (arr) => {
    return arr.sort((a,b) =>
      arr.filter(v => v===a).length - arr.filter(v => v===b).length
    ).pop();
  };

  const handleRefreshSuggestions = () => {
    setIsGenerating(true);
    setTimeout(() => {
      generateContextAwareSuggestions();
      setIsGenerating(false);
    }, 500);
  };

  if (isLoading || suggestions.length === 0) {
    return (
      <div className="flex items-center justify-center py-4">
        <div className="text-sm text-gray-500">Loading conversation starters...</div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-gray-700">Conversation Starters</h4>
        <button
          onClick={handleRefreshSuggestions}
          disabled={isGenerating}
          className="p-1 text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
          title="Refresh suggestions"
        >
          <ArrowPathIcon className={`h-4 w-4 ${isGenerating ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="grid gap-2">
        {suggestions.map((suggestion, index) => {
          const IconComponent = suggestion.icon;
          return (
            <button
              key={index}
              onClick={() => onSuggestionClick(suggestion.text, suggestion)}
              className={`flex items-start p-3 text-left rounded-lg border hover:shadow-sm transition-all duration-200 ${suggestion.color} hover:opacity-80`}
            >
              <IconComponent className="h-4 w-4 mt-0.5 mr-2 flex-shrink-0" />
              <span className="text-sm leading-relaxed">{suggestion.text}</span>
            </button>
          );
        })}
      </div>

      {recentEntries.length > 0 && (
        <div className="pt-2 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            💡 Suggestions are personalized based on your recent journal entries and mood patterns
          </p>
        </div>
      )}
    </div>
  );
};

export default ContextAwareSuggestions;