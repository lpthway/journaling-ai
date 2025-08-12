// frontend/src/components/Analytics/MoodDistributionChart.jsx
import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend } from 'recharts';
import { ChartPieIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import { analyticsApi } from '../../services/analyticsApi';
// Removed /* removed user id */ import - using authenticated user
import LoadingSpinner from '../Common/LoadingSpinner';

const MoodDistributionChart = ({ days = 30, className = "" }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);

  // Mood colors matching the screenshot exactly
  const MOOD_COLORS = {
    positive: '#10B981', // Green
    neutral: '#6B7280',  // Gray 
    negative: '#EF4444', // Red
    mixed: '#F59E0B'     // Orange/Yellow
  };

  useEffect(() => {
    loadMoodData();
  }, [days]);

  const loadMoodData = async () => {
    try {
      setLoading(true);
      setError(null);

      const moodStats = await analyticsApi.getEmotionalPatterns(days);

      // Transform data to match screenshot format
      if (moodStats.mood_distribution && Object.keys(moodStats.mood_distribution).length > 0) {
        const chartData = Object.entries(moodStats.mood_distribution).map(([mood, data]) => ({
          name: mood.charAt(0).toUpperCase() + mood.slice(1),
          value: data.count,
          percentage: Math.round(data.percentage),
          color: MOOD_COLORS[mood] || MOOD_COLORS.neutral
        }));

        setData(chartData);
        setStats(moodStats.statistics);
      } else {
        setData([]);
        setStats(null);
      }
    } catch (err) {
      console.error('Error loading mood data:', err);
      setError('Unable to load mood distribution');
    } finally {
      setLoading(false);
    }
  };

  const CustomCell = ({ fill }) => <Cell fill={fill} />;

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="md" />
        </div>
      </div>
    );
  }

  if (error || data.length === 0) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-2">
            <ChartPieIcon className="h-6 w-6 text-blue-600" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Mood Distribution</h3>
              <p className="text-sm text-gray-500">Last {days} days • 0 entries</p>
            </div>
          </div>
          <ArrowPathIcon className="h-4 w-4 text-gray-400" />
        </div>
        <div className="text-center text-gray-500 py-12">
          <ChartPieIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>No mood data available</p>
          <p className="text-sm">Start journaling to see your mood patterns</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      {/* Header matching screenshot */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <ChartPieIcon className="h-6 w-6 text-blue-600" />
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Mood Distribution</h3>
            <p className="text-sm text-gray-500">Last {days} days • {stats?.total_entries || 0} entries</p>
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
      <div className="h-64 mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              dataKey="value"
              stroke="none"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Legend matching screenshot exactly */}
      <div className="flex flex-wrap justify-center gap-6 mb-6">
        {data.map((entry, index) => (
          <div key={index} className="flex items-center space-x-2">
            <div 
              className="w-3 h-3 rounded-full" 
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-sm text-gray-600">
              {entry.name} ({entry.percentage}%)
            </span>
          </div>
        ))}
      </div>

      {/* Statistics row matching screenshot */}
      <div className="grid grid-cols-4 gap-4 text-center">
        <div>
          <div className="text-2xl font-bold text-gray-900">{stats?.total_entries || 0}</div>
          <div className="text-sm text-gray-500">Total Entries</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-green-600">
            {data.find(d => d.name === 'Positive')?.percentage || 0}%
          </div>
          <div className="text-sm text-gray-500">Positive</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-gray-600">
            {data.find(d => d.name === 'Neutral')?.percentage || 0}%
          </div>
          <div className="text-sm text-gray-500">Neutral</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-red-600">
            {data.find(d => d.name === 'Negative')?.percentage || 0}%
          </div>
          <div className="text-sm text-gray-500">Negative</div>
        </div>
      </div>
    </div>
  );
};

export default MoodDistributionChart;