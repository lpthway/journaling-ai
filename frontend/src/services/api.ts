import axios, { AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import {
  Entry,
  Topic,
  Session,
  Message,
  Template,
  CreateEntryData,
  UpdateEntryData,
  CreateTopicData,
  UpdateTopicData,
  CreateSessionData,
  UpdateSessionData,
  SendMessageData,
  SearchFilters,
  PaginatedResponse,
  InsightData,
  APIResponse,
  SessionType
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for authentication and debugging
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add authentication token if available
    const token = localStorage.getItem('access_token') || localStorage.getItem('auth_token');
    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
      console.log('Auth token added to request:', config.url);
    } else {
      console.log('No auth token found for request:', config.url);
    }
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling and token refresh
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      console.log('Token expired, attempting refresh...');
      
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          console.log('Attempting token refresh...');
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken
          });
          
          const { access_token, refresh_token: newRefreshToken } = response.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('auth_token', access_token); // Compatibility
          if (newRefreshToken) {
            localStorage.setItem('refresh_token', newRefreshToken);
          }
          
          console.log('Token refresh successful, retrying original request');
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          console.error('Token refresh failed:', refreshError);
          localStorage.removeItem('access_token');
          localStorage.removeItem('auth_token'); // Compatibility
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      } else {
        console.log('No refresh token found, redirecting to login');
        localStorage.removeItem('access_token');
        localStorage.removeItem('auth_token'); // Compatibility
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }
    
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Entry API
export const entryAPI = {
  create: (entryData: CreateEntryData): Promise<AxiosResponse<Entry>> => 
    api.post('/entries/', entryData),
  
  getAll: (params: SearchFilters = {}): Promise<AxiosResponse<Entry[]>> => 
    api.get('/entries/', { params: { ...params, _t: Date.now() } }),
  
  getById: (id: string): Promise<AxiosResponse<Entry>> => 
    api.get(`/entries/${id}?_t=${Date.now()}`),
  
  getByTopic: (topicId: string, params: SearchFilters = {}): Promise<AxiosResponse<Entry[]>> => 
    api.get(`/topics/${topicId}/entries`, { params }),
  
  update: (id: string, entryData: UpdateEntryData): Promise<AxiosResponse<Entry>> => 
    api.put(`/entries/${id}`, entryData),
  
  delete: (id: string): Promise<AxiosResponse<void>> => 
    api.delete(`/entries/${id}`),
  
  search: (query: string, limit: number = 10, topicId?: string): Promise<AxiosResponse<Entry[]>> => 
    api.get('/entries/search/semantic', { 
      params: { query, limit, topic_id: topicId } 
    }),
  
  advancedSearch: (filters: SearchFilters): Promise<AxiosResponse<Entry[]>> => 
    api.post('/entries/search/advanced', filters),
  
  getMoodStats: (days: number = 30): Promise<AxiosResponse<any>> => 
    api.get('/insights/mood-stats', { params: { days } }),
  
  // Favorites
  toggleFavorite: (id: string): Promise<AxiosResponse<Entry>> => 
    api.patch(`/entries/${id}/favorite`),
  
  getFavorites: (limit: number = 50): Promise<AxiosResponse<Entry[]>> => 
    api.get('/entries/favorites', { params: { limit } }),
  
  // Versioning
  getVersions: (id: string): Promise<AxiosResponse<Entry[]>> => 
    api.get(`/entries/${id}/versions`),
  
  revertToVersion: (id: string, version: number): Promise<AxiosResponse<Entry>> => 
    api.post(`/entries/${id}/revert/${version}`),
  
  // Templates
  getTemplates: (): Promise<AxiosResponse<Template[]>> => 
    api.get('/entries/templates'),
  
  getTemplate: (id: string): Promise<AxiosResponse<Template>> => 
    api.get(`/entries/templates/${id}`),
  
  createTemplate: (templateData: Partial<Template>): Promise<AxiosResponse<Template>> => 
    api.post('/entries/templates', templateData),
};

// Topic API
export const topicAPI = {
  create: (topicData: CreateTopicData): Promise<AxiosResponse<Topic>> => 
    api.post('/topics/', topicData),
  
  getAll: (): Promise<AxiosResponse<Topic[]>> => 
    api.get('/topics/'),
  
  getById: (id: string): Promise<AxiosResponse<Topic>> => 
    api.get(`/topics/${id}`),
  
  update: (id: string, topicData: UpdateTopicData): Promise<AxiosResponse<Topic>> => 
    api.put(`/topics/${id}`, topicData),
  
  delete: (id: string): Promise<AxiosResponse<void>> => 
    api.delete(`/topics/${id}`),
  
  getEntries: (id: string, params: SearchFilters = {}): Promise<AxiosResponse<Entry[]>> => 
    api.get(`/topics/${id}/entries`, { params }),
};

// Insights API
export const insightsAPI = {
  // Use new cached endpoints for blazing fast performance
  getCachedInsights: (days: number = 30): Promise<AxiosResponse<InsightData>> => 
    api.get('/insights/cached', { params: { time_range_days: days } }),
  
  refreshCache: (): Promise<AxiosResponse<void>> => 
    api.post('/insights/refresh'),
  
  getStatus: (): Promise<AxiosResponse<any>> => 
    api.get('/insights/status'),
  
  // Legacy AI endpoints (now cached internally)
  askQuestion: (question: string): Promise<AxiosResponse<string>> => 
    api.post('/insights/ask', null, { params: { question } }),
  
  getCoaching: (): Promise<AxiosResponse<string[]>> => 
    api.get('/insights/coaching'),
  
  // Legacy compatibility (redirected to cached)
  getPatterns: (): Promise<AxiosResponse<any[]>> => 
    api.get('/insights/patterns'),
  
  getMoodTrends: (days: number = 30): Promise<AxiosResponse<any[]>> => 
    api.get('/insights/mood-stats', { params: { days } }),
};

// Session API (Enhanced)
export const sessionAPI = {
  // Enhanced session management
  createSession: (sessionData: CreateSessionData): Promise<AxiosResponse<any>> => {
    // Convert frontend session data to enhanced chat format
    const enhancedData = {
      conversation_mode: (sessionData as any).session_type || 'supportive_listening',
      initial_context: {
        title: (sessionData as any).title || 'Enhanced Chat Session',
        metadata: (sessionData as any).metadata || {},
        frontend_integration: true
      }
    };
    return api.post('/chat/conversation/start', enhancedData).then(response => {
      // Convert enhanced chat response to frontend expected format
      const data = response.data;
      const sessionInfo = {
        id: data.session_id,
        session_id: data.session_id,
        title: (sessionData as any).title || 'Enhanced Chat Session',
        session_type: (sessionData as any).session_type || 'supportive_listening',
        conversation_mode: (sessionData as any).session_type || 'supportive_listening',
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
      
      return { 
        data: sessionInfo,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      } as AxiosResponse<any>;
    });
  },
  
  getSession: (sessionId: string): Promise<AxiosResponse<any>> => 
    api.get(`/chat/conversation/${sessionId}/history`),
  
  getSessions: (params: Record<string, any> = {}): Promise<AxiosResponse<any[]>> => {
    // Get sessions from localStorage since enhanced chat doesn't have session listing yet
    try {
      const storedSessions = JSON.parse(localStorage.getItem('chatSessions') || '[]');
      // Sort by last activity, most recent first
      const sortedSessions = storedSessions.sort((a: any, b: any) => 
        new Date(b.last_activity).getTime() - new Date(a.last_activity).getTime()
      );
      return Promise.resolve({ 
        data: sortedSessions.slice(0, params.limit || 50),
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      } as AxiosResponse<any[]>);
    } catch (error) {
      console.error('Error getting sessions from storage:', error);
      return Promise.resolve({ 
        data: [],
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      } as AxiosResponse<any[]>);
    }
  },

  // Clear all chat data (for cleanup)
  clearAllSessions: (): Promise<AxiosResponse<any>> => {
    try {
      localStorage.removeItem('chatSessions');
      return Promise.resolve({ 
        data: { success: true },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      } as AxiosResponse<any>);
    } catch (error) {
      console.error('Error clearing chat sessions:', error);
      return Promise.resolve({ 
        data: { success: false },
        status: 500,
        statusText: 'Error',
        headers: {},
        config: {} as any
      } as AxiosResponse<any>);
    }
  },
  
  updateSession: (sessionId: string, updateData: UpdateSessionData): Promise<AxiosResponse<any>> => 
    Promise.resolve({ 
      data: { id: sessionId, ...updateData },
      status: 200,
      statusText: 'OK',
      headers: {},
      config: {} as any
    } as AxiosResponse<any>),
  
  deleteSession: (sessionId: string): Promise<AxiosResponse<void>> => {
    // Remove from localStorage and end conversation
    try {
      const sessions = JSON.parse(localStorage.getItem('chatSessions') || '[]');
      const filteredSessions = sessions.filter((s: any) => s.id !== sessionId && s.session_id !== sessionId);
      localStorage.setItem('chatSessions', JSON.stringify(filteredSessions));
    } catch (error) {
      console.error('Error removing session from storage:', error);
    }
    
    return api.post(`/chat/conversation/${sessionId}/end`).catch(error => {
      // Even if API call fails, we've removed it from localStorage
      console.warn('Could not end conversation on server:', error);
      return Promise.resolve({ 
        data: { success: true },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      } as AxiosResponse<any>);
    });
  },
  
  // Session actions - enhanced chat handles these internally
  pauseSession: (sessionId: string): Promise<AxiosResponse<any>> => 
    Promise.resolve({ 
      data: { status: 'paused' },
      status: 200,
      statusText: 'OK',
      headers: {},
      config: {} as any
    } as AxiosResponse<any>),
  
  resumeSession: (sessionId: string): Promise<AxiosResponse<any>> => 
    Promise.resolve({ 
      data: { status: 'active' },
      status: 200,
      statusText: 'OK',
      headers: {},
      config: {} as any
    } as AxiosResponse<any>),
  
  // Enhanced messages
  sendMessage: (sessionId: string, messageData: SendMessageData): Promise<AxiosResponse<any>> => {
    const enhancedMessageData = {
      session_id: sessionId,
      message: (messageData as any).content,
      conversation_mode: 'supportive_listening',
      context_metadata: (messageData as any).context || {}
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
        const sessionIndex = sessions.findIndex((s: any) => s.id === sessionId || s.session_id === sessionId);
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
      
      return formattedResponse as any;
    });
  },
  
  getMessages: (sessionId: string, params: Record<string, any> = {}): Promise<AxiosResponse<any[]>> => 
    api.get(`/chat/conversation/${sessionId}/history`, { params }),
  
  getSuggestions: (sessionId: string): Promise<AxiosResponse<string[]>> => {
    // Return context-aware suggestions - will be handled by ContextAwareSuggestions component
    return Promise.resolve({ 
      data: [],
      status: 200,
      statusText: 'OK',
      headers: {},
      config: {} as any
    } as AxiosResponse<string[]>);
  },
  
  // Enhanced chat modes (replaces session types)
  getAvailableTypes: (): Promise<AxiosResponse<SessionType[]>> => 
    api.get('/sessions/types/available'),
};

// Chat API (Enhanced Chat Service)
export const chatAPI = {
  getConversations: (limit: number = 50): Promise<AxiosResponse<any>> => 
    api.get('/chat/conversations', { params: { limit } }),
  
  sendMessage: (messageData: any): Promise<AxiosResponse<any>> => 
    api.post('/chat/message', messageData),
  
  getConversationHistory: (sessionId: string, limit: number = 50): Promise<AxiosResponse<any>> => 
    api.get(`/chat/conversation/${sessionId}/history`, { params: { limit } }),
  
  getHealth: (): Promise<AxiosResponse<any>> => 
    api.get('/chat/health'),
  
  getStats: (): Promise<AxiosResponse<any>> => 
    api.get('/chat/stats'),
};

// Authentication API
export const authAPI = {
  login: (credentials: any): Promise<AxiosResponse<any>> => api.post('/auth/login', credentials),
  register: (userData: any): Promise<AxiosResponse<any>> => api.post('/auth/register', userData),
  logout: (refreshToken: string): Promise<AxiosResponse<any>> => api.post('/auth/logout', { refresh_token: refreshToken }),
  refreshToken: (refreshToken: string): Promise<AxiosResponse<any>> => api.post('/auth/refresh', { refresh_token: refreshToken }),
  getProfile: (): Promise<AxiosResponse<any>> => api.get('/auth/me'),
  updateProfile: (userData: any): Promise<AxiosResponse<any>> => api.put('/auth/me', userData),
  changePassword: (passwordData: any): Promise<AxiosResponse<any>> => api.post('/auth/change-password', passwordData),
  getAuthStatus: (): Promise<AxiosResponse<any>> => api.get('/auth/status'),
  
  // Admin endpoints
  admin: {
    getUsers: (params: any = {}): Promise<AxiosResponse<any>> => api.get('/auth/admin/users', { params }),
    createUser: (userData: any): Promise<AxiosResponse<any>> => api.post('/auth/admin/users/create', userData),
    updateUser: (userId: string, userData: any): Promise<AxiosResponse<any>> => api.put(`/auth/admin/users/${userId}`, userData),
    getUserSessions: (userId: string): Promise<AxiosResponse<any>> => api.get(`/auth/admin/users/${userId}/sessions`),
    revokeSession: (sessionId: string): Promise<AxiosResponse<any>> => api.delete(`/auth/admin/sessions/${sessionId}`),
    getSecurityStats: (): Promise<AxiosResponse<any>> => api.get('/auth/admin/security/stats'),
    getLoginAttempts: (params: any = {}): Promise<AxiosResponse<any>> => api.get('/auth/admin/login-attempts', { params }),
    cleanupTokens: (): Promise<AxiosResponse<any>> => api.post('/auth/admin/cleanup-tokens')
  }
};

// Advanced AI API
export const advancedAI = {
  // Personality Analysis
  getPersonalityProfile: (): Promise<AxiosResponse<any>> => 
    api.post('/ai/advanced/analysis/personality', {
      include_detailed_traits: true
    }),
  
  getPersonalityDimensions: (): Promise<AxiosResponse<any>> => 
    api.get('/ai/advanced/personality/dimensions'),
  
  // Pattern Analysis & Insights
  getComprehensiveAnalysis: (options: any = {}): Promise<AxiosResponse<any>> =>
    api.post('/ai/advanced/analysis/comprehensive', {
      timeframe: options.timeframe || 'monthly',
      include_predictions: options.include_predictions !== false,
      include_personality: options.include_personality !== false,
      max_entries: options.max_entries || 100
    }),
  
  getTemporalInsights: (options: any = {}): Promise<AxiosResponse<any>> => {
    const params: any = {};
    if (options.timeframe) params.timeframe = options.timeframe;
    if (options.max_entries) params.max_entries = options.max_entries;
    if (options.insight_types) params.insight_types = options.insight_types;
    
    return api.get('/ai/advanced/insights/temporal', { params });
  },
  
  getPredictiveAnalysis: (options: any = {}): Promise<AxiosResponse<any>> =>
    api.post('/ai/advanced/analysis/predictive', {
      prediction_horizon: options.prediction_horizon || 7,
      include_risk_assessment: options.include_risk_assessment !== false,
      include_opportunities: options.include_opportunities !== false
    }),
  
  // Health & Status
  getHealthCheck: (): Promise<AxiosResponse<any>> => api.get('/ai/advanced/health'),
  getServiceStats: (): Promise<AxiosResponse<any>> => api.get('/ai/advanced/stats'),
};

// Performance API
export const performanceAPI = {
  getStatus: (): Promise<AxiosResponse<any>> => api.get('/health/performance'),
  getCacheStatus: (): Promise<AxiosResponse<any>> => api.get('/health/cache'),
  runBenchmark: (): Promise<AxiosResponse<any>> => api.post('/monitoring/performance/benchmark')
};

// Dashboard API
export const dashboardAPI = {
  getOverview: (): Promise<AxiosResponse<any>> => api.get('/monitoring/metrics'),
  getQuickStats: async (): Promise<any> => {
    try {
      const [entriesRes, performanceRes] = await Promise.allSettled([
        entryAPI.getAll({ limit: 100 }), // Get more entries for better stats
        api.get('/health/performance')
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

// Health check
export const healthCheck = (): Promise<AxiosResponse<any>> => api.get('/health');

export default api;

// Enhanced Insights API - includes chat conversations
export const enhancedInsightsAPI = {
  askQuestion: (question: string): Promise<AxiosResponse<string>> => 
    api.post('/insights/ask', null, { params: { question } }),
  
  askJournalOnly: (question: string): Promise<AxiosResponse<string>> => 
    api.post('/insights/ask-journal-only', null, { params: { question } }),
  
  getEnhancedCoaching: (): Promise<AxiosResponse<string[]>> => 
    api.get('/insights/coaching'),
  
  getJournalOnlyCoaching: (): Promise<AxiosResponse<string[]>> => 
    api.get('/insights/coaching-journal-only'),
  
  getEnhancedPatterns: (): Promise<AxiosResponse<any[]>> => 
    api.get('/insights/patterns'),
  
  getChatInsights: (days: number = 30): Promise<AxiosResponse<any>> => 
    api.get('/insights/chat-insights', { params: { days } }),
  
  getComprehensiveMoodAnalysis: (days: number = 30): Promise<AxiosResponse<any>> => 
    api.get('/insights/mood-analysis-comprehensive', { params: { days } }),
  
  getComprehensiveTrends: (days: number = 30): Promise<AxiosResponse<any>> => 
    api.get('/insights/trends/comprehensive', { params: { days } }),
};

// Update existing insightsAPI to include new methods
Object.assign(insightsAPI, {
  ask: enhancedInsightsAPI.askQuestion,
  askJournalOnly: enhancedInsightsAPI.askJournalOnly,
  getEnhancedCoaching: enhancedInsightsAPI.getEnhancedCoaching,
  getEnhancedPatterns: enhancedInsightsAPI.getEnhancedPatterns,
  getChatInsights: enhancedInsightsAPI.getChatInsights,
  getComprehensiveMoodAnalysis: enhancedInsightsAPI.getComprehensiveMoodAnalysis,
  getComprehensiveTrends: enhancedInsightsAPI.getComprehensiveTrends,
});