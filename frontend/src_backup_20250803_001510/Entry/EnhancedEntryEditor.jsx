// frontend/src/components/Entry/EnhancedEntryEditor.jsx

import React, { useState, useEffect } from 'react';
import { 
  XMarkIcon, 
  TagIcon, 
  HashtagIcon, 
  ChatBubbleLeftRightIcon,
  DocumentTextIcon,
  SwitchHorizontalIcon 
} from '@heroicons/react/24/outline';
import { validateEntry, getWordCount } from '../../utils/helpers';
import LoadingSpinner from '../Common/LoadingSpinner';
import ChatInterface from './ChatInterface';

const EnhancedEntryEditor = ({ 
  entry = null, 
  onSave, 
  onCancel, 
  topics = [], 
  isLoading = false 
}) => {
  const [mode, setMode] = useState('traditional'); // 'traditional' or 'chat'
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    entry_type: 'journal',
    topic_id: '',
    tags: []
  });
  const [errors, setErrors] = useState({});
  const [newTag, setNewTag] = useState('');
  const [currentSession, setCurrentSession] = useState(null);

  // Initialize form data when entry changes
  useEffect(() => {
    if (entry) {
      setFormData({
        title: entry.title || '',
        content: entry.content || '',
        entry_type: entry.entry_type || 'journal',
        topic_id: entry.topic_id || '',
        tags: entry.tags || []
      });
    }
  }, [entry]);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  const handleAddTag = (e) => {
    e.preventDefault();
    const tag = newTag.trim();
    if (tag && !formData.tags.includes(tag)) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, tag]
      }));
      setNewTag('');
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    const validation = validateEntry(formData);
    if (!validation.isValid) {
      setErrors(validation.errors);
      return;
    }

    onSave(formData);
  };

  const handleModeSwitch = (newMode) => {
    setMode(newMode);
  };

  const handleSessionChange = (session) => {
    setCurrentSession(session);
    
    // Auto-populate title and content from chat if switching to traditional mode
    if (session && mode === 'traditional') {
      if (!formData.title) {
        setFormData(prev => ({ ...prev, title: session.title }));
      }
    }
  };

  const extractContentFromChat = () => {
    // This would extract meaningful content from the chat session
    // For now, we'll just use the session title
    return currentSession?.title || '';
  };

  const wordCount = getWordCount(formData.content);
  const isEditing = !!entry;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <h2 className="text-xl font-semibold text-gray-900">
              {isEditing ? 'Edit Entry' : 'New Entry'}
            </h2>
            
            {/* Mode Toggle */}
            <div className="flex items-center space-x-2 bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => handleModeSwitch('traditional')}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  mode === 'traditional'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <DocumentTextIcon className="w-4 h-4" />
                <span>Traditional</span>
              </button>
              <button
                onClick={() => handleModeSwitch('chat')}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  mode === 'chat'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <ChatBubbleLeftRightIcon className="w-4 h-4" />
                <span>AI Chat</span>
              </button>
            </div>
          </div>
          
          <button
            onClick={onCancel}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-md transition-colors"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 flex overflow-hidden">
          {mode === 'chat' ? (
            /* Chat Mode */
            <div className="flex-1 flex flex-col">
              <ChatInterface onSessionChange={handleSessionChange} />
              
              {/* Chat to Entry Conversion */}
              {currentSession && (
                <div className="border-t border-gray-200 p-4 bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        Ready to save as journal entry?
                      </p>
                      <p className="text-xs text-gray-500">
                        Convert your conversation into a traditional journal entry
                      </p>
                    </div>
                    <button
                      onClick={() => {
                        setMode('traditional');
                        if (!formData.content) {
                          setFormData(prev => ({ 
                            ...prev, 
                            content: extractContentFromChat(),
                            title: currentSession.title
                          }));
                        }
                      }}
                      className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                    >
                      <SwitchHorizontalIcon className="w-4 h-4" />
                      <span>Convert to Entry</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* Traditional Mode */
            <form onSubmit={handleSubmit} className="flex-1 flex flex-col">
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {/* Title */}
                <div>
                  <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                    Title
                  </label>
                  <input
                    type="text"
                    id="title"
                    value={formData.title}
                    onChange={(e) => handleInputChange('title', e.target.value)}
                    placeholder="What's on your mind?"
                    className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      errors.title ? 'border-red-300' : 'border-gray-300'
                    }`}
                  />
                  {errors.title && (
                    <p className="mt-1 text-sm text-red-600">{errors.title}</p>
                  )}
                </div>

                {/* Entry Type and Topic */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="entry_type" className="block text-sm font-medium text-gray-700 mb-2">
                      Type
                    </label>
                    <select
                      id="entry_type"
                      value={formData.entry_type}
                      onChange={(e) => handleInputChange('entry_type', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="journal">Journal Entry</option>
                      <option value="topic">Topic Entry</option>
                    </select>
                  </div>

                  {formData.entry_type === 'topic' && (
                    <div>
                      <label htmlFor="topic_id" className="block text-sm font-medium text-gray-700 mb-2">
                        Topic
                      </label>
                      <select
                        id="topic_id"
                        value={formData.topic_id}
                        onChange={(e) => handleInputChange('topic_id', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        <option value="">Select a topic</option>
                        {topics.map(topic => (
                          <option key={topic.id} value={topic.id}>
                            {topic.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                </div>

                {/* Content */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label htmlFor="content" className="block text-sm font-medium text-gray-700">
                      Content
                    </label>
                    <div className="flex items-center space-x-4">
                      <span className="text-sm text-gray-500">
                        {wordCount} words
                      </span>
                      {currentSession && (
                        <button
                          type="button"
                          onClick={() => setMode('chat')}
                          className="text-sm text-blue-600 hover:text-blue-700 flex items-center space-x-1"
                        >
                          <ChatBubbleLeftRightIcon className="w-4 h-4" />
                          <span>Continue in chat</span>
                        </button>
                      )}
                    </div>
                  </div>
                  <textarea
                    id="content"
                    value={formData.content}
                    onChange={(e) => handleInputChange('content', e.target.value)}
                    placeholder="Start writing your thoughts... or switch to chat mode for AI assistance"
                    rows={12}
                    className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none ${
                      errors.content ? 'border-red-300' : 'border-gray-300'
                    }`}
                  />
                  {errors.content && (
                    <p className="mt-1 text-sm text-red-600">{errors.content}</p>
                  )}
                </div>

                {/* Tags */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tags
                  </label>
                  
                  {/* Add new tag */}
                  <div className="flex space-x-2 mb-3">
                    <div className="flex-1 relative">
                      <HashtagIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <input
                        type="text"
                        value={newTag}
                        onChange={(e) => setNewTag(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleAddTag(e)}
                        placeholder="Add a tag"
                        className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <button
                      type="button"
                      onClick={handleAddTag}
                      className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
                    >
                      Add
                    </button>
                  </div>

                  {/* Existing tags */}
                  {formData.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {formData.tags.map((tag, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                        >
                          {tag}
                          <button
                            type="button"
                            onClick={() => handleRemoveTag(tag)}
                            className="ml-2 text-blue-600 hover:text-blue-800"
                          >
                            <XMarkIcon className="w-3 h-3" />
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200 bg-gray-50">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
                >
                  {isLoading && <LoadingSpinner size="sm" />}
                  <span>{isEditing ? 'Update Entry' : 'Save Entry'}</span>
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default EnhancedEntryEditor;