import React, { useState, useEffect } from 'react';
import { 
  ChartBarIcon, 
  LightBulbIcon, 
  QuestionMarkCircleIcon,
  ArrowTrendingUpIcon,
  HeartIcon,
  CalendarIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { insightsAPI, entryAPI } from '../services/api';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import MoodChart from '../components/Analytics/MoodChart';
import MoodTrends from '../components/Analytics/MoodTrends';
import AskQuestion from '../components/Insights/AskQuestion';
import CoachingSuggestions from '../components/Insights/CoachingSuggestions';
import PatternAnalysis from '../components/Insights/PatternAnalysis';

const Insights = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [moodStats, setMoodStats] = useState(null);
  const [patterns, setPatterns] = useState(null);

  const tabs = [
    { id: 'overview', name: 'Overview', icon: ChartBarIcon },
    { id: 'coaching', name: 'Coaching', icon: LightBulbIcon },
    { id: 'ask', name: 'Ask AI', icon: QuestionMarkCircleIcon },
    { id: 'trends', name: 'Trends', icon: ArrowTrendingUpIcon },
  ];

  useEffect(() => {
    loadInsightsData();
  }, []);

  const loadInsightsData = async () => {
    try {
      setLoading(true);
      const [moodResponse, patternsResponse] = await Promise.all([
        entryAPI.getMoodStats(30),
        insightsAPI.getPatterns()
      ]);
      
      setMoodStats(moodResponse.data);
      setPatterns(patternsResponse.data);
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
          Discover patterns, trends, and get AI-powered insights from your journaling
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
          <OverviewTab moodStats={moodStats} patterns={patterns} />
        )}
        {activeTab === 'coaching' && <CoachingSuggestions />}
        {activeTab === 'ask' && <AskQuestion />}
        {activeTab === 'trends' && <TrendsTab />}
      </div>
    </div>
  );
};

// Overview Tab Component
const OverviewTab = ({ moodStats, patterns }) => {
  if (!moodStats || !patterns?.patterns) {
    return (
      <div className="text-center py-12">
        <HeartIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No data available</h3>
        <p className="mt-1 text-sm text-gray-500">
          Start journaling to see your insights and patterns!
        </p>
      </div>
    );
  }

  const { mood_distribution, total_entries } = moodStats;
  const { writing_frequency, mood_distribution: patternMoods } = patterns.patterns;

  return (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <MetricCard
          title="Total Entries"
          value={total_entries}
          icon={CalendarIcon}
          color="blue"
        />
        <MetricCard
          title="Entries/Day"
          value={writing_frequency?.entries_per_day || 0}
          icon={ArrowTrendingUpIcon}
          color="green"
          suffix=" avg"
        />
        <MetricCard
          title="Avg Words"
          value={Math.round(writing_frequency?.avg_word_count || 0)}
          icon={ChartBarIcon}
          color="purple"
        />
        <MetricCard
          title="Streak"
          value="7"
          icon={HeartIcon}
          color="red"
          suffix=" days"
        />
      </div>

      {/* Mood Distribution Chart */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Mood Distribution (Last 30 Days)
        </h3>
        <MoodChart data={mood_distribution} />
      </div>

      {/* Quick Insights */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Insights</h3>
        <div className="space-y-3">
          <InsightItem
            text={`You've written ${total_entries} entries in the last 30 days`}
            type="info"
          />
          {writing_frequency?.entries_per_day > 0.5 && (
            <InsightItem
              text="Great consistency! You're maintaining a regular journaling habit"
              type="positive"
            />
          )}
          {getMoodInsight(mood_distribution) && (
            <InsightItem
              text={getMoodInsight(mood_distribution)}
              type="neutral"
            />
          )}
        </div>
      </div>

      {/* Pattern Analysis Preview */}
      <PatternAnalysis data={patterns} preview={true} />
    </div>
  );
};

// Trends Tab Component
const TrendsTab = () => {
  const [timeRange, setTimeRange] = useState(30);
  const [trendsData, setTrendsData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTrendsData();
  }, [timeRange]);

  const loadTrendsData = async () => {
    try {
      setLoading(true);
      const response = await insightsAPI.getMoodTrends(timeRange);
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
      {/* Time Range Selector */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Mood Trends</h2>
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
        <MoodTrends data={trendsData} timeRange={timeRange} />
      )}
    </div>
  );
};

// Metric Card Component
const MetricCard = ({ title, value, icon: Icon, color, suffix = '' }) => {
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    red: 'bg-red-500',
    yellow: 'bg-yellow-500',
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="flex items-center">
        <div className={`p-3 rounded-md ${colorClasses[color]}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900">
            {typeof value === 'number' ? value.toLocaleString() : value}
            <span className="text-sm font-normal text-gray-500">{suffix}</span>
          </p>
        </div>
      </div>
    </div>
  );
};

// Insight Item Component
const InsightItem = ({ text, type }) => {
  const typeClasses = {
    positive: 'bg-green-50 text-green-800 border-green-200',
    negative: 'bg-red-50 text-red-800 border-red-200',
    neutral: 'bg-blue-50 text-blue-800 border-blue-200',
    info: 'bg-gray-50 text-gray-800 border-gray-200',
  };

  return (
    <div className={`p-3 rounded-md border ${typeClasses[type]}`}>
      <p className="text-sm">{text}</p>
    </div>
  );
};

// Helper function to generate mood insights
const getMoodInsight = (moodDistribution) => {
  if (!moodDistribution) return null;
  
  const total = Object.values(moodDistribution).reduce((sum, count) => sum + count, 0);
  if (total === 0) return null;

  const positiveCount = (moodDistribution.very_positive || 0) + (moodDistribution.positive || 0);
  const negativeCount = (moodDistribution.very_negative || 0) + (moodDistribution.negative || 0);
  
  const positivePercent = Math.round((positiveCount / total) * 100);
  const negativePercent = Math.round((negativeCount / total) * 100);

  if (positivePercent > 60) {
    return `${positivePercent}% of your entries show positive mood - keep up the good vibes!`;
  } else if (negativePercent > 40) {
    return `You've had some challenging times recently. Consider reaching out to someone you trust.`;
  } else {
    return `Your mood seems balanced with ${positivePercent}% positive entries.`;
  }
};

export default Insights;