import React from 'react';
import { PlusIcon } from '@heroicons/react/24/outline';

const CreateTemplateForm = ({ 
  customTemplate, 
  setCustomTemplate, 
  newTag, 
  setNewTag, 
  onCreateTemplate, 
  onCancel,
  onAddTag,
  onRemoveTag 
}) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center">
            <PlusIcon className="w-5 h-5 mr-2" />
            Create Custom Template
          </h2>
          <button
            onClick={onCancel}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-md transition-colors"
          >
            ×
          </button>
        </div>

        {/* Form */}
        <div className="p-6 space-y-6">
          {/* Template Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Template Name *
            </label>
            <input
              type="text"
              value={customTemplate.name}
              onChange={(e) => setCustomTemplate(prev => ({ ...prev, name: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g., Weekly Review"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <input
              type="text"
              value={customTemplate.description}
              onChange={(e) => setCustomTemplate(prev => ({ ...prev, description: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Brief description of what this template is for"
            />
          </div>

          {/* Category */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Category
            </label>
            <select
              value={customTemplate.category}
              onChange={(e) => setCustomTemplate(prev => ({ ...prev, category: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="Custom">Custom</option>
              <option value="Reflection">Reflection</option>
              <option value="Planning">Planning</option>
              <option value="Creativity">Creativity</option>
              <option value="Wellness">Wellness</option>
              <option value="Work">Work</option>
            </select>
          </div>

          {/* Template Content */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Template Content *
            </label>
            <textarea
              value={customTemplate.content_template}
              onChange={(e) => setCustomTemplate(prev => ({ ...prev, content_template: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows="10"
              placeholder="Enter your template content here. Use {date} to insert current date."
            />
            <p className="mt-1 text-xs text-gray-500">
              Tip: Use {date} to automatically insert the current date
            </p>
          </div>

          {/* Tags */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tags
            </label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), onAddTag())}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Add a tag..."
              />
              <button
                type="button"
                onClick={onAddTag}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Add
              </button>
            </div>
            {customTemplate.tags.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {customTemplate.tags.map((tag, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                  >
                    {tag}
                    <button
                      type="button"
                      onClick={() => onRemoveTag(tag)}
                      className="ml-2 text-blue-600 hover:text-blue-800"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end space-x-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onCreateTemplate}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Create Template
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreateTemplateForm;