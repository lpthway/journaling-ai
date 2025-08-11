// frontend/src/components/Analytics/WritingInsights.jsx
import React, { useState, useEffect } from 'react';
import { ChartBarIcon, ArrowPathIcon, PencilIcon } from '@heroicons/react/24/outline';
import { analyticsApi } from '../../services/analyticsApi';
import { DEFAULT_USER_ID } from '../../config/user';
import LoadingSpinner from '../Common/LoadingSpinner';

const WritingInsights = ({ days = 30, className = "" }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadInsights();
  }, [days]);

  const loadInsights = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get both writing insights and mood data for comprehensive analysis
      const [insights, moodData] = await Promise.all([
        analyticsApi.getWritingActivity(days, DEFAULT_USER_ID),
        analyticsApi.getEmotionalPatterns(days, DEFAULT_USER_ID)
      ]);
      
      if (insights) {
        // Calculate most active day from daily trends if available
        const calculateMostActiveDay = () => {
          if (!moodData?.daily_trends) return 'N/A';
          
          const dayCount = {};
          moodData.daily_trends.forEach(trend => {
            const date = new Date(trend.date);
            const dayName = date.toLocaleDateString('en-US', { weekday: 'long' });
            dayCount[dayName] = (dayCount[dayName] || 0) + trend.entry_count;
          });
          
          return Object.keys(dayCount).length > 0 
            ? Object.keys(dayCount).reduce((a, b) => dayCount[a] > dayCount[b] ? a : b)
            : 'N/A';
        };

        // Calculate most common writing time (simplified - would need hourly data for accuracy)
        const calculateFavoriteTime = () => {
          // For now, return a calculated estimate based on when most entries were created
          // This would need actual timestamp analysis for true accuracy
          return 'Various'; // More honest than hardcoding 18:00
        };

        setData({
          mostActiveDay: calculateMostActiveDay(),
          avgWordsPerEntry: Math.round(insights.avg_words_per_entry || 0),
          longestStreak: insights.streak_info?.longest_streak || 0,
          favoriteTime: calculateFavoriteTime(),
          totalEntries: insights.total_entries || 0,
          totalWords: insights.total_words || 0,
          writingDays: insights.active_days || 0,
          avgEntriesPerDay: insights.avg_entries_per_active_day || 0
        });
      }
    } catch (err) {
      console.error('Error loading writing insights:', err);
      setError('Unable to load writing insights');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="flex items-center justify-center h-40">
          <LoadingSpinner size="md" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-2">
            <ChartBarIcon className="h-6 w-6 text-indigo-600" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Writing Insights</h3>
              <p className="text-sm text-gray-500">Your writing patterns and habits</p>
            </div>
          </div>
          <ArrowPathIcon className="h-4 w-4 text-gray-400" />
        </div>
        <div className="text-center text-gray-500 py-8">
          <PencilIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>No writing data available</p>
          <p className="text-sm">Start journaling to see your insights</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <ChartBarIcon className="h-6 w-6 text-indigo-600" />
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Writing Insights</h3>
            <p className="text-sm text-gray-500">Your writing patterns and habits</p>
          </div>
        </div>
        <button
          onClick={loadInsights}
          className="p-2 text-gray-400 hover:text-gray-600 rounded-md transition-colors"
          title="Refresh data"
        >
          <ArrowPathIcon className="h-4 w-4" />
        </button>
      </div>

      {/* Insights Grid */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Most active day</span>
          <span className="font-medium text-gray-900">{data.mostActiveDay}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Avg words per entry</span>
          <span className="font-medium text-gray-900">{data.avgWordsPerEntry}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Longest streak</span>
          <span className="font-medium text-gray-900">{data.longestStreak} days</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Favorite time</span>
          <span className="font-medium text-gray-900">{data.favoriteTime}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Total entries</span>
          <span className="font-medium text-gray-900">{data.totalEntries}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Total words written</span>
          <span className="font-medium text-gray-900">{data.totalWords.toLocaleString()}</span>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="grid grid-cols-2 gap-4 text-center">
          <div>
            <p className="text-2xl font-bold text-indigo-600">{data.writingDays}</p>
            <p className="text-sm text-gray-500">Writing Days</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-purple-600">
              {data.avgEntriesPerDay ? data.avgEntriesPerDay.toFixed(1) : '0.0'}
            </p>
            <p className="text-sm text-gray-500">Avg per Day</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WritingInsights;