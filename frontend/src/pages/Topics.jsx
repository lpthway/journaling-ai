import React, { useState, useEffect } from 'react';
import { PlusIcon, TagIcon, PencilIcon, TrashIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { topicAPI, entryAPI } from '../services/api';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import EmptyState from '../components/Common/EmptyState';
import { formatDate, getTopicColor } from '../utils/helpers';

const Topics = () => {
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingTopic, setEditingTopic] = useState(null);
  const [savingTopic, setSavingTopic] = useState(false);

  const colorOptions = [
    '#3B82F6', '#10B981', '#F59E0B', '#EF4444',
    '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'
  ];

  useEffect(() => {
    loadTopics();
  }, []);

  const loadTopics = async () => {
    try {
      const response = await topicAPI.getAll();
      setTopics(response.data);
    } catch (error) {
      console.error('Error loading topics:', error);
      toast.error('Failed to load topics');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTopic = () => {
    setEditingTopic(null);
    setShowCreateForm(true);
  };

  const handleEditTopic = (topic) => {
    setEditingTopic(topic);
    setShowCreateForm(true);
  };

  const handleDeleteTopic = async (topicId) => {
    if (!window.confirm('Are you sure you want to delete this topic? This will not delete the entries.')) {
      return;
    }

    try {
      await topicAPI.delete(topicId);
      setTopics(prev => prev.filter(topic => topic.id !== topicId));
      toast.success('Topic deleted successfully');
    } catch (error) {
      console.error('Error deleting topic:', error);
      toast.error('Failed to delete topic');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Topics</h1>
          <p className="mt-1 text-sm text-gray-500">
            Organize your thoughts into custom topics and threads
          </p>
        </div>
        
        <button
          onClick={handleCreateTopic}
          className="mt-4 sm:mt-0 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
        >
          <PlusIcon className="w-4 h-4 mr-2" />
          New Topic
        </button>
      </div>

      {/* Topics Grid */}
      {topics.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {topics.map(topic => (
            <TopicCard
              key={topic.id}
              topic={topic}
              onEdit={handleEditTopic}
              onDelete={handleDeleteTopic}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          icon={TagIcon}
          title="No topics yet"
          description="Create topics to organize your journal entries into themes, projects, or areas of focus."
          action={
            <button
              onClick={handleCreateTopic}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Create your first topic
            </button>
          }
        />
      )}

      {/* Topic Form Modal */}
      {showCreateForm && (
        <TopicForm
          topic={editingTopic}
          onSave={async (topicData) => {
            try {
              setSavingTopic(true);
              
              if (editingTopic) {
                const response = await topicAPI.update(editingTopic.id, topicData);
                setTopics(prev => prev.map(topic => 
                  topic.id === editingTopic.id ? response.data : topic
                ));
                toast.success('Topic updated successfully!');
              } else {
                const response = await topicAPI.create(topicData);
                setTopics(prev => [response.data, ...prev]);
                toast.success('Topic created successfully!');
              }
              
              setShowCreateForm(false);
              setEditingTopic(null);
            } catch (error) {
              console.error('Error saving topic:', error);
              toast.error('Failed to save topic');
            } finally {
              setSavingTopic(false);
            }
          }}
          onCancel={() => {
            setShowCreateForm(false);
            setEditingTopic(null);
          }}
          isLoading={savingTopic}
          colorOptions={colorOptions}
        />
      )}
    </div>
  );
};

// Topic Card Component
const TopicCard = ({ topic, onEdit, onDelete }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow duration-200">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className={`w-4 h-4 rounded-full ${getTopicColor(topic.color)}`} />
            <h3 className="text-lg font-semibold text-gray-900 truncate">
              {topic.name}
            </h3>
          </div>
          
          <div className="flex space-x-1">
            <button
              onClick={() => onEdit(topic)}
              className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
              title="Edit topic"
            >
              <PencilIcon className="w-4 h-4" />
            </button>
            <button
              onClick={() => onDelete(topic.id)}
              className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
              title="Delete topic"
            >
              <TrashIcon className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Description */}
        {topic.description && (
          <p className="text-gray-600 text-sm mb-4 line-clamp-2">
            {topic.description}
          </p>
        )}

        {/* Stats */}
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>{topic.entry_count} entries</span>
          {topic.last_entry_date && (
            <span>Last: {formatDate(topic.last_entry_date)}</span>
          )}
        </div>

        {/* Tags */}
        {topic.tags && topic.tags.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1">
            {topic.tags.slice(0, 3).map((tag, index) => (
              <span
                key={index}
                className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
              >
                {tag}
              </span>
            ))}
            {topic.tags.length > 3 && (
              <span className="text-xs text-gray-500">
                +{topic.tags.length - 3} more
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Topic Form Component
const TopicForm = ({ 
  topic = null, 
  onSave, 
  onCancel, 
  isLoading = false, 
  colorOptions = [] 
}) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    color: '#3B82F6',
    tags: []
  });
  const [newTag, setNewTag] = useState('');
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (topic) {
      setFormData({
        name: topic.name || '',
        description: topic.description || '',
        color: topic.color || '#3B82F6',
        tags: topic.tags || []
      });
    }
  }, [topic]);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
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
    
    if (!formData.name.trim()) {
      setErrors({ name: 'Topic name is required' });
      return;
    }

    onSave(formData);
  };

  const isEditing = !!topic;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            {isEditing ? 'Edit Topic' : 'New Topic'}
          </h2>
          <button
            onClick={onCancel}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-md transition-colors"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Name */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
              Name *
            </label>
            <input
              type="text"
              id="name"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              placeholder="e.g., Personal Growth, Work Projects"
              className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                errors.name ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {errors.name && (
              <p className="mt-1 text-sm text-red-600">{errors.name}</p>
            )}
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              id="description"
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              placeholder="Optional description for this topic"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            />
          </div>

          {/* Color */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Color
            </label>
            <div className="flex space-x-2">
              {colorOptions.map(color => (
                <button
                  key={color}
                  type="button"
                  onClick={() => handleInputChange('color', color)}
                  className={`w-8 h-8 rounded-full border-2 transition-all ${
                    formData.color === color 
                      ? 'border-gray-800 scale-110' 
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                  style={{ backgroundColor: color }}
                />
              ))}
            </div>
          </div>

          {/* Tags */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tags
            </label>
            
            <div className="flex space-x-2 mb-3">
              <input
                type="text"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAddTag(e)}
                placeholder="Add a tag"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              />
              <button
                type="button"
                onClick={handleAddTag}
                className="px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors text-sm"
              >
                Add
              </button>
            </div>

            {formData.tags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {formData.tags.map((tag, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800"
                  >
                    {tag}
                    <button
                      type="button"
                      onClick={() => handleRemoveTag(tag)}
                      className="ml-1 text-blue-600 hover:text-blue-800"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
            >
              {isLoading && <LoadingSpinner size="sm" />}
              <span>{isEditing ? 'Update Topic' : 'Create Topic'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Topics;