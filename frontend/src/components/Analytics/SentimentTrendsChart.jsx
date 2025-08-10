// frontend/src/components/Analytics/SentimentTrendsChart.jsx
import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { ChartBarIcon, ArrowPathIcon, CalendarDaysIcon } from '@heroicons/react/24/outline';
import { insightsAPI } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';

const SentimentTrendsChart = ({ days = 30, className = "" }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeframe, setTimeframe] = useState(days);

  useEffect(() => {
    loadSentimentData();
  }, [timeframe]);

  const loadSentimentData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await insightsAPI.getMoodTrends(timeframe);
      const sentimentData = response.data;

      // Transform the data for the line chart
      if (sentimentData.daily_sentiments && Object.keys(sentimentData.daily_sentiments).length > 0) {
        const chartData = Object.entries(sentimentData.daily_sentiments)
          .map(([date, sentiments]) => {
            // Calculate average sentiment for the day
            const avgSentiment = sentiments.reduce((sum, s) => sum + s, 0) / sentiments.length;
            
            return {
              date: new Date(date).toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric' 
              }),
              fullDate: date,
              sentiment: Number(avgSentiment.toFixed(2)),
              entries: sentiments.length,
              // Separate positive/negative for better visualization
              positive: sentiments.filter(s => s > 0.1).length,
              negative: sentiments.filter(s => s < -0.1).length,
              neutral: sentiments.filter(s => s >= -0.1 && s <= 0.1).length
            };
          })
          .sort((a, b) => new Date(a.fullDate) - new Date(b.fullDate))
          .slice(-timeframe); // Keep only the requested timeframe

        setData(chartData);
      } else {
        // No data available - show empty state
        setData([]);
      }
    } catch (err) {
      console.error('Error loading sentiment data:', err);
      setError('Unable to load sentiment trends');
    } finally {
      setLoading(false);
    }
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900 mb-2">{label}</p>
          <div className="space-y-1 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Sentiment Score:</span>
              <span className={`font-medium ${
                data.sentiment > 0.1 ? 'text-green-600' : 
                data.sentiment < -0.1 ? 'text-red-600' : 'text-gray-600'
              }`}>
                {data.sentiment > 0 ? '+' : ''}{data.sentiment}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Entries:</span>
              <span className="font-medium text-gray-900">{data.entries}</span>
            </div>
            {data.positive > 0 && (
              <div className="flex items-center justify-between">
                <span className="text-green-600">Positive:</span>
                <span className="font-medium text-green-600">{data.positive}</span>
              </div>
            )}
            {data.negative > 0 && (
              <div className="flex items-center justify-between">
                <span className="text-red-600">Negative:</span>
                <span className="font-medium text-red-600">{data.negative}</span>
              </div>
            )}
            {data.neutral > 0 && (
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Neutral:</span>
                <span className="font-medium text-gray-600">{data.neutral}</span>
              </div>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  const getSentimentColor = (sentiment) => {
    if (sentiment > 0.1) return '#10B981'; // Green
    if (sentiment < -0.1) return '#EF4444'; // Red
    return '#6B7280'; // Gray
  };

  const timeframeOptions = [
    { value: 7, label: '7 days' },
    { value: 14, label: '14 days' },
    { value: 30, label: '30 days' },
    { value: 90, label: '90 days' }
  ];

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
          <ChartBarIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p className="mb-2">{error}</p>
          <button 
            onClick={loadSentimentData}
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
          <ChartBarIcon className="h-6 w-6 text-blue-600" />
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Sentiment Trends</h3>
            <p className="text-sm text-gray-500">
              Daily sentiment patterns over time
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          {/* Timeframe Selector */}
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(Number(e.target.value))}
            className="text-sm border border-gray-300 rounded-md px-3 py-1 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {timeframeOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
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

      {/* Chart */}
      {data.length > 0 ? (
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="date" 
                stroke="#6b7280"
                fontSize={12}
                tick={{ fill: '#6b7280' }}
              />
              <YAxis 
                domain={[-1, 1]}
                stroke="#6b7280"
                fontSize={12}
                tick={{ fill: '#6b7280' }}
                tickFormatter={(value) => value.toFixed(1)}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="sentiment"
                stroke="#3B82F6"
                strokeWidth={3}
                dot={{ r: 4, strokeWidth: 2 }}
                activeDot={{ r: 6, strokeWidth: 2 }}
                animationDuration={1000}
              />
              {/* Zero line */}
              <Line
                type="monotone"
                dataKey={() => 0}
                stroke="#d1d5db"
                strokeWidth={1}
                strokeDasharray="3 3"
                dot={false}
                activeDot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="text-center py-12 text-gray-500">
          <ChartBarIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p className="text-sm">No sentiment data available</p>
          <p className="text-xs text-gray-400 mt-1">Start journaling to see your sentiment trends</p>
        </div>
      )}

      {/* Summary Stats */}
      {data.length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {data.reduce((sum, d) => sum + d.entries, 0)}
              </p>
              <p className="text-sm text-gray-500">Total Entries</p>
            </div>
            <div>
              <p className={`text-2xl font-bold ${
                data.reduce((sum, d) => sum + d.sentiment, 0) / data.length > 0 
                  ? 'text-green-600' : 'text-red-600'
              }`}>
                {((data.reduce((sum, d) => sum + d.sentiment, 0) / data.length) || 0).toFixed(2)}
              </p>
              <p className="text-sm text-gray-500">Avg Sentiment</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-green-600">
                {Math.round((data.filter(d => d.sentiment > 0.1).length / data.length) * 100) || 0}%
              </p>
              <p className="text-sm text-gray-500">Positive Days</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-600">
                {Math.max(...data.map(d => d.sentiment)).toFixed(2)}
              </p>
              <p className="text-sm text-gray-500">Highest Score</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SentimentTrendsChart;