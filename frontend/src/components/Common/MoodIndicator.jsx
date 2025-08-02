import React from 'react';
import { getMoodColor, getMoodEmoji, getMoodLabel } from '../../utils/helpers';

const MoodIndicator = ({ mood, size = 'sm', showLabel = false, className = '' }) => {
  if (!mood) return null;

  const sizeClasses = {
    xs: 'w-2 h-2',
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-6 h-6',
    xl: 'w-8 h-8',
  };

  const textSizeClasses = {
    xs: 'text-xs',
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
    xl: 'text-xl',
  };

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <div 
        className={`rounded-full ${getMoodColor(mood)} ${sizeClasses[size]} flex-shrink-0`}
        title={getMoodLabel(mood)}
      />
      {showLabel && (
        <span className={`text-gray-600 ${textSizeClasses[size]}`}>
          {getMoodEmoji(mood)} {getMoodLabel(mood)}
        </span>
      )}
    </div>
  );
};

export default MoodIndicator;