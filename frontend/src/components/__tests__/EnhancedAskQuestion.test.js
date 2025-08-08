import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import EnhancedAskQuestion from '../Insights/EnhancedAskQuestion';

// Mock API service
jest.mock('../../services/api', () => ({
  askQuestion: jest.fn(),
  getInsights: jest.fn(),
}));

// Wrapper component for router
const RouterWrapper = ({ children }) => (
  <BrowserRouter>{children}</BrowserRouter>
);

describe('EnhancedAskQuestion Component', () => {
  const mockAskQuestion = require('../../services/api').askQuestion;
  const mockGetInsights = require('../../services/api').getInsights;

  beforeEach(() => {
    mockAskQuestion.mockClear();
    mockGetInsights.mockClear();
  });

  test('renders question input and submit button', () => {
    render(
      <RouterWrapper>
        <EnhancedAskQuestion />
      </RouterWrapper>
    );

    expect(screen.getByPlaceholderText(/ask a question/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /ask/i })).toBeInTheDocument();
  });

  test('displays suggested questions', () => {
    render(
      <RouterWrapper>
        <EnhancedAskQuestion />
      </RouterWrapper>
    );

    expect(screen.getByText(/suggested questions/i)).toBeInTheDocument();
    expect(screen.getByText(/how has my mood changed/i)).toBeInTheDocument();
    expect(screen.getByText(/what are my common themes/i)).toBeInTheDocument();
  });

  test('handles question input', () => {
    render(
      <RouterWrapper>
        <EnhancedAskQuestion />
      </RouterWrapper>
    );

    const input = screen.getByPlaceholderText(/ask a question/i);
    fireEvent.change(input, { target: { value: 'What patterns do you see?' } });

    expect(input.value).toBe('What patterns do you see?');
  });

  test('submits question and displays loading state', async () => {
    mockAskQuestion.mockResolvedValue({
      answer: 'Your mood has been improving over the last month.',
      sources: ['entry1', 'entry2'],
      confidence: 0.85
    });

    render(
      <RouterWrapper>
        <EnhancedAskQuestion />
      </RouterWrapper>
    );

    const input = screen.getByPlaceholderText(/ask a question/i);
    const submitButton = screen.getByRole('button', { name: /ask/i });

    fireEvent.change(input, { target: { value: 'How is my mood?' } });
    fireEvent.click(submitButton);

    // Should show loading state
    expect(screen.getByText(/analyzing/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(mockAskQuestion).toHaveBeenCalledWith('How is my mood?');
    });
  });

  test('displays answer after successful submission', async () => {
    const mockResponse = {
      answer: 'Your mood has been improving over the last month.',
      sources: ['entry1', 'entry2'],
      confidence: 0.85,
      insights: ['You tend to be happier on weekends', 'Exercise correlates with better mood']
    };

    mockAskQuestion.mockResolvedValue(mockResponse);

    render(
      <RouterWrapper>
        <EnhancedAskQuestion />
      </RouterWrapper>
    );

    const input = screen.getByPlaceholderText(/ask a question/i);
    const submitButton = screen.getByRole('button', { name: /ask/i });

    fireEvent.change(input, { target: { value: 'How is my mood?' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Your mood has been improving over the last month.')).toBeInTheDocument();
    });

    // Should show confidence score
    expect(screen.getByText(/85% confident/i)).toBeInTheDocument();

    // Should show insights
    expect(screen.getByText('You tend to be happier on weekends')).toBeInTheDocument();
  });

  test('handles API errors gracefully', async () => {
    mockAskQuestion.mockRejectedValue(new Error('API Error'));

    render(
      <RouterWrapper>
        <EnhancedAskQuestion />
      </RouterWrapper>
    );

    const input = screen.getByPlaceholderText(/ask a question/i);
    const submitButton = screen.getByRole('button', { name: /ask/i });

    fireEvent.change(input, { target: { value: 'Test question' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/error analyzing/i)).toBeInTheDocument();
    });
  });

  test('handles suggested question clicks', async () => {
    mockAskQuestion.mockResolvedValue({
      answer: 'Suggested question answer',
      sources: [],
      confidence: 0.9
    });

    render(
      <RouterWrapper>
        <EnhancedAskQuestion />
      </RouterWrapper>
    );

    const suggestedQuestion = screen.getByText(/how has my mood changed/i);
    fireEvent.click(suggestedQuestion);

    await waitFor(() => {
      expect(mockAskQuestion).toHaveBeenCalled();
    });
  });

  test('displays question history', async () => {
    const mockHistory = [
      { id: 1, question: 'How is my mood?', timestamp: new Date().toISOString() },
      { id: 2, question: 'What are my themes?', timestamp: new Date().toISOString() }
    ];

    render(
      <RouterWrapper>
        <EnhancedAskQuestion questionHistory={mockHistory} />
      </RouterWrapper>
    );

    expect(screen.getByText(/recent questions/i)).toBeInTheDocument();
    expect(screen.getByText('How is my mood?')).toBeInTheDocument();
    expect(screen.getByText('What are my themes?')).toBeInTheDocument();
  });

  test('allows question refinement', async () => {
    const mockResponse = {
      answer: 'Your mood varies.',
      sources: ['entry1'],
      confidence: 0.6,
      suggestions: ['Be more specific about time period', 'Ask about specific emotions']
    };

    mockAskQuestion.mockResolvedValue(mockResponse);

    render(
      <RouterWrapper>
        <EnhancedAskQuestion />
      </RouterWrapper>
    );

    const input = screen.getByPlaceholderText(/ask a question/i);
    fireEvent.change(input, { target: { value: 'How is my mood?' } });
    fireEvent.click(screen.getByRole('button', { name: /ask/i }));

    await waitFor(() => {
      expect(screen.getByText(/try refining/i)).toBeInTheDocument();
    });

    // Should show refinement suggestions
    expect(screen.getByText('Be more specific about time period')).toBeInTheDocument();
  });

  test('supports voice input', () => {
    // Mock speech recognition
    const mockSpeechRecognition = {
      start: jest.fn(),
      stop: jest.fn(),
      addEventListener: jest.fn(),
    };

    global.webkitSpeechRecognition = jest.fn(() => mockSpeechRecognition);
    global.SpeechRecognition = jest.fn(() => mockSpeechRecognition);

    render(
      <RouterWrapper>
        <EnhancedAskQuestion />
      </RouterWrapper>
    );

    const voiceButton = screen.getByTestId('voice-input-button');
    expect(voiceButton).toBeInTheDocument();

    fireEvent.click(voiceButton);
    expect(mockSpeechRecognition.start).toHaveBeenCalled();
  });

  test('filters questions by category', () => {
    render(
      <RouterWrapper>
        <EnhancedAskQuestion />
      </RouterWrapper>
    );

    const categoryFilter = screen.getByTestId('category-filter');
    fireEvent.change(categoryFilter, { target: { value: 'mood' } });

    // Should show only mood-related suggestions
    const suggestions = screen.getAllByTestId('suggested-question');
    const moodSuggestions = suggestions.filter(s => 
      s.textContent.toLowerCase().includes('mood')
    );
    
    expect(moodSuggestions.length).toBeGreaterThan(0);
  });

  test('exports insights as PDF', async () => {
    const mockResponse = {
      answer: 'Your mood has been stable.',
      sources: ['entry1', 'entry2'],
      confidence: 0.8,
      charts: [{ type: 'line', data: [] }]
    };

    mockAskQuestion.mockResolvedValue(mockResponse);

    // Mock PDF export
    const mockJsPDF = {
      text: jest.fn(),
      save: jest.fn(),
      internal: { pageSize: { getWidth: () => 210 } }
    };
    global.jsPDF = jest.fn(() => mockJsPDF);

    render(
      <RouterWrapper>
        <EnhancedAskQuestion />
      </RouterWrapper>
    );

    // Submit question first
    const input = screen.getByPlaceholderText(/ask a question/i);
    fireEvent.change(input, { target: { value: 'Test question' } });
    fireEvent.click(screen.getByRole('button', { name: /ask/i }));

    await waitFor(() => {
      expect(screen.getByText('Your mood has been stable.')).toBeInTheDocument();
    });

    // Click export button
    const exportButton = screen.getByText(/export/i);
    fireEvent.click(exportButton);

    expect(mockJsPDF.save).toHaveBeenCalled();
  });

  test('handles real-time insights updates', async () => {
    const mockWebSocket = {
      addEventListener: jest.fn(),
      send: jest.fn(),
      close: jest.fn(),
    };

    global.WebSocket = jest.fn(() => mockWebSocket);

    render(
      <RouterWrapper>
        <EnhancedAskQuestion enableRealTime={true} />
      </RouterWrapper>
    );

    // Should establish WebSocket connection
    expect(global.WebSocket).toHaveBeenCalled();
  });

  test('supports keyboard shortcuts', () => {
    render(
      <RouterWrapper>
        <EnhancedAskQuestion />
      </RouterWrapper>
    );

    const input = screen.getByPlaceholderText(/ask a question/i);
    
    // Test Ctrl+Enter to submit
    fireEvent.change(input, { target: { value: 'Test question' } });
    fireEvent.keyDown(input, { key: 'Enter', ctrlKey: true });

    expect(mockAskQuestion).toHaveBeenCalled();
  });

  test('displays visualization charts', async () => {
    const mockResponse = {
      answer: 'Your mood trends show improvement.',
      sources: ['entry1'],
      confidence: 0.9,
      visualizations: [
        {
          type: 'line_chart',
          title: 'Mood Over Time',
          data: [{ date: '2025-01-01', mood: 0.7 }]
        }
      ]
    };

    mockAskQuestion.mockResolvedValue(mockResponse);

    render(
      <RouterWrapper>
        <EnhancedAskQuestion />
      </RouterWrapper>
    );

    const input = screen.getByPlaceholderText(/ask a question/i);
    fireEvent.change(input, { target: { value: 'Show mood trends' } });
    fireEvent.click(screen.getByRole('button', { name: /ask/i }));

    await waitFor(() => {
      expect(screen.getByText('Mood Over Time')).toBeInTheDocument();
    });

    // Should render chart container
    expect(screen.getByTestId('mood-chart')).toBeInTheDocument();
  });

  test('handles empty responses gracefully', async () => {
    mockAskQuestion.mockResolvedValue({
      answer: '',
      sources: [],
      confidence: 0.0
    });

    render(
      <RouterWrapper>
        <EnhancedAskQuestion />
      </RouterWrapper>
    );

    const input = screen.getByPlaceholderText(/ask a question/i);
    fireEvent.change(input, { target: { value: 'Empty question' } });
    fireEvent.click(screen.getByRole('button', { name: /ask/i }));

    await waitFor(() => {
      expect(screen.getByText(/no insights available/i)).toBeInTheDocument();
    });
  });
});