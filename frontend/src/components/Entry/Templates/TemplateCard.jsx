import React from 'react';
import { SparklesIcon } from '@heroicons/react/24/outline';

const TemplateCard = ({ template, onSelect, getCategoryColor }) => {
  return (
    <div 
      key={template.id}
      onClick={() => onSelect(template)}
      className="group bg-white rounded-lg shadow-sm border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all duration-200 cursor-pointer"
    >
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <SparklesIcon className="w-5 h-5 text-blue-500" />
            <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
              {template.name}
            </h3>
          </div>
          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(template.category)}`}>
            {template.category}
          </span>
        </div>

        {/* Description */}
        <p className="text-gray-600 text-sm mb-4">
          {template.description}
        </p>

        {/* Preview */}
        <div className="bg-gray-50 rounded-md p-3 mb-4">
          <div className="text-xs text-gray-500 mb-2">Template preview:</div>
          <div className="text-sm text-gray-700 font-mono whitespace-pre-wrap max-h-24 overflow-hidden">
            {(template.content || template.content_template || '').substring(0, 150)}...
          </div>
        </div>

        {/* Tags */}
        {template.tags && template.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-4">
            {template.tags.slice(0, 3).map((tag, index) => (
              <span
                key={index}
                className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
              >
                {tag}
              </span>
            ))}
            {template.tags.length > 3 && (
              <span className="text-xs text-gray-500">
                +{template.tags.length - 3} more
              </span>
            )}
          </div>
        )}

        {/* Prompts preview */}
        {template.prompts && template.prompts.length > 0 && (
          <div className="border-t border-gray-200 pt-3">
            <div className="text-xs text-gray-500 mb-2">Guided prompts included:</div>
            <div className="text-sm text-gray-600">
              {template.prompts.length} reflection questions
            </div>
          </div>
        )}

        {/* Use button */}
        <div className="mt-4 pt-3 border-t border-gray-200">
          <div className="text-center">
            <span className="text-sm text-blue-600 group-hover:text-blue-700 font-medium">
              Click to use template →
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TemplateCard;