import React from 'react';
import { toast as hotToast } from 'react-hot-toast';
import { 
  CheckCircleIcon, 
  ExclamationCircleIcon, 
  InformationCircleIcon,
  XCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

// Enhanced toast notifications with better UX
const createToast = (type, message, options = {}) => {
  const iconMap = {
    success: CheckCircleIcon,
    error: XCircleIcon,
    warning: ExclamationCircleIcon,
    info: InformationCircleIcon,
  };

  const colorMap = {
    success: 'text-green-600 bg-green-50 border-green-200',
    error: 'text-red-600 bg-red-50 border-red-200',
    warning: 'text-yellow-600 bg-yellow-50 border-yellow-200',
    info: 'text-blue-600 bg-blue-50 border-blue-200',
  };

  const Icon = iconMap[type];
  const colorClass = colorMap[type];

  return hotToast.custom(
    (t) => (
      <div
        className={`flex items-start space-x-3 max-w-sm w-full ${colorClass} border rounded-lg shadow-lg p-4 animate-slide-right ${
          t.visible ? 'animate-scale-in' : 'animate-fade-out'
        }`}
        role="alert"
        aria-live="polite"
      >
        <Icon className="w-5 h-5 mt-0.5 flex-shrink-0" aria-hidden="true" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium">
            {message}
          </p>
          {options.description && (
            <p className="mt-1 text-xs opacity-75">
              {options.description}
            </p>
          )}
        </div>
        <button
          onClick={() => hotToast.dismiss(t.id)}
          className="flex-shrink-0 p-1 -m-1 rounded-md hover:bg-white/20 transition-colors focus:outline-none focus:ring-2 focus:ring-current focus:ring-offset-2"
          aria-label="Close notification"
        >
          <XMarkIcon className="w-4 h-4" />
        </button>
      </div>
    ),
    {
      duration: options.duration || (type === 'error' ? 6000 : 4000),
      position: 'top-right',
      ...options,
    }
  );
};

export const toast = {
  success: (message, options) => createToast('success', message, options),
  error: (message, options) => createToast('error', message, options),
  warning: (message, options) => createToast('warning', message, options),
  info: (message, options) => createToast('info', message, options),
  
  // Promise-based toast for async operations
  promise: (promise, msgs) => {
    return hotToast.promise(
      promise,
      {
        loading: msgs.loading || 'Loading...',
        success: msgs.success || 'Success!',
        error: msgs.error || 'Something went wrong',
      },
      {
        style: {
          minWidth: '250px',
        },
        success: {
          duration: 3000,
          icon: '✅',
        },
        error: {
          duration: 5000,
          icon: '❌',
        },
      }
    );
  },
  
  // Dismiss all toasts
  dismiss: hotToast.dismiss,
  
  // Remove all toasts
  remove: hotToast.remove,
};

export default toast;