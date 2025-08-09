import React from 'react';
import { 
  ExclamationTriangleIcon, 
  WifiIcon, 
  ServerIcon, 
  ArrowPathIcon,
  HomeIcon 
} from '@heroicons/react/24/outline';

const ErrorState = ({ 
  type = 'generic',
  title,
  description,
  onRetry,
  onGoHome,
  showHomeButton = false,
  className = '' 
}) => {
  const getErrorConfig = () => {
    switch (type) {
      case 'network':
        return {
          icon: WifiIcon,
          title: title || 'Connection Problem',
          description: description || 'Please check your internet connection and try again.',
          color: 'orange'
        };
      case 'server':
        return {
          icon: ServerIcon,
          title: title || 'Server Error',
          description: description || 'Our servers are experiencing issues. Please try again in a few moments.',
          color: 'red'
        };
      case 'notfound':
        return {
          icon: ExclamationTriangleIcon,
          title: title || 'Not Found',
          description: description || 'The item you\'re looking for doesn\'t exist or has been moved.',
          color: 'gray'
        };
      default:
        return {
          icon: ExclamationTriangleIcon,
          title: title || 'Something went wrong',
          description: description || 'An unexpected error occurred. Please try again.',
          color: 'red'
        };
    }
  };

  const { icon: Icon, title: errorTitle, description: errorDescription, color } = getErrorConfig();

  const colorClasses = {
    red: {
      bg: 'bg-red-100',
      icon: 'text-red-600',
      button: 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
    },
    orange: {
      bg: 'bg-orange-100',
      icon: 'text-orange-600',
      button: 'bg-orange-600 hover:bg-orange-700 focus:ring-orange-500'
    },
    gray: {
      bg: 'bg-gray-100',
      icon: 'text-gray-600',
      button: 'bg-gray-600 hover:bg-gray-700 focus:ring-gray-500'
    }
  };

  const colors = colorClasses[color];

  return (
    <div className={`text-center py-12 ${className}`}>
      <div className={`mx-auto flex items-center justify-center h-16 w-16 rounded-full ${colors.bg} mb-4`}>
        <Icon className={`h-8 w-8 ${colors.icon}`} aria-hidden="true" />
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">{errorTitle}</h3>
      <p className="text-gray-500 mb-6 max-w-sm mx-auto">{errorDescription}</p>
      
      <div className="flex flex-col sm:flex-row gap-3 justify-center items-center">
        {onRetry && (
          <button
            onClick={onRetry}
            className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white ${colors.button} focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors`}
          >
            <ArrowPathIcon className="h-4 w-4 mr-2" />
            Try Again
          </button>
        )}
        
        {showHomeButton && (
          <button
            onClick={onGoHome || (() => window.location.href = '/')}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            <HomeIcon className="h-4 w-4 mr-2" />
            Go Home
          </button>
        )}
      </div>
    </div>
  );
};

export default ErrorState;