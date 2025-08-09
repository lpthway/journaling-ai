import React from 'react';

const SkeletonCard = ({ className = '' }) => {
  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 animate-pulse ${className}`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="h-6 bg-gray-200 rounded-md w-3/4 mb-2"></div>
          <div className="flex items-center space-x-4">
            <div className="h-4 bg-gray-200 rounded w-24"></div>
            <div className="h-4 bg-gray-200 rounded w-16"></div>
          </div>
        </div>
        <div className="flex items-center space-x-2 ml-4">
          <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
          <div className="flex space-x-1">
            <div className="w-6 h-6 bg-gray-200 rounded"></div>
            <div className="w-6 h-6 bg-gray-200 rounded"></div>
            <div className="w-6 h-6 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="mb-4 space-y-2">
        <div className="h-4 bg-gray-200 rounded w-full"></div>
        <div className="h-4 bg-gray-200 rounded w-5/6"></div>
        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="h-6 bg-gray-200 rounded-full w-16"></div>
          <div className="flex space-x-2">
            <div className="h-6 bg-gray-200 rounded-full w-12"></div>
            <div className="h-6 bg-gray-200 rounded-full w-12"></div>
          </div>
        </div>
        <div className="h-4 bg-gray-200 rounded w-20"></div>
      </div>
    </div>
  );
};

export default SkeletonCard;