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

// Request interceptor for debugging
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Debug: API Request logging disabled in production
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Entry API
export const entryAPI = {
  create: (entryData: CreateEntryData): Promise<AxiosResponse<Entry>> => 
    api.post('/entries/', entryData),
  
  getAll: (params: SearchFilters = {}): Promise<AxiosResponse<Entry[]>> => 
    api.get('/entries/', { params }),
  
  getById: (id: string): Promise<AxiosResponse<Entry>> => 
    api.get(`/entries/${id}`),
  
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

// Session API
export const sessionAPI = {
  // Session management
  createSession: (sessionData: CreateSessionData): Promise<AxiosResponse<Session>> => 
    api.post('/sessions/', sessionData),
  
  getSession: (sessionId: string): Promise<AxiosResponse<Session>> => 
    api.get(`/sessions/${sessionId}`),
  
  getSessions: (params: Record<string, any> = {}): Promise<AxiosResponse<Session[]>> => 
    api.get('/sessions/', { params }),
  
  updateSession: (sessionId: string, updateData: UpdateSessionData): Promise<AxiosResponse<Session>> => 
    api.put(`/sessions/${sessionId}`, updateData),
  
  deleteSession: (sessionId: string): Promise<AxiosResponse<void>> => 
    api.delete(`/sessions/${sessionId}`),
  
  // Session actions
  pauseSession: (sessionId: string): Promise<AxiosResponse<Session>> => 
    api.post(`/sessions/${sessionId}/pause`),
  
  resumeSession: (sessionId: string): Promise<AxiosResponse<Session>> => 
    api.post(`/sessions/${sessionId}/resume`),
  
  // Messages
  sendMessage: (sessionId: string, messageData: SendMessageData): Promise<AxiosResponse<Message>> => 
    api.post(`/sessions/${sessionId}/messages`, messageData),
  
  getMessages: (sessionId: string, params: Record<string, any> = {}): Promise<AxiosResponse<Message[]>> => 
    api.get(`/sessions/${sessionId}/messages`, { params }),
  
  getSuggestions: (sessionId: string): Promise<AxiosResponse<string[]>> => 
    api.get(`/sessions/${sessionId}/suggestions`),
  
  // Session types
  getAvailableTypes: (): Promise<AxiosResponse<SessionType[]>> => 
    api.get('/sessions/types/available'),
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