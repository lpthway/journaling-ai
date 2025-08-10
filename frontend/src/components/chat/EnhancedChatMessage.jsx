// frontend/src/components/chat/EnhancedChatMessage.jsx
import React, { useState } from 'react';
import { 
  UserIcon, 
  SparklesIcon, 
  ClockIcon, 
  ExclamationTriangleIcon,
  HeartIcon,
  ShieldExclamationIcon,
  InformationCircleIcon,
  ChevronDownIcon,
  ChevronUpIcon
} from '@heroicons/react/24/outline';
import { 
  ExclamationTriangleIcon as ExclamationTriangleIconSolid,
  HeartIcon as HeartIconSolid 
} from '@heroicons/react/24/solid';
import ReactMarkdown from 'react-markdown';
import { formatTime } from '../../utils/helpers';

const EnhancedChatMessage = ({ message, isTyping = false, contextEntries = [] }) => {
  const [showContext, setShowContext] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  // Safety check
  if (!message && !isTyping) {
    return null;
  }

  // Enhanced typing indicator
  if (isTyping) {
    return (
      <div className="flex justify-start mb-6">
        <div className="flex max-w-[85%] items-start space-x-3">
          <div className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center bg-gradient-to-br from-purple-500 via-pink-500 to-blue-500 text-white shadow-lg">
            <SparklesIcon className="w-5 h-5" />
          </div>
          <div className="flex-1">
            <div className="rounded-2xl px-6 py-4 bg-gradient-to-r from-gray-50 to-gray-100 border border-gray-200 rounded-bl-md shadow-sm">
              <div className="flex items-center space-x-2">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-pink-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
                <span className="text-sm text-gray-500 animate-pulse">AI is thinking...</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!message.role || !message.content) {
    return null;
  }

  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';

  // Extract crisis indicators from message metadata
  const crisisLevel = message.metadata?.crisis_level || 'NONE';
  const riskFactors = message.metadata?.risk_factors || [];
  const protectiveFactors = message.metadata?.protective_factors || [];
  const interventions = message.metadata?.immediate_interventions || [];
  const emotionAnalysis = message.metadata?.emotion_analysis || {};

  // Determine crisis indicator
  const getCrisisIndicator = () => {
    if (crisisLevel === 'CRITICAL') {
      return {
        icon: ExclamationTriangleIconSolid,
        color: 'text-red-600 bg-red-100',
        label: 'Crisis Support Available',
        message: 'We noticed you might be going through a difficult time. Support resources are available.'
      };
    } else if (crisisLevel === 'HIGH') {
      return {
        icon: ExclamationTriangleIcon,
        color: 'text-orange-600 bg-orange-100',
        label: 'Support Recommended',
        message: 'Consider reaching out to support resources if you need help.'
      };
    } else if (crisisLevel === 'MODERATE') {
      return {
        icon: HeartIcon,
        color: 'text-blue-600 bg-blue-100',
        label: 'Self-Care Reminder',
        message: 'Remember to take care of yourself and practice self-compassion.'
      };
    }
    return null;
  };

  const crisisIndicator = getCrisisIndicator();

  // Get emotion color
  const getEmotionColor = (emotion) => {
    const emotionColors = {
      'joy': 'text-yellow-600 bg-yellow-100',
      'sadness': 'text-blue-600 bg-blue-100', 
      'anger': 'text-red-600 bg-red-100',
      'fear': 'text-purple-600 bg-purple-100',
      'surprise': 'text-green-600 bg-green-100',
      'neutral': 'text-gray-600 bg-gray-100'
    };
    return emotionColors[emotion] || 'text-gray-600 bg-gray-100';
  };

  // Format message content with enhanced markdown support
  const formatContent = (content) => {
    return (
      <div className="prose prose-sm max-w-none leading-relaxed">
        <ReactMarkdown
          components={{
            p: ({children}) => <p className="mb-2 last:mb-0">{children}</p>,
            ul: ({children}) => <ul className="list-disc list-inside mb-2">{children}</ul>,
            ol: ({children}) => <ol className="list-decimal list-inside mb-2">{children}</ol>,
            li: ({children}) => <li className="mb-1">{children}</li>,
            strong: ({children}) => <strong className="font-semibold">{children}</strong>,
            em: ({children}) => <em className="italic">{children}</em>,
            code: ({children}) => <code className="bg-gray-200 px-1 py-0.5 rounded text-sm">{children}</code>,
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    );
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
      <div className={`flex max-w-[85%] ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start space-x-3`}>
        {/* Enhanced Avatar */}
        <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-lg ${
          isUser 
            ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white' 
            : 'bg-gradient-to-br from-purple-500 via-pink-500 to-blue-500 text-white'
        }`}>
          {isUser ? (
            <UserIcon className="w-5 h-5" />
          ) : (
            <SparklesIcon className="w-5 h-5" />
          )}
        </div>

        {/* Enhanced Message Content */}
        <div className={`flex-1 ${isUser ? 'mr-3' : 'ml-3'}`}>
          {/* Main Message Bubble */}
          <div className={`rounded-2xl px-6 py-4 shadow-sm ${
            isUser 
              ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-br-md border border-blue-500' 
              : 'bg-white text-gray-900 rounded-bl-md border border-gray-200'
          }`}>
            {formatContent(message.content)}
          </div>

          {/* Crisis Detection Indicator */}
          {!isUser && crisisIndicator && (
            <div className={`mt-3 p-3 rounded-lg border ${crisisIndicator.color.replace('text-', 'border-').replace('bg-', '').replace('100', '200')}`}>
              <div className="flex items-start space-x-2">
                <crisisIndicator.icon className={`h-5 w-5 mt-0.5 ${crisisIndicator.color.split(' ')[0]}`} />
                <div className="flex-1">
                  <p className={`text-sm font-medium ${crisisIndicator.color.split(' ')[0]}`}>
                    {crisisIndicator.label}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    {crisisIndicator.message}
                  </p>
                  {interventions.length > 0 && (
                    <div className="mt-2">
                      <button
                        onClick={() => setShowDetails(!showDetails)}
                        className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center"
                      >
                        {showDetails ? 'Hide' : 'View'} Support Resources
                        {showDetails ? (
                          <ChevronUpIcon className="ml-1 h-4 w-4" />
                        ) : (
                          <ChevronDownIcon className="ml-1 h-4 w-4" />
                        )}
                      </button>
                      {showDetails && (
                        <div className="mt-2 space-y-2 text-sm">
                          {interventions.map((intervention, index) => (
                            <div key={index} className="p-2 bg-gray-50 rounded-md">
                              <p className="font-medium">{intervention.intervention_type}</p>
                              <p className="text-gray-600">{intervention.description}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Emotion Analysis */}
          {!isUser && emotionAnalysis.primary_emotion && emotionAnalysis.primary_emotion !== 'neutral' && (
            <div className="mt-2 flex items-center space-x-2">
              <div className={`px-2 py-1 rounded-full text-xs ${getEmotionColor(emotionAnalysis.primary_emotion)}`}>
                {emotionAnalysis.primary_emotion} ({Math.round(emotionAnalysis.confidence * 100)}%)
              </div>
            </div>
          )}

          {/* Context from Recent Entries */}
          {!isUser && contextEntries.length > 0 && (
            <div className="mt-3">
              <button
                onClick={() => setShowContext(!showContext)}
                className="text-xs text-gray-500 hover:text-gray-700 flex items-center"
              >
                <InformationCircleIcon className="h-3 w-3 mr-1" />
                {showContext ? 'Hide' : 'Show'} conversation context
                {showContext ? (
                  <ChevronUpIcon className="ml-1 h-3 w-3" />
                ) : (
                  <ChevronDownIcon className="ml-1 h-3 w-3" />
                )}
              </button>
              
              {showContext && (
                <div className="mt-2 p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <p className="text-xs text-gray-600 mb-2">Referenced from your recent journal entries:</p>
                  <div className="space-y-2">
                    {contextEntries.slice(0, 2).map((entry, index) => (
                      <div key={index} className="text-xs">
                        <p className="font-medium text-gray-700">{entry.title}</p>
                        <p className="text-gray-600 line-clamp-2">
                          {entry.content.substring(0, 100)}...
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Enhanced Timestamp */}
          {message.timestamp && (
            <div className={`flex items-center mt-2 text-xs text-gray-500 ${isUser ? 'justify-end' : 'justify-start'}`}>
              <ClockIcon className="w-3 h-3 mr-1" />
              {formatTime(message.timestamp)}
              {message.metadata?.response_time_ms && (
                <span className="ml-2 opacity-75">
                  • {Math.round(message.metadata.response_time_ms)}ms
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EnhancedChatMessage;