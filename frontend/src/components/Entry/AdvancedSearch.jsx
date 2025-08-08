import React, { useState, useEffect } from 'react';
import { FunnelIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { entryAPI, topicAPI } from '../../services/api';

// Import decomposed filter components
import TextSearchFilter from './Search/TextSearchFilter';
import MoodTopicFilters from './Search/MoodTopicFilters';
import DateRangeFilter from './Search/DateRangeFilter';
import WordCountFilter from './Search/WordCountFilter';
import TagsFilter from './Search/TagsFilter';
import FavoritesFilter from './Search/FavoritesFilter';
import LimitFilter from './Search/LimitFilter';
import SearchActions from './Search/SearchActions';

const AdvancedSearch = ({ onSearch, onClose, isVisible }) => {
  const [filters, setFilters] = useState({
    query: '',
    mood: '',
    tags: [],
    topic_id: '',
    date_from: '',
    date_to: '',
    word_count_min: '',
    word_count_max: '',
    is_favorite: null,
    limit: 20
  });
  
  const [topics, setTopics] = useState([]);
  const [newTag, setNewTag] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    if (isVisible) {
      loadTopics();
    }
  }, [isVisible]);

  const loadTopics = async () => {
    try {
      const response = await topicAPI.getAll();
      setTopics(response.data);
    } catch (error) {
      console.error('Error loading topics:', error);
    }
  };

  const handleInputChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  };

  const handleAddTag = () => {
    const tag = newTag.trim();
    if (tag && !filters.tags.includes(tag)) {
      setFilters(prev => ({
        ...prev,
        tags: [...prev.tags, tag]
      }));
      setNewTag('');
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    setFilters(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    setIsSearching(true);
    
    try {
      // Clean up filters - remove empty values
      const cleanFilters = Object.fromEntries(
        Object.entries(filters).filter(([key, value]) => {
          if (value === '' || value === null || (Array.isArray(value) && value.length === 0)) {
            return false;
          }
          return true;
        })
      );
      
      await onSearch(cleanFilters);
      onClose();
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleClearFilters = () => {
    setFilters({
      query: '',
      mood: '',
      tags: [],
      topic_id: '',
      date_from: '',
      date_to: '',
      word_count_min: '',
      word_count_max: '',
      is_favorite: null,
      limit: 20
    });
    setNewTag('');
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center">
            <FunnelIcon className="w-5 h-5 mr-2" />
            Advanced Search
          </h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-md transition-colors"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSearch} className="p-6 space-y-6">
          {/* Text Search */}
          <TextSearchFilter
            value={filters.query}
            onChange={handleInputChange}
          />

          {/* Mood and Topic Filters */}
          <MoodTopicFilters
            mood={filters.mood}
            topic_id={filters.topic_id}
            topics={topics}
            onChange={handleInputChange}
          />

          {/* Date Range */}
          <DateRangeFilter
            date_from={filters.date_from}
            date_to={filters.date_to}
            onChange={handleInputChange}
          />

          {/* Word Count Range */}
          <WordCountFilter
            word_count_min={filters.word_count_min}
            word_count_max={filters.word_count_max}
            onChange={handleInputChange}
          />

          {/* Tags */}
          <TagsFilter
            tags={filters.tags}
            newTag={newTag}
            setNewTag={setNewTag}
            onAddTag={handleAddTag}
            onRemoveTag={handleRemoveTag}
          />

          {/* Favorites Filter */}
          <FavoritesFilter
            is_favorite={filters.is_favorite}
            onChange={handleInputChange}
          />

          {/* Results Limit */}
          <LimitFilter
            limit={filters.limit}
            onChange={handleInputChange}
          />

          {/* Actions */}
          <SearchActions
            isSearching={isSearching}
            onClear={handleClearFilters}
            onCancel={onClose}
            onSubmit={handleSearch}
          />
        </form>
      </div>
    </div>
  );
};

export default AdvancedSearch;