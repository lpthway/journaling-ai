import React from 'react';
import { TagIcon } from '@heroicons/react/24/outline';

const TagsFilter = ({ tags, newTag, setNewTag, onAddTag, onRemoveTag }) => {
  const handleAddTag = (e) => {
    e.preventDefault();
    onAddTag();
  };

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Tags
      </label>
      <div className="flex space-x-2 mb-3">
        <input
          type="text"
          value={newTag}
          onChange={(e) => setNewTag(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleAddTag(e)}
          placeholder="Add a tag to filter by"
          className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
        />
        <button
          type="button"
          onClick={handleAddTag}
          className="px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors text-sm"
        >
          Add
        </button>
      </div>
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {tags.map((tag, index) => (
            <span
              key={index}
              className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800"
            >
              <TagIcon className="w-3 h-3 mr-1" />
              {tag}
              <button
                type="button"
                onClick={() => onRemoveTag(tag)}
                className="ml-1 text-blue-600 hover:text-blue-800"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

export default TagsFilter;