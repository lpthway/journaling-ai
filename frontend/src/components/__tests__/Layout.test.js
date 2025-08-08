import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import Layout from '../Layout/Layout';

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useLocation: () => ({ pathname: '/journal' }),
}));

// Wrapper component for router
const RouterWrapper = ({ children }) => (
  <BrowserRouter>{children}</BrowserRouter>
);

describe('Layout Component', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
  });

  test('renders layout structure correctly', () => {
    render(
      <RouterWrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </RouterWrapper>
    );

    // Check for navigation elements
    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  test('displays navigation links', () => {
    render(
      <RouterWrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </RouterWrapper>
    );

    // Check for main navigation links
    expect(screen.getByText(/journal/i)).toBeInTheDocument();
    expect(screen.getByText(/chat/i)).toBeInTheDocument();
    expect(screen.getByText(/insights/i)).toBeInTheDocument();
  });

  test('highlights active navigation link', () => {
    render(
      <RouterWrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </RouterWrapper>
    );

    // Should highlight journal link for /journal path
    const journalLink = screen.getByText(/journal/i).closest('a');
    expect(journalLink).toHaveClass('active');
  });

  test('navigates to different sections', () => {
    render(
      <RouterWrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </RouterWrapper>
    );

    const chatLink = screen.getByText(/chat/i);
    fireEvent.click(chatLink);

    expect(mockNavigate).toHaveBeenCalledWith('/chat');
  });

  test('renders user menu when authenticated', () => {
    // Mock authentication state
    const mockUser = { name: 'Test User', email: 'test@example.com' };
    
    render(
      <RouterWrapper>
        <Layout user={mockUser}>
          <div>Test Content</div>
        </Layout>
      </RouterWrapper>
    );

    expect(screen.getByText('Test User')).toBeInTheDocument();
  });

  test('renders login prompt when not authenticated', () => {
    render(
      <RouterWrapper>
        <Layout user={null}>
          <div>Test Content</div>
        </Layout>
      </RouterWrapper>
    );

    expect(screen.getByText(/sign in/i)).toBeInTheDocument();
  });

  test('handles responsive navigation menu', () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 768,
    });

    render(
      <RouterWrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </RouterWrapper>
    );

    // Should show mobile menu toggle
    const menuToggle = screen.getByTestId('mobile-menu-toggle');
    expect(menuToggle).toBeInTheDocument();

    // Click to open mobile menu
    fireEvent.click(menuToggle);

    // Mobile navigation should be visible
    const mobileNav = screen.getByTestId('mobile-navigation');
    expect(mobileNav).toHaveClass('open');
  });

  test('shows notifications', async () => {
    const mockNotifications = [
      { id: 1, message: 'New insight available', type: 'info' },
      { id: 2, message: 'Journal entry saved', type: 'success' }
    ];

    render(
      <RouterWrapper>
        <Layout notifications={mockNotifications}>
          <div>Test Content</div>
        </Layout>
      </RouterWrapper>
    );

    // Should show notification bell
    const notificationBell = screen.getByTestId('notification-bell');
    expect(notificationBell).toBeInTheDocument();

    // Should show notification count
    expect(screen.getByText('2')).toBeInTheDocument();

    // Click to open notifications
    fireEvent.click(notificationBell);

    // Should show notification dropdown
    await waitFor(() => {
      expect(screen.getByText('New insight available')).toBeInTheDocument();
      expect(screen.getByText('Journal entry saved')).toBeInTheDocument();
    });
  });

  test('handles theme toggle', () => {
    const mockSetTheme = jest.fn();

    render(
      <RouterWrapper>
        <Layout theme="light" setTheme={mockSetTheme}>
          <div>Test Content</div>
        </Layout>
      </RouterWrapper>
    );

    const themeToggle = screen.getByTestId('theme-toggle');
    fireEvent.click(themeToggle);

    expect(mockSetTheme).toHaveBeenCalledWith('dark');
  });

  test('displays loading state', () => {
    render(
      <RouterWrapper>
        <Layout loading={true}>
          <div>Test Content</div>
        </Layout>
      </RouterWrapper>
    );

    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
  });

  test('handles search functionality', async () => {
    const mockOnSearch = jest.fn();

    render(
      <RouterWrapper>
        <Layout onSearch={mockOnSearch}>
          <div>Test Content</div>
        </Layout>
      </RouterWrapper>
    );

    const searchInput = screen.getByPlaceholderText(/search/i);
    fireEvent.change(searchInput, { target: { value: 'test search' } });
    fireEvent.keyPress(searchInput, { key: 'Enter', code: 'Enter' });

    expect(mockOnSearch).toHaveBeenCalledWith('test search');
  });

  test('renders breadcrumb navigation', () => {
    const mockBreadcrumbs = [
      { label: 'Home', path: '/' },
      { label: 'Journal', path: '/journal' },
      { label: 'Entry Details', path: '/journal/1' }
    ];

    render(
      <RouterWrapper>
        <Layout breadcrumbs={mockBreadcrumbs}>
          <div>Test Content</div>
        </Layout>
      </RouterWrapper>
    );

    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Journal')).toBeInTheDocument();
    expect(screen.getByText('Entry Details')).toBeInTheDocument();
  });

  test('handles keyboard navigation', () => {
    render(
      <RouterWrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </RouterWrapper>
    );

    const navigation = screen.getByRole('navigation');
    const firstLink = navigation.querySelector('a');

    // Test Tab navigation
    firstLink.focus();
    expect(document.activeElement).toBe(firstLink);

    // Test Enter key activation
    fireEvent.keyDown(firstLink, { key: 'Enter', code: 'Enter' });
    expect(mockNavigate).toHaveBeenCalled();
  });

  test('displays error boundary when child component fails', () => {
    const FailingComponent = () => {
      throw new Error('Test error');
    };

    // Mock console.error to avoid error output in tests
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <RouterWrapper>
        <Layout>
          <FailingComponent />
        </Layout>
      </RouterWrapper>
    );

    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();

    consoleSpy.mockRestore();
  });

  test('supports accessibility features', () => {
    render(
      <RouterWrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </RouterWrapper>
    );

    // Check for proper ARIA attributes
    const navigation = screen.getByRole('navigation');
    expect(navigation).toHaveAttribute('aria-label');

    // Check for skip link
    const skipLink = screen.getByText(/skip to main content/i);
    expect(skipLink).toBeInTheDocument();

    // Check for proper heading hierarchy
    const mainHeading = screen.getByRole('heading', { level: 1 });
    expect(mainHeading).toBeInTheDocument();
  });

  test('handles offline state', () => {
    // Mock navigator.onLine
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: false,
    });

    render(
      <RouterWrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </RouterWrapper>
    );

    expect(screen.getByText(/offline/i)).toBeInTheDocument();
  });

  test('renders footer information', () => {
    render(
      <RouterWrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </RouterWrapper>
    );

    const footer = screen.getByRole('contentinfo');
    expect(footer).toBeInTheDocument();
    expect(screen.getByText(/© 2025/i)).toBeInTheDocument();
  });

  test('handles window resize events', () => {
    render(
      <RouterWrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </RouterWrapper>
    );

    // Trigger window resize
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 500,
    });

    fireEvent(window, new Event('resize'));

    // Layout should adapt to mobile view
    const mobileNav = screen.getByTestId('mobile-navigation');
    expect(mobileNav).toBeInTheDocument();
  });
});