// frontend/src/App.tsx - Updated with chat routes and TypeScript

import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Layout from './components/Layout/Layout';
import ErrorBoundary from './components/Common/ErrorBoundary';
import Dashboard from './pages/Dashboard';
import Journal from './pages/Journal';
import Topics from './pages/Topics';
import Analytics from './pages/Analytics';
import Chat from './pages/Chat';
import EntryDetail from './pages/EntryDetail';
import Login from './pages/Login';
import AdminDashboard from './pages/AdminDashboard';
import ProtectedRoute from './components/ProtectedRoute';
import { healthCheck } from './services/api';

interface AppProps {}

const AppContent: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState<string | null>(null);
  const { isAuthenticated } = useAuth();

  // Handle search from header
  const handleSearch = (query: string): void => {
    setSearchQuery(query);
    // Navigate to journal page if not already there
    if (window.location.pathname !== '/') {
      window.location.href = '/';
    }
  };

  // Clear search when navigating away from journal
  const clearSearch = (): void => {
    setSearchQuery(null);
  };

  // Test API connection on app start
  useEffect(() => {
    const testConnection = async (): Promise<void> => {
      try {
        await healthCheck();
        // API connection successful
      } catch (error) {
        console.error('❌ API connection failed:', error);
        // Could show a connection status indicator
      }
    };
    
    testConnection();
  }, []);

  return (
    <div className="App">
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<Login />} />
        
        {/* Protected Routes */}
        <Route 
          path="/" 
          element={
            <ProtectedRoute>
              <Layout onSearch={handleSearch} />
            </ProtectedRoute>
          }
        >
          <Route 
            index 
            element={
              <ErrorBoundary>
                <Dashboard />
              </ErrorBoundary>
            } 
          />
          <Route 
            path="journal" 
            element={
              <ErrorBoundary>
                <Journal searchQuery={searchQuery as any} />
              </ErrorBoundary>
            } 
          />
          <Route 
            path="topics" 
            element={
              <ErrorBoundary>
                <Topics />
              </ErrorBoundary>
            }
          />
          <Route 
            path="analytics" 
            element={
              <ErrorBoundary>
                <Analytics />
              </ErrorBoundary>
            }
          />
          <Route 
            path="chat" 
            element={
              <ErrorBoundary>
                <Chat />
              </ErrorBoundary>
            }
          />
          <Route 
            path="chat/:sessionId" 
            element={
              <ErrorBoundary>
                <Chat />
              </ErrorBoundary>
            }
          />
          <Route 
            path="entry/:id" 
            element={
              <ErrorBoundary>
                <EntryDetail />
              </ErrorBoundary>
            }
          />
        </Route>
        
        {/* Admin Routes - Outside Layout for full-page admin interface */}
        <Route 
          path="/admin" 
          element={
            <ProtectedRoute adminRequired={true}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        
        {/* Default redirect */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
      
      {/* Enhanced global toast notifications */}
      <Toaster 
        position="top-right"
        containerStyle={{
          top: 20,
          right: 20,
        }}
        toastOptions={{
          duration: 4000,
          style: {
            background: '#ffffff',
            color: '#111827',
            border: '1px solid #e5e7eb',
            borderRadius: '0.5rem',
            padding: '12px 16px',
            fontSize: '14px',
            fontWeight: '500',
            maxWidth: '400px',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
          },
          success: {
            duration: 3000,
            style: {
              border: '1px solid #10b981',
              background: '#f0fdf4',
              color: '#065f46',
            },
            iconTheme: {
              primary: '#10b981',
              secondary: '#ffffff',
            },
          },
          error: {
            duration: 6000,
            style: {
              border: '1px solid #ef4444',
              background: '#fef2f2',
              color: '#991b1b',
            },
            iconTheme: {
              primary: '#ef4444',
              secondary: '#ffffff',
            },
          },
          loading: {
            style: {
              border: '1px solid #3b82f6',
              background: '#eff6ff',
              color: '#1e40af',
            },
            iconTheme: {
              primary: '#3b82f6',
              secondary: '#ffffff',
            },
          },
        }}
      />
    </div>
  );
};

const App: React.FC<AppProps> = () => {
  return (
    <ErrorBoundary>
      <Router>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </Router>
    </ErrorBoundary>
  );
};

export default App;