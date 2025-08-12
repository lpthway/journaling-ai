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
  SessionType,
  PerformanceStatus,
  PersonalityProfile,
  PredictiveAnalysis,
  AuthCredentials,
  RegisterData,
  UserProfile,
  PasswordChangeData,
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';
const DEFAULT_USER_ID = '11111111-1111-1111-1111-111111111111';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth token and debugging
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add auth token
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Debug logging
    if (process.env.NODE_ENV === 'development') {
      console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`, {
        params: config.params,
        data: config.data,
      });
    }
    
    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for debugging and error handling
api.interceptors.response.use(
  (response: AxiosResponse) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`✅ API Response: ${response.config.method?.toUpperCase()} ${response.config.url}`, {
        status: response.status,
        data: response.data,
      });
    }
    return response;
  },
  (error) => {
    console.error('❌ API Error:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      message: error.response?.data?.detail || error.message,
    });
    return Promise.reject(error);
  }
);

// Entry API
export const entryAPI = {
  getAll: (filters: SearchFilters = {}): Promise<AxiosResponse<PaginatedResponse<Entry>>> =>
    api.get('/entries/', { params: filters }),

  getById: (id: string): Promise<AxiosResponse<Entry>> =>
    api.get(`/entries/${id}`),

  create: (data: CreateEntryData): Promise<AxiosResponse<Entry>> =>
    api.post('/entries/', data),

  update: (id: string, data: UpdateEntryData): Promise<AxiosResponse<Entry>> =>
    api.put(`/entries/${id}`, data),

  delete: (id: string): Promise<AxiosResponse<void>> =>
    api.delete(`/entries/${id}`),

  search: (filters: SearchFilters): Promise<AxiosResponse<PaginatedResponse<Entry>>> =>
    api.get('/entries/search', { params: filters }),

  toggleFavorite: (id: string): Promise<AxiosResponse<Entry>> =>
    api.patch(`/entries/${id}/favorite`),

  getMoodStats: (): Promise<AxiosResponse<any>> =>
    api.get('/entries/mood-stats'),

  getRecentEntries: (limit: number = 10): Promise<AxiosResponse<Entry[]>> =>
    api.get('/entries/recent', { params: { limit } }),
};

// Topic API
export const topicAPI = {
  getAll: (): Promise<AxiosResponse<Topic[]>> =>
    api.get('/topics/'),

  getById: (id: string): Promise<AxiosResponse<Topic>> =>
    api.get(`/topics/${id}`),

  create: (data: CreateTopicData): Promise<AxiosResponse<Topic>> =>
    api.post('/topics/', data),

  update: (id: string, data: UpdateTopicData): Promise<AxiosResponse<Topic>> =>
    api.put(`/topics/${id}`, data),

  delete: (id: string): Promise<AxiosResponse<void>> =>
    api.delete(`/topics/${id}`),

  getEntries: (id: string, filters: SearchFilters = {}): Promise<AxiosResponse<PaginatedResponse<Entry>>> =>
    api.get(`/topics/${id}/entries`, { params: filters }),
};

// Insights API
export const insightsAPI = {
  ask: (question: string): Promise<AxiosResponse<any>> =>
    api.post('/insights/ask', null, { params: { question } }),

  getCoaching: (): Promise<AxiosResponse<InsightData>> =>
    api.get('/insights/coaching'),

  getPatterns: (): Promise<AxiosResponse<InsightData>> =>
    api.get('/insights/patterns'),

  getMoodTrends: (days: number = 30): Promise<AxiosResponse<any>> =>
    api.get('/insights/mood-trends', { params: { days } }),

  getEmotionalPatterns: (days: number = 30): Promise<AxiosResponse<any>> =>
    api.get('/insights/emotional-patterns', { params: { days } }),

  getWritingInsights: (days: number = 30): Promise<AxiosResponse<any>> =>
    api.get('/insights/writing-insights', { params: { days } }),
};

// Session API
export const sessionAPI = {
  getAll: (): Promise<AxiosResponse<Session[]>> =>
    api.get('/sessions/'),

  getById: (id: string): Promise<AxiosResponse<Session>> =>
    api.get(`/sessions/${id}`),

  create: (data: CreateSessionData): Promise<AxiosResponse<Session>> =>
    api.post('/sessions/', data),

  update: (id: string, data: UpdateSessionData): Promise<AxiosResponse<Session>> =>
    api.put(`/sessions/${id}`, data),

  delete: (id: string): Promise<AxiosResponse<void>> =>
    api.delete(`/sessions/${id}`),

  getMessages: (id: string): Promise<AxiosResponse<Message[]>> =>
    api.get(`/sessions/${id}/messages`),

  sendMessage: (id: string, data: SendMessageData): Promise<AxiosResponse<Message>> =>
    api.post(`/sessions/${id}/messages`, data),

  getRecommendedType: (): Promise<AxiosResponse<{ recommended_type: SessionType; reason: string }>> =>
    api.get('/sessions/recommended-type'),

  streamMessage: (sessionId: string, content: string): Promise<Response> => {
    const url = `${API_BASE_URL}/chat/stream`;
    const token = localStorage.getItem('auth_token');
    
    return fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
      },
      body: JSON.stringify({
        session_id: sessionId,
        content: content
      })
    });
  },
};

// Chat API
export const chatAPI = {
  sendMessage: (sessionId: string, content: string, metadata?: Record<string, any>): Promise<AxiosResponse<Message>> =>
    api.post('/chat/message', {
      session_id: sessionId,
      content,
      metadata
    }),

  getSession: (sessionId: string): Promise<AxiosResponse<Session>> =>
    api.get(`/chat/sessions/${sessionId}`),

  createSession: (type: SessionType, title?: string): Promise<AxiosResponse<Session>> =>
    api.post('/chat/sessions', { type, title }),

  streamMessage: (sessionId: string, content: string): Promise<Response> => {
    const url = `${API_BASE_URL}/chat/stream`;
    const token = localStorage.getItem('auth_token');
    
    return fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
      },
      body: JSON.stringify({
        session_id: sessionId,
        content: content
      })
    });
  },
};

// Health Check
export const healthCheck = (): Promise<AxiosResponse<any>> => api.get('/health');

// Performance API
export const performanceAPI = {
  getStatus: (): Promise<AxiosResponse<PerformanceStatus>> =>
    api.get('/health/performance'),
  getCacheStatus: (): Promise<AxiosResponse<any>> =>
    api.get('/health/cache'),
  runBenchmark: (): Promise<AxiosResponse<any>> =>
    api.post('/monitoring/performance/benchmark')
};

// Advanced AI API
export const advancedAI = {
  // Personality Analysis
  getPersonalityProfile: (userId: string = DEFAULT_USER_ID): Promise<AxiosResponse<PersonalityProfile>> => 
    api.post('/ai/advanced/analysis/personality', {
      user_id: userId,
      include_detailed_traits: true
    }),
  
  getPersonalityDimensions: (userId: string = DEFAULT_USER_ID): Promise<AxiosResponse<any>> => 
    api.get('/ai/advanced/personality/dimensions', { params: { user_id: userId } }),
  
  // Pattern Analysis & Insights
  getComprehensiveAnalysis: (userId: string = DEFAULT_USER_ID, options: any = {}): Promise<AxiosResponse<any>> =>
    api.post('/ai/advanced/analysis/comprehensive', {
      user_id: userId,
      timeframe: options.timeframe || 'monthly',
      include_predictions: options.include_predictions !== false,
      include_personality: options.include_personality !== false,
      max_entries: options.max_entries || 100
    }),
  
  getTemporalInsights: (userId: string = DEFAULT_USER_ID, options: any = {}): Promise<AxiosResponse<any>> => {
    const params: any = { user_id: userId };
    if (options.timeframe) params.timeframe = options.timeframe;
    if (options.max_entries) params.max_entries = options.max_entries;
    if (options.insight_types) params.insight_types = options.insight_types;
    
    return api.get('/ai/advanced/insights/temporal', { params });
  },
  
  getPredictiveAnalysis: (userId: string = DEFAULT_USER_ID, options: any = {}): Promise<AxiosResponse<PredictiveAnalysis>> =>
    api.post('/ai/advanced/analysis/predictive', {
      user_id: userId,
      prediction_horizon: options.prediction_horizon || 7,
      include_risk_assessment: options.include_risk_assessment !== false,
      include_opportunities: options.include_opportunities !== false
    }),
  
  // Health & Status
  getHealthCheck: (): Promise<AxiosResponse<any>> => api.get('/ai/advanced/health'),
  getServiceStats: (): Promise<AxiosResponse<any>> => api.get('/ai/advanced/stats'),
};

// Dashboard API
export const dashboardAPI = {
  getOverview: (): Promise<AxiosResponse<any>> => api.get('/monitoring/metrics'),
  getQuickStats: async (): Promise<{ entries: Entry[]; performance: PerformanceStatus | null }> => {
    try {
      const [entriesRes, performanceRes] = await Promise.allSettled([
        entryAPI.getAll({ limit: 100 }), // Get more entries for better stats
        performanceAPI.getStatus()
      ]);
      
      return {
        entries: entriesRes.status === 'fulfilled' ? entriesRes.value.data.items : [],
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
  login: (credentials: AuthCredentials): Promise<AxiosResponse<{ access_token: string; user: UserProfile }>> =>
    api.post('/auth/login', credentials),
  register: (userData: RegisterData): Promise<AxiosResponse<{ user: UserProfile }>> =>
    api.post('/auth/register', userData),
  logout: (refreshToken: string): Promise<AxiosResponse<void>> =>
    api.post('/auth/logout', { refresh_token: refreshToken }),
  refreshToken: (refreshToken: string): Promise<AxiosResponse<{ access_token: string }>> =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),
  getProfile: (): Promise<AxiosResponse<UserProfile>> =>
    api.get('/auth/me'),
  updateProfile: (userData: Partial<UserProfile>): Promise<AxiosResponse<UserProfile>> =>
    api.put('/auth/me', userData),
  changePassword: (passwordData: PasswordChangeData): Promise<AxiosResponse<void>> =>
    api.post('/auth/change-password', passwordData),
  getAuthStatus: (): Promise<AxiosResponse<{ authenticated: boolean; user?: UserProfile }>> =>
    api.get('/auth/status'),
  
  // Admin endpoints
  admin: {
    getUsers: (params: any = {}): Promise<AxiosResponse<PaginatedResponse<UserProfile>>> =>
      api.get('/auth/admin/users', { params }),
    createUser: (userData: RegisterData): Promise<AxiosResponse<UserProfile>> =>
      api.post('/auth/admin/users/create', userData),
    updateUser: (userId: string, userData: Partial<UserProfile>): Promise<AxiosResponse<UserProfile>> =>
      api.put(`/auth/admin/users/${userId}`, userData),
    getUserSessions: (userId: string): Promise<AxiosResponse<any[]>> =>
      api.get(`/auth/admin/users/${userId}/sessions`),
    revokeSession: (sessionId: string): Promise<AxiosResponse<void>> =>
      api.delete(`/auth/admin/sessions/${sessionId}`),
    getSecurityStats: (): Promise<AxiosResponse<any>> =>
      api.get('/auth/admin/security/stats'),
    getLoginAttempts: (params: any = {}): Promise<AxiosResponse<any[]>> =>
      api.get('/auth/admin/login-attempts', { params }),
    cleanupTokens: (): Promise<AxiosResponse<void>> =>
      api.post('/auth/admin/cleanup-tokens')
  }
};

// Enhanced Insights API - includes chat conversations
export const enhancedInsightsAPI = {
  askQuestion: (question: string): Promise<AxiosResponse<any>> =>
    api.post('/insights/ask', null, { params: { question } }),
  askJournalOnly: (question: string): Promise<AxiosResponse<any>> =>
    api.post('/insights/ask-journal-only', null, { params: { question } }),
  getEnhancedCoaching: (): Promise<AxiosResponse<InsightData>> =>
    api.get('/insights/coaching'),
  getJournalOnlyCoaching: (): Promise<AxiosResponse<InsightData>> =>
    api.get('/insights/coaching-journal-only'),
  getEnhancedPatterns: (): Promise<AxiosResponse<InsightData>> =>
    api.get('/insights/patterns'),
  getChatInsights: (days: number = 30): Promise<AxiosResponse<any>> =>
    api.get('/insights/chat-insights', { params: { days } }),
  getComprehensiveMoodAnalysis: (days: number = 30): Promise<AxiosResponse<any>> =>
    api.get('/insights/mood-analysis-comprehensive', { params: { days } }),
  getComprehensiveTrends: (days: number = 30): Promise<AxiosResponse<any>> =>
    api.get('/insights/trends/comprehensive', { params: { days } }),
};

// Update existing insightsAPI to include new methods
insightsAPI.ask = enhancedInsightsAPI.askQuestion;

export default api;
