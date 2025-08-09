// frontend/src/components/Performance/OptimizedInsights.jsx
/**
 * Performance-optimized insights component with caching and lazy loading
 */

import React, { memo, useState, useCallback, useMemo } from 'react';
import { ChartBarIcon, SparklesIcon, TrendingUpIcon, HeartIcon } from '@heroicons/react/24/outline';
import { useMemoizedInsights, useDebounce } from '../../hooks/usePerformanceOptimization';

// Memoized mood chart component
const MoodChart = memo(({ moodDistribution }) => {
  const chartData = useMemo(() => {
    const moods = {
      'very_happy': { label: 'Very Happy', color: 'bg-green-500', value: 5 },
      'happy': { label: 'Happy', color: 'bg-green-400', value: 4 },
      'neutral': { label: 'Neutral', color: 'bg-gray-400', value: 3 },
      'sad': { label: 'Sad', color: 'bg-orange-400', value: 2 },
      'very_sad': { label: 'Very Sad', color: 'bg-red-500', value: 1 }
    };

    const totalEntries = Object.values(moodDistribution).reduce((sum, count) => sum + count, 0);
    
    return Object.entries(moodDistribution).map(([mood, count]) => ({
      mood,
      label: moods[mood]?.label || mood,
      color: moods[mood]?.color || 'bg-gray-400',
      count,
      percentage: totalEntries > 0 ? Math.round((count / totalEntries) * 100) : 0
    })).sort((a, b) => moods[b.mood]?.value - moods[a.mood]?.value);
  }, [moodDistribution]);

  if (chartData.length === 0) {
    return (
      <div className="text-center py-8">
        <ChartBarIcon className="w-12 h-12 text-gray-400 mx-auto mb-2" />
        <p className="text-gray-500">No mood data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {chartData.map((item) => (
        <div key={item.mood} className="flex items-center space-x-3">
          <div className="flex-shrink-0 w-16 text-sm text-gray-600">
            {item.label}
          </div>
          <div className="flex-1 bg-gray-200 rounded-full h-4 relative overflow-hidden">
            <div
              className={`h-full ${item.color} transition-all duration-500 ease-out`}
              style={{ width: `${item.percentage}%` }}
            />
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-xs font-medium text-white mix-blend-difference">
                {item.count} ({item.percentage}%)
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
});

MoodChart.displayName = 'MoodChart';

// Memoized stats card component
const StatsCard = memo(({ icon: Icon, title, value, subtitle, color = 'blue' }) => {
  const colorClasses = useMemo(() => {
    const colors = {
      blue: 'bg-blue-50 text-blue-600',
      green: 'bg-green-50 text-green-600',
      purple: 'bg-purple-50 text-purple-600',
      orange: 'bg-orange-50 text-orange-600'
    };
    return colors[color] || colors.blue;
  }, [color]);

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 hover:shadow-md transition-shadow">
      <div className="flex items-center">
        <div className={`p-3 rounded-lg ${colorClasses}`}>
          <Icon className="w-6 h-6" />
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {subtitle && (
            <p className="text-sm text-gray-500">{subtitle}</p>
          )}
        </div>
      </div>
    </div>
  );
});

StatsCard.displayName = 'StatsCard';

// Memoized recent entries component
const RecentEntries = memo(({ entries, onEntryClick }) => {
  if (!entries || entries.length === 0) {
    return (
      <div className="text-center py-8">
        <SparklesIcon className="w-12 h-12 text-gray-400 mx-auto mb-2" />
        <p className="text-gray-500">No recent entries</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {entries.map((entry) => (
        <div
          key={entry.id}
          onClick={() => onEntryClick?.(entry.id)}
          className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
        >
          <div className="flex justify-between items-start">
            <div className="flex-1 min-w-0">
              <h4 className="font-medium text-gray-900 truncate">
                {entry.title || 'Untitled Entry'}
              </h4>
              <div className="flex items-center gap-2 mt-1 text-sm text-gray-500">
                <span>
                  {new Date(entry.created_at).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric'
                  })}
                </span>
                <span>•</span>
                <span className="capitalize">
                  {entry.mood?.replace('_', ' ') || 'neutral'}
                </span>
                {entry.is_favorite && (
                  <>
                    <span>•</span>
                    <HeartIcon className="w-4 h-4 text-red-500" />
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
});

RecentEntries.displayName = 'RecentEntries';

// Main optimized insights component
const OptimizedInsights = ({ entries = [], onEntryClick, className = '' }) => {
  const [selectedPeriod, setSelectedPeriod] = useState(30);
  
  // Debounce period changes to avoid excessive recalculations
  const debouncedPeriod = useDebounce(selectedPeriod, 200);
  
  // Filter entries by period with memoization
  const filteredEntries = useMemo(() => {
    if (!entries || entries.length === 0) return [];
    
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - debouncedPeriod);
    
    return entries.filter(entry => {
      const entryDate = new Date(entry.created_at);
      return entryDate >= cutoffDate;
    });
  }, [entries, debouncedPeriod]);

  // Calculate insights with memoization
  const insights = useMemoizedInsights(filteredEntries);

  // Handle period change
  const handlePeriodChange = useCallback((period) => {
    setSelectedPeriod(period);
  }, []);

  // Mood trend calculation
  const moodTrend = useMemo(() => {
    if (insights.averageMood > 3.5) return { label: 'Positive', color: 'green' };
    if (insights.averageMood < 2.5) return { label: 'Challenging', color: 'orange' };
    return { label: 'Balanced', color: 'blue' };
  }, [insights.averageMood]);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Period selector */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Your Insights</h2>
        <div className="flex rounded-lg border border-gray-300">
          {[7, 30, 90].map((period) => (
            <button
              key={period}
              onClick={() => handlePeriodChange(period)}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                selectedPeriod === period
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              } ${period === 7 ? 'rounded-l-lg' : ''} ${period === 90 ? 'rounded-r-lg' : ''}`}
            >
              {period === 7 ? 'Week' : period === 30 ? 'Month' : '3 Months'}
            </button>
          ))}
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          icon={SparklesIcon}
          title="Total Entries"
          value={insights.totalEntries}
          subtitle={`Last ${selectedPeriod} days`}
          color="blue"
        />
        <StatsCard
          icon={TrendingUpIcon}
          title="Average Mood"
          value={insights.averageMood.toFixed(1)}
          subtitle={`${moodTrend.label} trend`}
          color={moodTrend.color}
        />
        <StatsCard
          icon={ChartBarIcon}
          title="Writing Streak"
          value="—"
          subtitle="Coming soon"
          color="purple"
        />
        <StatsCard
          icon={HeartIcon}
          title="Favorites"
          value={entries.filter(e => e.is_favorite).length}
          subtitle="Saved entries"
          color="orange"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Mood distribution */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Mood Distribution</h3>
          <MoodChart moodDistribution={insights.moodDistribution} />
        </div>

        {/* Recent entries */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Entries</h3>
          <RecentEntries entries={insights.recentEntries} onEntryClick={onEntryClick} />
        </div>
      </div>

      {/* Performance indicator */}
      <div className="text-xs text-gray-500 text-center">
        ⚡ Performance optimized • Data from {insights.totalEntries} entries
      </div>
    </div>
  );
};

export default OptimizedInsights;