import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  PencilIcon, 
  TrashIcon, 
  TagIcon,
  ClockIcon,
  HeartIcon,
  StarIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline';
import { HeartIcon as HeartSolidIcon } from '@heroicons/react/24/solid';
import { toast } from 'react-hot-toast';
import { entryAPI } from '../services/api';
import { formatDate, formatTime, getWordCount } from '../utils/helpers';
import MoodIndicator from '../components/Common/MoodIndicator';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import EntryEditor from '../components/Entry/EntryEditor';

const EntryDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [entry, setEntry] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isTogglingFavorite, setIsTogglingFavorite] = useState(false);

  useEffect(() => {
    loadEntry();
  }, [id]);

  const loadEntry = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await entryAPI.getById(id);
      setEntry(response.data);
    } catch (error) {
      console.error('Error loading entry:', error);
      setError('Failed to load entry');
      toast.error('Failed to load entry');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this entry?')) {
      try {
        await entryAPI.delete(entry.id);
        toast.success('Entry deleted successfully');
        navigate('/');
      } catch (error) {
        console.error('Error deleting entry:', error);
        toast.error('Failed to delete entry');
      }
    }
  };

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleSaveEntry = async (entryData) => {
    try {
      const response = await entryAPI.update(entry.id, entryData);
      setEntry(response.data);
      setIsEditing(false);
      toast.success('Entry updated successfully');
    } catch (error) {
      console.error('Error updating entry:', error);
      toast.error('Failed to update entry');
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
  };

  const handleToggleFavorite = async () => {
    setIsTogglingFavorite(true);
    try {
      const response = await entryAPI.toggleFavorite(entry.id);
      setEntry(response.data);
      toast.success(response.data.is_favorite ? 'Added to favorites' : 'Removed from favorites');
    } catch (error) {
      console.error('Error toggling favorite:', error);
      toast.error('Failed to update favorite status');
    } finally {
      setIsTogglingFavorite(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !entry) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Entry Not Found</h2>
          <p className="text-gray-600 mb-6">{error || 'The entry you are looking for does not exist.'}</p>
          <Link
            to="/"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            <ArrowLeftIcon className="w-4 h-4 mr-2" />
            Back to Journal
          </Link>
        </div>
      </div>
    );
  }

  if (isEditing) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="mb-6">
          <Link
            to="/"
            className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
          >
            <ArrowLeftIcon className="w-4 h-4 mr-1" />
            Back to Journal
          </Link>
        </div>
        <EntryEditor
          entry={entry}
          onSave={handleSaveEntry}
          onCancel={handleCancelEdit}
          saving={false}
        />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <Link
          to="/"
          className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-4"
        >
          <ArrowLeftIcon className="w-4 h-4 mr-1" />
          Back to Journal
        </Link>
        
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-3 mb-2">
              <h1 className="text-3xl font-bold text-gray-900">
                {entry.title}
              </h1>
              {entry.is_favorite && (
                <StarIcon className="w-6 h-6 text-yellow-400 fill-current" />
              )}
              {entry.version > 1 && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                  v{entry.version}
                </span>
              )}
            </div>
            
            <div className="flex items-center space-x-6 text-sm text-gray-500">
              <div className="flex items-center space-x-2">
                <ClockIcon className="w-4 h-4" />
                <span>{formatDate(entry.created_at)}</span>
                <span>•</span>
                <span>{formatTime(entry.created_at)}</span>
              </div>
              <span>•</span>
              <span>{getWordCount(entry.content)} words</span>
              <div className="flex items-center space-x-2">
                <MoodIndicator mood={entry.mood} size="md" />
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2 ml-6">
            {/* Favorite Toggle */}
            <button
              onClick={handleToggleFavorite}
              disabled={isTogglingFavorite}
              className={`p-2 rounded-md transition-colors ${
                entry.is_favorite
                  ? 'text-red-500 hover:text-red-600 hover:bg-red-50'
                  : 'text-gray-400 hover:text-red-500 hover:bg-red-50'
              }`}
              title={entry.is_favorite ? 'Remove from favorites' : 'Add to favorites'}
            >
              {entry.is_favorite ? (
                <HeartSolidIcon className="w-5 h-5" />
              ) : (
                <HeartIcon className="w-5 h-5" />
              )}
            </button>
            <button
              onClick={handleEdit}
              className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
              title="Edit entry"
            >
              <PencilIcon className="w-5 h-5" />
            </button>
            <button
              onClick={handleDelete}
              className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
              title="Delete entry"
            >
              <TrashIcon className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-8">
          <div className="prose max-w-none">
            <div className="text-gray-800 leading-relaxed whitespace-pre-wrap">
              {entry.content}
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-6 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {/* Topic */}
          {entry.topic_id && (
            <div className="flex items-center space-x-2 text-sm text-blue-600">
              <TagIcon className="w-4 h-4" />
              <span>Topic</span>
            </div>
          )}
          
          {/* Tags */}
          {entry.tags && entry.tags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {entry.tags.map((tag, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
        
        {entry.updated_at !== entry.created_at && (
          <div className="text-sm text-gray-500">
            Last updated: {formatDate(entry.updated_at)} at {formatTime(entry.updated_at)}
          </div>
        )}
      </div>
    </div>
  );
};

export default EntryDetail;