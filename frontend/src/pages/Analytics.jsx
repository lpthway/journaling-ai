// frontend/src/pages/Analytics.jsx
import React, { useState, useEffect } from 'react';
import { 
  ChartBarIcon, 
  ChartPieIcon, 
  CalendarDaysIcon,
  ArrowTrendingUpIcon 
} from '@heroicons/react/24/outline';
import MoodDistributionChart from '../components/Analytics/MoodDistributionChart';
import SentimentTrendsChart from '../components/Analytics/SentimentTrendsChart';
import WritingActivityHeatmap from '../components/Analytics/WritingActivityHeatmap';
import PersonalityProfile from '../components/Dashboard/PersonalityProfile';
import { analyticsApi } from '../services/analyticsApi';
import { DEFAULT_USER_ID } from '../config/user';

const Analytics = () => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadAnalyticsData();
  }, []);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      const data = await analyticsApi.getAnalyticsSummary(30);
      setAnalyticsData(data);
      setError(null);
    } catch (err) {
      console.error('Error loading analytics:', err);
      setError('Unable to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-3">
            <ArrowTrendingUpIcon className="h-8 w-8 text-blue-600" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
              <p className="text-gray-600 mt-1">
                Comprehensive insights into your journaling patterns and emotional well-being
              </p>
            </div>
          </div>
        </div>

        {/* Analytics Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Mood Distribution Chart */}
          <MoodDistributionChart className="lg:col-span-1" />

          {/* Sentiment Trends Chart */}
          <SentimentTrendsChart className="lg:col-span-1" />
        </div>

        {/* Writing Activity Heatmap - Full Width */}
        <div className="mb-8">
          <WritingActivityHeatmap className="w-full" />
        </div>

        {/* Personality Profile - Full Width */}
        <div className="mb-8">
          <PersonalityProfile userId={DEFAULT_USER_ID} />
        </div>

        {/* Additional Analytics Cards - Populated with real data */}
        {analyticsData && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {/* Quick Stats Card */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center space-x-3 mb-4">
                <ChartBarIcon className="h-6 w-6 text-indigo-600" />
                <h3 className="text-lg font-semibold text-gray-900">Writing Insights</h3>
              </div>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Most active day</span>
                  <span className="font-medium text-gray-900">{analyticsData.writingInsights.mostActiveDay}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Avg words per entry</span>
                  <span className="font-medium text-gray-900">{Math.round(analyticsData.writingInsights.avgWordsPerEntry)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Longest streak</span>
                  <span className="font-medium text-gray-900">{analyticsData.writingInsights.longestStreak} days</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Favorite time</span>
                  <span className="font-medium text-gray-900">{analyticsData.writingInsights.favoriteTime}</span>
                </div>
              </div>
            </div>

            {/* Mood Insights Card */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center space-x-3 mb-4">
                <ChartPieIcon className="h-6 w-6 text-green-600" />
                <h3 className="text-lg font-semibold text-gray-900">Emotional Patterns</h3>
              </div>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Emotional stability</span>
                  <span className="font-medium text-green-600">{analyticsData.emotionalPatterns.emotionalStability}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Positive trend</span>
                  <span className="font-medium text-green-600">↗ {analyticsData.emotionalPatterns.positiveTrend}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Resilience score</span>
                  <span className="font-medium text-gray-900">{analyticsData.emotionalPatterns.resilienceScore}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Growth areas</span>
                  <span className="font-medium text-blue-600">{analyticsData.emotionalPatterns.growthAreas} identified</span>
                </div>
              </div>
            </div>

            {/* Goals & Progress Card */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center space-x-3 mb-4">
                <CalendarDaysIcon className="h-6 w-6 text-purple-600" />
                <h3 className="text-lg font-semibold text-gray-900">Progress Tracking</h3>
              </div>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Daily goal progress</span>
                  <span className="font-medium text-purple-600">{analyticsData.progressTracking.dailyGoalProgress}%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Weekly goal</span>
                  <span className="font-medium text-green-600">
                    {analyticsData.progressTracking.weeklyGoalStatus === 'Complete' ? '✓ ' : ''}
                    {analyticsData.progressTracking.weeklyGoalStatus}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Monthly target</span>
                  <span className="font-medium text-gray-900">{analyticsData.progressTracking.monthlyTarget}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Achievement level</span>
                  <span className="font-medium text-yellow-600">{analyticsData.progressTracking.achievementLevel}</span>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Loading and Error States */}
        {loading && (
          <div className="mb-8 text-center py-8">
            <div className="text-gray-600">Loading analytics data...</div>
          </div>
        )}
        
        {error && !analyticsData && (
          <div className="mb-8 text-center py-8">
            <div className="text-red-600">{error}</div>
            <button 
              onClick={loadAnalyticsData}
              className="mt-2 text-indigo-600 hover:text-indigo-800 underline"
            >
              Try Again
            </button>
          </div>
        )}
        
        {!loading && !error && !analyticsData && (
          <div className="mb-8 text-center py-8">
            <div className="text-gray-600">No analytics data available. Start journaling to see insights!</div>
          </div>
        )}

        {/* Export and Actions */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Data & Insights</h3>
              <p className="text-sm text-gray-600">
                Export your data or get personalized recommendations based on your patterns
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <button className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors">
                Export Data
              </button>
              <button className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors">
                Get Recommendations
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;