import React from 'react';
import { ArrowTopRightOnSquareIcon } from '@heroicons/react/24/outline';

const SourceItem = ({ source, type }) => {
  const handleSourceClick = () => {
    if (type === 'journal') {
      window.location.href = `/journal#entry-${source.id}`;
    } else {
      window.location.href = `/chat/${source.id}`;
    }
  };

  return (
    <div className="p-3 bg-white rounded border border-gray-200 hover:border-gray-300 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-1">
            <span className="text-xs font-medium text-gray-600">
              {type === 'journal' ? source.title || 'Untitled Entry' : source.session_type}
            </span>
            <span className="text-xs text-gray-500">
              {source.similarity}% match
            </span>
          </div>
          <p className="text-xs text-gray-600 mb-2 line-clamp-2">
            {source.snippet}
          </p>
          <p className="text-xs text-gray-500">
            {source.date} {type === 'conversation' && `• ${source.message_count} messages`}
          </p>
        </div>
        <button
          onClick={handleSourceClick}
          className="ml-3 p-1 text-gray-400 hover:text-blue-600 transition-colors"
          title={`Go to ${type}`}
        >
          <ArrowTopRightOnSquareIcon className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default SourceItem;