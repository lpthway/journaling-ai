import React from 'react';
import SourceItem from './SourceItem';

const DetailedSourcesList = ({ sources }) => {
  return (
    <div className="mt-4 p-4 bg-gray-50 rounded-lg">
      <h4 className="text-sm font-medium text-gray-900 mb-3">Detailed Sources</h4>
      
      {/* Journal Entries */}
      {sources.journal_entries?.length > 0 && (
        <div className="mb-4">
          <h5 className="text-xs font-medium text-gray-700 mb-2">📔 Journal Entries</h5>
          <div className="space-y-2">
            {sources.journal_entries.map((entry, index) => (
              <SourceItem key={entry.id || index} source={entry} type="journal" />
            ))}
          </div>
        </div>
      )}

      {/* Conversations */}
      {sources.conversations?.length > 0 && (
        <div>
          <h5 className="text-xs font-medium text-gray-700 mb-2">💬 Conversations</h5>
          <div className="space-y-2">
            {sources.conversations.map((conversation, index) => (
              <SourceItem key={conversation.id || index} source={conversation} type="conversation" />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default DetailedSourcesList;