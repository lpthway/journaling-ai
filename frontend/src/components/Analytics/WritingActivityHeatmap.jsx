// frontend/src/components/Analytics/WritingActivityHeatmap.jsx
import React, { useState, useEffect } from 'react';
import { CalendarIcon, ArrowPathIcon, FireIcon } from '@heroicons/react/24/outline';
import { entryAPI } from '../../services/api';
import { DEFAULT_USER_ID } from '../../config/user';
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

      // Get entries from the last 365 days for the correct user
      const response = await entryAPI.getAll({ 
        limit: 1000,
        user_id: DEFAULT_USER_ID 
      });
      const entries = response.data || [];

      // Group entries by date
      const activityMap = {};
      let maxCount = 0;

      entries.forEach(entry => {
        // Convert UTC timestamp to local date string for consistent comparison
        const entryDate = new Date(entry.created_at);
        const year = entryDate.getFullYear();
        const month = String(entryDate.getMonth() + 1).padStart(2, '0');
        const day = String(entryDate.getDate()).padStart(2, '0');
        const date = `${year}-${month}-${day}`; // Local date in YYYY-MM-DD format
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

  // Generate monthly grids for the last 4 months
  const generateMonthlyGrids = () => {
    const today = new Date();
    const todayLocalStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
    const monthlyGrids = [];
    

    // Generate last 4 months (including current month)
    for (let monthsBack = 3; monthsBack >= 0; monthsBack--) {
      const monthDate = new Date(today.getFullYear(), today.getMonth() - monthsBack, 1);
      const monthName = monthDate.toLocaleDateString('en-US', { month: 'long' });
      const monthShort = monthDate.toLocaleDateString('en-US', { month: 'short' });
      const year = monthDate.getFullYear();
      
      
      // Get first and last day of month properly
      const firstDay = new Date(year, monthDate.getMonth(), 1);
      const lastDay = new Date(year, monthDate.getMonth() + 1, 0);
      
      // Fix potential timezone issues by ensuring we work in local timezone
      firstDay.setHours(12, 0, 0, 0); // Set to noon to avoid midnight timezone issues
      lastDay.setHours(12, 0, 0, 0);
      
      // Start from Sunday of the first week containing the first day
      const startOfGrid = new Date(firstDay);
      startOfGrid.setDate(firstDay.getDate() - firstDay.getDay());
      
      // Generate weeks for this month
      const weeks = [];
      let currentWeekStart = new Date(startOfGrid);
      
      
      while (currentWeekStart <= lastDay) {
        const week = [];
        
        for (let day = 0; day < 7; day++) {
          // Create a proper local date object for each day
          const currentDate = new Date(currentWeekStart);
          currentDate.setDate(currentWeekStart.getDate() + day);
          currentDate.setHours(12, 0, 0, 0); // Set to noon to avoid timezone issues
          
          // Use local date formatting instead of ISO string
          const year = currentDate.getFullYear();
          const month = String(currentDate.getMonth() + 1).padStart(2, '0');
          const dayStr = String(currentDate.getDate()).padStart(2, '0');
          const dateStr = `${year}-${month}-${dayStr}`;
          
          const activity = data[dateStr] || null;
          
          const isCurrentMonth = currentDate.getMonth() === monthDate.getMonth();
          
          // Create consistent local date comparison  
          const isToday = dateStr === todayLocalStr;
          
          
          week.push({
            date: currentDate,
            dateStr,
            activity,
            isToday,
            isFuture: dateStr > todayLocalStr,
            isCurrentMonth
          });
        }
        
        weeks.push(week);
        currentWeekStart.setDate(currentWeekStart.getDate() + 7);
        
        // Stop if we've gone too far past the month
        if (currentWeekStart.getDate() > 7 && currentWeekStart.getMonth() !== monthDate.getMonth()) {
          break;
        }
      }
      
      monthlyGrids.push({
        monthName,
        monthShort,
        year,
        weeks
      });
    }

    return monthlyGrids;
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

  const monthlyGrids = React.useMemo(() => generateMonthlyGrids(), [data]);

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
              Daily journaling patterns over the last 4 months
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

      {/* Monthly Heatmaps - Horizontal Layout */}
      <div className="mb-6 overflow-x-auto">
        <div className="flex space-x-8 min-w-max">
          {monthlyGrids.map((month, monthIndex) => (
            <div key={monthIndex} className="flex-shrink-0">
              {/* Month title */}
              <div className="mb-3 text-center">
                <h4 className="text-sm font-medium text-gray-700">
                  {month.monthShort} {month.year}
                </h4>
              </div>
              
              {/* Day headers */}
              <div className="flex justify-center mb-2">
                <div className="flex space-x-1">
                  {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map((day, index) => (
                    <div key={index} className="w-3 h-3 flex items-center justify-center">
                      <span className="text-xs text-gray-400 font-medium">{day}</span>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Monthly grid */}
              <div className="space-y-1">
                {month.weeks.map((week, weekIndex) => (
                  <div key={weekIndex} className="flex space-x-1">
                    {week.map((day, dayIndex) => (
                      <div
                        key={`${monthIndex}-${weekIndex}-${dayIndex}`}
                        className={`w-3 h-3 rounded-sm cursor-pointer transition-all duration-200 ${
                          !day.isCurrentMonth 
                            ? 'bg-transparent' // Hide days from other months
                            : day.isFuture 
                            ? 'bg-gray-50 border border-gray-200 cursor-not-allowed' 
                            : `${getIntensityClass(day.activity?.count)} hover:ring-2 hover:ring-green-400`
                        } ${
                          day.isCurrentMonth && !day.isFuture ? 'border border-gray-300' : ''
                        } ${
                          day.isToday ? 'ring-1 ring-blue-600' : ''
                        } ${
                          hoveredDate === day.dateStr ? 'ring-2 ring-green-500' : ''
                        }`}
                        title={
                          !day.isCurrentMonth ? '' :
                          day.isFuture 
                            ? `${day.date.toLocaleDateString()} (future)`
                            : `${day.date.toLocaleDateString()}: ${day.activity?.count || 0} entries${day.isToday ? ' (today)' : ''}`
                        }
                        onMouseEnter={() => day.isCurrentMonth && !day.isFuture && setHoveredDate(day.dateStr)}
                        onMouseLeave={() => setHoveredDate(null)}
                        onClick={() => day.isCurrentMonth && !day.isFuture && setSelectedDate(day)}
                      />
                    ))}
                  </div>
                ))}
              </div>
            </div>
          ))}
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
            {Math.round((Object.keys(data).length / 112) * 100) || 0}%
          </p>
          <p className="text-sm text-gray-500">Consistency</p>
        </div>
      </div>
    </div>
  );
};

export default WritingActivityHeatmap;