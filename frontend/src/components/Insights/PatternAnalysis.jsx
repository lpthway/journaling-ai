import React from 'react';
import { ChartBarIcon, ArrowTrendingUpIcon, TagIcon, ClockIcon } from '@heroicons/react/24/outline';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const PatternAnalysis = ({ data, preview = false }) => {
  if (!data?.patterns) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div className="text-center py-8">
          <ChartBarIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No pattern data available</h3>
          <p className="mt-1 text-sm text-gray-500">
            Write more entries to see your writing patterns!
          </p>
        </div>
      </div>
    );
  }

  const { patterns } = data;
  const {
    mood_distribution,
    writing_frequency,
    topic_usage,
    recent_trend
  } = patterns;

  // Prepare topic usage data for chart
  const topicChartData = Object.entries(topic_usage || {}).map(([topicId, count]) => ({
    topic: `Topic ${topicId.substring(0, 8)}...`,
    entries: count
  })).slice(0, 5); // Show top 5 topics

  if (preview) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Pattern Analysis Preview</h3>
          <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
            View Full Analysis
          </button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <PatternCard
            icon={ArrowTrendingUpIcon}
            title="Writing Trend"
            value={recent_trend || 'stable'}
            color="blue"
          />
          <PatternCard
            icon={ClockIcon}
            title="Consistency"
            value={`${writing_frequency?.entries_per_day || 0}/day`}
            color="green"
          />
          <PatternCard
            icon={TagIcon}
            title="Active Topics"
            value={Object.keys(topic_usage || {}).length}
            color="purple"
          />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <PatternCard
          icon={ArrowTrendingUpIcon}
          title="Recent Trend"
          value={recent_trend || 'stable'}
          description={getTrendDescription(recent_trend)}
          color="blue"
        />
        <PatternCard
          icon={ClockIcon}
          title="Daily Average"
          value={`${writing_frequency?.entries_per_day || 0}`}
          description="entries per day"
          color="green"
        />
        <PatternCard
          icon={ChartBarIcon}
          title="Avg Words"
          value={Math.round(writing_frequency?.avg_word_count || 0)}
          description="words per entry"
          color="purple"
        />
        <PatternCard
          icon={TagIcon}
          title="Active Topics"
          value={Object.keys(topic_usage || {}).length}
          description="topics in use"
          color="orange"
        />
      </div>

      {/* Writing Frequency Analysis */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Writing Frequency</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Consistency Score</h4>
            <div className="relative pt-1">
              <div className="flex mb-2 items-center justify-between">
                <div>
                  <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-green-600 bg-green-200">
                    {getConsistencyLabel(writing_frequency?.entries_per_day || 0)}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-xs font-semibold inline-block text-green-600">
                    {Math.round((writing_frequency?.entries_per_day || 0) * 100)}%
                  </span>
                </div>
              </div>
              <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-green-200">
                <div
                  style={{ width: `${Math.min((writing_frequency?.entries_per_day || 0) * 100, 100)}%` }}
                  className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-green-500"
                ></div>
              </div>
            </div>
          </div>
          
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Writing Insights</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Total entries analyzed: {writing_frequency?.total_entries || 0}</li>
              <li>• Average session length: {Math.round(writing_frequency?.avg_word_count || 0)} words</li>
              <li>• Writing momentum: {recent_trend || 'stable'}</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Topic Usage Chart */}
      {topicChartData.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Topic Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topicChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="topic" 
                  tick={{ fontSize: 12 }}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip 
                  formatter={(value) => [value, 'Entries']}
                  labelStyle={{ color: '#374151' }}
                />
                <Bar dataKey="entries" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Mood Patterns */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Mood Patterns</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Mood Distribution</h4>
            <div className="space-y-2">
              {Object.entries(mood_distribution || {}).map(([mood, count]) => {
                const total = Object.values(mood_distribution || {}).reduce((sum, c) => sum + c, 0);
                const percentage = total > 0 ? Math.round((count / total) * 100) : 0;
                
                return (
                  <div key={mood} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 capitalize">
                      {mood.replace('_', ' ')}
                    </span>
                    <div className="flex items-center space-x-2">
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${percentage}%` }}
                        ></div>
                      </div>
                      <span className="text-sm text-gray-500 w-10 text-right">
                        {percentage}%
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Insights</h4>
            <div className="text-sm text-gray-600 space-y-2">
              {getMoodInsights(mood_distribution).map((insight, index) => (
                <div key={index} className="flex items-start space-x-2">
                  <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                  <span>{insight}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Pattern Card Component
const PatternCard = ({ icon: Icon, title, value, description, color }) => {
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    orange: 'bg-orange-500',
    red: 'bg-red-500',
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="flex items-center">
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900 capitalize">{value}</p>
          {description && (
            <p className="text-xs text-gray-500 mt-1">{description}</p>
          )}
        </div>
      </div>
    </div>
  );
};

// Helper functions
const getTrendDescription = (trend) => {
  const descriptions = {
    improving: 'Writing more frequently',
    declining: 'Writing less frequently',
    stable: 'Consistent writing pattern',
    insufficient_data: 'Need more data'
  };
  return descriptions[trend] || 'No trend data';
};

const getConsistencyLabel = (entriesPerDay) => {
  if (entriesPerDay >= 0.8) return 'Excellent';
  if (entriesPerDay >= 0.5) return 'Good';
  if (entriesPerDay >= 0.3) return 'Fair';
  return 'Improving';
};

const getMoodInsights = (moodDistribution) => {
  if (!moodDistribution) return ['No mood data available'];
  
  const insights = [];
  const total = Object.values(moodDistribution).reduce((sum, count) => sum + count, 0);
  
  if (total === 0) return ['No mood data available'];
  
  const positive = ((moodDistribution.very_positive || 0) + (moodDistribution.positive || 0)) / total;
  const negative = ((moodDistribution.very_negative || 0) + (moodDistribution.negative || 0)) / total;
  
  if (positive > 0.6) {
    insights.push('You maintain a generally positive outlook in your writing');
  }
  
  if (negative > 0.4) {
    insights.push('You\'ve been processing some challenging emotions recently');
  }
  
  if (moodDistribution.neutral && moodDistribution.neutral / total > 0.5) {
    insights.push('Many of your entries reflect a balanced, neutral perspective');
  }
  
  return insights.length > 0 ? insights : ['Your mood patterns show a balanced emotional range'];
};

export default PatternAnalysis;