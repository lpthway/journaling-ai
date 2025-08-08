import React from 'react';

const WordCountFilter = ({ word_count_min, word_count_max, onChange }) => {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Word Count
      </label>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Minimum</label>
          <input
            type="number"
            min="0"
            value={word_count_min}
            onChange={(e) => onChange('word_count_min', e.target.value)}
            placeholder="Min words"
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Maximum</label>
          <input
            type="number"
            min="0"
            value={word_count_max}
            onChange={(e) => onChange('word_count_max', e.target.value)}
            placeholder="Max words"
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>
    </div>
  );
};

export default WordCountFilter;