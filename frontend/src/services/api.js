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
  update: (id, entryData) => api.put(`/entries/${id}`, entryData),
  delete: (id) => api.delete(`/entries/${id}`),
  search: (query, limit = 10, topicId = null) => 
    api.get('/entries/search/semantic', { 
      params: { query, limit, topic_id: topicId } 
    }),
  getMoodStats: (days = 30) => api.get('/entries/stats/mood', { params: { days } }),
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
  askQuestion: (question) => api.post('/insights/ask', null, { params: { question } }),
  getCoaching: () => api.get('/insights/coaching'),
  getPatterns: () => api.get('/insights/patterns'),
  getMoodTrends: (days = 30) => api.get('/insights/trends/mood', { params: { days } }),
};

// Health check
export const healthCheck = () => api.get('/health');

export default api;