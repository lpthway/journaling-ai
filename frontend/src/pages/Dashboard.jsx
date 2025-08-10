// frontend/src/pages/Dashboard.jsx
import React, { useState, useEffect } from 'react';
import { 
  ChartBarIcon, 
  PencilSquareIcon, 
  ChatBubbleLeftRightIcon,
  HeartIcon,
  FireIcon,
  ArrowTrendingUpIcon,
  ClockIcon,
  BookOpenIcon
} from '@heroicons/react/24/outline';
import { 
  HeartIcon as HeartIconSolid,
  FireIcon as FireIconSolid 
} from '@heroicons/react/24/solid';
import { Link } from 'react-router-dom';
import { entryAPI, insightsAPI, dashboardAPI, performanceAPI } from '../services/api';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import ErrorState from '../components/Common/ErrorState';
import MoodIndicator from '../components/Common/MoodIndicator';
import MoodTimeline from '../components/Dashboard/MoodTimeline';
import PersonalityProfile from '../components/Dashboard/PersonalityProfile';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dashboardData, setDashboardData] = useState({
    stats: {
      totalEntries: 0,
      currentStreak: 0,
      entriesThisWeek: 0,
      avgWordsPerEntry: 0,
      totalWords: 0
    },
    recentEntries: [],
    allEntries: [],
    moodTrends: [],
    performance: null,
    insights: []
  });

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Use the new dashboard API for better performance
      const [dashboardResponse, moodResponse, performanceResponse] = await Promise.allSettled([
        entryAPI.getAll({ limit: 100 }), // Get more entries for better stats calculation
        entryAPI.getMoodStats(7), // Last 7 days
        performanceAPI.getStatus().catch(() => null)
      ]);

      const allEntries = dashboardResponse.status === 'fulfilled' ? dashboardResponse.value.data : [];
      const moodData = moodResponse.status === 'fulfilled' ? moodResponse.value.data : null;
      const performanceData = performanceResponse.status === 'fulfilled' ? performanceResponse.value : null;

      // Calculate stats from all entries for better accuracy
      const stats = calculateStats(allEntries);
      
      setDashboardData({
        stats,
        recentEntries: allEntries.slice(0, 3), // Show only 3 most recent entries
        allEntries: allEntries, // Store all entries for timeline
        moodTrends: moodData?.mood_distribution || [],
        performance: performanceData,
        insights: generateInsights(stats, moodData)
      });

    } catch (err) {
      console.error('Error loading dashboard data:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (entries) => {
    if (!entries || entries.length === 0) {
      return {
        totalEntries: 0,
        currentStreak: 0,
        entriesThisWeek: 0,
        avgWordsPerEntry: 0,
        totalWords: 0
      };
    }

    const now = new Date();
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    
    const entriesThisWeek = entries.filter(entry => 
      new Date(entry.created_at) > weekAgo
    ).length;

    const totalWords = entries.reduce((sum, entry) => sum + (entry.word_count || 0), 0);
    const avgWords = entries.length > 0 ? Math.round(totalWords / entries.length) : 0;

    // Simple streak calculation (consecutive days with entries)
    let streak = 0;
    const today = new Date().toDateString();
    const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000).toDateString();
    
    if (entries.length > 0) {
      const latestEntryDate = new Date(entries[0].created_at).toDateString();
      if (latestEntryDate === today || latestEntryDate === yesterday) {
        streak = 1; // Simplified - in real app, would check consecutive days
      }
    }

    return {
      totalEntries: entries.length,
      currentStreak: streak,
      entriesThisWeek,
      avgWordsPerEntry: avgWords,
      totalWords
    };
  };

  const generateInsights = (stats, moodData) => {
    const insights = [];
    
    if (stats.currentStreak > 0) {
      insights.push({
        type: 'positive',
        icon: FireIconSolid,
        title: 'Great consistency!',
        message: `You're on a ${stats.currentStreak} day writing streak.`
      });
    }

    if (stats.entriesThisWeek > 3) {
      insights.push({
        type: 'positive',
        icon: ArrowTrendingUpIcon,
        title: 'Active week',
        message: `You've written ${stats.entriesThisWeek} entries this week.`
      });
    }

    if (stats.avgWordsPerEntry > 200) {
      insights.push({
        type: 'info',
        icon: BookOpenIcon,
        title: 'Detailed writer',
        message: `Your entries average ${stats.avgWordsPerEntry} words.`
      });
    }

    return insights;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error} onRetry={loadDashboardData} />;
  }

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-6 text-white">
        <h1 className="text-3xl font-bold mb-2">Welcome back!</h1>
        <p className="text-blue-100">
          Ready to continue your journaling journey? Here's what's happening.
        </p>
      </div>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Current Streak"
          value={dashboardData.stats.currentStreak}
          suffix="days"
          icon={FireIcon}
          color="orange"
          trend={dashboardData.stats.currentStreak > 0 ? 'up' : null}
        />
        <StatCard
          title="This Week"
          value={dashboardData.stats.entriesThisWeek}
          suffix="entries"
          icon={PencilSquareIcon}
          color="blue"
        />
        <StatCard
          title="Total Entries"
          value={dashboardData.stats.totalEntries}
          icon={BookOpenIcon}
          color="green"
        />
        <StatCard
          title="Avg Words"
          value={dashboardData.stats.avgWordsPerEntry}
          suffix="per entry"
          icon={ChartBarIcon}
          color="purple"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Entries */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Recent Entries</h2>
              <Link
                to="/journal"
                className="text-blue-600 hover:text-blue-700 text-sm font-medium"
              >
                View all
              </Link>
            </div>
            
            {dashboardData.recentEntries.length === 0 ? (
              <div className="text-center py-8">
                <BookOpenIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <p className="text-gray-500 mb-4">No entries yet</p>
                <Link
                  to="/journal"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  <PencilSquareIcon className="h-4 w-4 mr-2" />
                  Write your first entry
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {dashboardData.recentEntries.map((entry) => (
                  <Link
                    key={entry.id}
                    to={`/entry/${entry.id}`}
                    className="block p-3 rounded-lg border hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-medium text-gray-900 truncate">
                          {entry.title}
                        </h3>
                        <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                          {entry.content?.substring(0, 100)}...
                        </p>
                        <div className="flex items-center mt-2 text-xs text-gray-400">
                          <ClockIcon className="h-3 w-3 mr-1" />
                          {formatDate(entry.created_at)}
                          {entry.word_count && (
                            <>
                              <span className="mx-2">•</span>
                              {entry.word_count} words
                            </>
                          )}
                        </div>
                      </div>
                      {entry.mood && (
                        <div className="ml-3 flex-shrink-0">
                          <MoodIndicator mood={entry.mood} size="sm" />
                        </div>
                      )}
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions & Insights */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <Link
                to="/journal"
                className="flex items-center p-3 rounded-lg border border-blue-200 bg-blue-50 hover:bg-blue-100 transition-colors"
              >
                <PencilSquareIcon className="h-5 w-5 text-blue-600 mr-3" />
                <span className="text-blue-700 font-medium">Write New Entry</span>
              </Link>
              
              <Link
                to="/chat"
                className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <ChatBubbleLeftRightIcon className="h-5 w-5 text-gray-600 mr-3" />
                <span className="text-gray-700">Start AI Chat</span>
              </Link>
              
              <Link
                to="/insights"
                className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <ChartBarIcon className="h-5 w-5 text-gray-600 mr-3" />
                <span className="text-gray-700">View Insights</span>
              </Link>
            </div>
          </div>

          {/* Mood Timeline */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <MoodTimeline entries={dashboardData.recentEntries.concat(
              // Get additional entries from our recent fetch for better timeline
              dashboardData.allEntries?.slice(3, 10) || []
            )} />
          </div>

          {/* AI Insights */}
          {dashboardData.insights.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">AI Insights</h2>
              <div className="space-y-3">
                {dashboardData.insights.map((insight, index) => (
                  <div key={index} className="flex items-start p-3 rounded-lg bg-gray-50">
                    <insight.icon className={`h-5 w-5 mr-3 mt-0.5 ${
                      insight.type === 'positive' ? 'text-green-600' : 
                      insight.type === 'warning' ? 'text-yellow-600' : 'text-blue-600'
                    }`} />
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {insight.title}
                      </p>
                      <p className="text-sm text-gray-600">
                        {insight.message}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Personality Profile */}
          <PersonalityProfile userId="1e05fb66-160a-4305-b84a-805c2f0c6910" />

          {/* System Performance (if admin/debug mode) */}
          {dashboardData.performance && process.env.NODE_ENV === 'development' && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">System Status</h2>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Cache Hit Rate</span>
                  <span className={`font-medium ${
                    dashboardData.performance.targets_compliance?.cache_hit_rate_target 
                      ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {(dashboardData.performance.performance_report?.cache?.hit_rate * 100 || 0).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">DB Response</span>
                  <span className={`font-medium ${
                    dashboardData.performance.targets_compliance?.db_query_target 
                      ? 'text-green-600' : 'text-yellow-600'
                  }`}>
                    {(dashboardData.performance.performance_report?.database?.query_response_time_ms || 0).toFixed(1)}ms
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Reusable StatCard Component
const StatCard = ({ title, value, suffix, icon: Icon, color, trend }) => {
  const colorClasses = {
    blue: 'bg-blue-500 text-blue-600',
    green: 'bg-green-500 text-green-600', 
    purple: 'bg-purple-500 text-purple-600',
    orange: 'bg-orange-500 text-orange-600',
    red: 'bg-red-500 text-red-600'
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-center">
        <div className={`flex-shrink-0 p-3 rounded-lg bg-opacity-10 ${colorClasses[color]?.split(' ')[0] || 'bg-gray-500'}`}>
          <Icon className={`h-6 w-6 ${colorClasses[color]?.split(' ')[1] || 'text-gray-600'}`} />
        </div>
        <div className="ml-4 flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <div className="flex items-baseline">
            <p className="text-2xl font-semibold text-gray-900">{value}</p>
            {suffix && (
              <p className="ml-2 text-sm text-gray-500">{suffix}</p>
            )}
            {trend === 'up' && (
              <ArrowTrendingUpIcon className="ml-2 h-4 w-4 text-green-500" />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;