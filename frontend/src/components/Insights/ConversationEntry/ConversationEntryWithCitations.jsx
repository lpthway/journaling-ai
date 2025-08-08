import React, { useState } from 'react';
import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline';
import MarkdownWithCitations from '../Citations/MarkdownWithCitations';
import DetailedSourcesList from '../Citations/DetailedSourcesList';

const ConversationEntryWithCitations = ({ entry }) => {
  const [showCitations, setShowCitations] = useState(false);

  return (
    <div className="mb-8">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6">
          {/* Question */}
          <div className="mb-4">
            <div className="flex items-center space-x-2 mb-2">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 font-medium text-sm">Q</span>
              </div>
              <span className="text-sm text-gray-500">{entry.timestamp}</span>
            </div>
            <p className="text-gray-900 font-medium pl-10">
              {entry.question}
            </p>
          </div>

          {/* Answer */}
          <div className="pl-10">
            <div className="flex items-center space-x-2 mb-3">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-green-600 font-medium text-sm">A</span>
              </div>
              <button
                onClick={() => setShowCitations(!showCitations)}
                className="flex items-center space-x-1 px-2 py-1 text-xs text-gray-500 hover:text-gray-700 rounded transition-colors"
                title={showCitations ? 'Hide citations' : 'Show citations'}
              >
                <span>
                  {showCitations ? (
                    <ChevronUpIcon className="w-3 h-3" />
                  ) : (
                    <ChevronDownIcon className="w-3 h-3" />
                  )}
                </span>
                <span>Citations</span>
              </button>
            </div>
            
            <div className="prose prose-sm max-w-none text-gray-700 leading-relaxed">
              <MarkdownWithCitations 
                text={entry.answer} 
                sources={entry.detailedSources}
              />
            </div>

            {/* Sources Summary */}
            <div className="mt-4 pt-3 border-t border-gray-100">
              {entry.sources && typeof entry.sources === 'object' && entry.sources.journal_entries !== undefined ? (
                <div className="flex flex-wrap gap-4 text-xs text-gray-500">
                  <span className="text-blue-600">
                    📔 {entry.sources.journal_entries || 0} journal entries
                  </span>
                  <span className="text-purple-600">
                    💬 {entry.sources.chat_messages || 0} conversations
                  </span>
                </div>
              ) : (
                <p className="text-xs text-gray-500">
                  Based on {entry.sources?.sources_used || 0} journal entries
                </p>
              )}
              {entry.timePeriod && (
                <p className="text-xs text-gray-500 mt-1">
                  Time period: {entry.timePeriod}
                </p>
              )}
            </div>

            {/* Detailed Sources (collapsible) */}
            {showCitations && entry.detailedSources && (
              <DetailedSourcesList sources={entry.detailedSources} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConversationEntryWithCitations;