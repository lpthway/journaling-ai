// frontend/src/components/Dashboard/PersonalityProfile.jsx
import React, { useState, useEffect } from 'react';
import { 
  UserIcon, 
  SparklesIcon, 
  LightBulbIcon,
  ArrowTrendingUpIcon,
  HeartIcon,
  CpuChipIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { advancedAI } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';

const PersonalityProfile = ({ userId = '1e05fb66-160a-4305-b84a-805c2f0c6910' }) => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    loadPersonalityProfile();
  }, [userId]);

  const loadPersonalityProfile = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await advancedAI.getPersonalityProfile(userId);
      setProfile(response.data);
      setLastUpdated(new Date(response.data.last_updated));
      
    } catch (err) {
      console.error('Error loading personality profile:', err);
      setError('Unable to load personality profile. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const getDimensionLabel = (dimension) => {
    const labels = {
      extraversion: 'Extraversion',
      neuroticism: 'Emotional Stability', 
      openness: 'Openness',
      conscientiousness: 'Conscientiousness',
      agreeableness: 'Agreeableness'
    };
    return labels[dimension] || dimension;
  };

  const getDimensionIcon = (dimension) => {
    const icons = {
      extraversion: UserIcon,
      neuroticism: HeartIcon,
      openness: SparklesIcon,
      conscientiousness: CpuChipIcon,
      agreeableness: HeartIcon
    };
    return icons[dimension] || LightBulbIcon;
  };

  const getDimensionColor = (value) => {
    if (value >= 0.7) return 'text-green-600 bg-green-100';
    if (value >= 0.4) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getDimensionDescription = (dimension, value) => {
    const descriptions = {
      extraversion: {
        high: 'You tend to be outgoing and energetic',
        medium: 'You have a balanced social energy',
        low: 'You prefer quiet, contemplative activities'
      },
      neuroticism: {
        high: 'You may experience stress more intensely', 
        medium: 'You have moderate emotional stability',
        low: 'You tend to be emotionally stable and calm'
      },
      openness: {
        high: 'You\'re highly creative and open to new experiences',
        medium: 'You balance tradition with new ideas',
        low: 'You prefer familiar and conventional approaches'
      },
      conscientiousness: {
        high: 'You\'re highly organized and goal-oriented',
        medium: 'You balance structure with flexibility', 
        low: 'You prefer spontaneity over rigid planning'
      },
      agreeableness: {
        high: 'You\'re highly cooperative and trusting',
        medium: 'You balance cooperation with assertiveness',
        low: 'You tend to be more competitive and skeptical'
      }
    };

    const level = value >= 0.7 ? 'high' : (value >= 0.4 ? 'medium' : 'low');
    return descriptions[dimension]?.[level] || 'Analyzing your patterns...';
  };

  const formatPercentage = (value) => Math.round(value * 100);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-center h-32">
          <LoadingSpinner size="md" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center text-gray-500">
          <p>{error}</p>
          <button 
            onClick={loadPersonalityProfile}
            className="mt-2 text-blue-600 hover:text-blue-700 text-sm font-medium"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  if (!profile) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <CpuChipIcon className="h-6 w-6 text-purple-600" />
          <h3 className="text-lg font-semibold text-gray-900">Personality Profile</h3>
        </div>
        <button
          onClick={loadPersonalityProfile}
          className="p-2 text-gray-400 hover:text-gray-600 rounded-md transition-colors"
          title="Refresh profile"
        >
          <ArrowPathIcon className="h-4 w-4" />
        </button>
      </div>

      {/* Confidence Score */}
      <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Profile Confidence</span>
          <span className="text-2xl font-bold text-purple-600">
            {formatPercentage(profile.confidence_score)}%
          </span>
        </div>
        <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full transition-all duration-500"
            style={{ width: `${formatPercentage(profile.confidence_score)}%` }}
          />
        </div>
      </div>

      {/* Personality Dimensions */}
      <div className="mb-6">
        <h4 className="text-md font-medium text-gray-900 mb-4">Big Five Personality Dimensions</h4>
        <div className="space-y-3">
          {Object.entries(profile.dimensions).map(([dimension, value]) => {
            const Icon = getDimensionIcon(dimension);
            const colorClass = getDimensionColor(value);
            
            return (
              <div key={dimension} className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
                <div className={`p-2 rounded-md ${colorClass}`}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-sm font-medium text-gray-900">
                      {getDimensionLabel(dimension)}
                    </p>
                    <span className="text-sm font-semibold text-gray-700">
                      {formatPercentage(value)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5 mb-2">
                    <div 
                      className={`h-1.5 rounded-full transition-all duration-500 ${
                        value >= 0.7 ? 'bg-green-500' : 
                        value >= 0.4 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${formatPercentage(value)}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-600">
                    {getDimensionDescription(dimension, value)}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Communication Style */}
      {profile.communication_style && (
        <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center space-x-2 mb-2">
            <SparklesIcon className="h-4 w-4 text-blue-600" />
            <h5 className="text-sm font-medium text-blue-900">Communication Style</h5>
          </div>
          <p className="text-sm text-blue-700 capitalize font-medium">
            {profile.communication_style.replace('_', ' ')}
          </p>
        </div>
      )}

      {/* Strengths and Growth Areas */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {/* Strengths */}
        {profile.strengths && profile.strengths.length > 0 && (
          <div className="p-4 bg-green-50 rounded-lg border border-green-200">
            <div className="flex items-center space-x-2 mb-3">
              <ArrowTrendingUpIcon className="h-4 w-4 text-green-600" />
              <h5 className="text-sm font-medium text-green-900">Strengths</h5>
            </div>
            <ul className="space-y-1">
              {profile.strengths.map((strength, index) => (
                <li key={index} className="text-sm text-green-700">
                  • {strength}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Growth Areas */}
        {profile.growth_areas && profile.growth_areas.length > 0 && (
          <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
            <div className="flex items-center space-x-2 mb-3">
              <LightBulbIcon className="h-4 w-4 text-orange-600" />
              <h5 className="text-sm font-medium text-orange-900">Growth Areas</h5>
            </div>
            <ul className="space-y-1">
              {profile.growth_areas.map((area, index) => (
                <li key={index} className="text-sm text-orange-700">
                  • {area}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Traits */}
      {profile.traits && profile.traits.length > 0 && (
        <div className="mb-4">
          <h5 className="text-sm font-medium text-gray-900 mb-2">Key Traits</h5>
          <div className="flex flex-wrap gap-2">
            {profile.traits.map((trait, index) => (
              <span 
                key={index}
                className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800"
              >
                {trait}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Last Updated */}
      {lastUpdated && (
        <div className="text-xs text-gray-500 text-center border-t border-gray-200 pt-3">
          Last updated: {lastUpdated.toLocaleDateString()} at {lastUpdated.toLocaleTimeString()}
        </div>
      )}
    </div>
  );
};

export default PersonalityProfile;