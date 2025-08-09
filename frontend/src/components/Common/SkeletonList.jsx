import React from 'react';
import SkeletonCard from './SkeletonCard';

const SkeletonList = ({ count = 6, className = '' }) => {
  return (
    <div className={`space-y-6 ${className}`}>
      {Array.from({ length: count }, (_, index) => (
        <SkeletonCard key={index} />
      ))}
    </div>
  );
};

export default SkeletonList;