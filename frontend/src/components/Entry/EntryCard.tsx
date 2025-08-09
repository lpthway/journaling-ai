import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  PencilIcon, 
  TrashIcon, 
  TagIcon,
  ClockIcon,
  HeartIcon,
  StarIcon
} from '@heroicons/react/24/outline';
import { HeartIcon as HeartSolidIcon } from '@heroicons/react/24/solid';
import { formatDate, formatTime, truncateText, getWordCount } from '../../utils/helpers';
import MoodIndicator from '../Common/MoodIndicator';
import { entryAPI } from '../../services/api';
import { toast } from 'react-hot-toast';
import { Entry } from '../../types';

interface EntryCardProps {
  entry: Entry;
  onEdit: (entry: Entry) => void;
  onDelete: (id: string) => void;
  onToggleFavorite?: (entry: Entry) => void;
  showTopic?: boolean;
}

const EntryCard: React.FC<EntryCardProps> = ({ 
  entry, 
  onEdit, 
  onDelete, 
  onToggleFavorite, 
  showTopic = true 
}) => {
  const navigate = useNavigate();
  const [isTogglingFavorite, setIsTogglingFavorite] = useState<boolean>(false);

  const handleDelete = (e: React.MouseEvent<HTMLButtonElement>): void => {
    e.preventDefault();
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this entry?')) {
      onDelete(entry.id);
    }
  };

  const handleEdit = (e: React.MouseEvent<HTMLButtonElement>): void => {
    e.preventDefault();
    e.stopPropagation();
    onEdit(entry);
  };

  const handleToggleFavorite = async (e: React.MouseEvent<HTMLButtonElement>): Promise<void> => {
    e.preventDefault();
    e.stopPropagation();
    
    setIsTogglingFavorite(true);
    try {
      const response = await entryAPI.toggleFavorite(entry.id);
      if (onToggleFavorite) {
        onToggleFavorite(response.data);
      }
      toast.success(response.data.is_favorite ? 'Added to favorites' : 'Removed from favorites');
    } catch (error) {
      console.error('Error toggling favorite:', error);
      toast.error('Failed to update favorite status');
    } finally {
      setIsTogglingFavorite(false);
    }
  };

  const handleReadMore = (e: React.MouseEvent<HTMLButtonElement>): void => {
    e.preventDefault();
    e.stopPropagation();
    navigate(`/entry/${entry.id}`);
  };

  return (
    <article 
      className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 hover:scale-[1.01] animate-fade-in"
      aria-labelledby={`entry-title-${entry.id}`}
      role="article"
    >
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2">
              <h3 
                id={`entry-title-${entry.id}`}
                className="text-lg font-semibold text-gray-900 truncate"
              >
                {entry.title}
              </h3>
              {entry.is_favorite && (
                <StarIcon className="w-5 h-5 text-yellow-400 fill-current" />
              )}
              {entry.version > 1 && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  v{entry.version}
                </span>
              )}
            </div>
            <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500">
              <div className="flex items-center space-x-1">
                <ClockIcon className="w-4 h-4" />
                <span>{formatDate(entry.created_at)}</span>
                <span>•</span>
                <span>{formatTime(entry.created_at)}</span>
              </div>
              <span>•</span>
              <span>{getWordCount(entry.content)} words</span>
            </div>
          </div>
          
          <div className="flex items-center space-x-2 ml-4">
            <MoodIndicator mood={entry.mood} size="md" />
            <div className="flex space-x-1">
              {/* Favorite Toggle */}
              <button
                onClick={handleToggleFavorite}
                disabled={isTogglingFavorite}
                className={`p-1.5 rounded-md transition-all duration-200 transform hover:scale-110 focus:scale-110 ${
                  entry.is_favorite
                    ? 'text-red-500 hover:text-red-600 hover:bg-red-50'
                    : 'text-gray-400 hover:text-red-500 hover:bg-red-50'
                }`}
                title={entry.is_favorite ? 'Remove from favorites' : 'Add to favorites'}
                aria-label={entry.is_favorite ? 'Remove from favorites' : 'Add to favorites'}
                aria-pressed={entry.is_favorite}
              >
                {entry.is_favorite ? (
                  <HeartSolidIcon className="w-4 h-4" />
                ) : (
                  <HeartIcon className="w-4 h-4" />
                )}
              </button>
              <button
                onClick={handleEdit}
                className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-all duration-200 transform hover:scale-110 focus:scale-110"
                title="Edit entry"
                aria-label="Edit entry"
              >
                <PencilIcon className="w-4 h-4" />
              </button>
              <button
                onClick={handleDelete}
                className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-all duration-200 transform hover:scale-110 focus:scale-110"
                title="Delete entry"
                aria-label="Delete entry"
              >
                <TrashIcon className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Content Preview */}
        <div className="mb-4">
          <p className="text-gray-700 leading-relaxed">
            {truncateText(entry.content, 200)}
          </p>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {/* Topic */}
            {showTopic && entry.topic_id && (
              <div className="flex items-center space-x-1 text-sm text-blue-600">
                <TagIcon className="w-4 h-4" />
                <span>Topic</span>
              </div>
            )}
            
            {/* Tags */}
            {entry.tags && entry.tags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {entry.tags.slice(0, 3).map((tag, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                  >
                    {tag}
                  </span>
                ))}
                {entry.tags.length > 3 && (
                  <span className="text-xs text-gray-500">
                    +{entry.tags.length - 3} more
                  </span>
                )}
              </div>
            )}
          </div>

          <button
            onClick={handleReadMore}
            className="text-sm font-medium text-blue-600 hover:text-blue-700 transition-all duration-200 hover:translate-x-1"
            aria-label={`Read more about ${entry.title}`}
          >
            Read more →
          </button>
        </div>
      </div>
    </article>
  );
};

export default EntryCard;