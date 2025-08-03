import React, { useState, useEffect } from 'react';
import { PlusIcon, BookOpenIcon, CalendarIcon, FunnelIcon, DocumentTextIcon, HeartIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { entryAPI, topicAPI } from '../services/api';
import EntryCard from '../components/Entry/EntryCard';
import EntryEditor from '../components/Entry/EntryEditor';
import AdvancedSearch from '../components/Entry/AdvancedSearch';
import EntryTemplates from '../components/Entry/EntryTemplates';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import EmptyState from '../components/Common/EmptyState';
import MoodIndicator from '../components/Common/MoodIndicator';

const Journal = ({ searchQuery = null }) => {
  const [entries, setEntries] = useState([]);
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showEditor, setShowEditor] = useState(false);
  const [showAdvancedSearch, setShowAdvancedSearch] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const [editingEntry, setEditingEntry] = useState(null);
  const [savingEntry, setSavingEntry] = useState(false);
  const [activeView, setActiveView] = useState('all'); // all, favorites
  const [searchResults, setSearchResults] = useState(null);
  const [filters, setFilters] = useState({
    mood: '',
    topic: '',
    dateRange: '30' // days
  });

  // Load data on component mount
  useEffect(() => {
    loadData();
  }, []);

  // Handle search
  useEffect(() => {
    if (searchQuery) {
      handleSearch(searchQuery);
    } else {
      loadEntries();
    }
  }, [searchQuery]);

  const loadData = async () => {
    try {
      const [entriesResponse, topicsResponse] = await Promise.all([
        entryAPI.getAll({ limit: 50 }),
        topicAPI.getAll()
      ]);
      
      setEntries(entriesResponse.data);
      setTopics(topicsResponse.data);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load journal data');
    } finally {
      setLoading(false);
    }
  };

  const loadEntries = async () => {
    try {
      setLoading(true);
      let response;
      
      if (activeView === 'favorites') {
        response = await entryAPI.getFavorites(50);
        setEntries(response.data);
      } else {
        const params = { limit: 50 };
        
        // Apply filters
        if (filters.topic) {
          params.topic_id = filters.topic;
        }
        
        if (filters.dateRange) {
          const days = parseInt(filters.dateRange);
          const dateFrom = new Date();
          dateFrom.setDate(dateFrom.getDate() - days);
          params.date_from = dateFrom.toISOString().split('T')[0];
        }

        response = await entryAPI.getAll(params);
        setEntries(response.data);
      }
    } catch (error) {
      console.error('Error loading entries:', error);
      toast.error('Failed to load entries');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (query) => {
    try {
      setLoading(true);
      const response = await entryAPI.search(query, 20);
      const searchEntries = response.data.results.map(result => result.entry);
      setEntries(searchEntries);
    } catch (error) {
      console.error('Error searching entries:', error);
      toast.error('Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateEntry = () => {
    setEditingEntry(null);
    setShowEditor(true);
  };

  const handleCreateFromTemplate = () => {
    setShowTemplates(true);
  };

  const handleSelectTemplate = (templateData) => {
    // Don't set editingEntry for template-based new entries
    // Just pass the template data directly to the editor
    setEditingEntry({
      title: templateData.title,
      content: templateData.content,
      tags: templateData.tags,
      template_id: templateData.template_id,
      isTemplate: true // Add flag to indicate this is template-based
    });
    setShowEditor(true);
  };

  const handleAdvancedSearch = (results) => {
    setSearchResults(results);
    setShowAdvancedSearch(false);
  };

  const handleToggleFavorite = (updatedEntry) => {
    setEntries(prev => prev.map(entry => 
      entry.id === updatedEntry.id ? updatedEntry : entry
    ));
  };

  const handleViewChange = (view) => {
    setActiveView(view);
    setSearchResults(null);
  };

  const handleEditEntry = (entry) => {
    setEditingEntry(entry);
    setShowEditor(true);
  };

  const handleSaveEntry = async (entryData) => {
    try {
      setSavingEntry(true);
      
      if (editingEntry && editingEntry.id && !editingEntry.isTemplate) {
        // Update existing entry (has valid ID and not template-based)
        const response = await entryAPI.update(editingEntry.id, entryData);
        setEntries(prev => prev.map(entry => 
          entry.id === editingEntry.id ? response.data : entry
        ));
        toast.success('Entry updated successfully!');
      } else {
        // Create new entry (no ID or template-based)
        const response = await entryAPI.create(entryData);
        setEntries(prev => [response.data, ...prev]);
        toast.success('Entry created successfully!');
      }
      
      setShowEditor(false);
      setEditingEntry(null);
    } catch (error) {
      console.error('Error saving entry:', error);
      toast.error('Failed to save entry');
    } finally {
      setSavingEntry(false);
    }
  };

  const handleDeleteEntry = async (entryId) => {
    try {
      await entryAPI.delete(entryId);
      setEntries(prev => prev.filter(entry => entry.id !== entryId));
      toast.success('Entry deleted successfully');
    } catch (error) {
      console.error('Error deleting entry:', error);
      toast.error('Failed to delete entry');
    }
  };

  const handleFilterChange = (filterType, value) => {
    setFilters(prev => ({ ...prev, [filterType]: value }));
  };

  // Apply filters after state update
  useEffect(() => {
    if (!searchQuery && !searchResults) {
      loadEntries();
    }
  }, [filters, activeView]);

  const filteredEntries = (searchResults ? searchResults.entries : entries).filter(entry => {
    if (filters.mood && entry.mood !== filters.mood) {
      return false;
    }
    return true;
  });

  const currentTitle = searchResults 
    ? `Search Results (${filteredEntries.length})`
    : searchQuery 
      ? `Search: "${searchQuery}"`
      : activeView === 'favorites' 
        ? 'Favorite Entries'
        : 'Your Journal';

  if (loading && entries.length === 0) {
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
          <h1 className="text-2xl font-bold text-gray-900">
            {currentTitle}
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            {filteredEntries.length} {filteredEntries.length === 1 ? 'entry' : 'entries'}
            {(searchQuery || searchResults) && (
              <button
                onClick={() => {
                  setSearchResults(null);
                  window.location.reload();
                }}
                className="ml-2 text-blue-600 hover:text-blue-700"
              >
                Clear search
              </button>
            )}
          </p>
        </div>
        
        <div className="mt-4 sm:mt-0 flex space-x-2">
          {/* View Toggle */}
          <div className="inline-flex rounded-md shadow-sm">
            <button
              onClick={() => handleViewChange('all')}
              className={`px-3 py-2 text-sm font-medium rounded-l-md border ${
                activeView === 'all'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              } transition-colors`}
            >
              All Entries
            </button>
            <button
              onClick={() => handleViewChange('favorites')}
              className={`px-3 py-2 text-sm font-medium rounded-r-md border-t border-r border-b ${
                activeView === 'favorites'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              } transition-colors flex items-center`}
            >
              <HeartIcon className="w-4 h-4 mr-1" />
              Favorites
            </button>
          </div>

          {/* Action Buttons */}
          <button
            onClick={() => setShowAdvancedSearch(true)}
            className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            <FunnelIcon className="w-4 h-4 mr-2" />
            Advanced Search
          </button>
          
          <button
            onClick={handleCreateFromTemplate}
            className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            <DocumentTextIcon className="w-4 h-4 mr-2" />
            Use Template
          </button>
          
          <button
            onClick={handleCreateEntry}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            New Entry
          </button>
        </div>
      </div>

      {/* Filters */}
      {!searchQuery && (
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Mood Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Filter by Mood
              </label>
              <select
                value={filters.mood}
                onChange={(e) => handleFilterChange('mood', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              >
                <option value="">All moods</option>
                <option value="very_positive">Very Positive</option>
                <option value="positive">Positive</option>
                <option value="neutral">Neutral</option>
                <option value="negative">Negative</option>
                <option value="very_negative">Very Negative</option>
              </select>
            </div>

            {/* Topic Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Filter by Topic
              </label>
              <select
                value={filters.topic}
                onChange={(e) => handleFilterChange('topic', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              >
                <option value="">All topics</option>
                {topics.map(topic => (
                  <option key={topic.id} value={topic.id}>
                    {topic.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Date Range Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Time Period
              </label>
              <select
                value={filters.dateRange}
                onChange={(e) => handleFilterChange('dateRange', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              >
                <option value="7">Last 7 days</option>
                <option value="30">Last 30 days</option>
                <option value="90">Last 3 months</option>
                <option value="365">Last year</option>
                <option value="">All time</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Entries Grid */}
      {filteredEntries.length > 0 ? (
        <div className="grid gap-6">
          {filteredEntries.map(entry => (
            <EntryCard
              key={entry.id}
              entry={entry}
              onEdit={handleEditEntry}
              onDelete={handleDeleteEntry}
              onToggleFavorite={handleToggleFavorite}
              showTopic={true}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          icon={BookOpenIcon}
          title={searchQuery ? "No entries found" : "No journal entries yet"}
          description={
            searchQuery 
              ? "Try adjusting your search terms or clear the search to see all entries."
              : "Start your journaling journey by creating your first entry. Reflect on your day, thoughts, and experiences."
          }
          action={
            !searchQuery && (
              <button
                onClick={handleCreateEntry}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                <PlusIcon className="w-4 h-4 mr-2" />
                Write your first entry
              </button>
            )
          }
        />
      )}

      {/* Entry Editor Modal */}
      {showEditor && (
        <EntryEditor
          entry={editingEntry}
          onSave={handleSaveEntry}
          onCancel={() => {
            setShowEditor(false);
            setEditingEntry(null);
          }}
          topics={topics}
          isLoading={savingEntry}
        />
      )}

      {/* Advanced Search Modal */}
      {showAdvancedSearch && (
        <AdvancedSearch
          isVisible={showAdvancedSearch}
          onClose={() => setShowAdvancedSearch(false)}
          onSearch={handleAdvancedSearch}
        />
      )}

      {/* Entry Templates Modal */}
      {showTemplates && (
        <EntryTemplates
          isVisible={showTemplates}
          onClose={() => setShowTemplates(false)}
          onSelectTemplate={handleSelectTemplate}
        />
      )}
    </div>
  );
};

export default Journal;