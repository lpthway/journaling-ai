import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import EntryCard from '../Entry/EntryCard';

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

// Wrapper component for router
const RouterWrapper = ({ children }) => (
  <BrowserRouter>{children}</BrowserRouter>
);

describe('EntryCard Component', () => {
  const mockEntry = {
    id: 1,
    content: 'This is a test journal entry content.',
    mood: 'positive',
    sentiment_score: 0.8,
    created_at: '2025-08-08T12:00:00Z',
    updated_at: '2025-08-08T12:00:00Z',
    tags: ['test', 'journal'],
  };

  beforeEach(() => {
    mockNavigate.mockClear();
  });

  test('renders entry content correctly', () => {
    render(
      <RouterWrapper>
        <EntryCard entry={mockEntry} />
      </RouterWrapper>
    );

    expect(screen.getByText(mockEntry.content)).toBeInTheDocument();
    expect(screen.getByText(/positive/i)).toBeInTheDocument();
  });

  test('displays entry creation date', () => {
    render(
      <RouterWrapper>
        <EntryCard entry={mockEntry} />
      </RouterWrapper>
    );

    // Should display formatted date
    expect(screen.getByText(/Aug 8, 2025/i)).toBeInTheDocument();
  });

  test('displays entry tags', () => {
    render(
      <RouterWrapper>
        <EntryCard entry={mockEntry} />
      </RouterWrapper>
    );

    expect(screen.getByText('test')).toBeInTheDocument();
    expect(screen.getByText('journal')).toBeInTheDocument();
  });

  test('shows mood indicator', () => {
    render(
      <RouterWrapper>
        <EntryCard entry={mockEntry} />
      </RouterWrapper>
    );

    const moodIndicator = screen.getByTestId('mood-indicator');
    expect(moodIndicator).toBeInTheDocument();
    expect(moodIndicator).toHaveClass('mood-positive');
  });

  test('navigates to entry detail on click', () => {
    render(
      <RouterWrapper>
        <EntryCard entry={mockEntry} />
      </RouterWrapper>
    );

    const entryCard = screen.getByTestId('entry-card');
    fireEvent.click(entryCard);

    expect(mockNavigate).toHaveBeenCalledWith(`/entries/${mockEntry.id}`);
  });

  test('handles long content with truncation', () => {
    const longEntry = {
      ...mockEntry,
      content: 'This is a very long journal entry content that should be truncated when displayed in the card view to prevent the card from becoming too large and overwhelming the user interface. '.repeat(5),
    };

    render(
      <RouterWrapper>
        <EntryCard entry={longEntry} />
      </RouterWrapper>
    );

    const contentElement = screen.getByTestId('entry-content');
    expect(contentElement).toBeInTheDocument();
    
    // Should show truncated content or "Read more" indicator
    expect(
      contentElement.textContent.length < longEntry.content.length ||
      screen.queryByText(/read more/i)
    ).toBeTruthy();
  });

  test('renders without tags gracefully', () => {
    const entryWithoutTags = {
      ...mockEntry,
      tags: [],
    };

    render(
      <RouterWrapper>
        <EntryCard entry={entryWithoutTags} />
      </RouterWrapper>
    );

    const tagsSection = screen.queryByTestId('entry-tags');
    expect(tagsSection).toBeNull();
  });

  test('handles missing mood gracefully', () => {
    const entryWithoutMood = {
      ...mockEntry,
      mood: null,
    };

    render(
      <RouterWrapper>
        <EntryCard entry={entryWithoutMood} />
      </RouterWrapper>
    );

    const moodIndicator = screen.queryByTestId('mood-indicator');
    // Should either not render or show default/neutral mood
    if (moodIndicator) {
      expect(moodIndicator).toHaveClass('mood-neutral');
    }
  });

  test('displays sentiment score when available', () => {
    render(
      <RouterWrapper>
        <EntryCard entry={mockEntry} />
      </RouterWrapper>
    );

    // Should display sentiment score (0.8 = 80%)
    expect(screen.getByText(/80%/i)).toBeInTheDocument();
  });

  test('has proper accessibility attributes', () => {
    render(
      <RouterWrapper>
        <EntryCard entry={mockEntry} />
      </RouterWrapper>
    );

    const entryCard = screen.getByTestId('entry-card');
    expect(entryCard).toHaveAttribute('tabIndex', '0');
    expect(entryCard).toHaveAttribute('role', 'button');
    expect(entryCard).toHaveAttribute('aria-label');
  });

  test('supports keyboard navigation', () => {
    render(
      <RouterWrapper>
        <EntryCard entry={mockEntry} />
      </RouterWrapper>
    );

    const entryCard = screen.getByTestId('entry-card');
    
    // Test Enter key
    fireEvent.keyDown(entryCard, { key: 'Enter', code: 'Enter' });
    expect(mockNavigate).toHaveBeenCalledWith(`/entries/${mockEntry.id}`);

    mockNavigate.mockClear();

    // Test Space key
    fireEvent.keyDown(entryCard, { key: ' ', code: 'Space' });
    expect(mockNavigate).toHaveBeenCalledWith(`/entries/${mockEntry.id}`);
  });

  test('renders with compact layout prop', () => {
    render(
      <RouterWrapper>
        <EntryCard entry={mockEntry} compact={true} />
      </RouterWrapper>
    );

    const entryCard = screen.getByTestId('entry-card');
    expect(entryCard).toHaveClass('compact');
  });

  test('shows loading state', () => {
    render(
      <RouterWrapper>
        <EntryCard entry={mockEntry} loading={true} />
      </RouterWrapper>
    );

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  test('handles click with onSelect callback', () => {
    const mockOnSelect = jest.fn();
    
    render(
      <RouterWrapper>
        <EntryCard entry={mockEntry} onSelect={mockOnSelect} />
      </RouterWrapper>
    );

    const entryCard = screen.getByTestId('entry-card');
    fireEvent.click(entryCard);

    expect(mockOnSelect).toHaveBeenCalledWith(mockEntry);
  });

  test('prevents navigation when disabled', () => {
    render(
      <RouterWrapper>
        <EntryCard entry={mockEntry} disabled={true} />
      </RouterWrapper>
    );

    const entryCard = screen.getByTestId('entry-card');
    fireEvent.click(entryCard);

    expect(mockNavigate).not.toHaveBeenCalled();
    expect(entryCard).toHaveAttribute('aria-disabled', 'true');
  });
});