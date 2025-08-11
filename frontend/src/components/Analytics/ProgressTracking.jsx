// frontend/src/components/Analytics/ProgressTracking.jsx
import React, { useState, useEffect } from 'react';
import { CalendarDaysIcon, ArrowPathIcon, TrophyIcon } from '@heroicons/react/24/outline';
import { analyticsApi } from '../../services/analyticsApi';
import { DEFAULT_USER_ID } from '../../config/user';
import LoadingSpinner from '../Common/LoadingSpinner';

const ProgressTracking = ({ days = 30, className = "" }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadProgressData();
  }, [days]);

  const loadProgressData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get writing activity data to calculate progress
      const activityData = await analyticsApi.getWritingActivity(days, DEFAULT_USER_ID);
      
      if (activityData) {
        // Calculate current week's progress
        const totalEntries = activityData.total_entries || 0;
        const activeDays = activityData.active_days || 0;
        const consistencyPercentage = activityData.consistency_percentage || 0;
        
        // Daily goal: at least 1 entry per day
        const dailyGoalProgress = Math.min(100, Math.round(consistencyPercentage));
        
        // Weekly goal: 7 entries per week (assume 4 weeks in 30 days)
        const weeksInPeriod = Math.ceil(days / 7);
        const expectedWeeklyEntries = weeksInPeriod * 7;
        const weeklyGoalStatus = totalEntries >= expectedWeeklyEntries ? 'Complete' : 'In Progress';
        
        // Monthly target: based on total entries
        const monthlyTarget = `${totalEntries}/${Math.max(30, days)} entries`;
        
        // Achievement level based on consistency
        const getAchievementLevel = (progress) => {
          if (progress >= 90) return 'Expert';
          if (progress >= 75) return 'Advanced';
          if (progress >= 60) return 'Intermediate';
          if (progress >= 40) return 'Beginner';
          return 'Getting Started';
        };

        setData({
          dailyGoalProgress,
          weeklyGoalStatus,
          monthlyTarget,
          achievementLevel: getAchievementLevel(dailyGoalProgress),
          streakDays: activityData.streak_info?.longest_streak || 0,
          completionRate: Math.round(consistencyPercentage),
          avgEntriesPerWeek: Math.round((totalEntries / weeksInPeriod) * 10) / 10,
          nextMilestone: totalEntries < 10 ? '10 entries' : 
                        totalEntries < 25 ? '25 entries' :
                        totalEntries < 50 ? '50 entries' : '100 entries'
        });
      }
    } catch (err) {
      console.error('Error loading progress data:', err);
      setError('Unable to load progress tracking');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="flex items-center justify-center h-40">
          <LoadingSpinner size="md" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-2">
            <CalendarDaysIcon className="h-6 w-6 text-purple-600" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Progress Tracking</h3>
              <p className="text-sm text-gray-500">Your journaling goals and achievements</p>
            </div>
          </div>
          <ArrowPathIcon className="h-4 w-4 text-gray-400" />
        </div>
        <div className="text-center text-gray-500 py-8">
          <TrophyIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>No progress data available</p>
          <p className="text-sm">Set goals to track your progress</p>
        </div>
      </div>
    );
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'Complete': return 'text-green-600';
      case 'In Progress': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };

  const getAchievementColor = (level) => {
    switch (level) {
      case 'Expert': return 'text-purple-600';
      case 'Advanced': return 'text-blue-600';
      case 'Intermediate': return 'text-green-600';
      case 'Beginner': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <CalendarDaysIcon className="h-6 w-6 text-purple-600" />
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Progress Tracking</h3>
            <p className="text-sm text-gray-500">Your journaling goals and achievements</p>
          </div>
        </div>
        <button
          onClick={loadProgressData}
          className="p-2 text-gray-400 hover:text-gray-600 rounded-md transition-colors"
          title="Refresh data"
        >
          <ArrowPathIcon className="h-4 w-4" />
        </button>
      </div>

      {/* Progress Metrics */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Daily goal progress</span>
          <div className="flex items-center space-x-2">
            <span className="font-medium text-purple-600">{data.dailyGoalProgress}%</span>
            <div className="w-16 h-2 bg-gray-200 rounded-full">
              <div 
                className="h-full bg-purple-600 rounded-full transition-all duration-300"
                style={{ width: `${data.dailyGoalProgress}%` }}
              />
            </div>
          </div>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Weekly goal</span>
          <span className={`font-medium ${getStatusColor(data.weeklyGoalStatus)}`}>
            {data.weeklyGoalStatus === 'Complete' ? '✓ ' : ''}
            {data.weeklyGoalStatus}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Monthly target</span>
          <span className="font-medium text-gray-900">{data.monthlyTarget}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Achievement level</span>
          <span className={`font-medium ${getAchievementColor(data.achievementLevel)}`}>
            {data.achievementLevel}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Current streak</span>
          <span className="font-medium text-orange-600">{data.streakDays} days</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Next milestone</span>
          <span className="font-medium text-blue-600">{data.nextMilestone}</span>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="grid grid-cols-2 gap-4 text-center">
          <div>
            <p className="text-2xl font-bold text-purple-600">{data.completionRate}%</p>
            <p className="text-sm text-gray-500">Completion Rate</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-green-600">{data.avgEntriesPerWeek}</p>
            <p className="text-sm text-gray-500">Avg per Week</p>
          </div>
        </div>
      </div>

      {/* Motivational Message */}
      <div className="mt-4 p-3 bg-purple-50 rounded-lg border border-purple-100">
        <div className="flex items-center space-x-2">
          <TrophyIcon className="h-5 w-5 text-purple-600" />
          <p className="text-sm text-purple-700">
            {data.dailyGoalProgress >= 80 
              ? "Great job! You're maintaining excellent consistency!" 
              : data.dailyGoalProgress >= 60
              ? "Good progress! Keep building your journaling habit."
              : "Every entry counts. Keep going to build momentum!"}
          </p>
        </div>
      </div>
    </div>
  );
};

export default ProgressTracking;