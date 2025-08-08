import React from 'react';
import { HeartIcon } from '@heroicons/react/24/outline';

const FavoritesFilter = ({ is_favorite, onChange }) => {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Favorites
      </label>
      <div className="flex space-x-4">
        <label className="inline-flex items-center">
          <input
            type="radio"
            name="favorite"
            checked={is_favorite === null}
            onChange={() => onChange('is_favorite', null)}
            className="form-radio h-4 w-4 text-blue-600"
          />
          <span className="ml-2 text-sm text-gray-700">All entries</span>
        </label>
        <label className="inline-flex items-center">
          <input
            type="radio"
            name="favorite"
            checked={is_favorite === true}
            onChange={() => onChange('is_favorite', true)}
            className="form-radio h-4 w-4 text-blue-600"
          />
          <HeartIcon className="w-4 h-4 ml-2 mr-1 text-red-500" />
          <span className="text-sm text-gray-700">Favorites only</span>
        </label>
        <label className="inline-flex items-center">
          <input
            type="radio"
            name="favorite"
            checked={is_favorite === false}
            onChange={() => onChange('is_favorite', false)}
            className="form-radio h-4 w-4 text-blue-600"
          />
          <span className="ml-2 text-sm text-gray-700">Non-favorites</span>
        </label>
      </div>
    </div>
  );
};

export default FavoritesFilter;