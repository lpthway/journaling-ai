import React, { useState, useEffect } from 'react';
import { PlusIcon, BookOpenIcon, CalendarIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { entryAPI, topicAPI } from '../services/api';
import EntryCard from '../components/Entry/EntryCard';
import EntryEditor from '../components/Entry/EntryEditor';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import EmptyState from '../components/Common/EmptyState';
import MoodIndicator from '../components/Common/MoodIndicator';

const Journal = ({ searchQuery = null }) => {
  const [entries, setEntries] = useState([]);
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showEditor, setShowEditor] = useState(false);
  const [editingEntry, setEditingEntry] = useState(null);
  const [savingEntry, setSavingEntry] = useState(false);
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

      const response = await entryAPI.getAll(params);
      setEntries(response.data);
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

  const handleEditEntry = (entry) => {
    setEditingEntry(entry);
    setShowEditor(true);
  };

  const handleSaveEntry = async (entryData) => {
    try {
      setSavingEntry(true);
      
      if (editingEntry) {
        // Update existing entry
        const response = await entryAPI.update(editingEntry.id, entryData);
        setEntries(prev => prev.map(entry => 
          entry.id === editingEntry.id ? response.data : entry
        ));
        toast.success('Entry updated successfully!');
      } else {
        // Create new entry
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
    if (!searchQuery) {
      loadEntries();
    }
  }, [filters]);

  const filteredEntries = entries.filter(entry => {
    if (filters.mood && entry.mood !== filters.mood) {
      return false;
    }
    return true;
  });

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
            {searchQuery ? `Search: "${searchQuery}"` : 'Your Journal'}
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            {filteredEntries.length} {filteredEntries.length === 1 ? 'entry' : 'entries'}
            {searchQuery && (
              <button
                onClick={() => window.location.reload()}
                className="ml-2 text-blue-600 hover:text-blue-700"
              >
                Clear search
              </button>
            )}
          </p>
        </div>
        
        <button
          onClick={handleCreateEntry}
          className="mt-4 sm:mt-0 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
        >
          <PlusIcon className="w-4 h-4 mr-2" />
          New Entry
        </button>
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
    </div>
  );
};

export default Journal;