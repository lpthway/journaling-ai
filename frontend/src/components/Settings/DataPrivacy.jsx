// frontend/src/components/Settings/DataPrivacy.jsx
import React, { useState, useEffect } from 'react';
import { 
  ShieldCheckIcon, 
  DocumentArrowDownIcon, 
  TrashIcon, 
  ExclamationTriangleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import LoadingSpinner from '../Common/LoadingSpinner';

const DataPrivacy = () => {
  const { user } = useAuth();
  const [privacySummary, setPrivacySummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [exportLoading, setExportLoading] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  useEffect(() => {
    loadPrivacySummary();
  }, []);

  const loadPrivacySummary = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/v1/user-data/privacy-summary', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPrivacySummary(data);
      } else {
        setError('Failed to load privacy summary');
      }
    } catch (err) {
      setError('Failed to load privacy information');
    } finally {
      setLoading(false);
    }
  };

  const handleDataExport = async (format) => {
    try {
      setExportLoading(true);
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/v1/user-data/export?format=${format}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        // Create blob and download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        
        // Get filename from response headers
        const contentDisposition = response.headers.get('content-disposition');
        const filename = contentDisposition 
          ? contentDisposition.split('filename=')[1].replace(/"/g, '')
          : `data_export_${format}.${format}`;
        
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } else {
        setError('Data export failed');
      }
    } catch (err) {
      setError('Failed to export data');
    } finally {
      setExportLoading(false);
    }
  };

  const handleAccountDeletion = async () => {
    if (deleteConfirmation !== 'DELETE_MY_ACCOUNT') {
      setError('Please type "DELETE_MY_ACCOUNT" to confirm deletion');
      return;
    }

    try {
      setDeleteLoading(true);
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/v1/user-data/account', {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          confirmation: deleteConfirmation
        })
      });

      if (response.ok) {
        // Account deleted successfully - logout and redirect
        localStorage.removeItem('auth_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login?message=account_deleted';
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Account deletion failed');
      }
    } catch (err) {
      setError('Failed to delete account');
    } finally {
      setDeleteLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center space-x-3 mb-6">
          <ShieldCheckIcon className="h-8 w-8 text-blue-600" />
          <h2 className="text-2xl font-bold text-gray-900">Data Privacy & Security</h2>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
            <div className="flex">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Privacy Summary */}
        {privacySummary && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div className="bg-blue-50 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-blue-900 mb-3">Your Data Summary</h3>
              <div className="space-y-2 text-sm text-blue-800">
                <p>Total Entries: <span className="font-medium">{privacySummary.data_summary.total_entries}</span></p>
                <p>Total Topics: <span className="font-medium">{privacySummary.data_summary.total_topics}</span></p>
                <p>Chat Sessions: <span className="font-medium">{privacySummary.data_summary.total_chat_sessions}</span></p>
                <p>Data Age: <span className="font-medium">{privacySummary.data_summary.data_age_days} days</span></p>
              </div>
            </div>

            <div className="bg-green-50 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-green-900 mb-3">Privacy Controls</h3>
              <div className="space-y-2 text-sm text-green-800">
                <p>Data Encryption: <span className="font-medium text-green-700">✓ Enabled</span></p>
                <p>Admin Access: <span className="font-medium text-green-700">✓ Logged & Audited</span></p>
                <p>AI Processing: <span className="font-medium text-green-700">✓ Consent Required</span></p>
                <p>GDPR Compliant: <span className="font-medium text-green-700">✓ Yes</span></p>
              </div>
            </div>
          </div>
        )}

        {/* Data Export Section */}
        <div className="border-t pt-6 mb-8">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Export Your Data</h3>
          <p className="text-gray-600 mb-4">
            Download all your personal data in your preferred format. This includes all journal entries, 
            topics, chat sessions, and account information.
          </p>
          
          <div className="flex flex-wrap gap-4">
            <button
              onClick={() => handleDataExport('json')}
              disabled={exportLoading}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              <DocumentArrowDownIcon className="h-5 w-5 mr-2" />
              {exportLoading ? 'Exporting...' : 'Export as JSON'}
            </button>
            
            <button
              onClick={() => handleDataExport('csv')}
              disabled={exportLoading}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
            >
              <DocumentArrowDownIcon className="h-5 w-5 mr-2" />
              {exportLoading ? 'Exporting...' : 'Export as CSV'}
            </button>
            
            <button
              onClick={() => handleDataExport('html')}
              disabled={exportLoading}
              className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50"
            >
              <DocumentArrowDownIcon className="h-5 w-5 mr-2" />
              {exportLoading ? 'Exporting...' : 'Export as HTML'}
            </button>
          </div>
        </div>

        {/* Account Deletion Section */}
        <div className="border-t pt-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Delete Account</h3>
          
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
            <div className="flex">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <h4 className="text-sm font-medium text-red-800">
                  Warning: This action is irreversible
                </h4>
                <p className="mt-1 text-sm text-red-700">
                  Deleting your account will permanently remove all your data including journal entries, 
                  topics, chat sessions, and account information. This cannot be undone.
                </p>
              </div>
            </div>
          </div>

          {!showDeleteConfirm ? (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
            >
              <TrashIcon className="h-5 w-5 mr-2" />
              Delete My Account
            </button>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Type "DELETE_MY_ACCOUNT" to confirm:
                </label>
                <input
                  type="text"
                  value={deleteConfirmation}
                  onChange={(e) => setDeleteConfirmation(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                  placeholder="DELETE_MY_ACCOUNT"
                />
              </div>
              
              <div className="flex space-x-4">
                <button
                  onClick={handleAccountDeletion}
                  disabled={deleteLoading || deleteConfirmation !== 'DELETE_MY_ACCOUNT'}
                  className="flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
                >
                  <TrashIcon className="h-5 w-5 mr-2" />
                  {deleteLoading ? 'Deleting...' : 'Confirm Deletion'}
                </button>
                
                <button
                  onClick={() => {
                    setShowDeleteConfirm(false);
                    setDeleteConfirmation('');
                  }}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Information Section */}
        <div className="border-t pt-6 mt-8">
          <div className="flex items-start space-x-3">
            <InformationCircleIcon className="h-6 w-6 text-blue-600 flex-shrink-0 mt-1" />
            <div className="text-sm text-gray-600">
              <h4 className="font-medium text-gray-900 mb-2">Your Privacy Rights</h4>
              <ul className="space-y-1">
                <li>• Right to access your personal data</li>
                <li>• Right to export your data in portable formats</li>
                <li>• Right to delete your account and all associated data</li>
                <li>• Right to know how your data is processed</li>
                <li>• All data access is logged and audited for security</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataPrivacy;