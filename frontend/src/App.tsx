// frontend/src/App.tsx - Updated with chat routes and TypeScript

import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout/Layout';
import Journal from './pages/Journal';
import Topics from './pages/Topics';
import Insights from './pages/Insights';
import Chat from './pages/Chat';
import EntryDetail from './pages/EntryDetail';
import { healthCheck } from './services/api';

interface AppProps {}

const App: React.FC<AppProps> = () => {
  const [searchQuery, setSearchQuery] = useState<string | null>(null);

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
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Layout onSearch={handleSearch} />}>
            <Route 
              index 
              element={<Journal searchQuery={searchQuery as any} />} 
            />
            <Route 
              path="topics" 
              element={<Topics />}
            />
            <Route 
              path="insights" 
              element={<Insights />}
            />
            {/* New Chat Routes */}
            <Route 
              path="chat" 
              element={<Chat />}
            />
            <Route 
              path="chat/:sessionId" 
              element={<Chat />}
            />
            {/* Entry Detail Route */}
            <Route 
              path="entry/:id" 
              element={<EntryDetail />}
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
        
        {/* Global toast notifications */}
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
            success: {
              duration: 3000,
              iconTheme: {
                primary: '#10B981',
                secondary: '#fff',
              },
            },
            error: {
              duration: 5000,
              iconTheme: {
                primary: '#EF4444',
                secondary: '#fff',
              },
            },
          }}
        />
      </div>
    </Router>
  );
};

export default App;