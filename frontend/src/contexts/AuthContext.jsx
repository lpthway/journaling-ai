import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('auth_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      checkAuthStatus();
    } else {
      setLoading(false);
    }
  }, [token]);

  const checkAuthStatusWithToken = async (authToken) => {
    try {
      console.log('🔍 Checking auth status with fresh token:', authToken?.substring(0, 20) + '...');
      
      const response = await fetch('http://localhost:8000/api/v1/auth/status', {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      console.log('🔍 Auth status response:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('🔍 Auth status data:', data);
        if (data.authenticated) {
          console.log('✅ Setting user:', data.user);
          setUser(data.user);
        } else {
          console.log('❌ Not authenticated, logging out');
          logout();
        }
      } else {
        console.log('❌ Auth status failed, logging out');
        logout();
      }
    } catch (error) {
      console.error('❌ Auth check failed:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const checkAuthStatus = async () => {
    return checkAuthStatusWithToken(token);
  };

  const login = async (username, password, rememberMe = false) => {
    try {
      console.log('🔍 Attempting login with:', { username, rememberMe });
      
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username_or_email: username,
          password,
          remember_me: rememberMe
        }),
      });

      console.log('🔍 Login response status:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('✅ Login successful, setting tokens');
        
        // Set token in state and localStorage
        setToken(data.access_token);
        localStorage.setItem('auth_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        
        // Get user info using the fresh token directly
        await checkAuthStatusWithToken(data.access_token);
        return { success: true };
      } else {
        const error = await response.json();
        console.log('❌ Login failed:', error);
        return { success: false, error: error.detail };
      }
    } catch (error) {
      console.log('❌ Login error:', error);
      return { success: false, error: 'Login failed' };
    }
  };

  const logout = async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken && token) {
        await fetch('http://localhost:8000/api/v1/auth/logout', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            refresh_token: refreshToken
          }),
        });
      }
    } catch (error) {
      console.error('Logout request failed:', error);
    } finally {
      setUser(null);
      setToken(null);
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
    }
  };

  const register = async (userData) => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      if (response.ok) {
        return { success: true };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail };
      }
    } catch (error) {
      return { success: false, error: 'Registration failed' };
    }
  };

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    register,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'ADMIN' || user?.role === 'SUPERUSER' || user?.is_superuser
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};