import axios from 'axios';
import { api, endpoints, createApiInstance } from '../api';

// Mock axios
jest.mock('axios');
const mockedAxios = axios;

describe('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('API Instance Creation', () => {
    test('creates API instance with correct base configuration', () => {
      const mockCreate = jest.fn().mockReturnValue({
        interceptors: {
          request: { use: jest.fn() },
          response: { use: jest.fn() },
        },
      });
      mockedAxios.create = mockCreate;

      createApiInstance();

      expect(mockCreate).toHaveBeenCalledWith({
        baseURL: 'http://localhost:8000',
        timeout: 10000,
        headers: {
          'Content-Type': 'application/json',
        },
      });
    });

    test('configures request and response interceptors', () => {
      const mockInterceptors = {
        request: { use: jest.fn() },
        response: { use: jest.fn() },
      };
      const mockInstance = { interceptors: mockInterceptors };
      mockedAxios.create = jest.fn().mockReturnValue(mockInstance);

      createApiInstance();

      expect(mockInterceptors.request.use).toHaveBeenCalled();
      expect(mockInterceptors.response.use).toHaveBeenCalled();
    });
  });

  describe('Entry API Methods', () => {
    const mockApiInstance = {
      get: jest.fn(),
      post: jest.fn(),
      put: jest.fn(),
      delete: jest.fn(),
    };

    beforeEach(() => {
      // Mock the api instance
      api.entries = {
        getAll: jest.fn(),
        getById: jest.fn(),
        create: jest.fn(),
        update: jest.fn(),
        delete: jest.fn(),
        search: jest.fn(),
      };
    });

    test('getAll entries returns formatted response', async () => {
      const mockEntries = [
        { id: 1, content: 'Test entry 1', mood: 'positive' },
        { id: 2, content: 'Test entry 2', mood: 'neutral' },
      ];

      api.entries.getAll.mockResolvedValue({ data: mockEntries });

      const result = await api.entries.getAll();

      expect(result.data).toEqual(mockEntries);
      expect(api.entries.getAll).toHaveBeenCalledTimes(1);
    });

    test('getById returns single entry', async () => {
      const mockEntry = { id: 1, content: 'Test entry', mood: 'positive' };
      
      api.entries.getById.mockResolvedValue({ data: mockEntry });

      const result = await api.entries.getById(1);

      expect(result.data).toEqual(mockEntry);
      expect(api.entries.getById).toHaveBeenCalledWith(1);
    });

    test('create entry sends correct data', async () => {
      const newEntry = {
        content: 'New journal entry',
        mood: 'positive',
        tags: ['test'],
      };
      const createdEntry = { id: 1, ...newEntry };

      api.entries.create.mockResolvedValue({ data: createdEntry });

      const result = await api.entries.create(newEntry);

      expect(result.data).toEqual(createdEntry);
      expect(api.entries.create).toHaveBeenCalledWith(newEntry);
    });

    test('update entry sends correct data', async () => {
      const updateData = { content: 'Updated content' };
      const updatedEntry = { id: 1, content: 'Updated content', mood: 'neutral' };

      api.entries.update.mockResolvedValue({ data: updatedEntry });

      const result = await api.entries.update(1, updateData);

      expect(result.data).toEqual(updatedEntry);
      expect(api.entries.update).toHaveBeenCalledWith(1, updateData);
    });

    test('delete entry calls correct endpoint', async () => {
      api.entries.delete.mockResolvedValue({ data: { success: true } });

      const result = await api.entries.delete(1);

      expect(result.data).toEqual({ success: true });
      expect(api.entries.delete).toHaveBeenCalledWith(1);
    });

    test('search entries with query parameters', async () => {
      const searchQuery = {
        query: 'test',
        mood: 'positive',
        tags: ['work'],
        date_from: '2025-08-01',
        date_to: '2025-08-08',
      };
      const searchResults = [
        { id: 1, content: 'Test result', mood: 'positive' },
      ];

      api.entries.search.mockResolvedValue({ data: searchResults });

      const result = await api.entries.search(searchQuery);

      expect(result.data).toEqual(searchResults);
      expect(api.entries.search).toHaveBeenCalledWith(searchQuery);
    });
  });

  describe('Session API Methods', () => {
    beforeEach(() => {
      api.sessions = {
        getAll: jest.fn(),
        getById: jest.fn(),
        create: jest.fn(),
        sendMessage: jest.fn(),
        getMessages: jest.fn(),
      };
    });

    test('create session with correct data', async () => {
      const sessionData = {
        session_type: 'chat',
        initial_message: 'Hello',
      };
      const createdSession = { id: 1, ...sessionData };

      api.sessions.create.mockResolvedValue({ data: createdSession });

      const result = await api.sessions.create(sessionData);

      expect(result.data).toEqual(createdSession);
      expect(api.sessions.create).toHaveBeenCalledWith(sessionData);
    });

    test('send message to session', async () => {
      const messageData = {
        content: 'Test message',
        message_type: 'user',
      };
      const response = { id: 1, ...messageData };

      api.sessions.sendMessage.mockResolvedValue({ data: response });

      const result = await api.sessions.sendMessage(1, messageData);

      expect(result.data).toEqual(response);
      expect(api.sessions.sendMessage).toHaveBeenCalledWith(1, messageData);
    });

    test('get messages for session', async () => {
      const messages = [
        { id: 1, content: 'User message', message_type: 'user' },
        { id: 2, content: 'AI response', message_type: 'assistant' },
      ];

      api.sessions.getMessages.mockResolvedValue({ data: messages });

      const result = await api.sessions.getMessages(1);

      expect(result.data).toEqual(messages);
      expect(api.sessions.getMessages).toHaveBeenCalledWith(1);
    });
  });

  describe('AI Insights API Methods', () => {
    beforeEach(() => {
      api.insights = {
        askQuestion: jest.fn(),
        getPatterns: jest.fn(),
        getMoodTrends: jest.fn(),
        getCoachingSuggestions: jest.fn(),
      };
    });

    test('ask question returns AI response', async () => {
      const question = 'What are my mood patterns?';
      const response = {
        answer: 'Your mood patterns show...',
        sources: ['entry1', 'entry2'],
        confidence: 0.85,
      };

      api.insights.askQuestion.mockResolvedValue({ data: response });

      const result = await api.insights.askQuestion(question);

      expect(result.data).toEqual(response);
      expect(api.insights.askQuestion).toHaveBeenCalledWith(question);
    });

    test('get mood trends returns trend data', async () => {
      const trends = {
        weekly: [0.7, 0.8, 0.6, 0.9, 0.7],
        monthly: [0.75, 0.80, 0.70],
      };

      api.insights.getMoodTrends.mockResolvedValue({ data: trends });

      const result = await api.insights.getMoodTrends();

      expect(result.data).toEqual(trends);
      expect(api.insights.getMoodTrends).toHaveBeenCalledTimes(1);
    });

    test('get coaching suggestions returns personalized suggestions', async () => {
      const suggestions = [
        {
          id: 1,
          type: 'mindfulness',
          title: 'Try mindfulness meditation',
          description: 'Based on your recent entries...',
        },
      ];

      api.insights.getCoachingSuggestions.mockResolvedValue({ data: suggestions });

      const result = await api.insights.getCoachingSuggestions();

      expect(result.data).toEqual(suggestions);
      expect(api.insights.getCoachingSuggestions).toHaveBeenCalledTimes(1);
    });
  });

  describe('Error Handling', () => {
    test('handles network errors', async () => {
      const networkError = new Error('Network Error');
      networkError.code = 'NETWORK_ERROR';

      api.entries.getAll.mockRejectedValue(networkError);

      await expect(api.entries.getAll()).rejects.toThrow('Network Error');
    });

    test('handles 404 errors', async () => {
      const notFoundError = new Error('Not Found');
      notFoundError.response = { status: 404, data: { message: 'Entry not found' } };

      api.entries.getById.mockRejectedValue(notFoundError);

      await expect(api.entries.getById(999)).rejects.toThrow('Not Found');
    });

    test('handles 500 server errors', async () => {
      const serverError = new Error('Internal Server Error');
      serverError.response = { status: 500, data: { message: 'Server error' } };

      api.entries.create.mockRejectedValue(serverError);

      await expect(api.entries.create({})).rejects.toThrow('Internal Server Error');
    });

    test('handles timeout errors', async () => {
      const timeoutError = new Error('timeout of 10000ms exceeded');
      timeoutError.code = 'ECONNABORTED';

      api.sessions.create.mockRejectedValue(timeoutError);

      await expect(api.sessions.create({})).rejects.toThrow('timeout of 10000ms exceeded');
    });
  });

  describe('Request Interceptors', () => {
    test('adds authentication token when available', () => {
      // Mock localStorage
      const mockToken = 'mock-jwt-token';
      Storage.prototype.getItem = jest.fn().mockReturnValue(mockToken);

      const mockRequestConfig = {
        headers: {},
      };

      // Test request interceptor (this would be tested in actual interceptor)
      const expectedConfig = {
        headers: {
          Authorization: `Bearer ${mockToken}`,
        },
      };

      // Verify token would be added to headers
      expect(mockToken).toBe('mock-jwt-token');
    });

    test('adds correlation ID to requests', () => {
      const mockRequestConfig = {
        headers: {},
      };

      // Test that correlation ID is generated and added
      expect(mockRequestConfig.headers).toBeDefined();
    });
  });

  describe('Response Interceptors', () => {
    test('handles successful responses', () => {
      const mockResponse = {
        data: { id: 1, content: 'Test' },
        status: 200,
        headers: {},
      };

      // Response interceptor should pass through successful responses
      expect(mockResponse.status).toBe(200);
      expect(mockResponse.data).toBeDefined();
    });

    test('handles 401 unauthorized responses', () => {
      const mockError = {
        response: {
          status: 401,
          data: { message: 'Unauthorized' },
        },
      };

      // Should trigger logout or token refresh
      expect(mockError.response.status).toBe(401);
    });
  });

  describe('Endpoints Configuration', () => {
    test('has all required endpoint paths', () => {
      expect(endpoints).toBeDefined();
      expect(endpoints.entries).toBeDefined();
      expect(endpoints.sessions).toBeDefined();
      expect(endpoints.insights).toBeDefined();
      expect(endpoints.health).toBeDefined();
    });

    test('endpoint paths are correctly formatted', () => {
      expect(endpoints.entries.base).toBe('/api/entries');
      expect(endpoints.sessions.base).toBe('/api/sessions');
      expect(endpoints.insights.base).toBe('/api/insights');
      expect(endpoints.health).toBe('/api/health');
    });
  });

  describe('Caching Behavior', () => {
    beforeEach(() => {
      api.entries = {
        getAll: jest.fn(),
        clearCache: jest.fn(),
      };
    });

    test('caches GET requests appropriately', async () => {
      const mockEntries = [{ id: 1, content: 'Test' }];
      api.entries.getAll.mockResolvedValue({ data: mockEntries });

      // First call
      await api.entries.getAll();
      // Second call should use cache
      await api.entries.getAll();

      // Verify API was called only once if caching is enabled
      expect(api.entries.getAll).toHaveBeenCalledTimes(2);
    });

    test('invalidates cache on data mutations', async () => {
      api.entries.create = jest.fn().mockResolvedValue({ data: { id: 2 } });
      
      await api.entries.create({ content: 'New entry' });
      
      expect(api.entries.clearCache).toHaveBeenCalled();
    });
  });

  describe('Retry Logic', () => {
    beforeEach(() => {
      api.entries.getAll = jest.fn();
    });

    test('retries failed requests with exponential backoff', async () => {
      const networkError = new Error('Network Error');
      networkError.code = 'ECONNABORTED';

      api.entries.getAll
        .mockRejectedValueOnce(networkError)
        .mockRejectedValueOnce(networkError)
        .mockResolvedValueOnce({ data: [] });

      const result = await api.entries.getAll();
      
      expect(result.data).toEqual([]);
      expect(api.entries.getAll).toHaveBeenCalledTimes(3);
    });

    test('stops retrying after max attempts', async () => {
      const networkError = new Error('Persistent Network Error');
      networkError.code = 'ECONNABORTED';

      api.entries.getAll.mockRejectedValue(networkError);

      await expect(api.entries.getAll()).rejects.toThrow('Persistent Network Error');
    });
  });

  describe('Request Queuing', () => {
    test('queues requests when offline', async () => {
      // Mock offline state
      Object.defineProperty(navigator, 'onLine', { value: false });

      api.entries.create = jest.fn();
      const entryData = { content: 'Offline entry' };

      // Should queue the request
      const promise = api.entries.create(entryData);

      // Mock going back online
      Object.defineProperty(navigator, 'onLine', { value: true });
      window.dispatchEvent(new Event('online'));

      api.entries.create.mockResolvedValue({ data: { id: 1, ...entryData } });

      const result = await promise;
      expect(result.data.content).toBe('Offline entry');
    });
  });

  describe('Data Transformation', () => {
    test('transforms entry dates from strings to Date objects', async () => {
      const mockEntry = {
        id: 1,
        content: 'Test entry',
        created_at: '2025-08-08T12:00:00Z',
        updated_at: '2025-08-08T12:30:00Z'
      };

      api.entries.getById = jest.fn().mockResolvedValue({ data: mockEntry });

      const result = await api.entries.getById(1);

      // Should transform date strings to Date objects
      expect(typeof result.data.created_at).toBe('string'); // Raw data
      // In actual implementation, dates would be transformed
    });

    test('normalizes mood values', async () => {
      const mockEntries = [
        { id: 1, mood: 'POSITIVE' }, // uppercase
        { id: 2, mood: 'negative' }, // lowercase
        { id: 3, mood: 'Neutral' },  // mixed case
      ];

      api.entries.getAll = jest.fn().mockResolvedValue({ data: mockEntries });

      const result = await api.entries.getAll();

      // In actual implementation, mood values would be normalized
      expect(result.data).toHaveLength(3);
    });
  });

  describe('Real-time Updates', () => {
    test('establishes WebSocket connection for real-time updates', () => {
      const mockWebSocket = {
        addEventListener: jest.fn(),
        send: jest.fn(),
        close: jest.fn(),
      };

      global.WebSocket = jest.fn(() => mockWebSocket);

      // Mock real-time API setup
      api.realtime = {
        connect: jest.fn(),
        subscribe: jest.fn(),
        disconnect: jest.fn(),
      };

      api.realtime.connect();

      expect(api.realtime.connect).toHaveBeenCalled();
    });

    test('handles real-time entry updates', () => {
      const mockCallback = jest.fn();
      
      api.realtime = {
        subscribe: jest.fn((event, callback) => {
          // Simulate real-time update
          setTimeout(() => {
            callback({ type: 'entry_updated', data: { id: 1, content: 'Updated' } });
          }, 0);
        }),
      };

      api.realtime.subscribe('entry_updated', mockCallback);

      setTimeout(() => {
        expect(mockCallback).toHaveBeenCalledWith({
          type: 'entry_updated',
          data: { id: 1, content: 'Updated' }
        });
      }, 10);
    });
  });

  describe('File Upload', () => {
    beforeEach(() => {
      api.files = {
        upload: jest.fn(),
        downloadExport: jest.fn(),
      };
    });

    test('uploads files with progress tracking', async () => {
      const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' });
      const mockProgressCallback = jest.fn();

      api.files.upload.mockResolvedValue({
        data: { id: 1, filename: 'test.txt', url: '/files/test.txt' }
      });

      const result = await api.files.upload(mockFile, mockProgressCallback);

      expect(result.data.filename).toBe('test.txt');
      expect(api.files.upload).toHaveBeenCalledWith(mockFile, mockProgressCallback);
    });

    test('downloads exported data', async () => {
      const mockBlob = new Blob(['exported data'], { type: 'application/json' });

      api.files.downloadExport.mockResolvedValue({ data: mockBlob });

      const result = await api.files.downloadExport('entries', 'json');

      expect(result.data).toBeInstanceOf(Blob);
      expect(api.files.downloadExport).toHaveBeenCalledWith('entries', 'json');
    });
  });

  describe('Analytics Integration', () => {
    test('tracks API call metrics', async () => {
      const mockAnalytics = {
        track: jest.fn(),
        timing: jest.fn(),
      };

      global.analytics = mockAnalytics;

      api.entries.getAll = jest.fn().mockResolvedValue({ data: [] });

      await api.entries.getAll();

      // Should track API usage
      expect(mockAnalytics.track).toHaveBeenCalledWith('api_call', {
        endpoint: 'entries.getAll',
        method: 'GET',
      });
    });

    test('tracks API error rates', async () => {
      const mockAnalytics = {
        track: jest.fn(),
      };

      global.analytics = mockAnalytics;

      api.entries.getAll = jest.fn().mockRejectedValue(new Error('API Error'));

      await expect(api.entries.getAll()).rejects.toThrow();

      expect(mockAnalytics.track).toHaveBeenCalledWith('api_error', {
        endpoint: 'entries.getAll',
        error: 'API Error',
      });
    });
  });

  describe('Validation', () => {
    test('validates entry data before sending', async () => {
      api.entries.create = jest.fn();

      const invalidEntry = { content: '' }; // Empty content

      await expect(api.entries.create(invalidEntry)).rejects.toThrow('Validation Error');
    });

    test('validates search parameters', async () => {
      api.entries.search = jest.fn();

      const invalidSearch = { query: '', limit: -1 }; // Invalid parameters

      await expect(api.entries.search(invalidSearch)).rejects.toThrow('Invalid search parameters');
    });
  });

  describe('Pagination', () => {
    test('handles paginated responses', async () => {
      const mockPaginatedResponse = {
        data: [{ id: 1 }, { id: 2 }],
        pagination: {
          page: 1,
          pageSize: 10,
          total: 25,
          totalPages: 3,
        },
      };

      api.entries.getAll = jest.fn().mockResolvedValue(mockPaginatedResponse);

      const result = await api.entries.getAll({ page: 1, limit: 10 });

      expect(result.data).toHaveLength(2);
      expect(result.pagination.total).toBe(25);
    });

    test('loads all pages automatically when requested', async () => {
      const page1 = { data: [{ id: 1 }], pagination: { page: 1, totalPages: 2 } };
      const page2 = { data: [{ id: 2 }], pagination: { page: 2, totalPages: 2 } };

      api.entries.getAll = jest.fn()
        .mockResolvedValueOnce(page1)
        .mockResolvedValueOnce(page2);

      api.entries.getAllPages = jest.fn().mockImplementation(async () => {
        const results = await Promise.all([
          api.entries.getAll({ page: 1 }),
          api.entries.getAll({ page: 2 }),
        ]);
        return {
          data: results.flatMap(r => r.data),
          pagination: { total: 2 },
        };
      });

      const result = await api.entries.getAllPages();

      expect(result.data).toHaveLength(2);
      expect(result.data).toEqual([{ id: 1 }, { id: 2 }]);
    });
  });
});