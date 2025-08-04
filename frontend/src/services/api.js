import axios from 'axios';

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
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
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
  getAll: (params = {}) => api.get('/entries/', { params }),
  getById: (id) => api.get(`/entries/${id}`),
  getByTopic: (topicId, params = {}) => api.get(`/topics/${topicId}/entries`, { params }),
  update: (id, entryData) => api.put(`/entries/${id}`, entryData),
  delete: (id) => api.delete(`/entries/${id}`),
  search: (query, limit = 10, topicId = null) => 
    api.get('/entries/search/semantic', { 
      params: { query, limit, topic_id: topicId } 
    }),
  advancedSearch: (filters) => api.post('/entries/search/advanced', filters),
  getMoodStats: (days = 30) => api.get('/insights/mood-stats', { params: { days } }),
  
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

// Session API - Add this to your existing api.js file
export const sessionAPI = {
  // Session management
  createSession: (sessionData) => api.post('/sessions/', sessionData),
  
  getSession: (sessionId) => api.get(`/sessions/${sessionId}`),
  
  getSessions: (params = {}) => api.get('/sessions/', { params }),
  
  updateSession: (sessionId, updateData) => api.put(`/sessions/${sessionId}`, updateData),
  
  deleteSession: (sessionId) => api.delete(`/sessions/${sessionId}`),
  
  // Session actions
  pauseSession: (sessionId) => api.post(`/sessions/${sessionId}/pause`),
  
  resumeSession: (sessionId) => api.post(`/sessions/${sessionId}/resume`),
  
  // Messages
  sendMessage: (sessionId, messageData) => api.post(`/sessions/${sessionId}/messages`, messageData),
  
  getMessages: (sessionId, params = {}) => api.get(`/sessions/${sessionId}/messages`, { params }),
  
  getSuggestions: (sessionId) => api.get(`/sessions/${sessionId}/suggestions`),
  
  // Session types
  getAvailableTypes: () => api.get('/sessions/types/available'),
};

// Health check
export const healthCheck = () => api.get('/health');

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
