// frontend/src/components/Chat/ChatInterface.jsx

import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'react-hot-toast';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import SessionTypeSelector from './SessionTypeSelector';
import LoadingSpinner from '../Common/LoadingSpinner';
import { sessionAPI } from '../../services/api';

const ChatInterface = ({ sessionId = null, onSessionChange }) => {
  const [session, setSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [showTypeSelector, setShowTypeSelector] = useState(!sessionId);
  
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);

  // Scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Load existing session or show type selector
  useEffect(() => {
    if (sessionId) {
      loadSession(sessionId);
    } else {
      setShowTypeSelector(true);
    }
  }, [sessionId]);

  // Helper function to validate message object
  const isValidMessage = (msg) => {
    return msg && 
           typeof msg === 'object' && 
           msg.id && 
           msg.role && 
           typeof msg.content === 'string';
  };

  // Helper function to filter and validate messages
  const filterValidMessages = (messageArray) => {
    if (!Array.isArray(messageArray)) {
      console.warn('ChatInterface: messages is not an array', messageArray);
      return [];
    }
    
    return messageArray.filter((msg, index) => {
      const valid = isValidMessage(msg);
      if (!valid) {
        console.warn(`ChatInterface: Invalid message at index ${index}:`, msg);
      }
      return valid;
    });
  };

  const loadSession = async (id) => {
    try {
      setIsLoading(true);
      const response = await sessionAPI.getSession(id);
      const sessionData = response.data;
      
      setSession(sessionData);
      
      // Filter and validate messages
      const validMessages = filterValidMessages(sessionData.recent_messages || []);
      setMessages(validMessages);
      setShowTypeSelector(false);
      
      // Load suggestions
      loadSuggestions(id);
    } catch (error) {
      console.error('Error loading session:', error);
      toast.error('Failed to load conversation');
    } finally {
      setIsLoading(false);
    }
  };

  const createSession = async (sessionType, context = {}) => {
    try {
      setIsLoading(true);
      const response = await sessionAPI.createSession({
        session_type: sessionType,
        metadata: context
      });
      
      const newSession = response.data;
      setSession(newSession);
      
      // Filter and validate messages
      const validMessages = filterValidMessages(newSession.recent_messages || []);
      setMessages(validMessages);
      setShowTypeSelector(false);
      
      if (onSessionChange) {
        onSessionChange(newSession);
      }
      
      // Load suggestions for new session
      loadSuggestions(newSession.id);
      
      toast.success('Conversation started!');
    } catch (error) {
      console.error('Error creating session:', error);
      toast.error('Failed to start conversation');
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async (content) => {
    if (!session || !content.trim()) {
      console.warn('ChatInterface: Cannot send message - no session or empty content');
      return;
    }

    const userMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString()
    };

    // Add user message immediately
    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);

    try {
      const response = await sessionAPI.sendMessage(session.id, {
        content: content.trim()
      });

      // Validate and add AI response
      if (response.data && isValidMessage(response.data)) {
        setMessages(prev => [...prev, response.data]);
      } else {
        console.error('ChatInterface: Invalid AI response:', response.data);
        toast.error('Received invalid response from AI');
      }
      
      // Refresh suggestions
      loadSuggestions(session.id);
      
    } catch (error) {
      console.error('Error sending message:', error);
      toast.error('Failed to send message');
      
      // Remove user message on error
      setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
    } finally {
      setIsTyping(false);
    }
  };

  const loadSuggestions = async (sessionId) => {
    try {
      const response = await sessionAPI.getSuggestions(sessionId);
      const suggestionData = response.data;
      
      if (suggestionData && Array.isArray(suggestionData.suggestions)) {
        setSuggestions(suggestionData.suggestions);
      } else {
        setSuggestions([]);
      }
    } catch (error) {
      console.error('Error loading suggestions:', error);
      // Don't show error for suggestions, just fail silently
      setSuggestions([]);
    }
  };

  const pauseSession = async () => {
    if (!session) return;
    
    try {
      await sessionAPI.pauseSession(session.id);
      setSession(prev => ({ ...prev, status: 'paused' }));
      toast.success('Conversation paused');
    } catch (error) {
      console.error('Error pausing session:', error);
      toast.error('Failed to pause conversation');
    }
  };

  const resumeSession = async () => {
    if (!session) return;
    
    try {
      const response = await sessionAPI.resumeSession(session.id);
      setSession(prev => ({ ...prev, status: 'active' }));
      
      // Add resume message if provided and valid
      if (response.data && response.data.resume_message && isValidMessage(response.data.resume_message)) {
        setMessages(prev => [...prev, response.data.resume_message]);
      }
      
      toast.success('Conversation resumed');
    } catch (error) {
      console.error('Error resuming session:', error);
      toast.error('Failed to resume conversation');
    }
  };

  if (showTypeSelector) {
    return (
      <SessionTypeSelector
        onSelectType={createSession}
        onCancel={() => setShowTypeSelector(false)}
        isLoading={isLoading}
      />
    );
  }

  if (isLoading && !session) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      {session && (
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div>
            <h3 className="font-semibold text-gray-900">{session.title}</h3>
            <p className="text-sm text-gray-500 capitalize">
              {session.session_type.replace('_', ' ')} • {session.message_count} messages
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            {session.status === 'active' ? (
              <button
                onClick={pauseSession}
                className="px-3 py-1 text-sm text-orange-600 hover:text-orange-700 border border-orange-200 rounded-md hover:bg-orange-50 transition-colors"
              >
                Pause
              </button>
            ) : (
              <button
                onClick={resumeSession}
                className="px-3 py-1 text-sm text-green-600 hover:text-green-700 border border-green-200 rounded-md hover:bg-green-50 transition-colors"
              >
                Resume
              </button>
            )}
            
            <button
              onClick={() => setShowTypeSelector(true)}
              className="px-3 py-1 text-sm text-blue-600 hover:text-blue-700 border border-blue-200 rounded-md hover:bg-blue-50 transition-colors"
            >
              New Chat
            </button>
          </div>
        </div>
      )}

      {/* Messages Container */}
      <div 
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4"
        style={{ minHeight: '400px', maxHeight: '600px' }}
      >
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        
        {/* Typing Indicator */}
        {isTyping && (
          <ChatMessage 
            message={null} 
            isTyping={true} 
          />
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput
        onSendMessage={sendMessage}
        isLoading={isTyping}
        suggestions={suggestions}
        disabled={session?.status === 'paused'}
        placeholder={
          session?.status === 'paused' 
            ? "Resume the conversation to continue..." 
            : "Share what's on your mind..."
        }
      />
    </div>
  );
};

export default ChatInterface;
