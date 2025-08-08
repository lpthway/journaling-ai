// frontend/src/components/OptimizedInsights.js - High-Performance Insights Component

import React, { useState, useEffect, useCallback } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const OptimizedInsights = () => {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [cacheInfo, setCacheInfo] = useState(null);
  const [timeRange, setTimeRange] = useState(30);
  const [refreshing, setRefreshing] = useState(false);

  // Fetch cached insights - this should be FAST (under 500ms)
  const fetchInsights = useCallback(async (forceRefresh = false) => {
    setLoading(true);
    setError(null);
    
    const startTime = Date.now();
    
    try {
      const params = new URLSearchParams({
        time_range_days: timeRange.toString(),
        force_refresh: forceRefresh.toString(),
        include_cache_info: 'true'
      });
      
      const response = await fetch(`/api/v1/insights/cached?${params}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      const responseTime = Date.now() - startTime;
      
      setInsights(result.data);
      setCacheInfo({
        ...result.cache_info,
        response_time_ms: responseTime,
        is_fresh: result.is_fresh,
        last_updated: result.last_updated
      });
      
      // Insights loaded successfully
      
    } catch (err) {
      console.error('❌ Error fetching insights:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  // Trigger background cache refresh
  const refreshCache = async () => {
    setRefreshing(true);
    
    try {
      const response = await fetch('/api/v1/insights/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        // Cache refresh initiated
        // Reload insights after a brief delay
        setTimeout(() => fetchInsights(), 2000);
      }
    } catch (err) {
      console.error('❌ Error refreshing cache:', err);
    } finally {
      setRefreshing(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchInsights();
  }, [fetchInsights]);

  // Render mood trends chart
  const renderMoodChart = () => {
    const moodData = insights?.mood_trends;
    if (!moodData?.daily_mood_scores) return null;

    const dates = Object.keys(moodData.daily_mood_scores).sort();
    const chartData = dates.map(date => ({
      date: new Date(date).toLocaleDateString(),
      moodScore: moodData.daily_mood_scores[date]
    }));

    const CustomTooltip = ({ active, payload, label }) => {
      if (active && payload && payload.length) {
        return (
          <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
            <p className="text-sm font-medium">{label}</p>
            <p className="text-sm text-blue-600">
              Mood Score: {payload[0].value?.toFixed(2)}
            </p>
          </div>
        );
      }
      return null;
    };

    return (
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 12 }}
              stroke="#6b7280"
            />
            <YAxis 
              domain={[-1, 1]}
              tick={{ fontSize: 12 }}
              stroke="#6b7280"
              tickFormatter={(value) => {
                if (value === 1) return 'Positive';
                if (value === 0) return 'Neutral';
                if (value === -1) return 'Negative';
                return value.toFixed(1);
              }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="moodScore"
              name="Mood Score"
              stroke="rgb(59, 130, 246)"
              strokeWidth={2}
              dot={{ fill: "rgb(59, 130, 246)", strokeWidth: 2, r: 3 }}
              activeDot={{ r: 5, fill: "rgb(59, 130, 246)" }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  };

  // Render cache status indicator
  const renderCacheStatus = () => {
    if (!cacheInfo) return null;

    const isStale = Object.values(cacheInfo).some(info => 
      typeof info === 'object' && info?.status === 'stale'
    );

    return (
      <div className="bg-gray-50 rounded-lg p-4 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${
              cacheInfo.is_fresh ? 'bg-green-500' : 'bg-yellow-500'
            }`} />
            <span className="text-sm font-medium">
              {cacheInfo.is_fresh ? 'Data is fresh' : 'Data refreshing in background'}
            </span>
            <span className="text-xs text-gray-500">
              Loaded in {cacheInfo.response_time_ms}ms
            </span>
          </div>
          
          <button
            onClick={refreshCache}
            disabled={refreshing}
            className="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
        
        {cacheInfo.last_updated && (
          <div className="text-xs text-gray-500 mt-1">
            Last updated: {new Date(cacheInfo.last_updated).toLocaleString()}
          </div>
        )}
      </div>
    );
  };

  // Render statistics cards
  const renderStatsCards = () => {
    const entryStats = insights?.entry_stats || {};
    const chatStats = insights?.chat_stats || {};
    const moodData = insights?.mood_trends || {};

    const stats = [
      {
        title: 'Total Entries',
        value: entryStats.total_entries || 0,
        icon: '📝',
        color: 'blue'
      },
      {
        title: 'Total Words',
        value: (entryStats.total_words || 0).toLocaleString(),
        icon: '💬',
        color: 'green'
      },
      {
        title: 'Chat Sessions',
        value: chatStats.total_sessions || 0,
        icon: '🗨️',
        color: 'purple'
      },
      {
        title: 'Average Mood',
        value: moodData.average_mood ? moodData.average_mood.toFixed(2) : 'N/A',
        icon: '😊',
        color: 'yellow'
      }
    ];

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat, index) => (
          <div key={index} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="text-2xl mr-3">{stat.icon}</div>
              <div>
                <div className="text-2xl font-bold text-gray-900">{stat.value}</div>
                <div className="text-sm text-gray-600">{stat.title}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  if (loading && !insights) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-600">Loading insights...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center">
          <div className="text-red-500 text-xl mr-3">⚠️</div>
          <div>
            <h3 className="text-lg font-semibold text-red-800">Error Loading Insights</h3>
            <p className="text-red-600">{error}</p>
            <button
              onClick={() => fetchInsights()}
              className="mt-3 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          ⚡ Insights Dashboard
        </h1>
        <p className="text-gray-600">
          High-performance analytics with intelligent caching - loads in under 500ms
        </p>
      </div>

      {/* Cache Status */}
      {renderCacheStatus()}

      {/* Time Range Selector */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Time Range
        </label>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(Number(e.target.value))}
          className="border border-gray-300 rounded-md px-3 py-2"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
          <option value={365}>Last year</option>
        </select>
      </div>

      {insights && (
        <>
          {/* Statistics Cards */}
          {renderStatsCards()}

          {/* Mood Trends Chart */}
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Mood Trends</h2>
            {renderMoodChart()}
          </div>

          {/* Mood Distribution */}
          {insights.mood_trends?.mood_distribution && (
            <div className="bg-white rounded-lg shadow p-6 mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Mood Distribution</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(insights.mood_trends.mood_distribution).map(([mood, count]) => (
                  <div key={mood} className="text-center p-4 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-gray-900">{count}</div>
                    <div className="text-sm text-gray-600 capitalize">{mood.replace('_', ' ')}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Performance Info */}
          <div className="bg-blue-50 rounded-lg p-4 text-sm text-blue-800">
            <strong>⚡ Performance:</strong> This page loads instantly using cached analytics. 
            Data is refreshed in the background every few hours to stay current without 
            slowing down your experience.
          </div>
        </>
      )}
    </div>
  );
};

export default OptimizedInsights;
