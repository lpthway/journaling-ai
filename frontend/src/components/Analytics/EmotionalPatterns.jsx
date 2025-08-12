// frontend/src/components/Analytics/EmotionalPatterns.jsx
import React, { useState, useEffect } from 'react';
import { ChartPieIcon, ArrowPathIcon, HeartIcon } from '@heroicons/react/24/outline';
import { analyticsApi } from '../../services/analyticsApi';
// Removed /* removed user id */ import - using authenticated user
import LoadingSpinner from '../Common/LoadingSpinner';

const EmotionalPatterns = ({ days = 30, className = "" }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadEmotionalData();
  }, [days]);

  const loadEmotionalData = async () => {
    try {
      setLoading(true);
      setError(null);

      const patterns = await analyticsApi.getEmotionalPatterns(days);
      
      if (patterns && patterns.statistics) {
        const stats = patterns.statistics;
        const moodDist = patterns.mood_distribution || {};
        
        // Calculate emotional stability based on sentiment variance
        const getStabilityLevel = (consistency) => {
          if (consistency >= 80) return 'Excellent';
          if (consistency >= 70) return 'Good';
          if (consistency >= 60) return 'Fair';
          return 'Needs Focus';
        };

        // Calculate sentiment level (not a real trend - would need historical data)
        const getSentimentLevel = (sentiment) => {
          if (sentiment > 0.6) return 'Very Positive';
          if (sentiment > 0.5) return 'Positive'; 
          if (sentiment > 0.4) return 'Neutral+';
          if (sentiment > 0.3) return 'Neutral';
          return 'Needs Attention';
        };

        // Calculate resilience score out of 10
        const getResilienceScore = (sentiment, consistency) => {
          // API sentiment is 0-1, so convert to 0-10 scale properly
          const baseScore = sentiment * 10; // Convert 0-1 to 0-10
          const consistencyBonus = (consistency / 100) * 2; // Max 2 bonus points
          return Math.min(10, Math.round((baseScore + consistencyBonus) * 10) / 10);
        };

        // Calculate actual positive percentage from mood distribution
        const actualPositivePercentage = moodDist.positive ? Math.round(moodDist.positive.percentage) : 0;
        
        // Calculate mood stability score (more meaningful than variance)
        const calculateMoodStability = () => {
          if (!moodDist.positive || !moodDist.negative || !moodDist.neutral) return 0;
          
          const positive = moodDist.positive.percentage;
          const negative = moodDist.negative.percentage;
          const neutral = moodDist.neutral.percentage;
          
          // Higher stability = less extreme moods, more balanced
          // Score based on how balanced the distribution is vs extreme concentration
          const extremeConcentration = Math.max(positive, negative, neutral);
          const stabilityScore = 100 - extremeConcentration;
          
          return Math.max(0, Math.min(100, stabilityScore));
        };
        
        // Count growth areas based on actual data
        const calculateGrowthAreas = () => {
          let areas = 0;
          if (stats.overall_sentiment < 0.4) areas++; // Low overall sentiment
          if (stats.consistency_percentage < 70) areas++; // Inconsistent mood
          if (moodDist.negative && moodDist.negative.percentage > 40) areas++; // High negativity
          return Math.max(1, areas); // At least 1 area
        };

        // Calculate emotional range from mood distribution
        const calculateEmotionalRange = () => {
          if (!moodDist.positive || !moodDist.negative) return 'Limited Data';
          const range = moodDist.positive.percentage + moodDist.negative.percentage;
          if (range > 60) return 'Wide Range';
          if (range > 30) return 'Balanced';
          return 'Stable';
        };

        setData({
          emotionalStability: getStabilityLevel(stats.consistency_percentage),
          positiveTrend: getSentimentLevel(stats.overall_sentiment),
          resilienceScore: getResilienceScore(stats.overall_sentiment, stats.consistency_percentage),
          growthAreas: calculateGrowthAreas(),
          moodVariance: calculateMoodStability() / 100, // Convert to 0-1 for percentage display
          positivePercentage: actualPositivePercentage, // Use actual percentage from API
          stabilityTrend: stats.consistency_percentage >= 70 ? 'Improving' : 'Fluctuating',
          emotionalRange: calculateEmotionalRange()
        });
      }
    } catch (err) {
      console.error('Error loading emotional patterns:', err);
      setError('Unable to load emotional patterns');
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
            <ChartPieIcon className="h-6 w-6 text-green-600" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Emotional Patterns</h3>
              <p className="text-sm text-gray-500">Your emotional well-being insights</p>
            </div>
          </div>
          <ArrowPathIcon className="h-4 w-4 text-gray-400" />
        </div>
        <div className="text-center text-gray-500 py-8">
          <HeartIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>No emotional data available</p>
          <p className="text-sm">Start journaling to see your patterns</p>
        </div>
      </div>
    );
  }

  const getStabilityColor = (stability) => {
    switch (stability) {
      case 'Excellent': return 'text-green-600';
      case 'Good': return 'text-green-600';
      case 'Fair': return 'text-yellow-600';
      default: return 'text-red-600';
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <ChartPieIcon className="h-6 w-6 text-green-600" />
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Emotional Patterns</h3>
            <p className="text-sm text-gray-500">Your emotional well-being insights</p>
          </div>
        </div>
        <button
          onClick={loadEmotionalData}
          className="p-2 text-gray-400 hover:text-gray-600 rounded-md transition-colors"
          title="Refresh data"
        >
          <ArrowPathIcon className="h-4 w-4" />
        </button>
      </div>

      {/* Emotional Insights Grid */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Emotional stability</span>
          <span className={`font-medium ${getStabilityColor(data.emotionalStability)}`}>
            {data.emotionalStability}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Overall sentiment</span>
          <span className="font-medium text-gray-600">{data.positiveTrend}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Resilience score</span>
          <span className="font-medium text-gray-900">{data.resilienceScore}/10</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Growth areas</span>
          <span className="font-medium text-blue-600">{data.growthAreas} identified</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Emotional range</span>
          <span className="font-medium text-gray-900">{data.emotionalRange}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Stability trend</span>
          <span className={`font-medium ${data.stabilityTrend === 'Improving' ? 'text-green-600' : 'text-yellow-600'}`}>
            {data.stabilityTrend}
          </span>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="grid grid-cols-2 gap-4 text-center">
          <div>
            <p className="text-2xl font-bold text-green-600">{data.positivePercentage}%</p>
            <p className="text-sm text-gray-500">Positive Mood</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-blue-600">
              {Math.round(data.moodVariance * 100)}%
            </p>
            <p className="text-sm text-gray-500">Mood Balance</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmotionalPatterns;