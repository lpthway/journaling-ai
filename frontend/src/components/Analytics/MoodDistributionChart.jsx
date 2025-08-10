// frontend/src/components/Analytics/MoodDistributionChart.jsx
import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { ChartPieIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import { insightsAPI } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';

const MoodDistributionChart = ({ days = 30, className = "" }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [totalEntries, setTotalEntries] = useState(0);

  // Mood colors for the chart
  const MOOD_COLORS = {
    positive: '#10B981', // Green
    negative: '#EF4444', // Red
    neutral: '#6B7280',  // Gray
    mixed: '#F59E0B',    // Yellow
    unknown: '#9CA3AF'   // Light gray
  };

  useEffect(() => {
    loadMoodData();
  }, [days]);

  const loadMoodData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await insightsAPI.getMoodTrends(days);
      const moodStats = response.data;

      // Transform the data for the pie chart
      if (moodStats.mood_distribution && Object.keys(moodStats.mood_distribution).length > 0) {
        const chartData = Object.entries(moodStats.mood_distribution).map(([mood, count]) => ({
          name: mood.charAt(0).toUpperCase() + mood.slice(1),
          value: count,
          percentage: moodStats.total_entries > 0 ? Math.round((count / moodStats.total_entries) * 100) : 0,
          color: MOOD_COLORS[mood] || MOOD_COLORS.unknown
        }));

        setData(chartData);
        setTotalEntries(moodStats.total_entries || 0);
      } else {
        // No data available - show empty state
        setData([]);
        setTotalEntries(0);
      }
    } catch (err) {
      console.error('Error loading mood data:', err);
      setError('Unable to load mood distribution');
    } finally {
      setLoading(false);
    }
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900">{data.name}</p>
          <p className="text-sm text-gray-600">
            {data.value} entries ({data.percentage}%)
          </p>
        </div>
      );
    }
    return null;
  };

  const CustomLegend = ({ payload }) => {
    return (
      <div className="flex flex-wrap justify-center gap-4 mt-4">
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center space-x-2">
            <div 
              className="w-3 h-3 rounded-full" 
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-sm text-gray-600">
              {entry.value} ({entry.payload.percentage}%)
            </span>
          </div>
        ))}
      </div>
    );
  };

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
          <ChartPieIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p className="mb-2">{error}</p>
          <button 
            onClick={loadMoodData}
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
          <ChartPieIcon className="h-6 w-6 text-blue-600" />
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Mood Distribution</h3>
            <p className="text-sm text-gray-500">
              Last {days} days • {totalEntries} entries
            </p>
          </div>
        </div>
        <button
          onClick={loadMoodData}
          className="p-2 text-gray-400 hover:text-gray-600 rounded-md transition-colors"
          title="Refresh data"
        >
          <ArrowPathIcon className="h-4 w-4" />
        </button>
      </div>

      {/* Chart */}
      {data.length > 0 ? (
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={100}
                paddingAngle={2}
                dataKey="value"
                animationBegin={0}
                animationDuration={800}
              >
                {data.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry.color}
                    stroke="#ffffff"
                    strokeWidth={2}
                  />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend content={<CustomLegend />} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="text-center py-12 text-gray-500">
          <ChartPieIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p className="text-sm">No mood data available</p>
          <p className="text-xs text-gray-400 mt-1">Start journaling to see your mood patterns</p>
        </div>
      )}

      {/* Summary Stats */}
      {data.length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-gray-900">{totalEntries}</p>
              <p className="text-sm text-gray-500">Total Entries</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-green-600">
                {data.find(d => d.name === 'Positive')?.percentage || 0}%
              </p>
              <p className="text-sm text-gray-500">Positive</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-600">
                {data.find(d => d.name === 'Neutral')?.percentage || 0}%
              </p>
              <p className="text-sm text-gray-500">Neutral</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-red-600">
                {data.find(d => d.name === 'Negative')?.percentage || 0}%
              </p>
              <p className="text-sm text-gray-500">Negative</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MoodDistributionChart;