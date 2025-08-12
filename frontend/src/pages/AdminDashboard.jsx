import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { authAPI } from '../services/api';
import CreateUserModal from '../components/Admin/CreateUserModal';

const AdminDashboard = () => {
  const { user, token, isAdmin } = useAuth();
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    if (isAdmin) {
      loadDashboardData();
    }
  }, [isAdmin, token]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load security stats
      const statsResponse = await authAPI.admin.getSecurityStats();
      setStats(statsResponse.data);

      // Load users list
      const usersResponse = await authAPI.admin.getUsers({ limit: 100 });
      setUsers(usersResponse.data);

    } catch (err) {
      setError('Failed to load dashboard data');
      console.error('Dashboard load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUserAction = async (action, userId, data = {}) => {
    try {
      if (action === 'disable') {
        data = { is_active: false };
      } else if (action === 'enable') {
        data = { is_active: true };
      } else if (action === 'makeAdmin') {
        data = { role: 'ADMIN' };
      } else if (action === 'makeUser') {
        data = { role: 'USER' };
      }

      await authAPI.admin.updateUser(userId, data);
      // Reload users list
      await loadDashboardData();
    } catch (err) {
      setError('Action failed');
      console.error('User action error:', err);
    }
  };

  const handleCreateUser = async (userData) => {
    try {
      await authAPI.admin.createUser(userData);
      // Reload dashboard data to show new user
      await loadDashboardData();
      setError(null);
    } catch (err) {
      console.error('Create user error:', err);
      throw new Error(err.response?.data?.detail || 'Failed to create user');
    }
  };

  if (!isAdmin) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Access Denied</h1>
          <p>You need admin privileges to access this area.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p>Loading admin dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-gray-600">Manage users, sessions, and security</p>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            {error}
            <button 
              onClick={() => setError(null)}
              className="float-right font-bold text-red-500"
            >
              ×
            </button>
          </div>
        )}

        {/* Security Stats */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-medium text-gray-900">Total Users</h3>
              <p className="text-3xl font-bold text-blue-600">
                {Object.values(stats.user_counts_by_role || {}).reduce((a, b) => a + b, 0)}
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-medium text-gray-900">Active Sessions</h3>
              <p className="text-3xl font-bold text-green-600">{stats.active_sessions}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-medium text-gray-900">Failed Logins Today</h3>
              <p className="text-3xl font-bold text-red-600">{stats.failed_attempts_today}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-medium text-gray-900">Admin Users</h3>
              <p className="text-3xl font-bold text-purple-600">
                {(stats.user_counts_by_role?.ADMIN || 0) + (stats.user_counts_by_role?.SUPERUSER || 0)}
              </p>
            </div>
          </div>
        )}

        {/* Users Management */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900">User Management</h2>
            <button 
              onClick={() => setShowCreateModal(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              + Create User
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Login
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.map((userItem) => (
                  <tr key={userItem.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {userItem.display_name || userItem.username}
                        </div>
                        <div className="text-sm text-gray-500">{userItem.username}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {userItem.email}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        userItem.role === 'SUPERUSER' ? 'bg-purple-100 text-purple-800' :
                        userItem.role === 'ADMIN' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {userItem.role}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        userItem.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {userItem.is_active ? 'Active' : 'Disabled'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {userItem.last_login ? new Date(userItem.last_login).toLocaleDateString() : 'Never'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      {userItem.is_active ? (
                        <button
                          onClick={() => handleUserAction('disable', userItem.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Disable
                        </button>
                      ) : (
                        <button
                          onClick={() => handleUserAction('enable', userItem.id)}
                          className="text-green-600 hover:text-green-900"
                        >
                          Enable
                        </button>
                      )}
                      
                      {userItem.role === 'USER' ? (
                        <button
                          onClick={() => handleUserAction('makeAdmin', userItem.id)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          Make Admin
                        </button>
                      ) : userItem.role === 'ADMIN' && (
                        <button
                          onClick={() => handleUserAction('makeUser', userItem.id)}
                          className="text-gray-600 hover:text-gray-900"
                        >
                          Make User
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Create User Modal */}
        <CreateUserModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreateUser}
        />
      </div>
    </div>
  );
};

export default AdminDashboard;