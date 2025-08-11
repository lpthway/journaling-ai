// frontend/src/components/Analytics/SentimentTrendsChart.jsx
import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ChartBarIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import { analyticsApi } from '../../services/analyticsApi';
import { DEFAULT_USER_ID } from '../../config/user';
import LoadingSpinner from '../Common/LoadingSpinner';

const SentimentTrendsChart = ({ days = 30, className = "" }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    loadSentimentData();
  }, [days]);

  const loadSentimentData = async () => {
    try {
      setLoading(true);
      setError(null);

      const sentimentData = await analyticsApi.getEmotionalPatterns(days, DEFAULT_USER_ID);

      // Transform daily trends data for the line chart
      if (sentimentData.daily_trends && sentimentData.daily_trends.length > 0) {
        const chartData = sentimentData.daily_trends.map(day => ({
          date: new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          sentiment: day.avg_sentiment || 0,
          entries: day.entry_count || 0
        }));

        setData(chartData);
        // Calculate actual positive days from daily trends
        const positiveDaysCount = sentimentData.daily_trends.filter(day => 
          day.avg_sentiment > 0.5 // Days with sentiment above neutral
        ).length;
        const positiveDaysPercentage = Math.round((positiveDaysCount / sentimentData.daily_trends.length) * 100);

        setStats({
          totalEntries: sentimentData.statistics.total_entries,
          avgSentiment: sentimentData.statistics.overall_sentiment,
          positiveDays: positiveDaysPercentage, // Now shows actual positive days percentage
          highestScore: Math.max(...chartData.map(d => d.sentiment))
        });
      } else {
        setData([]);
        setStats(null);
      }
    } catch (err) {
      console.error('Error loading sentiment data:', err);
      setError('Unable to load sentiment trends');
    } finally {
      setLoading(false);
    }
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

  if (error || data.length === 0) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-2">
            <ChartBarIcon className="h-6 w-6 text-blue-600" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Sentiment Trends</h3>
              <p className="text-sm text-gray-500">Daily sentiment patterns over time</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <select className="text-sm border border-gray-300 rounded px-3 py-1">
              <option value="30">{days} days</option>
            </select>
            <ArrowPathIcon className="h-4 w-4 text-gray-400" />
          </div>
        </div>
        <div className="text-center text-gray-500 py-12">
          <ChartBarIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>No sentiment data available</p>
          <p className="text-sm">Start journaling to see your sentiment trends</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      {/* Header matching screenshot */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <ChartBarIcon className="h-6 w-6 text-blue-600" />
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Sentiment Trends</h3>
            <p className="text-sm text-gray-500">Daily sentiment patterns over time</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <select 
            value={days}
            className="text-sm border border-gray-300 rounded px-3 py-1 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="30">30 days</option>
            <option value="60">60 days</option>
            <option value="90">90 days</option>
          </select>
          <button
            onClick={loadSentimentData}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-md transition-colors"
            title="Refresh data"
          >
            <ArrowPathIcon className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Line Chart */}
      <div className="h-64 mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 12 }}
              stroke="#6b7280"
            />
            <YAxis 
              domain={[-1, 1]}
              tick={{ fontSize: 12 }}
              stroke="#6b7280"
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}
              formatter={(value, name) => [value.toFixed(2), 'Sentiment']}
            />
            <Line 
              type="monotone" 
              dataKey="sentiment" 
              stroke="#3b82f6" 
              strokeWidth={2}
              dot={{ r: 3, fill: '#3b82f6' }}
              activeDot={{ r: 5, fill: '#3b82f6' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Statistics row matching screenshot */}
      <div className="grid grid-cols-4 gap-4 text-center">
        <div>
          <div className="text-2xl font-bold text-gray-900">{stats?.totalEntries || 0}</div>
          <div className="text-sm text-gray-500">Total Entries</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-green-600">
            {(stats?.avgSentiment || 0).toFixed(2)}
          </div>
          <div className="text-sm text-gray-500">Avg Sentiment</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-blue-600">
            {stats?.positiveDays || 0}%
          </div>
          <div className="text-sm text-gray-500">Positive Days</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-purple-600">
            {(stats?.highestScore || 0).toFixed(2)}
          </div>
          <div className="text-sm text-gray-500">Highest Score</div>
        </div>
      </div>
    </div>
  );
};

export default SentimentTrendsChart;