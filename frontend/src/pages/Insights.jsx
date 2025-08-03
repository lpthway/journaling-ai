// frontend/src/pages/Insights.jsx - Enhanced Overview Tab

import React, { useState, useEffect } from 'react';
import { 
  ChartBarIcon, 
  LightBulbIcon, 
  QuestionMarkCircleIcon,
  ArrowTrendingUpIcon,
  HeartIcon,
  CalendarIcon,
  ChatBubbleLeftRightIcon,
  BookOpenIcon,
  ClockIcon,
  FireIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { insightsAPI, entryAPI, sessionAPI } from '../services/api';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import MoodChart from '../components/Analytics/MoodChart';
import MoodTrends from '../components/Analytics/MoodTrends';
import EnhancedAskQuestion from '../components/Insights/EnhancedAskQuestion';
import CoachingSuggestions from '../components/Insights/CoachingSuggestions';
import PatternAnalysis from '../components/Insights/PatternAnalysis';

const Insights = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [overviewData, setOverviewData] = useState({
    moodStats: null,
    patterns: null,
    chatInsights: null,
    comprehensiveMood: null
  });

  const tabs = [
    { id: 'overview', name: 'Overview', icon: ChartBarIcon },
    { id: 'coaching', name: 'Coaching', icon: LightBulbIcon },
    { id: 'ask', name: 'Ask AI', icon: QuestionMarkCircleIcon },
    { id: 'trends', name: 'Trends', icon: ArrowTrendingUpIcon },
    { id: 'patterns', name: 'Patterns', icon: HeartIcon },
  ];

  useEffect(() => {
    loadOverviewData();
  }, []);

  const loadOverviewData = async () => {
    try {
      setLoading(true);
      
      // Load all data in parallel
      const [
        moodResponse,
        patternsResponse,
        chatInsightsResponse,
        comprehensiveMoodResponse
      ] = await Promise.all([
        entryAPI.getMoodStats(30),
        insightsAPI.getPatterns(),
        insightsAPI.getChatInsights(30).catch(() => ({ data: null })), // Graceful fallback
        insightsAPI.getComprehensiveMoodAnalysis(30).catch(() => ({ data: null }))
      ]);
      
      setOverviewData({
        moodStats: moodResponse.data,
        patterns: patternsResponse.data,
        chatInsights: chatInsightsResponse.data,
        comprehensiveMood: comprehensiveMoodResponse.data
      });
    } catch (error) {
      console.error('Error loading insights:', error);
      toast.error('Failed to load insights data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Insights & Analytics</h1>
        <p className="mt-1 text-sm text-gray-500">
          Discover patterns, trends, and get AI-powered insights from your journaling and conversations
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`group inline-flex items-center py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="w-5 h-5 mr-2" />
                {tab.name}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-96">
        {activeTab === 'overview' && (
          <EnhancedOverviewTab data={overviewData} setActiveTab={setActiveTab} />
        )}
        {activeTab === 'coaching' && <CoachingSuggestions />}
        {activeTab === 'ask' && <EnhancedAskQuestion />}
        {activeTab === 'trends' && <TrendsTab />}
        {activeTab === 'patterns' && (
          loading ? (
            <div className="flex justify-center items-center h-64">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-2 text-sm text-gray-500">Loading pattern analysis...</p>
              </div>
            </div>
          ) : (
            <PatternAnalysis data={overviewData.patterns} />
          )
        )}
      </div>
    </div>
  );
};

// Enhanced Overview Tab Component
const EnhancedOverviewTab = ({ data, setActiveTab }) => {
  const { moodStats, patterns, chatInsights, comprehensiveMood } = data;

  if (!moodStats && !chatInsights) {
    return (
      <div className="text-center py-12">
        <HeartIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No data available</h3>
        <p className="mt-1 text-sm text-gray-500">
          Start journaling and having conversations to see your insights and patterns!
        </p>
      </div>
    );
  }

  // Calculate combined metrics
  const totalJournalEntries = moodStats?.total_entries || 0;
  const totalConversations = chatInsights?.total_conversations || 0;
  const totalInteractions = totalJournalEntries + totalConversations;

  const journalFrequency = patterns?.patterns?.writing_frequency?.entries_per_day || 0;
  const avgWordsPerEntry = Math.round(patterns?.patterns?.writing_frequency?.avg_word_count || 0);
  const avgMessagesPerChat = chatInsights?.average_length || 0;

  // Calculate streak (simplified for demo)
  const currentStreak = 7; // This would be calculated from actual data

  return (
    <div className="space-y-6">
      {/* Enhanced Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <EnhancedMetricCard
          title="Total Interactions"
          value={totalInteractions}
          subtitle={`${totalJournalEntries} entries, ${totalConversations} chats`}
          icon={ChartBarIcon}
          color="blue"
          trend={totalInteractions > 0 ? "up" : "neutral"}
        />
        <EnhancedMetricCard
          title="Journal Activity"
          value={journalFrequency.toFixed(2)}
          subtitle="entries per day"
          icon={BookOpenIcon}
          color="green"
          trend={journalFrequency > 0.5 ? "up" : journalFrequency > 0.1 ? "neutral" : "down"}
        />
        <EnhancedMetricCard
          title="Chat Activity"
          value={avgMessagesPerChat.toFixed(1)}
          subtitle="avg messages per chat"
          icon={ChatBubbleLeftRightIcon}
          color="purple"
          trend={avgMessagesPerChat > 5 ? "up" : avgMessagesPerChat > 2 ? "neutral" : "down"}
        />
        <EnhancedMetricCard
          title="Current Streak"
          value={currentStreak}
          subtitle="days active"
          icon={FireIcon}
          color="orange"
          trend={currentStreak >= 7 ? "up" : currentStreak >= 3 ? "neutral" : "down"}
        />
      </div>

      {/* Content Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Activity Overview */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Activity Overview (Last 30 Days)
          </h3>
          <div className="space-y-4">
            <ActivityBar
              label="Journal Entries"
              value={totalJournalEntries}
              maxValue={Math.max(totalJournalEntries, totalConversations, 1)}
              color="blue"
              icon={BookOpenIcon}
            />
            <ActivityBar
              label="Conversations"
              value={totalConversations}
              maxValue={Math.max(totalJournalEntries, totalConversations, 1)}
              color="purple"
              icon={ChatBubbleLeftRightIcon}
            />
          </div>
          
          {chatInsights?.most_used_session_type && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              <p className="text-sm text-gray-600">
                <span className="font-medium">Favorite chat type:</span>{' '}
                {chatInsights.most_used_session_type.replace('_', ' ')}
              </p>
              {chatInsights?.peak_conversation_hour && (
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Peak chat time:</span>{' '}
                  {chatInsights.peak_conversation_hour}:00
                </p>
              )}
            </div>
          )}
        </div>

        {/* Enhanced Mood Distribution */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Mood Distribution
            {comprehensiveMood && (
              <span className="text-sm font-normal text-gray-500 ml-2">
                (Combined Analysis)
              </span>
            )}
          </h3>
          <MoodChart 
            data={comprehensiveMood?.combined_mood_distribution ? 
              Object.fromEntries(
                Object.entries(comprehensiveMood.combined_mood_distribution)
                  .map(([mood, data]) => [mood, data.total])
              ) : 
              moodStats?.mood_distribution
            } 
          />
          
          {comprehensiveMood && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium text-blue-600">📔 Journal:</span>
                  <span className="ml-1">{comprehensiveMood.sources?.journal_entries || 0}</span>
                </div>
                <div>
                  <span className="font-medium text-purple-600">💬 Chats:</span>
                  <span className="ml-1">{comprehensiveMood.sources?.chat_conversations || 0}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Enhanced Quick Insights */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Insights</h3>
        <div className="space-y-3">
          <EnhancedInsightItem
            text={`You've had ${totalInteractions} total interactions in the last 30 days (${totalJournalEntries} journal entries, ${totalConversations} conversations)`}
            type="info"
          />
          
          {journalFrequency > 0.5 && (
            <EnhancedInsightItem
              text="Great journaling consistency! You're maintaining a regular writing habit"
              type="positive"
            />
          )}
          
          {totalConversations > 0 && (
            <EnhancedInsightItem
              text={`You're actively using AI conversations for reflection with an average of ${avgMessagesPerChat.toFixed(1)} messages per chat`}
              type="positive"
            />
          )}
          
          {getEnhancedMoodInsight(comprehensiveMood?.combined_mood_distribution || moodStats?.mood_distribution) && (
            <EnhancedInsightItem
              text={getEnhancedMoodInsight(comprehensiveMood?.combined_mood_distribution || moodStats?.mood_distribution)}
              type="neutral"
            />
          )}
          
          {chatInsights?.insights && chatInsights.insights.length > 0 && (
            <EnhancedInsightItem
              text={chatInsights.insights[0]}
              type="info"
            />
          )}
        </div>
      </div>

      {/* Enhanced Pattern Analysis Preview */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Pattern Analysis Preview</h3>
          <button 
            onClick={() => setActiveTab('patterns')}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
          >
            View Full Analysis
          </button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <PatternCard
            icon={ArrowTrendingUpIcon}
            title="Writing Trend"
            value={patterns?.patterns?.recent_trend || 'stable'}
            color="blue"
          />
          <PatternCard
            icon={ClockIcon}
            title="Consistency"
            value={`${journalFrequency.toFixed(2)}/day`}
            color="green"
          />
          <PatternCard
            icon={ChatBubbleLeftRightIcon}
            title="Chat Engagement"
            value={totalConversations > 0 ? `${totalConversations} chats` : 'No chats'}
            color="purple"
          />
        </div>
        
        {/* Cross-Platform Insights */}
        {totalJournalEntries > 0 && totalConversations > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <h4 className="text-sm font-medium text-gray-900 mb-2">Cross-Platform Insights</h4>
            <div className="text-sm text-gray-600 space-y-1">
              <p>• You're using both journaling and conversations for reflection</p>
              <p>• {((totalConversations / totalInteractions) * 100).toFixed(0)}% of your reflections are conversational</p>
              <p>• This balanced approach can provide richer insights</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Enhanced Metric Card Component
const EnhancedMetricCard = ({ title, value, subtitle, icon: Icon, color, trend }) => {
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    orange: 'bg-orange-500',
    red: 'bg-red-500',
  };

  const trendClasses = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-600'
  };

  const trendIcons = {
    up: '↗',
    down: '↘',
    neutral: '→'
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="flex items-center">
        <div className={`p-3 rounded-md ${colorClasses[color]}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        <div className="ml-4 flex-1">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <div className="flex items-center space-x-2">
            <p className="text-2xl font-bold text-gray-900">
              {typeof value === 'number' ? value.toLocaleString() : value}
            </p>
            <span className={`text-sm ${trendClasses[trend]}`}>
              {trendIcons[trend]}
            </span>
          </div>
          {subtitle && (
            <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
      </div>
    </div>
  );
};

// Activity Bar Component
const ActivityBar = ({ label, value, maxValue, color, icon: Icon }) => {
  const percentage = maxValue > 0 ? (value / maxValue) * 100 : 0;
  
  const colorClasses = {
    blue: 'bg-blue-500',
    purple: 'bg-purple-500',
    green: 'bg-green-500',
  };

  return (
    <div className="flex items-center space-x-3">
      <Icon className="w-5 h-5 text-gray-400 flex-shrink-0" />
      <div className="flex-1">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-gray-700">{label}</span>
          <span className="text-sm text-gray-500">{value}</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`${colorClasses[color]} h-2 rounded-full transition-all duration-300`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    </div>
  );
};

// Enhanced Insight Item Component
const EnhancedInsightItem = ({ text, type }) => {
  const typeClasses = {
    positive: 'bg-green-50 text-green-800 border-green-200',
    negative: 'bg-red-50 text-red-800 border-red-200',
    neutral: 'bg-blue-50 text-blue-800 border-blue-200',
    info: 'bg-gray-50 text-gray-800 border-gray-200',
  };

  const typeIcons = {
    positive: '✨',
    negative: '💭',
    neutral: '📊',
    info: 'ℹ️',
  };

  return (
    <div className={`p-3 rounded-md border ${typeClasses[type]}`}>
      <p className="text-sm flex items-start space-x-2">
        <span>{typeIcons[type]}</span>
        <span>{text}</span>
      </p>
    </div>
  );
};

// Pattern Card Component (reused)
const PatternCard = ({ icon: Icon, title, value, color }) => {
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    orange: 'bg-orange-500',
  };

  return (
    <div className="bg-white p-4 rounded-lg border border-gray-200">
      <div className="flex items-center">
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        <div className="ml-3">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-lg font-bold text-gray-900 capitalize">{value}</p>
        </div>
      </div>
    </div>
  );
};

// Enhanced mood insight helper function
const getEnhancedMoodInsight = (moodDistribution) => {
  if (!moodDistribution) return null;
  
  let total = 0;
  let positiveCount = 0;
  let negativeCount = 0;

  // Handle both formats: simple mood_distribution and combined analysis
  Object.entries(moodDistribution).forEach(([mood, countOrData]) => {
    const count = typeof countOrData === 'object' ? countOrData.total : countOrData;
    total += count;
    
    if (mood.includes('positive')) {
      positiveCount += count;
    } else if (mood.includes('negative')) {
      negativeCount += count;
    }
  });
  
  if (total === 0) return null;
  
  const positivePercent = Math.round((positiveCount / total) * 100);
  const negativePercent = Math.round((negativeCount / total) * 100);

  if (positivePercent > 60) {
    return `${positivePercent}% of your interactions show positive mood across all platforms - excellent emotional wellbeing!`;
  } else if (negativePercent > 40) {
    return `You've been processing some challenging emotions recently across your reflections. Consider reaching out for support.`;
  } else {
    return `Your mood appears balanced with ${positivePercent}% positive interactions across journaling and conversations.`;
  }
};

// Trends Tab Component (unchanged)
const TrendsTab = () => {
  const [timeRange, setTimeRange] = useState(30);
  const [trendsData, setTrendsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [useComprehensive, setUseComprehensive] = useState(true);

  useEffect(() => {
    loadTrendsData();
  }, [timeRange, useComprehensive]);

  const loadTrendsData = async () => {
    try {
      setLoading(true);
      const response = useComprehensive 
        ? await insightsAPI.getComprehensiveTrends(timeRange)
        : await insightsAPI.getMoodTrends(timeRange);
      setTrendsData(response.data);
    } catch (error) {
      console.error('Error loading trends:', error);
      toast.error('Failed to load trends data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h2 className="text-lg font-semibold text-gray-900">Mood Trends</h2>
          
          {/* Data Source Toggle */}
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Data source:</span>
            <button
              onClick={() => setUseComprehensive(!useComprehensive)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${
                useComprehensive ? 'bg-blue-600' : 'bg-gray-300'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  useComprehensive ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
            <span className="text-sm font-medium text-gray-900">
              {useComprehensive ? 'Journal + Chat' : 'Journal Only'}
            </span>
          </div>
        </div>

        {/* Time Range Selector */}
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(parseInt(e.target.value))}
          className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 3 months</option>
          <option value={365}>Last year</option>
        </select>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      ) : (
        <MoodTrends 
          data={trendsData} 
          timeRange={timeRange} 
          isComprehensive={useComprehensive}
        />
      )}
    </div>
  );
};

export default Insights;