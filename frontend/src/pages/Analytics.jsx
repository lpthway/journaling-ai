// frontend/src/pages/Analytics.jsx
import React, { useState, useEffect } from 'react';
import { 
  ArrowTrendingUpIcon 
} from '@heroicons/react/24/outline';
import MoodDistributionChart from '../components/Analytics/MoodDistributionChart';
import SentimentTrendsChart from '../components/Analytics/SentimentTrendsChart';
import WritingActivityHeatmap from '../components/Analytics/WritingActivityHeatmap';
import WritingInsights from '../components/Analytics/WritingInsights';
import EmotionalPatterns from '../components/Analytics/EmotionalPatterns';
import ProgressTracking from '../components/Analytics/ProgressTracking';
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

        {/* Main Analytics Grid - Top Row (Charts) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <MoodDistributionChart className="lg:col-span-1" />
          <SentimentTrendsChart className="lg:col-span-1" />
        </div>

        {/* Writing Activity Heatmap - Full Width */}
        <div className="mb-8">
          <WritingActivityHeatmap className="w-full" />
        </div>

        {/* Insights Grid - Three Column Layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <WritingInsights className="lg:col-span-1" />
          <EmotionalPatterns className="lg:col-span-1" />
          <ProgressTracking className="lg:col-span-1" />
        </div>

        {/* Personality Profile - Full Width */}
        <div className="mb-8">
          <PersonalityProfile userId={DEFAULT_USER_ID} />
        </div>
        
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