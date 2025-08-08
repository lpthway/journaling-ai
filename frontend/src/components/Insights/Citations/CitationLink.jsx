import React from 'react';
import { ArrowTopRightOnSquareIcon } from '@heroicons/react/24/outline';

const CitationLink = ({ source }) => {
  const handleCitationClick = () => {
    if (source.sourceType === 'journal') {
      // Navigate to journal entry
      window.location.href = `/journal#entry-${source.id}`;
    } else if (source.sourceType === 'conversation') {
      // Navigate to chat conversation
      window.location.href = `/chat/${source.id}`;
    }
  };

  return (
    <button
      onClick={handleCitationClick}
      className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 hover:bg-blue-200 transition-colors"
      title={`${source.sourceType === 'journal' ? 'Journal' : 'Chat'}: ${source.snippet?.substring(0, 50)}...`}
    >
      [{source.citationNumber}]
      <ArrowTopRightOnSquareIcon className="w-3 h-3 ml-1" />
    </button>
  );
};

export default CitationLink;