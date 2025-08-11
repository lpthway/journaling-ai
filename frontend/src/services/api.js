import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth token and debugging
api.interceptors.request.use(
  (config) => {
    // Add auth token
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Entry API
export const entryAPI = {
  create: (entryData) => api.post('/entries/', entryData),
  getAll: (params = {}) => api.get('/entries/', { params: { ...params, _t: Date.now() } }),
  getById: (id) => api.get(`/entries/${id}?_t=${Date.now()}`),
  getByTopic: (topicId, params = {}) => api.get(`/topics/${topicId}/entries`, { params }),
  update: (id, entryData) => api.put(`/entries/${id}`, entryData),
  delete: (id) => api.delete(`/entries/${id}`),
  search: (query, limit = 10, topicId = null) => 
    api.get('/entries/search/semantic', { 
      params: { query, limit, topic_id: topicId } 
    }),
  advancedSearch: (filters) => api.post('/entries/search/advanced', filters),
  getMoodStats: (days = 30) => api.get('/entries/analytics/mood', { params: { days } }),
  
  // Favorites
  toggleFavorite: (id) => api.patch(`/entries/${id}/favorite`),
  getFavorites: (limit = 50) => api.get('/entries/favorites', { params: { limit } }),
  
  // Versioning
  getVersions: (id) => api.get(`/entries/${id}/versions`),
  revertToVersion: (id, version) => api.post(`/entries/${id}/revert/${version}`),
  
  // Templates
  getTemplates: () => api.get('/entries/templates'),
  getTemplate: (id) => api.get(`/entries/templates/${id}`),
  createTemplate: (templateData) => api.post('/entries/templates', templateData),
};

// Topic API
export const topicAPI = {
  create: (topicData) => api.post('/topics/', topicData),
  getAll: () => api.get('/topics/'),
  getById: (id) => api.get(`/topics/${id}`),
  update: (id, topicData) => api.put(`/topics/${id}`, topicData),
  delete: (id) => api.delete(`/topics/${id}`),
  getEntries: (id, params = {}) => api.get(`/topics/${id}/entries`, { params }),
};

// Insights API
export const insightsAPI = {
  // Use new cached endpoints for blazing fast performance
  getCachedInsights: (days = 30) => api.get('/insights/cached', { params: { time_range_days: days } }),
  refreshCache: () => api.post('/insights/refresh'),
  getStatus: () => api.get('/insights/status'),
  
  // Legacy AI endpoints (now cached internally)
  askQuestion: (question) => api.post('/insights/ask', null, { params: { question } }),
  getCoaching: () => api.get('/insights/coaching'),
  
  // Legacy compatibility (redirected to cached)
  getPatterns: () => api.get('/insights/patterns'),
  getMoodTrends: (days = 30) => api.get('/insights/mood-stats', { params: { days } }),
};

// Enhanced Chat API - Updated to use /api/v1/chat endpoints
export const sessionAPI = {
  // Enhanced session management
  createSession: (sessionData) => {
    // Convert frontend session data to enhanced chat format
    const enhancedData = {
      user_id: sessionData.user_id || DEFAULT_USER_ID,
      conversation_mode: sessionData.session_type || 'supportive_listening',
      initial_context: {
        title: sessionData.title || 'Enhanced Chat Session',
        metadata: sessionData.metadata || {},
        frontend_integration: true
      }
    };
    return api.post('/chat/conversation/start', enhancedData).then(response => {
      // Convert enhanced chat response to frontend expected format
      const data = response.data;
      const sessionInfo = {
        id: data.session_id,
        session_id: data.session_id,
        title: sessionData.title || 'Enhanced Chat Session',
        session_type: sessionData.session_type || 'supportive_listening',
        conversation_mode: sessionData.session_type || 'supportive_listening',
        status: 'active',
        message_count: 0,
        recent_messages: [],
        created_at: new Date().toISOString(),
        last_activity: new Date().toISOString()
      };
      
      // Store session in localStorage
      try {
        const existingSessions = JSON.parse(localStorage.getItem('chatSessions') || '[]');
        existingSessions.unshift(sessionInfo); // Add to beginning
        localStorage.setItem('chatSessions', JSON.stringify(existingSessions.slice(0, 100))); // Keep max 100
      } catch (error) {
        console.error('Error storing session:', error);
      }
      
      return { data: sessionInfo };
    });
  },
  
  getSession: (sessionId) => api.get(`/chat/conversation/${sessionId}/history`),
  
  getSessions: (params = {}) => {
    // Get sessions from localStorage since enhanced chat doesn't have session listing yet
    try {
      const storedSessions = JSON.parse(localStorage.getItem('chatSessions') || '[]');
      // Sort by last activity, most recent first
      const sortedSessions = storedSessions.sort((a, b) => 
        new Date(b.last_activity) - new Date(a.last_activity)
      );
      return Promise.resolve({ data: sortedSessions.slice(0, params.limit || 50) });
    } catch (error) {
      console.error('Error getting sessions from storage:', error);
      return Promise.resolve({ data: [] });
    }
  },

  // Clear all chat data (for cleanup)
  clearAllSessions: () => {
    try {
      localStorage.removeItem('chatSessions');
      return Promise.resolve({ success: true });
    } catch (error) {
      console.error('Error clearing chat sessions:', error);
      return Promise.resolve({ success: false });
    }
  },
  
  updateSession: (sessionId, updateData) => {
    // Enhanced chat handles session updates differently
    return Promise.resolve({ data: { id: sessionId, ...updateData } });
  },
  
  deleteSession: (sessionId) => {
    // Remove from localStorage and end conversation
    try {
      const sessions = JSON.parse(localStorage.getItem('chatSessions') || '[]');
      const filteredSessions = sessions.filter(s => s.id !== sessionId && s.session_id !== sessionId);
      localStorage.setItem('chatSessions', JSON.stringify(filteredSessions));
    } catch (error) {
      console.error('Error removing session from storage:', error);
    }
    
    return api.post(`/chat/conversation/${sessionId}/end`).catch(error => {
      // Even if API call fails, we've removed it from localStorage
      console.warn('Could not end conversation on server:', error);
      return Promise.resolve({ data: { success: true } });
    });
  },
  
  // Session actions - enhanced chat handles these internally
  pauseSession: (sessionId) => Promise.resolve({ data: { status: 'paused' } }),
  resumeSession: (sessionId) => Promise.resolve({ data: { status: 'active' } }),
  
  // Enhanced messages
  sendMessage: (sessionId, messageData) => {
    const enhancedMessageData = {
      user_id: DEFAULT_USER_ID,
      session_id: sessionId,
      message: messageData.content,
      conversation_mode: 'supportive_listening',
      context_metadata: messageData.context || {}
    };
    return api.post('/chat/message', enhancedMessageData).then(response => {
      const data = response.data;
      // Convert enhanced chat response to frontend expected format
      const formattedResponse = {
        data: {
          id: data.message_id,
          role: 'assistant',
          content: data.content,
          timestamp: data.timestamp,
          metadata: {
            crisis_level: data.crisis_indicators?.length > 0 ? 'HIGH' : 'NONE',
            emotion_analysis: {
              primary_emotion: 'supportive',
              confidence: data.confidence_score
            },
            response_time_ms: Math.round((data.processing_metadata?.processing_time_seconds || 0) * 1000),
            conversation_stage: data.conversation_stage,
            response_style: data.response_style,
            therapeutic_techniques: data.therapeutic_techniques,
            emotional_support_level: data.emotional_support_level
          }
        }
      };
      
      // Update session in localStorage
      try {
        const sessions = JSON.parse(localStorage.getItem('chatSessions') || '[]');
        const sessionIndex = sessions.findIndex(s => s.id === sessionId || s.session_id === sessionId);
        if (sessionIndex !== -1) {
          sessions[sessionIndex].last_activity = new Date().toISOString();
          sessions[sessionIndex].message_count = (sessions[sessionIndex].message_count || 0) + 1;
          sessions[sessionIndex].recent_messages = sessions[sessionIndex].recent_messages || [];
          sessions[sessionIndex].recent_messages.push({
            role: 'assistant',
            content: formattedResponse.data.content.substring(0, 100) + '...',
            timestamp: formattedResponse.data.timestamp
          });
          // Keep only last 3 messages for preview
          sessions[sessionIndex].recent_messages = sessions[sessionIndex].recent_messages.slice(-3);
          localStorage.setItem('chatSessions', JSON.stringify(sessions));
        }
      } catch (error) {
        console.error('Error updating session:', error);
      }
      
      return formattedResponse;
    });
  },
  
  getMessages: (sessionId, params = {}) => api.get(`/chat/conversation/${sessionId}/history`, { params }),
  
  getSuggestions: (sessionId) => {
    // Return context-aware suggestions - will be handled by ContextAwareSuggestions component
    return Promise.resolve({ data: [] });
  },
  
  // Enhanced chat modes (replaces session types)
  getAvailableTypes: () => api.get('/sessions/types/available'),
};

// Health check and performance
export const healthCheck = () => api.get('/health');
export const performanceAPI = {
  getStatus: () => api.get('/health/performance'),
  getCacheStatus: () => api.get('/health/cache'),
  runBenchmark: () => api.post('/monitoring/performance/benchmark')
};

// Advanced AI API
export const advancedAI = {
  // Personality Analysis
  getPersonalityProfile: (userId = DEFAULT_USER_ID) => 
    api.post('/ai/advanced/analysis/personality', {
      user_id: userId,
      include_detailed_traits: true
    }),
  
  getPersonalityDimensions: (userId = DEFAULT_USER_ID) => 
    api.get('/ai/advanced/personality/dimensions', { params: { user_id: userId } }),
  
  // Pattern Analysis & Insights
  getComprehensiveAnalysis: (userId = DEFAULT_USER_ID, options = {}) =>
    api.post('/ai/advanced/analysis/comprehensive', {
      user_id: userId,
      timeframe: options.timeframe || 'monthly',
      include_predictions: options.include_predictions !== false,
      include_personality: options.include_personality !== false,
      max_entries: options.max_entries || 100
    }),
  
  getTemporalInsights: (userId = DEFAULT_USER_ID, options = {}) => {
    const params = { user_id: userId };
    if (options.timeframe) params.timeframe = options.timeframe;
    if (options.max_entries) params.max_entries = options.max_entries;
    if (options.insight_types) params.insight_types = options.insight_types;
    
    return api.get('/ai/advanced/insights/temporal', { params });
  },
  
  getPredictiveAnalysis: (userId = DEFAULT_USER_ID, options = {}) =>
    api.post('/ai/advanced/analysis/predictive', {
      user_id: userId,
      prediction_horizon: options.prediction_horizon || 7,
      include_risk_assessment: options.include_risk_assessment !== false,
      include_opportunities: options.include_opportunities !== false
    }),
  
  // Health & Status
  getHealthCheck: () => api.get('/ai/advanced/health'),
  getServiceStats: () => api.get('/ai/advanced/stats'),
};

// Dashboard API
export const dashboardAPI = {
  getOverview: () => api.get('/monitoring/metrics'),
  getQuickStats: async () => {
    try {
      const [entriesRes, performanceRes] = await Promise.allSettled([
        entryAPI.getAll({ limit: 100 }), // Get more entries for better stats
        performanceAPI.getStatus()
      ]);
      
      return {
        entries: entriesRes.status === 'fulfilled' ? entriesRes.value.data : [],
        performance: performanceRes.status === 'fulfilled' ? performanceRes.value.data : null
      };
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      throw error;
    }
  }
};

// Authentication API
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (userData) => api.post('/auth/register', userData),
  logout: (refreshToken) => api.post('/auth/logout', { refresh_token: refreshToken }),
  refreshToken: (refreshToken) => api.post('/auth/refresh', { refresh_token: refreshToken }),
  getProfile: () => api.get('/auth/me'),
  updateProfile: (userData) => api.put('/auth/me', userData),
  changePassword: (passwordData) => api.post('/auth/change-password', passwordData),
  getAuthStatus: () => api.get('/auth/status'),
  
  // Admin endpoints
  admin: {
    getUsers: (params = {}) => api.get('/auth/admin/users', { params }),
    createUser: (userData) => api.post('/auth/admin/users/create', userData),
    updateUser: (userId, userData) => api.put(`/auth/admin/users/${userId}`, userData),
    getUserSessions: (userId) => api.get(`/auth/admin/users/${userId}/sessions`),
    revokeSession: (sessionId) => api.delete(`/auth/admin/sessions/${sessionId}`),
    getSecurityStats: () => api.get('/auth/admin/security/stats'),
    getLoginAttempts: (params = {}) => api.get('/auth/admin/login-attempts', { params }),
    cleanupTokens: () => api.post('/auth/admin/cleanup-tokens')
  }
};

export default api;
// Enhanced Insights API - includes chat conversations
export const enhancedInsightsAPI = {
  askQuestion: (question) => api.post('/insights/ask', null, { params: { question } }),
  askJournalOnly: (question) => api.post('/insights/ask-journal-only', null, { params: { question } }),
  getEnhancedCoaching: () => api.get('/insights/coaching'),
  getJournalOnlyCoaching: () => api.get('/insights/coaching-journal-only'),
  getEnhancedPatterns: () => api.get('/insights/patterns'),
  getChatInsights: (days = 30) => api.get('/insights/chat-insights', { params: { days } }),
  getComprehensiveMoodAnalysis: (days = 30) => api.get('/insights/mood-analysis-comprehensive', { params: { days } }),
  getComprehensiveTrends: (days = 30) => api.get('/insights/trends/comprehensive', { params: { days } }),
};

// Update existing insightsAPI to include new methods
insightsAPI.ask = enhancedInsightsAPI.askQuestion;
insightsAPI.askJournalOnly = enhancedInsightsAPI.askJournalOnly;
insightsAPI.getEnhancedCoaching = enhancedInsightsAPI.getEnhancedCoaching;
insightsAPI.getEnhancedPatterns = enhancedInsightsAPI.getEnhancedPatterns;
insightsAPI.getChatInsights = enhancedInsightsAPI.getChatInsights;
insightsAPI.getComprehensiveMoodAnalysis = enhancedInsightsAPI.getComprehensiveMoodAnalysis;
insightsAPI.getComprehensiveTrends = enhancedInsightsAPI.getComprehensiveTrends;
