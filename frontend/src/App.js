// frontend/src/App.js - Updated with chat routes

import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard';  // New dashboard import
import Journal from './pages/Journal';
import Topics from './pages/Topics';
import Insights from './pages/Insights';
import Analytics from './pages/Analytics';  // New analytics import
import Chat from './pages/Chat';  // New import
import EntryDetail from './pages/EntryDetail';
import { healthCheck } from './services/api';

function App() {
  const [searchQuery, setSearchQuery] = useState(null);

  // Handle search from header
  const handleSearch = (query) => {
    setSearchQuery(query);
    // Navigate to journal page if not already there
    if (window.location.pathname !== '/journal') {
      window.location.href = '/journal';
    }
  };

  // Clear search when navigating away from journal
  const clearSearch = () => {
    setSearchQuery(null);
  };

  // Test API connection on app start
  React.useEffect(() => {
    const testConnection = async () => {
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
              element={<Dashboard />} 
            />
            <Route 
              path="journal" 
              element={<Journal searchQuery={searchQuery} />} 
            />
            <Route 
              path="topics" 
              element={<Topics />}
              loader={clearSearch}
            />
            <Route 
              path="insights" 
              element={<Insights />}
              loader={clearSearch}
            />
            <Route 
              path="analytics" 
              element={<Analytics />}
              loader={clearSearch}
            />
            {/* New Chat Routes */}
            <Route 
              path="chat" 
              element={<Chat />}
              loader={clearSearch}
            />
            <Route 
              path="chat/:sessionId" 
              element={<Chat />}
              loader={clearSearch}
            />
            {/* Entry Detail Route */}
            <Route 
              path="entry/:id" 
              element={<EntryDetail />}
              loader={clearSearch}
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
}

export default App;