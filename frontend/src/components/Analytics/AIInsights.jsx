// frontend/src/components/Analytics/AIInsights.jsx
import React, { useState, useEffect } from 'react';
import { 
  SparklesIcon, 
  LightBulbIcon,
  TrendingUpIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  ArrowPathIcon,
  ChartBarIcon,
  BrainIcon,
  EyeIcon,
  CalendarDaysIcon
} from '@heroicons/react/24/outline';
import { advancedAI } from '../../services/api';
// Removed /* removed user id */ import - using authenticated user
import LoadingSpinner from '../Common/LoadingSpinner';

const AIInsights = ({ className = '' }) => {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('temporal');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadInsights();
  }, [userId]);

  const loadInsights = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Get comprehensive analysis from backend
      const response = await advancedAI.getComprehensiveAnalysis(userId, {
        timeframe: 'monthly',
        include_predictions: true,
        include_personality: false, // Already have this elsewhere
        max_entries: 100
      });
      
      setInsights(response.data);
      
    } catch (err) {
      console.error('Error loading AI insights:', err);
      setError('Unable to load AI insights. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const refreshInsights = async () => {
    setRefreshing(true);
    await loadInsights();
    setRefreshing(false);
  };

  const getInsightIcon = (insightType) => {
    const icons = {
      pattern_recognition: ChartBarIcon,
      emotional_trend: TrendingUpIcon,
      content_analysis: BrainIcon,
      behavioral_pattern: EyeIcon,
      temporal_pattern: ClockIcon
    };
    return icons[insightType] || SparklesIcon;
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-orange-600 bg-orange-100';
  };

  const getSignificanceColor = (significance) => {
    if (significance >= 0.7) return 'bg-purple-500';
    if (significance >= 0.5) return 'bg-blue-500';
    return 'bg-gray-500';
  };

  const formatConfidence = (confidence) => Math.round(confidence * 100);

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="flex items-center justify-center h-32">
          <LoadingSpinner size="md" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="text-center text-gray-500">
          <ExclamationTriangleIcon className="h-8 w-8 mx-auto mb-2 text-gray-400" />
          <p className="mb-2">{error}</p>
          <button 
            onClick={loadInsights}
            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  if (!insights) {
    return null;
  }

  const tabs = [
    { id: 'temporal', name: 'Pattern Insights', icon: ChartBarIcon },
    { id: 'predictions', name: 'Predictions', icon: TrendingUpIcon },
    { id: 'summary', name: 'Analysis Summary', icon: BrainIcon }
  ];

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="border-b border-gray-200 p-6 pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <SparklesIcon className="h-6 w-6 text-purple-600" />
            <h3 className="text-lg font-semibold text-gray-900">AI-Generated Insights</h3>
          </div>
          <button
            onClick={refreshInsights}
            disabled={refreshing}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-md transition-colors disabled:opacity-50"
            title="Refresh insights"
          >
            <ArrowPathIcon className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
        
        {/* Processing Info */}
        <div className="flex items-center space-x-4 text-sm text-gray-600 mt-2">
          <span>{insights.analysis_summary.entries_analyzed} entries analyzed</span>
          <span>•</span>
          <span>{insights.analysis_summary.insights_generated} insights generated</span>
          <span>•</span>
          <span>{insights.analysis_summary.processing_time_seconds}s processing time</span>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-purple-500 text-purple-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.name}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {activeTab === 'temporal' && (
          <div className="space-y-4">
            {insights.temporal_insights.map((insight, index) => {
              const Icon = getInsightIcon(insight.insight_type);
              const confidenceColor = getConfidenceColor(insight.confidence);
              const significanceWidth = Math.round(insight.significance * 100);
              
              return (
                <div key={index} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start space-x-3">
                    <div className={`p-2 rounded-md ${confidenceColor}`}>
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-md font-semibold text-gray-900">{insight.title}</h4>
                        <div className="flex items-center space-x-2 text-sm text-gray-500">
                          <span>{formatConfidence(insight.confidence)}% confidence</span>
                        </div>
                      </div>
                      
                      <p className="text-gray-700 mb-3">{insight.description}</p>
                      
                      {/* Significance bar */}
                      <div className="mb-3">
                        <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                          <span>Significance</span>
                          <span>{formatConfidence(insight.significance)}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-1">
                          <div 
                            className={`h-1 rounded-full transition-all duration-500 ${getSignificanceColor(insight.significance)}`}
                            style={{ width: `${significanceWidth}%` }}
                          />
                        </div>
                      </div>
                      
                      {/* Recommendations */}
                      {insight.recommendations && insight.recommendations.length > 0 && (
                        <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
                          <div className="flex items-center space-x-2 mb-2">
                            <LightBulbIcon className="h-4 w-4 text-blue-600" />
                            <span className="text-sm font-medium text-blue-900">Recommendations</span>
                          </div>
                          <ul className="space-y-1 text-sm text-blue-800">
                            {insight.recommendations.map((rec, recIndex) => (
                              <li key={recIndex}>• {rec}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {activeTab === 'predictions' && insights.predictive_analysis && (
          <div className="space-y-6">
            {/* Mood Forecast */}
            <div className="border border-gray-200 rounded-lg p-4">
              <h4 className="text-md font-semibold text-gray-900 mb-3 flex items-center">
                <CalendarDaysIcon className="h-5 w-5 mr-2 text-green-600" />
                7-Day Mood Forecast
              </h4>
              <div className="grid grid-cols-7 gap-2 mb-4">
                {insights.predictive_analysis.predicted_mood_trends.mood_forecast?.map((day, index) => (
                  <div key={index} className="text-center">
                    <div className="text-xs text-gray-500 mb-1">
                      {new Date(day.date).toLocaleDateString('en', { weekday: 'short' })}
                    </div>
                    <div className={`w-8 h-8 mx-auto rounded-full flex items-center justify-center text-xs font-medium ${
                      day.mood === 'positive' ? 'bg-green-100 text-green-800' :
                      day.mood === 'neutral' ? 'bg-gray-100 text-gray-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {Math.round(day.confidence * 100)}%
                    </div>
                  </div>
                ))}
              </div>
              <div className="text-sm text-gray-600">
                Overall trend: <span className="font-medium text-green-600">
                  {insights.predictive_analysis.predicted_mood_trends.next_7_days.trend.replace('_', ' ')}
                </span>
              </div>
            </div>

            {/* Risk Factors */}
            {insights.predictive_analysis.risk_factors?.length > 0 && (
              <div className="border border-orange-200 rounded-lg p-4 bg-orange-50">
                <h4 className="text-md font-semibold text-gray-900 mb-3 flex items-center">
                  <ExclamationTriangleIcon className="h-5 w-5 mr-2 text-orange-600" />
                  Risk Factors to Monitor
                </h4>
                <div className="space-y-3">
                  {insights.predictive_analysis.risk_factors.map((risk, index) => (
                    <div key={index} className="bg-white border border-orange-200 rounded-md p-3">
                      <div className="flex items-center justify-between mb-2">
                        <h5 className="font-medium text-gray-900">{risk.factor.replace('_', ' ')}</h5>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          risk.impact === 'high' ? 'bg-red-100 text-red-800' :
                          risk.impact === 'medium' ? 'bg-orange-100 text-orange-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {Math.round(risk.probability * 100)}% probability
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{risk.description}</p>
                      {risk.recommendations && (
                        <div className="text-sm">
                          <span className="font-medium text-gray-700">Recommendations:</span>
                          <ul className="mt-1 text-gray-600">
                            {risk.recommendations.map((rec, recIndex) => (
                              <li key={recIndex}>• {rec}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Opportunity Windows */}
            {insights.predictive_analysis.opportunity_windows?.length > 0 && (
              <div className="border border-green-200 rounded-lg p-4 bg-green-50">
                <h4 className="text-md font-semibold text-gray-900 mb-3 flex items-center">
                  <TrendingUpIcon className="h-5 w-5 mr-2 text-green-600" />
                  Opportunity Windows
                </h4>
                <div className="space-y-3">
                  {insights.predictive_analysis.opportunity_windows.map((opp, index) => (
                    <div key={index} className="bg-white border border-green-200 rounded-md p-3">
                      <div className="flex items-center justify-between mb-2">
                        <h5 className="font-medium text-gray-900">{opp.opportunity.replace('_', ' ')}</h5>
                        <div className="text-right">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            opp.potential_impact === 'high' ? 'bg-green-100 text-green-800' :
                            opp.potential_impact === 'medium' ? 'bg-blue-100 text-blue-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {Math.round(opp.probability * 100)}% probability
                          </span>
                          <div className="text-xs text-gray-500 mt-1">
                            {opp.optimal_timeframe}
                          </div>
                        </div>
                      </div>
                      <p className="text-sm text-gray-600">{opp.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'summary' && (
          <div className="space-y-4">
            {/* Analysis Overview */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {insights.analysis_summary.entries_analyzed}
                </div>
                <div className="text-sm text-blue-600">Entries Analyzed</div>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {insights.analysis_summary.insights_generated}
                </div>
                <div className="text-sm text-purple-600">Insights Generated</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {insights.analysis_summary.processing_time_seconds}s
                </div>
                <div className="text-sm text-green-600">Processing Time</div>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <div className="text-2xl font-bold text-orange-600">
                  {insights.analysis_summary.timeframe}
                </div>
                <div className="text-sm text-orange-600">Analysis Timeframe</div>
              </div>
            </div>

            {/* Recommendations Priority */}
            {insights.predictive_analysis?.recommendation_priority && (
              <div className="border border-gray-200 rounded-lg p-4">
                <h4 className="text-md font-semibold text-gray-900 mb-3 flex items-center">
                  <LightBulbIcon className="h-5 w-5 mr-2 text-yellow-600" />
                  Priority Recommendations
                </h4>
                <div className="space-y-2">
                  {insights.predictive_analysis.recommendation_priority.map((rec, index) => (
                    <div key={index} className="flex items-start space-x-3 p-2 hover:bg-gray-50 rounded-md">
                      <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium">
                        {index + 1}
                      </div>
                      <span className="text-sm text-gray-700">{rec}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Processing Metadata */}
            <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
              <h4 className="text-md font-semibold text-gray-900 mb-3">Processing Details</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium text-gray-700">Service Version:</span>
                  <span className="ml-2 text-gray-600">{insights.processing_metadata.service_version}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Cache Utilized:</span>
                  <span className="ml-2 text-gray-600">{insights.processing_metadata.cache_utilized ? 'Yes' : 'No'}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Analysis Time:</span>
                  <span className="ml-2 text-gray-600">
                    {new Date(insights.processing_metadata.analysis_timestamp).toLocaleString()}
                  </span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">AI Models Used:</span>
                  <span className="ml-2 text-gray-600">{insights.processing_metadata.ai_models_used?.length || 0}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIInsights;