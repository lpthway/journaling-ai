import React from 'react';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';

const SearchActions = ({ isSearching, onClear, onCancel, onSubmit }) => {
  return (
    <div className="flex items-center justify-between space-x-3 pt-4 border-t border-gray-200">
      <button
        type="button"
        onClick={onClear}
        className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
      >
        Clear All
      </button>
      
      <div className="flex space-x-3">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isSearching}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
        >
          {isSearching ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              <span>Searching...</span>
            </>
          ) : (
            <>
              <MagnifyingGlassIcon className="w-4 h-4" />
              <span>Search</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default SearchActions;