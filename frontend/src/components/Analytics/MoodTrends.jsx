import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { format, parseISO } from 'date-fns';

const MoodTrends = ({ data, timeRange, isComprehensive = false }) => {
  const [selectedView, setSelectedView] = useState('combined'); // 'combined', 'journal', 'chat'
  
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
          <p className="text-sm font-medium mb-2">{format(parseISO(data.fullDate), 'MMM d, yyyy')}</p>
          
          {isComprehensive ? (
            <div className="space-y-1">
              {data.combined_mood_score !== null && (
                <p className="text-sm text-gray-600">
                  Combined Score: {data.combined_mood_score.toFixed(1)}
                </p>
              )}
              {data.journal_mood_score !== null && (
                <p className="text-sm text-blue-600">
                  📔 Journal: {data.journal_mood_score.toFixed(1)} ({data.journal_entry_count} entries)
                </p>
              )}
              {data.chat_mood_score !== null && (
                <p className="text-sm text-purple-600">
                  💬 Chat: {data.chat_mood_score.toFixed(1)} ({data.chat_conversation_count} conversations)
                </p>
              )}
              {data.total_activity_count === 0 && (
                <p className="text-sm text-gray-400">No activity</p>
              )}
            </div>
          ) : (
            <div>
              <p className="text-sm text-gray-600">
                Mood Score: {data.mood_score?.toFixed(1) || 'N/A'}
              </p>
              <p className="text-sm text-gray-600">
                Entries: {data.entry_count || 0}
              </p>
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  // Get trend direction and stats
  const getTrendInfo = () => {
    if (isComprehensive) {
      const trends = {
        combined: data.combined_trend_direction,
        journal: data.journal_trend_direction,
        chat: data.chat_trend_direction
      };
      
      const totals = {
        combined: data.total_activities,
        journal: data.total_journal_entries,
        chat: data.total_chat_conversations
      };
      
      return { trends, totals };
    } else {
      return {
        trends: { [selectedView]: data.trend_direction },
        totals: { [selectedView]: data.total_entries }
      };
    }
  };

  const { trends, totals } = getTrendInfo();

  const trendColors = {
    improving: 'text-green-600',
    declining: 'text-red-600',
    stable: 'text-gray-600',
    insufficient_data: 'text-gray-400'
  };

  const trendText = {
    improving: 'Improving',
    declining: 'Declining',
    stable: 'Stable',
    insufficient_data: 'Insufficient data'
  };

  // Determine which lines to show based on selected view
  const getDataKey = () => {
    if (!isComprehensive) return 'mood_score';
    
    switch (selectedView) {
      case 'journal': return 'journal_mood_score';
      case 'chat': return 'chat_mood_score';
      case 'combined': return 'combined_mood_score';
      default: return 'combined_mood_score';
    }
  };

  const getLineColor = () => {
    switch (selectedView) {
      case 'journal': return '#3B82F6'; // Blue
      case 'chat': return '#8B5CF6'; // Purple
      case 'combined': return '#10B981'; // Green
      default: return '#3B82F6';
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Mood Trends</h3>
          {isComprehensive ? (
            <div className="text-sm text-gray-500 space-y-1">
              <p>📔 {totals.journal} journal entries • 💬 {totals.chat} conversations</p>
              <p>{data.data_summary?.days_with_any_activity || 0} active days out of {timeRange}</p>
            </div>
          ) : (
            <p className="text-sm text-gray-500">
              {totals[selectedView]} entries over {timeRange} days
            </p>
          )}
        </div>
        <div className={`text-sm font-medium ${trendColors[trends[selectedView]]}`}>
          {trendText[trends[selectedView]]} trend
        </div>
      </div>

      {/* View Toggle (only for comprehensive data) */}
      {isComprehensive && (
        <div className="flex space-x-2 mb-4">
          <button
            onClick={() => setSelectedView('combined')}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              selectedView === 'combined'
                ? 'bg-green-100 text-green-700 border border-green-200'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            Combined
          </button>
          <button
            onClick={() => setSelectedView('journal')}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              selectedView === 'journal'
                ? 'bg-blue-100 text-blue-700 border border-blue-200'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            📔 Journal Only
          </button>
          <button
            onClick={() => setSelectedView('chat')}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              selectedView === 'chat'
                ? 'bg-purple-100 text-purple-700 border border-purple-200'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            💬 Chat Only
          </button>
        </div>
      )}

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
              dataKey={getDataKey()}
              stroke={getLineColor()}
              strokeWidth={2}
              dot={{ fill: getLineColor(), strokeWidth: 2, r: 3 }}
              activeDot={{ r: 5, fill: getLineColor() }}
              connectNulls={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Activity Summary (for comprehensive view) */}
      {isComprehensive && data.data_summary && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-600 mb-1">Activity Summary:</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
            <div>
              <span className="font-medium">{data.data_summary.days_with_journal_entries}</span>
              <span className="text-gray-500"> days with journals</span>
            </div>
            <div>
              <span className="font-medium">{data.data_summary.days_with_chat_conversations}</span>
              <span className="text-gray-500"> days with chats</span>
            </div>
            <div>
              <span className="font-medium">{data.data_summary.days_with_any_activity}</span>
              <span className="text-gray-500"> active days</span>
            </div>
            <div>
              <span className="font-medium">{Math.round((data.data_summary.days_with_any_activity / data.data_summary.total_days_in_period) * 100)}%</span>
              <span className="text-gray-500"> activity rate</span>
            </div>
          </div>
        </div>
      )}

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