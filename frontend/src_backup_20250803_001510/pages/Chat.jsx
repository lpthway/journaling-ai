// frontend/src/pages/Chat.jsx

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ChatBubbleLeftRightIcon, 
  PlusIcon, 
  ClockIcon,
  UserIcon 
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import ChatInterface from './ChatInterface';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import EmptyState from '../components/Common/EmptyState';
import { sessionAPI } from '../services/api';
import { formatDate, formatTime } from '../utils/helpers';

const Chat = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showSidebar, setShowSidebar] = useState(true);

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    if (sessionId && sessions.length > 0) {
      const session = sessions.find(s => s.id === sessionId);
      if (session) {
        setCurrentSession(session);
      } else {
        // Session not found, redirect to chat home
        navigate('/chat');
      }
    }
  }, [sessionId, sessions, navigate]);

  const loadSessions = async () => {
    try {
      setLoading(true);
      const response = await sessionAPI.getSessions({ limit: 50 });
      setSessions(response.data);
    } catch (error) {
      console.error('Error loading sessions:', error);
      toast.error('Failed to load conversations');
    } finally {
      setLoading(false);
    }
  };

  const handleNewSession = () => {
    navigate('/chat');
    setCurrentSession(null);
  };

  const handleSessionSelect = (session) => {
    navigate(`/chat/${session.id}`);
  };

  const handleSessionChange = (newSession) => {
    setCurrentSession(newSession);
    setSessions(prev => [newSession, ...prev.filter(s => s.id !== newSession.id)]);
    navigate(`/chat/${newSession.id}`);
  };

  const handleDeleteSession = async (sessionToDelete) => {
    if (!window.confirm('Are you sure you want to delete this conversation?')) {
      return;
    }

    try {
      await sessionAPI.deleteSession(sessionToDelete.id);
      setSessions(prev => prev.filter(s => s.id !== sessionToDelete.id));
      
      if (currentSession?.id === sessionToDelete.id) {
        navigate('/chat');
        setCurrentSession(null);
      }
      
      toast.success('Conversation deleted');
    } catch (error) {
      console.error('Error deleting session:', error);
      toast.error('Failed to delete conversation');
    }
  };

  const getSessionTypeIcon = (sessionType) => {
    const icons = {
      'reflection_buddy': '💭',
      'inner_voice': '🧠',
      'growth_challenge': '🌱',
      'pattern_detective': '🔍',
      'free_chat': '💬'
    };
    return icons[sessionType] || '💬';
  };

  const getSessionTypeName = (sessionType) => {
    const names = {
      'reflection_buddy': 'Reflection Buddy',
      'inner_voice': 'Inner Voice',
      'growth_challenge': 'Growth Challenge',
      'pattern_detective': 'Pattern Detective',
      'free_chat': 'Free Chat'
    };
    return names[sessionType] || 'Conversation';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Sidebar */}
      {showSidebar && (
        <div className="w-80 border-r border-gray-200 flex flex-col">
          {/* Header */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Conversations</h2>
              <button
                onClick={handleNewSession}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-blue-600 bg-blue-50 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                <PlusIcon className="w-4 h-4 mr-1" />
                New Chat
              </button>
            </div>
          </div>

          {/* Sessions List */}
          <div className="flex-1 overflow-y-auto">
            {sessions.length > 0 ? (
              <div className="divide-y divide-gray-200">
                {sessions.map((session) => (
                  <SessionItem
                    key={session.id}
                    session={session}
                    isActive={currentSession?.id === session.id}
                    onClick={() => handleSessionSelect(session)}
                    onDelete={() => handleDeleteSession(session)}
                    getTypeIcon={getSessionTypeIcon}
                    getTypeName={getSessionTypeName}
                  />
                ))}
              </div>
            ) : (
              <div className="p-4">
                <EmptyState
                  icon={ChatBubbleLeftRightIcon}
                  title="No conversations yet"
                  description="Start your first AI-guided conversation to begin your journaling journey."
                  action={
                    <button
                      onClick={handleNewSession}
                      className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                    >
                      <PlusIcon className="w-4 h-4 mr-2" />
                      Start First Conversation
                    </button>
                  }
                />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {currentSession || !sessionId ? (
          <ChatInterface 
            sessionId={sessionId} 
            onSessionChange={handleSessionChange}
          />
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <EmptyState
              icon={ChatBubbleLeftRightIcon}
              title="Select a conversation"
              description="Choose a conversation from the sidebar or start a new one."
              action={
                <button
                  onClick={handleNewSession}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                >
                  <PlusIcon className="w-4 h-4 mr-2" />
                  New Conversation
                </button>
              }
            />
          </div>
        )}
      </div>
    </div>
  );
};

// Session Item Component
const SessionItem = ({ 
  session, 
  isActive, 
  onClick, 
  onDelete, 
  getTypeIcon, 
  getTypeName 
}) => {
  const [showMenu, setShowMenu] = useState(false);

  const getLastMessage = () => {
    if (session.recent_messages && session.recent_messages.length > 0) {
      const lastMessage = session.recent_messages[session.recent_messages.length - 1];
      return lastMessage.content.length > 60 
        ? lastMessage.content.substring(0, 60) + '...'
        : lastMessage.content;
    }
    return 'No messages yet';
  };

  const getStatusColor = () => {
    const colors = {
      'active': 'text-green-600',
      'paused': 'text-orange-600',
      'completed': 'text-gray-600'
    };
    return colors[session.status] || 'text-gray-600';
  };

  return (
    <div
      className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors relative ${
        isActive ? 'bg-blue-50 border-r-2 border-blue-600' : ''
      }`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-1">
            <span className="text-lg">{getTypeIcon(session.session_type)}</span>
            <h3 className="text-sm font-medium text-gray-900 truncate">
              {session.title}
            </h3>
          </div>
          
          <p className="text-xs text-gray-500 mb-2">
            {getTypeName(session.session_type)} • {session.message_count} messages
          </p>
          
          <p className="text-sm text-gray-600 line-clamp-2 mb-2">
            {getLastMessage()}
          </p>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs text-gray-500">
              <ClockIcon className="w-3 h-3" />
              <span>{formatDate(session.last_activity)}</span>
            </div>
            
            <span className={`text-xs font-medium capitalize ${getStatusColor()}`}>
              {session.status}
            </span>
          </div>
        </div>
        
        {/* Menu Button */}
        <div className="relative">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowMenu(!showMenu);
            }}
            className="p-1 text-gray-400 hover:text-gray-600 rounded"
          >
            ⋮
          </button>
          
          {showMenu && (
            <div className="absolute right-0 top-6 w-32 bg-white border border-gray-200 rounded-md shadow-lg z-10">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete();
                  setShowMenu(false);
                }}
                className="block w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50"
              >
                Delete
              </button>
            </div>
          )}
        </div>
      </div>
      
      {/* Close menu when clicking outside */}
      {showMenu && (
        <div
          className="fixed inset-0 z-5"
          onClick={() => setShowMenu(false)}
        />
      )}
    </div>
  );
};

export default Chat;