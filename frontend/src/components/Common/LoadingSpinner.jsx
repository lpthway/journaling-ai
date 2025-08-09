import React from 'react';

const LoadingSpinner = ({ 
  size = 'md', 
  className = '', 
  text = '', 
  fullScreen = false,
  overlay = false 
}) => {
  const sizeClasses = {
    xs: 'w-3 h-3',
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12',
    '2xl': 'w-16 h-16',
  };

  const textSizeClasses = {
    xs: 'text-xs',
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
    xl: 'text-xl',
    '2xl': 'text-2xl',
  };

  const SpinnerContent = () => (
    <div className={`flex flex-col items-center justify-center space-y-3 ${className}`}>
      <div className={`animate-spin rounded-full border-2 border-gray-200 border-t-blue-600 ${sizeClasses[size]}`} />
      {text && (
        <p className={`text-gray-600 font-medium ${textSizeClasses[size]} animate-pulse`}>
          {text}
        </p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-white">
        <SpinnerContent />
      </div>
    );
  }

  if (overlay) {
    return (
      <div className="fixed inset-0 z-40 flex items-center justify-center bg-black bg-opacity-25 backdrop-blur-sm">
        <div className="bg-white rounded-lg p-8 shadow-xl">
          <SpinnerContent />
        </div>
      </div>
    );
  }

  return <SpinnerContent />;
};

export default LoadingSpinner;