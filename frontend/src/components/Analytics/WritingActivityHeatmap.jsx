// frontend/src/components/Analytics/WritingActivityHeatmap.jsx
import React, { useState, useEffect } from 'react';
import { CalendarIcon, ArrowPathIcon, FireIcon } from '@heroicons/react/24/outline';
import { entryAPI } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';

const WritingActivityHeatmap = ({ className = "" }) => {
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDate, setSelectedDate] = useState(null);
  const [hoveredDate, setHoveredDate] = useState(null);
  const [maxEntries, setMaxEntries] = useState(0);

  useEffect(() => {
    loadActivityData();
  }, []);

  const loadActivityData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get entries from the last 365 days
      const response = await entryAPI.getAll({ limit: 1000 });
      const entries = response.data || [];

      // Group entries by date
      const activityMap = {};
      let maxCount = 0;

      entries.forEach(entry => {
        const date = entry.created_at.split('T')[0]; // Get YYYY-MM-DD format
        if (!activityMap[date]) {
          activityMap[date] = {
            count: 0,
            entries: [],
            totalWords: 0
          };
        }
        activityMap[date].count++;
        activityMap[date].entries.push(entry);
        activityMap[date].totalWords += (entry.content?.split(' ').length || 0);
        
        maxCount = Math.max(maxCount, activityMap[date].count);
      });

      setData(activityMap);
      setMaxEntries(maxCount);

      // If no real data, show empty state
      if (Object.keys(activityMap).length === 0) {
        setData({});
        setMaxEntries(0);
      }
    } catch (err) {
      console.error('Error loading activity data:', err);
      setError('Unable to load activity data');
    } finally {
      setLoading(false);
    }
  };

  // Generate calendar grid for the last 12 weeks (84 days)
  const generateCalendarGrid = () => {
    const grid = [];
    const today = new Date();
    const startDate = new Date(today);
    startDate.setDate(startDate.getDate() - 83); // 12 weeks back

    // Find the start of the week (Sunday)
    const startOfWeek = new Date(startDate);
    startOfWeek.setDate(startDate.getDate() - startDate.getDay());

    for (let week = 0; week < 12; week++) {
      const weekData = [];
      for (let day = 0; day < 7; day++) {
        const currentDate = new Date(startOfWeek);
        currentDate.setDate(startOfWeek.getDate() + (week * 7) + day);
        const dateStr = currentDate.toISOString().split('T')[0];
        
        weekData.push({
          date: currentDate,
          dateStr,
          activity: data[dateStr] || null,
          isToday: dateStr === today.toISOString().split('T')[0],
          isFuture: currentDate > today
        });
      }
      grid.push(weekData);
    }

    return grid;
  };

  const getIntensityClass = (count) => {
    if (!count || count === 0) return 'bg-gray-100';
    if (maxEntries === 0) return 'bg-gray-100';
    
    const intensity = count / maxEntries;
    if (intensity <= 0.25) return 'bg-green-200';
    if (intensity <= 0.5) return 'bg-green-300';
    if (intensity <= 0.75) return 'bg-green-400';
    return 'bg-green-500';
  };

  const getDayName = (dayIndex) => {
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    return days[dayIndex];
  };

  const getMonthName = (date) => {
    return date.toLocaleDateString('en-US', { month: 'short' });
  };

  const calendarGrid = generateCalendarGrid();

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="md" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="text-center text-gray-500">
          <CalendarIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p className="mb-2">{error}</p>
          <button 
            onClick={loadActivityData}
            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <CalendarIcon className="h-6 w-6 text-green-600" />
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Writing Activity</h3>
            <p className="text-sm text-gray-500">
              Daily journaling patterns over the last 12 weeks
            </p>
          </div>
        </div>
        <button
          onClick={loadActivityData}
          className="p-2 text-gray-400 hover:text-gray-600 rounded-md transition-colors"
          title="Refresh data"
        >
          <ArrowPathIcon className="h-4 w-4" />
        </button>
      </div>

      {/* Calendar Heatmap */}
      <div className="mb-6 overflow-x-auto">
        <div className="min-w-full">
          {/* Month labels */}
          <div className="flex mb-2">
            <div className="w-8"></div> {/* Space for day labels */}
            {calendarGrid.map((week, weekIndex) => {
              const firstDay = week[0];
              const showMonth = firstDay.date.getDate() <= 7;
              return (
                <div key={weekIndex} className="flex-1 text-center">
                  {showMonth && (
                    <span className="text-xs text-gray-500 font-medium">
                      {getMonthName(firstDay.date)}
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          {/* Day labels and heatmap */}
          <div className="flex">
            {/* Day labels */}
            <div className="flex flex-col space-y-1 mr-2">
              <div className="h-3"></div> {/* Spacer */}
              {['Mon', 'Wed', 'Fri'].map((day, index) => (
                <div key={day} className="h-3 flex items-center">
                  <span className="text-xs text-gray-500 font-medium w-6">
                    {index === 0 ? 'Mon' : index === 1 ? 'Wed' : 'Fri'}
                  </span>
                </div>
              ))}
            </div>

            {/* Heatmap grid */}
            <div className="flex space-x-1">
              {calendarGrid.map((week, weekIndex) => (
                <div key={weekIndex} className="flex flex-col space-y-1">
                  {week.map((day, dayIndex) => (
                    <div
                      key={`${weekIndex}-${dayIndex}`}
                      className={`w-3 h-3 rounded-sm cursor-pointer border transition-all duration-200 ${
                        day.isFuture 
                          ? 'bg-gray-50 border-gray-200 cursor-not-allowed' 
                          : `${getIntensityClass(day.activity?.count)} border-gray-200 hover:ring-2 hover:ring-green-300`
                      } ${
                        day.isToday ? 'ring-2 ring-blue-400' : ''
                      } ${
                        hoveredDate === day.dateStr ? 'ring-2 ring-green-400' : ''
                      }`}
                      title={
                        day.isFuture 
                          ? `${day.date.toLocaleDateString()} (future)`
                          : `${day.date.toLocaleDateString()}: ${day.activity?.count || 0} entries`
                      }
                      onMouseEnter={() => !day.isFuture && setHoveredDate(day.dateStr)}
                      onMouseLeave={() => setHoveredDate(null)}
                      onClick={() => !day.isFuture && setSelectedDate(day)}
                    />
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <span>Less</span>
          <div className="flex space-x-1">
            <div className="w-3 h-3 bg-gray-100 rounded-sm border border-gray-200"></div>
            <div className="w-3 h-3 bg-green-200 rounded-sm border border-gray-200"></div>
            <div className="w-3 h-3 bg-green-300 rounded-sm border border-gray-200"></div>
            <div className="w-3 h-3 bg-green-400 rounded-sm border border-gray-200"></div>
            <div className="w-3 h-3 bg-green-500 rounded-sm border border-gray-200"></div>
          </div>
          <span>More</span>
        </div>
        
        <div className="text-xs text-gray-500">
          {Object.keys(data).length} days active • {maxEntries} max entries/day
        </div>
      </div>

      {/* Selected Date Details */}
      {selectedDate && selectedDate.activity && (
        <div className="p-4 bg-green-50 rounded-lg border border-green-200">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <FireIcon className="h-5 w-5 text-green-600" />
              <h4 className="font-medium text-green-900">
                {selectedDate.date.toLocaleDateString('en-US', { 
                  weekday: 'long', 
                  month: 'long', 
                  day: 'numeric' 
                })}
              </h4>
            </div>
            <button
              onClick={() => setSelectedDate(null)}
              className="text-green-600 hover:text-green-700 text-sm font-medium"
            >
              Close
            </button>
          </div>
          
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">
                {selectedDate.activity.count}
              </p>
              <p className="text-green-700">Entries</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">
                {selectedDate.activity.totalWords}
              </p>
              <p className="text-green-700">Words</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">
                {Math.round(selectedDate.activity.totalWords / selectedDate.activity.count) || 0}
              </p>
              <p className="text-green-700">Avg Words</p>
            </div>
          </div>
          
          {selectedDate.activity.entries.length > 0 && (
            <div className="mt-4">
              <h5 className="text-sm font-medium text-green-900 mb-2">Entries:</h5>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {selectedDate.activity.entries.map((entry, index) => (
                  <div key={entry.id || index} className="text-sm text-green-700">
                    • {entry.title || 'Untitled Entry'}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center pt-6 border-t border-gray-200">
        <div>
          <p className="text-2xl font-bold text-gray-900">
            {Object.keys(data).length}
          </p>
          <p className="text-sm text-gray-500">Active Days</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-green-600">
            {Object.values(data).reduce((sum, day) => sum + day.count, 0)}
          </p>
          <p className="text-sm text-gray-500">Total Entries</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-blue-600">
            {Object.keys(data).length > 0 
              ? Math.round(Object.values(data).reduce((sum, day) => sum + day.count, 0) / Object.keys(data).length * 10) / 10
              : 0}
          </p>
          <p className="text-sm text-gray-500">Avg per Day</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-purple-600">
            {Math.round((Object.keys(data).length / 84) * 100) || 0}%
          </p>
          <p className="text-sm text-gray-500">Consistency</p>
        </div>
      </div>
    </div>
  );
};

export default WritingActivityHeatmap;