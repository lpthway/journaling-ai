// Test Data Fixtures for E2E Tests

/**
 * Sample journal entries for testing
 */
const sampleEntries = [
  {
    id: 'test-entry-1',
    title: 'My First Test Entry',
    content: 'Today was a great day! I learned something new about testing.',
    mood: 'happy',
    tags: ['learning', 'testing', 'positive'],
    date: new Date('2025-08-09').toISOString()
  },
  {
    id: 'test-entry-2', 
    title: 'Reflection on Growth',
    content: 'I\'ve been thinking about personal growth and how challenges help us develop resilience.',
    mood: 'thoughtful',
    tags: ['growth', 'reflection', 'mindfulness'],
    date: new Date('2025-08-08').toISOString()
  },
  {
    id: 'test-entry-3',
    title: 'Difficult Day',
    content: 'Today was challenging. I felt overwhelmed with work but managed to get through it.',
    mood: 'stressed',
    tags: ['work', 'stress', 'perseverance'],
    date: new Date('2025-08-07').toISOString()
  },
  {
    id: 'test-entry-4',
    title: 'Weekend Adventures',
    content: 'Spent the weekend hiking in the mountains. The fresh air and exercise were exactly what I needed.',
    mood: 'excited',
    tags: ['adventure', 'nature', 'exercise', 'weekend'],
    date: new Date('2025-08-06').toISOString()
  }
];

/**
 * Sample chat messages for testing
 */
const sampleChatMessages = [
  {
    role: 'user',
    content: 'Hello, I\'d like to talk about my day.',
    timestamp: new Date().toISOString()
  },
  {
    role: 'assistant', 
    content: 'Hi! I\'d be happy to hear about your day. What would you like to share?',
    timestamp: new Date().toISOString()
  },
  {
    role: 'user',
    content: 'I had a really productive morning, but I\'m feeling a bit overwhelmed now.',
    timestamp: new Date().toISOString()
  },
  {
    role: 'assistant',
    content: 'It sounds like you had a good start to your day, which is wonderful. Feeling overwhelmed is completely normal, especially after a productive period. What specifically is contributing to that feeling right now?',
    timestamp: new Date().toISOString()
  }
];

/**
 * Sample search queries for testing
 */
const sampleSearchQueries = [
  {
    query: 'happy',
    expectedResults: 1,
    description: 'Search for entries with happy mood'
  },
  {
    query: 'testing',
    expectedResults: 1,
    description: 'Search for entries containing "testing"'
  },
  {
    query: 'growth mindfulness',
    expectedResults: 1,
    description: 'Search for entries with multiple keywords'
  },
  {
    query: 'nonexistent',
    expectedResults: 0,
    description: 'Search with no expected results'
  },
  {
    query: 'work stress',
    expectedResults: 1,
    description: 'Search for work-related stress entries'
  }
];

/**
 * Sample user interactions for testing UI flows
 */
const userFlows = {
  newUser: {
    entryCreation: [
      { action: 'navigate', target: '/' },
      { action: 'click', target: '[data-testid="new-entry-btn"]' },
      { action: 'fill', target: '[data-testid="entry-title"]', value: 'My First Journal Entry' },
      { action: 'fill', target: '[data-testid="entry-content"]', value: 'This is my first journal entry. I\'m excited to start this journey!' },
      { action: 'select', target: '[data-testid="mood-select"]', value: 'excited' },
      { action: 'click', target: '[data-testid="save-entry-btn"]' },
      { action: 'verify', target: '[data-testid="toast"]', expect: 'saved' }
    ],
    
    firstChat: [
      { action: 'navigate', target: '/chat' },
      { action: 'fill', target: '[data-testid="chat-input"]', value: 'Hello! I just created my first journal entry.' },
      { action: 'click', target: '[data-testid="send-message-btn"]' },
      { action: 'wait', target: '[data-testid="ai-message"]', timeout: 30000 },
      { action: 'verify', target: '[data-testid="ai-message"]', expect: 'contain text' }
    ]
  },
  
  experiencedUser: {
    searchAndFilter: [
      { action: 'navigate', target: '/' },
      { action: 'fill', target: '[data-testid="search-input"]', value: 'happy' },
      { action: 'click', target: '[data-testid="search-btn"]' },
      { action: 'wait', target: '[data-testid="search-results"]' },
      { action: 'verify', target: '[data-testid="search-results"]', expect: 'visible' }
    ],
    
    advancedInsights: [
      { action: 'navigate', target: '/insights' },
      { action: 'click', target: '[data-testid="tab-ask"]' },
      { action: 'fill', target: '[data-testid="question-input"]', value: 'What patterns do you see in my journal entries?' },
      { action: 'click', target: '[data-testid="ask-question-btn"]' },
      { action: 'wait', target: '[data-testid="ai-response"]', timeout: 30000 },
      { action: 'verify', target: '[data-testid="ai-response"]', expect: 'contain text' }
    ]
  }
};

/**
 * Test environment configurations
 */
const testEnvironments = {
  development: {
    baseURL: 'http://localhost:3000',
    apiURL: 'http://localhost:8000',
    timeout: 30000
  },
  staging: {
    baseURL: 'https://staging.journaling-ai.com',
    apiURL: 'https://api-staging.journaling-ai.com',
    timeout: 60000
  },
  production: {
    baseURL: 'https://journaling-ai.com',
    apiURL: 'https://api.journaling-ai.com',
    timeout: 60000
  }
};

/**
 * Mock API responses for offline testing
 */
const mockApiResponses = {
  entries: {
    getAll: {
      success: true,
      data: sampleEntries,
      total: sampleEntries.length
    },
    create: {
      success: true,
      data: { id: 'new-entry-id', ...sampleEntries[0] }
    }
  },
  
  sessions: {
    getAll: {
      success: true, 
      data: [
        {
          id: 'session-1',
          type: 'general',
          created_at: new Date().toISOString(),
          message_count: 4
        }
      ]
    },
    create: {
      success: true,
      data: { id: 'new-session-id', type: 'general' }
    }
  },
  
  insights: {
    overview: {
      success: true,
      data: {
        totalEntries: 4,
        averageMood: 'positive',
        topTags: ['growth', 'testing', 'work'],
        streakDays: 3
      }
    }
  }
};

/**
 * Browser-specific configurations
 */
const browserConfigs = {
  chrome: {
    headless: true,
    viewport: { width: 1280, height: 720 },
    deviceScaleFactor: 1
  },
  firefox: {
    headless: true,
    viewport: { width: 1280, height: 720 }
  },
  safari: {
    headless: true,
    viewport: { width: 1280, height: 720 }
  },
  mobile: {
    headless: true,
    viewport: { width: 375, height: 667 },
    deviceScaleFactor: 2,
    isMobile: true,
    hasTouch: true
  }
};

module.exports = {
  sampleEntries,
  sampleChatMessages,
  sampleSearchQueries,
  userFlows,
  testEnvironments,
  mockApiResponses,
  browserConfigs
};