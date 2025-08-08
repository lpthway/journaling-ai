import React from 'react';

const LimitFilter = ({ limit, onChange }) => {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Results Limit
      </label>
      <select
        value={limit}
        onChange={(e) => onChange('limit', parseInt(e.target.value))}
        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      >
        <option value={10}>10 results</option>
        <option value={20}>20 results</option>
        <option value={50}>50 results</option>
        <option value={100}>100 results</option>
      </select>
    </div>
  );
};

export default LimitFilter;