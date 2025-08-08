import React from 'react';
import { ArrowTopRightOnSquareIcon } from '@heroicons/react/24/outline';

const InlineCitationLink = ({ citation, text, number }) => {
  const handleCitationClick = () => {
    if (citation.sourceType === 'journal') {
      // Navigate to journal entry
      window.location.href = `/journal#entry-${citation.id}`;
    } else if (citation.sourceType === 'conversation') {
      // Navigate to chat conversation
      window.location.href = `/chat/${citation.id}`;
    }
  };

  return (
    <span className="inline">
      <button
        onClick={handleCitationClick}
        className="font-medium text-gray-900 hover:text-blue-600 transition-colors"
        title={`${citation.sourceType === 'journal' ? 'Journal' : 'Chat'}: ${citation.snippet?.substring(0, 50)}...`}
      >
        {text}
      </button>
      <sup>
        <button
          onClick={handleCitationClick}
          className="inline-flex items-center px-1 py-0.5 ml-1 rounded text-xs font-bold bg-blue-100 text-blue-700 hover:bg-blue-200 transition-colors border border-blue-200"
          title={`Click to view source: ${citation.snippet?.substring(0, 50)}...`}
        >
          [{number}]
          <ArrowTopRightOnSquareIcon className="w-2 h-2 ml-0.5" />
        </button>
      </sup>
    </span>
  );
};

export default InlineCitationLink;