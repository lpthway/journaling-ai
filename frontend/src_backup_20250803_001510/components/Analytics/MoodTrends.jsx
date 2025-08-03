import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { format, parseISO } from 'date-fns';

const MoodTrends = ({ data, timeRange }) => {
  if (!data?.daily_data || data.daily_data.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div className="text-center py-8">
          <p className="text-gray-500">No trend data available for the selected period</p>
        </div>
      </div>
    );
  }

  // Format data for the chart
  const chartData = data.daily_data.map(item => ({
    ...item,
    date: format(parseISO(item.date), 'MMM d'),
    fullDate: item.date
  }));

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="text-sm font-medium mb-1">{format(parseISO(data.fullDate), 'MMM d, yyyy')}</p>
          <p className="text-sm text-gray-600">
            Mood Score: {data.mood_score.toFixed(1)}
          </p>
          <p className="text-sm text-gray-600">
            Entries: {data.entry_count}
          </p>
        </div>
      );
    }
    return null;
  };

  const getMoodScoreColor = (score) => {
    if (score >= 1) return '#10B981'; // Green
    if (score >= 0.5) return '#6EE7B7'; // Light Green
    if (score >= -0.5) return '#9CA3AF'; // Gray
    if (score >= -1) return '#F87171'; // Light Red
    return '#EF4444'; // Red
  };

  const trendDirection = data.trend_direction;
  const trendColors = {
    improving: 'text-green-600',
    declining: 'text-red-600',
    stable: 'text-gray-600',
    insufficient_data: 'text-gray-400'
  };

  const trendText = {
    improving: 'Improving trend',
    declining: 'Declining trend',
    stable: 'Stable trend',
    insufficient_data: 'Not enough data'
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Mood Trends</h3>
          <p className="text-sm text-gray-500">
            {data.total_entries} entries over {timeRange} days
          </p>
        </div>
        <div className={`text-sm font-medium ${trendColors[trendDirection]}`}>
          {trendText[trendDirection]}
        </div>
      </div>

      {/* Chart */}
      <div className="h-64 mb-4">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 12 }}
              stroke="#6b7280"
            />
            <YAxis 
              domain={[-2, 2]}
              tick={{ fontSize: 12 }}
              stroke="#6b7280"
              tickFormatter={(value) => {
                if (value === 2) return 'Very Positive';
                if (value === 1) return 'Positive';
                if (value === 0) return 'Neutral';
                if (value === -1) return 'Negative';
                if (value === -2) return 'Very Negative';
                return value;
              }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line 
              type="monotone" 
              dataKey="mood_score" 
              stroke="#3B82F6"
              strokeWidth={2}
              dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, fill: '#1D4ED8' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Mood Scale Reference */}
      <div className="border-t pt-4">
        <p className="text-xs text-gray-500 mb-2">Mood Scale:</p>
        <div className="flex items-center space-x-4 text-xs">
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span>Very Negative (-2)</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 rounded-full bg-red-300"></div>
            <span>Negative (-1)</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 rounded-full bg-gray-400"></div>
            <span>Neutral (0)</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 rounded-full bg-green-300"></div>
            <span>Positive (1)</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span>Very Positive (2)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MoodTrends;