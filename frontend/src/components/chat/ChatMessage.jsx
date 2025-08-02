// frontend/src/components/Chat/ChatMessage.jsx

import React from 'react';
import { UserIcon, SparklesIcon, ClockIcon } from '@heroicons/react/24/outline';
import { formatTime } from '../../utils/helpers';

const ChatMessage = ({ message, isTyping = false }) => {
  // Safety check - return null if message is undefined
  if (!message && !isTyping) {
    return null;
  }

  const isUser = message?.role === 'user';
  const isAssistant = message?.role === 'assistant';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start space-x-3`}>
        {/* Avatar */}
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

        {/* Message Content */}
        <div className={`${isUser ? 'mr-3' : 'ml-3'}`}>
          <div className={`rounded-2xl px-4 py-3 ${
            isUser 
              ? 'bg-blue-600 text-white rounded-br-md' 
              : 'bg-gray-100 text-gray-900 rounded-bl-md'
          } ${isTyping ? 'animate-pulse' : ''}`}>
            {isTyping ? (
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            ) : (
              <p className="whitespace-pre-wrap leading-relaxed">{message?.content || ''}</p>
            )}
          </div>
          
          {/* Timestamp */}
          {!isTyping && message?.timestamp && (
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

export default ChatMessage;