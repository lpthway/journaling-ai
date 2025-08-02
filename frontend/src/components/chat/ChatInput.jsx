// frontend/src/components/Chat/ChatInput.jsx

import React, { useState } from 'react';
import { PaperAirplaneIcon } from '@heroicons/react/24/outline';
import LoadingSpinner from '../Common/LoadingSpinner';

const ChatInput = ({ 
  onSendMessage, 
  isLoading = false, 
  suggestions = [], 
  disabled = false,
  placeholder = "Share what's on your mind..."
}) => {
  const [message, setMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmedMessage = message.trim();
    
    if (trimmedMessage && onSendMessage && !isLoading && !disabled) {
      onSendMessage(trimmedMessage);
      setMessage(''); // Clear input after sending
    }
  };

  const handleSuggestionClick = (suggestion) => {
    if (!disabled && !isLoading && onSendMessage) {
      onSendMessage(suggestion);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="border-t border-gray-200 p-4 bg-white">
      {/* Suggestions */}
      {suggestions && suggestions.length > 0 && !disabled && (
        <div className="mb-3">
          <p className="text-xs text-gray-500 mb-2">Suggested responses:</p>
          <div className="flex flex-wrap gap-2">
            {suggestions.slice(0, 3).map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                disabled={isLoading}
                className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="flex items-end space-x-3">
        <div className="flex-1">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            disabled={disabled || isLoading}
            rows={1}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            style={{
              minHeight: '40px',
              maxHeight: '120px',
              height: 'auto'
            }}
            onInput={(e) => {
              // Auto-resize textarea
              e.target.style.height = 'auto';
              e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
            }}
          />
        </div>
        
        <button
          type="submit"
          disabled={!message.trim() || isLoading || disabled}
          className="flex-shrink-0 w-10 h-10 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
        >
          {isLoading ? (
            <LoadingSpinner size="sm" />
          ) : (
            <PaperAirplaneIcon className="w-5 h-5" />
          )}
        </button>
      </form>
    </div>
  );
};

export default ChatInput;
