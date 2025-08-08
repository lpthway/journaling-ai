// Debug version of ChatMessage for troubleshooting

import React from 'react';
import { UserIcon, SparklesIcon, ClockIcon } from '@heroicons/react/24/outline';
import { formatTime } from '../../utils/helpers';

const ChatMessageDebug = ({ message, isTyping = false }) => {
  // Debug logging
  // Debug logging disabled for production

  // Enhanced safety checks with detailed logging
  if (!message && !isTyping) {
    console.warn('ChatMessage: message is undefined and not typing');
    return (
      <div className="bg-red-100 border border-red-300 text-red-700 px-4 py-3 rounded mb-4">
        <strong>Debug:</strong> Message is undefined and not typing
      </div>
    );
  }

  if (isTyping) {
    // Rendering typing indicator
    return (
      <div className="flex justify-start mb-4">
        <div className="flex max-w-[80%] items-start space-x-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-gradient-to-br from-purple-500 to-pink-500 text-white">
            <SparklesIcon className="w-4 h-4" />
          </div>
          <div className="ml-3">
            <div className="rounded-2xl px-4 py-3 bg-gray-100 text-gray-900 rounded-bl-md">
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Enhanced validation with specific error reporting
  const issues = [];
  if (!message.role) issues.push('missing role');
  if (!message.content) issues.push('missing content');
  if (!message.id) issues.push('missing id');

  if (issues.length > 0) {
    console.error('ChatMessage: Invalid message object:', { message, issues });
    return (
      <div className="bg-yellow-100 border border-yellow-300 text-yellow-700 px-4 py-3 rounded mb-4">
        <strong>Debug:</strong> Message validation failed - {issues.join(', ')}
        <pre className="mt-2 text-xs">{JSON.stringify(message, null, 2)}</pre>
      </div>
    );
  }

  const isUser = message.role === 'user';
  // Rendering valid message

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start space-x-3`}>
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser 
            ? 'bg-blue-600 text-white' 
            : 'bg-gradient-to-br from-purple-500 to-pink-500 text-white'
        }`}>
          {isUser ? (
            <UserIcon className="w-4 h-4" />
          ) : (
            <SparklesIcon className="w-4 h-4" />
          )}
        </div>
        <div className={`${isUser ? 'mr-3' : 'ml-3'}`}>
          <div className={`rounded-2xl px-4 py-3 ${
            isUser 
              ? 'bg-blue-600 text-white rounded-br-md' 
              : 'bg-gray-100 text-gray-900 rounded-bl-md'
          }`}>
            <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
          </div>
          {message.timestamp && (
            <div className={`flex items-center mt-1 text-xs text-gray-500 ${isUser ? 'justify-end' : 'justify-start'}`}>
              <ClockIcon className="w-3 h-3 mr-1" />
              {formatTime(message.timestamp)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatMessageDebug;
