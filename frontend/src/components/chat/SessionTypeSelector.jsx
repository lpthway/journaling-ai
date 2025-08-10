// frontend/src/components/Chat/SessionTypeSelector.jsx

import React, { useState, useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import LoadingSpinner from '../Common/LoadingSpinner';
import { sessionAPI } from '../../services/api';

const SessionTypeSelector = ({ onSelectType, onCancel, isLoading = false }) => {
  const [sessionTypes, setSessionTypes] = useState([]);
  const [selectedType, setSelectedType] = useState(null);
  const [loadingTypes, setLoadingTypes] = useState(true);

  // Helper function to get icons for enhanced chat modes
  const getIconForMode = (mode) => {
    const iconMap = {
      'supportive_listening': '💭',
      'therapeutic_guidance': '🧠', 
      'cognitive_reframing': '🔄',
      'mindfulness_coaching': '🧘',
      'goal_setting': '🎯',
      'crisis_support': '🚨',
      'reflection_facilitation': '✨',
      'emotional_processing': '💙'
    };
    return iconMap[mode] || '💬';
  };

  useEffect(() => {
    loadSessionTypes();
  }, []);

  const loadSessionTypes = async () => {
    try {
      const response = await sessionAPI.getAvailableTypes();
      // Enhanced chat API returns {available_modes: {...}} format
      const modes = response.data.available_modes || {};
      const typesArray = Object.entries(modes).map(([key, value]) => ({
        type: key,
        name: value.name,
        description: value.description,
        icon: getIconForMode(key),
        tags: value.suitable_for || []
      }));
      setSessionTypes(typesArray);
    } catch (error) {
      console.error('Error loading session types:', error);
      // Fallback session types (using enhanced chat modes)
      setSessionTypes([
        {
          type: 'supportive_listening',
          name: 'Supportive Listening',
          description: 'Active listening with validation and empathy',
          icon: '💭',
          tags: ['emotional distress', 'validation', 'empathy']
        },
        {
          type: 'therapeutic_guidance',
          name: 'Therapeutic Guidance',
          description: 'Structured therapeutic conversation with professional techniques',
          icon: '🧠',
          tags: ['problem-solving', 'skill building', 'guidance']
        },
        {
          type: 'cognitive_reframing',
          name: 'Cognitive Reframing',
          description: 'Focus on identifying and challenging negative thought patterns',
          icon: '🔄',
          tags: ['negative thinking', 'perspective', 'reframing']
        },
        {
          type: 'mindfulness_coaching',
          name: 'Mindfulness Coaching',
          description: 'Present-moment awareness and mindfulness practices',
          icon: '🧘',
          tags: ['anxiety', 'stress', 'mindfulness']
        },
        {
          type: 'goal_setting',
          name: 'Goal Setting',
          description: 'Collaborative goal setting and action planning',
          icon: '🎯',
          tags: ['personal growth', 'planning', 'motivation']
        }
      ]);
    } finally {
      setLoadingTypes(false);
    }
  };

  const handleStartSession = () => {
    if (selectedType && onSelectType) {
      onSelectType(selectedType.type);
    }
  };

  if (loadingTypes) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 max-h-[80vh] overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Start a Conversation</h2>
          <p className="text-sm text-gray-500 mt-1">
            Choose the type of conversation you'd like to have
          </p>
        </div>
        {onCancel && (
          <button
            onClick={onCancel}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-md transition-colors"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Session Type Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {sessionTypes && sessionTypes.length > 0 ? sessionTypes.map((type) => (
          <div
            key={type.type}
            onClick={() => setSelectedType(type)}
            className={`p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 hover:shadow-md ${
              selectedType?.type === type.type
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-start space-x-3">
              <div className="text-2xl">{type.icon}</div>
              <div className="flex-1">
                <h3 className="font-medium text-gray-900 mb-1">{type.name}</h3>
                <p className="text-sm text-gray-600 mb-3">{type.description}</p>
                
                {/* Tags */}
                <div className="flex flex-wrap gap-1">
                  {type.tags.map((tag, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )) : (
          <div className="col-span-full flex items-center justify-center py-8">
            <div className="text-center">
              <p className="text-gray-500 mb-2">No conversation types available</p>
              <button 
                onClick={loadSessionTypes}
                className="text-blue-600 hover:text-blue-700 text-sm font-medium"
              >
                Try again
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-500">
          {selectedType ? (
            <span>✨ Ready to start a <strong>{selectedType.name}</strong> session</span>
          ) : (
            <span>Select a conversation type to get started</span>
          )}
        </div>
        
        <div className="flex items-center space-x-3">
          {onCancel && (
            <button
              onClick={onCancel}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              Cancel
            </button>
          )}
          
          <button
            onClick={handleStartSession}
            disabled={!selectedType || isLoading}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading && <LoadingSpinner size="sm" className="mr-2" />}
            {isLoading ? 'Starting...' : 'Start Conversation'}
          </button>
        </div>
      </div>

      {/* Quick Tips */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h4 className="text-sm font-medium text-gray-900 mb-2">💡 Quick Tips:</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• You can pause and resume conversations anytime</li>
          <li>• Each conversation type has its own personality and approach</li>
          <li>• Your conversations are saved and can be revisited later</li>
          <li>• Feel free to be open and honest - this is your safe space</li>
        </ul>
      </div>
    </div>
  );
};

export default SessionTypeSelector;