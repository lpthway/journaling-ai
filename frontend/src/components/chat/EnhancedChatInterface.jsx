// frontend/src/components/chat/EnhancedChatInterface.jsx
import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'react-hot-toast';
import { 
  PauseIcon, 
  PlayIcon, 
  PlusIcon,
  ChartBarIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import EnhancedChatMessage from './EnhancedChatMessage';
import ChatInput from './ChatInput';
import SessionTypeSelector from './SessionTypeSelector';
import ContextAwareSuggestions from './ContextAwareSuggestions';
import LoadingSpinner from '../Common/LoadingSpinner';
import { sessionAPI, entryAPI } from '../../services/api';

const EnhancedChatInterface = ({ sessionId = null, onSessionChange }) => {
  const [session, setSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [recentEntries, setRecentEntries] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [showTypeSelector, setShowTypeSelector] = useState(!sessionId);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [contextualSuggestions, setContextualSuggestions] = useState([]);
  
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);

  // Scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Load session and context data
  useEffect(() => {
    if (sessionId) {
      loadSession(sessionId);
    } else {
      setShowTypeSelector(true);
    }
    loadRecentEntries();
  }, [sessionId]);

  const loadRecentEntries = async () => {
    try {
      const response = await entryAPI.getAll({ limit: 10 });
      setRecentEntries(response.data || []);
    } catch (error) {
      console.error('Error loading recent entries:', error);
      setRecentEntries([]);
    }
  };

  const isValidMessage = (msg) => {
    return msg && typeof msg === 'object' && msg.id && msg.role && typeof msg.content === 'string';
  };

  const filterValidMessages = (messageArray) => {
    if (!Array.isArray(messageArray)) {
      return [];
    }
    return messageArray.filter((msg, index) => {
      const valid = isValidMessage(msg);
      if (!valid) {
        console.warn(`EnhancedChatInterface: Invalid message at index ${index}:`, msg);
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
      const validMessages = filterValidMessages(sessionData.recent_messages || []);
      setMessages(validMessages);
      setShowTypeSelector(false);
      
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
      
      // Enhanced context with recent entries
      const enhancedContext = {
        ...context,
        recent_entries_preview: recentEntries.slice(0, 3).map(entry => ({
          title: entry.title,
          mood: entry.mood,
          created_at: entry.created_at,
          tags: entry.tags
        }))
      };

      const response = await sessionAPI.createSession({
        session_type: sessionType,
        title: generateSessionTitle(sessionType, recentEntries),
        metadata: enhancedContext
      });
      
      const newSession = response.data;
      setSession(newSession);
      const validMessages = filterValidMessages(newSession.recent_messages || []);
      setMessages(validMessages);
      setShowTypeSelector(false);
      
      if (onSessionChange) {
        onSessionChange(newSession);
      }
      
      toast.success('Enhanced conversation started!');
    } catch (error) {
      console.error('Error creating session:', error);
      toast.error('Failed to start conversation');
    } finally {
      setIsLoading(false);
    }
  };

  const generateSessionTitle = (sessionType, entries) => {
    const typeLabels = {
      'supportive_listening': 'Supportive Listening Session',
      'therapeutic_guidance': 'Therapeutic Guidance Session',
      'cognitive_reframing': 'Cognitive Reframing Session',
      'mindfulness_coaching': 'Mindfulness Coaching Session',
      'goal_setting': 'Goal Setting Session',
      'crisis_support': 'Crisis Support Session',
      'reflection_facilitation': 'Reflection Session',
      'emotional_processing': 'Emotional Processing Session'
    };

    let title = typeLabels[sessionType] || 'Enhanced Chat Session';
    
    if (entries.length > 0) {
      const latestEntry = entries[0];
      const timeAgo = new Date() - new Date(latestEntry.created_at);
      const hoursAgo = Math.round(timeAgo / (1000 * 60 * 60));
      
      if (hoursAgo < 6) {
        title += ` - Following up on "${latestEntry.title}"`;
      }
    }
    
    return title;
  };

  const sendMessage = async (content, suggestionContext = null) => {
    if (!session || !content.trim()) {
      return;
    }

    const userMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString(),
      metadata: suggestionContext ? { suggestion_context: suggestionContext } : {}
    };

    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);

    try {
      // Enhanced message with context
      const messagePayload = {
        content: content.trim(),
        context: {
          recent_entries: recentEntries.slice(0, 3),
          session_type: session.session_type,
          suggestion_context: suggestionContext
        }
      };

      const response = await sessionAPI.sendMessage(session.id, messagePayload);

      if (response.data && isValidMessage(response.data)) {
        // Enhanced message with crisis detection and emotion analysis
        const enhancedMessage = {
          ...response.data,
          metadata: {
            ...response.data.metadata,
            response_time_ms: response.headers?.['x-response-time'] || null
          }
        };
        
        setMessages(prev => [...prev, enhancedMessage]);

        // Check for crisis indicators and show appropriate toast
        if (enhancedMessage.metadata?.crisis_level === 'CRITICAL') {
          toast.error('Crisis support resources have been provided in the chat', {
            duration: 10000,
            icon: '🚨'
          });
        } else if (enhancedMessage.metadata?.crisis_level === 'HIGH') {
          toast('Support resources are available if you need them', {
            duration: 8000,
            icon: '💙'
          });
        }
      }
      
    } catch (error) {
      console.error('Error sending message:', error);
      toast.error('Failed to send message');
      setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
    } finally {
      setIsTyping(false);
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
      
      if (response.data?.resume_message && isValidMessage(response.data.resume_message)) {
        setMessages(prev => [...prev, response.data.resume_message]);
      }
      
      toast.success('Conversation resumed');
    } catch (error) {
      console.error('Error resuming session:', error);
      toast.error('Failed to resume conversation');
    }
  };

  // Calculate session analytics
  const getSessionAnalytics = () => {
    if (!messages.length) return null;

    const userMessages = messages.filter(m => m.role === 'user');
    const aiMessages = messages.filter(m => m.role === 'assistant');
    
    const emotions = aiMessages
      .map(m => m.metadata?.emotion_analysis?.primary_emotion)
      .filter(Boolean);
    
    const crisisLevels = aiMessages
      .map(m => m.metadata?.crisis_level)
      .filter(level => level && level !== 'NONE');

    return {
      messageCount: messages.length,
      userMessages: userMessages.length,
      aiMessages: aiMessages.length,
      avgMessageLength: userMessages.length > 0 
        ? Math.round(userMessages.reduce((sum, m) => sum + m.content.length, 0) / userMessages.length)
        : 0,
      detectedEmotions: [...new Set(emotions)],
      crisisIndicators: crisisLevels.length
    };
  };

  const analytics = getSessionAnalytics();

  if (showTypeSelector) {
    return (
      <div className="space-y-6">
        {recentEntries.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <InformationCircleIcon className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-blue-900 mb-1">
                  Context-Aware Conversation
                </p>
                <p className="text-sm text-blue-700">
                  The AI will be aware of your recent journal entries to provide more personalized support.
                  Your latest entry: "{recentEntries[0]?.title}"
                </p>
              </div>
            </div>
          </div>
        )}
        
        <SessionTypeSelector
          onSelectType={createSession}
          onCancel={() => setShowTypeSelector(false)}
          isLoading={isLoading}
          recentEntries={recentEntries.slice(0, 2)}
        />
      </div>
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
    <div className="flex flex-col h-full">
      {/* Enhanced Header */}
      {session && (
        <div className="flex-shrink-0 bg-white border-b border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 text-lg">{session.title}</h3>
              <div className="flex items-center space-x-4 text-sm text-gray-500">
                <span className="capitalize">{(session.session_type || session.conversation_mode || 'chat').replace('_', ' ')}</span>
                <span>•</span>
                <span>{session.message_count || messages.length} messages</span>
                {analytics && analytics.crisisIndicators > 0 && (
                  <>
                    <span>•</span>
                    <div className="flex items-center text-orange-600">
                      <ExclamationTriangleIcon className="h-4 w-4 mr-1" />
                      <span>Support provided</span>
                    </div>
                  </>
                )}
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              {analytics && (
                <button
                  onClick={() => setShowAnalytics(!showAnalytics)}
                  className="px-3 py-1 text-sm text-gray-600 hover:text-gray-700 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
                >
                  <ChartBarIcon className="h-4 w-4 inline mr-1" />
                  Insights
                </button>
              )}
              
              {session.status === 'active' ? (
                <button
                  onClick={pauseSession}
                  className="px-3 py-1 text-sm text-orange-600 hover:text-orange-700 border border-orange-200 rounded-md hover:bg-orange-50 transition-colors"
                >
                  <PauseIcon className="h-4 w-4 inline mr-1" />
                  Pause
                </button>
              ) : (
                <button
                  onClick={resumeSession}
                  className="px-3 py-1 text-sm text-green-600 hover:text-green-700 border border-green-200 rounded-md hover:bg-green-50 transition-colors"
                >
                  <PlayIcon className="h-4 w-4 inline mr-1" />
                  Resume
                </button>
              )}
              
              <button
                onClick={() => setShowTypeSelector(true)}
                className="px-3 py-1 text-sm text-blue-600 hover:text-blue-700 border border-blue-200 rounded-md hover:bg-blue-50 transition-colors"
              >
                <PlusIcon className="h-4 w-4 inline mr-1" />
                New Chat
              </button>
            </div>
          </div>

          {/* Analytics Panel */}
          {showAnalytics && analytics && (
            <div className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
              <h4 className="text-sm font-medium text-gray-900 mb-2">Conversation Insights</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Messages</p>
                  <p className="font-medium">{analytics.messageCount}</p>
                </div>
                <div>
                  <p className="text-gray-500">Avg Length</p>
                  <p className="font-medium">{analytics.avgMessageLength} chars</p>
                </div>
                <div>
                  <p className="text-gray-500">Emotions</p>
                  <p className="font-medium">{analytics.detectedEmotions.join(', ') || 'None detected'}</p>
                </div>
                <div>
                  <p className="text-gray-500">Support Level</p>
                  <p className={`font-medium ${analytics.crisisIndicators > 0 ? 'text-orange-600' : 'text-green-600'}`}>
                    {analytics.crisisIndicators > 0 ? 'Active Support' : 'Normal'}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Enhanced Messages Container */}
      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 flex flex-col">
          <div 
            ref={messagesContainerRef}
            className="flex-1 overflow-y-auto p-6 space-y-1"
          >
            {messages.map((message) => (
              <EnhancedChatMessage 
                key={message.id} 
                message={message}
                contextEntries={recentEntries.slice(0, 3)}
              />
            ))}
            
            {isTyping && (
              <EnhancedChatMessage 
                message={null} 
                isTyping={true} 
              />
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Enhanced Input with Context Suggestions */}
          <div className="flex-shrink-0 border-t border-gray-200 bg-white">
            {messages.length === 0 && !isTyping && (
              <div className="p-4 border-b border-gray-100">
                <ContextAwareSuggestions
                  recentEntries={recentEntries}
                  currentMood={recentEntries[0]?.mood}
                  onSuggestionClick={(text, context) => sendMessage(text, context)}
                  isLoading={false}
                />
              </div>
            )}
            
            <ChatInput
              onSendMessage={(content) => sendMessage(content)}
              isLoading={isTyping}
              disabled={session?.status === 'paused'}
              placeholder={
                session?.status === 'paused' 
                  ? "Resume the conversation to continue..." 
                  : "Share what's on your mind..."
              }
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedChatInterface;