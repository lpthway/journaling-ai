// frontend/src/services/analyticsApi.js
import api from './api';

class AnalyticsAPI {
  // Get comprehensive writing statistics
  async getWritingInsights(days = 30, userId = '1e05fb66-160a-4305-b84a-805c2f0c6910') {
    try {
      const response = await api.get(`/entries/analytics/writing?days=${days}&user_id=${userId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching writing insights:', error);
      throw error;
    }
  }

  // Get mood and emotional patterns  
  async getEmotionalPatterns(days = 30, userId = '1e05fb66-160a-4305-b84a-805c2f0c6910') {
    try {
      const response = await api.get(`/entries/analytics/mood?days=${days}&user_id=${userId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching emotional patterns:', error);
      throw error;
    }
  }

  // Get comprehensive analytics summary (combines multiple endpoints)
  async getAnalyticsSummary(days = 30, userId = '1e05fb66-160a-4305-b84a-805c2f0c6910') {
    try {
      const [writingData, moodData] = await Promise.all([
        this.getWritingInsights(days, userId),
        this.getEmotionalPatterns(days, userId)
      ]);

      // Transform the data into the format expected by Analytics page cards
      return {
        writingInsights: {
          mostActiveDay: this.getMostActiveDay(writingData),
          avgWordsPerEntry: writingData.avg_word_count || 0,
          longestStreak: writingData.longest_streak || 0,
          favoriteTime: this.getFavoriteWritingTime(writingData),
          totalEntries: writingData.total_entries || 0,
          writingFrequency: writingData.entries_per_day || 0
        },
        emotionalPatterns: {
          emotionalStability: this.calculateEmotionalStability(moodData),
          positiveTrend: this.calculatePositiveTrend(moodData),
          resilienceScore: this.calculateResilienceScore(moodData),
          growthAreas: this.identifyGrowthAreas(moodData)
        },
        progressTracking: {
          dailyGoalProgress: this.calculateDailyProgress(writingData),
          weeklyGoalStatus: this.calculateWeeklyGoalStatus(writingData),
          monthlyTarget: this.calculateMonthlyTarget(writingData, days),
          achievementLevel: this.calculateAchievementLevel(writingData)
        }
      };
    } catch (error) {
      console.error('Error fetching analytics summary:', error);
      return null;
    }
  }

  // Helper methods to transform API data
  getMostActiveDay(writingData) {
    if (!writingData.activity_by_day) return 'N/A';
    
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const dayActivity = writingData.activity_by_day;
    
    let maxActivity = 0;
    let mostActiveDay = 'N/A';
    
    Object.entries(dayActivity).forEach(([day, count]) => {
      if (count > maxActivity) {
        maxActivity = count;
        mostActiveDay = days[parseInt(day)] || day;
      }
    });
    
    return mostActiveDay;
  }

  getFavoriteWritingTime(writingData) {
    if (!writingData.activity_by_hour) return 'N/A';
    
    const hourActivity = writingData.activity_by_hour;
    let maxActivity = 0;
    let favoriteHour = null;
    
    Object.entries(hourActivity).forEach(([hour, count]) => {
      if (count > maxActivity) {
        maxActivity = count;
        favoriteHour = parseInt(hour);
      }
    });
    
    if (favoriteHour === null) return 'N/A';
    
    if (favoriteHour >= 5 && favoriteHour < 12) return 'Morning';
    if (favoriteHour >= 12 && favoriteHour < 17) return 'Afternoon';
    if (favoriteHour >= 17 && favoriteHour < 21) return 'Evening';
    return 'Night';
  }

  calculateEmotionalStability(moodData) {
    if (!moodData.mood_distribution) return 'N/A';
    
    const distribution = moodData.mood_distribution;
    const positive = (distribution.joy || 0) + (distribution.optimism || 0);
    const negative = (distribution.sadness || 0) + (distribution.anger || 0) + (distribution.fear || 0);
    const total = Object.values(distribution).reduce((sum, count) => sum + count, 0);
    
    if (total === 0) return 'N/A';
    
    const positiveRatio = positive / total;
    if (positiveRatio > 0.6) return 'Good';
    if (positiveRatio > 0.4) return 'Moderate';
    return 'Needs Attention';
  }

  calculatePositiveTrend(moodData) {
    if (!moodData.mood_trends) return '+0%';
    
    // This would need mood trend data over time
    // For now, return a placeholder
    return '+0%';
  }

  calculateResilienceScore(moodData) {
    if (!moodData.mood_distribution) return 'N/A';
    
    const distribution = moodData.mood_distribution;
    const total = Object.values(distribution).reduce((sum, count) => sum + count, 0);
    
    if (total === 0) return 'N/A';
    
    // Simple resilience calculation based on emotional diversity and positive emotions
    const diversity = Object.keys(distribution).length;
    const positive = (distribution.joy || 0) + (distribution.optimism || 0);
    const positiveRatio = positive / total;
    
    const score = (diversity / 10 + positiveRatio) * 5;
    return `${Math.min(score, 10).toFixed(1)}/10`;
  }

  identifyGrowthAreas(moodData) {
    if (!moodData.mood_distribution) return 0;
    
    // Count areas that could be improved (low positive emotions, high stress, etc.)
    const distribution = moodData.mood_distribution;
    const total = Object.values(distribution).reduce((sum, count) => sum + count, 0);
    
    if (total === 0) return 0;
    
    let areas = 0;
    if ((distribution.sadness || 0) / total > 0.3) areas++;
    if ((distribution.anger || 0) / total > 0.2) areas++;
    if ((distribution.fear || 0) / total > 0.2) areas++;
    if ((distribution.joy || 0) / total < 0.2) areas++;
    
    return areas;
  }

  calculateDailyProgress(writingData) {
    if (!writingData.entries_per_day) return 0;
    
    // Assume goal is 1 entry per day
    const progress = Math.min(writingData.entries_per_day * 100, 100);
    return Math.round(progress);
  }

  calculateWeeklyGoalStatus(writingData) {
    if (!writingData.entries_per_day) return 'Unknown';
    
    // Assume weekly goal is 5 entries
    const weeklyEntries = writingData.entries_per_day * 7;
    return weeklyEntries >= 5 ? 'Complete' : 'In Progress';
  }

  calculateMonthlyTarget(writingData, days) {
    if (!writingData.total_entries) return 'N/A';
    
    const targetDays = Math.min(days, 30);
    return `${writingData.total_entries}/${targetDays} days`;
  }

  calculateAchievementLevel(writingData) {
    if (!writingData.entries_per_day) return 'Starting';
    
    const rate = writingData.entries_per_day;
    if (rate >= 1) return 'Excellent';
    if (rate >= 0.7) return 'Committed';
    if (rate >= 0.4) return 'Regular';
    return 'Starting';
  }
}

export const analyticsApi = new AnalyticsAPI();
