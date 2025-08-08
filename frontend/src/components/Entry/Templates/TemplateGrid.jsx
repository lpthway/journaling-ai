import React from 'react';
import { DocumentTextIcon } from '@heroicons/react/24/outline';
import TemplateCard from './TemplateCard';

const TemplateGrid = ({ templates, onSelectTemplate, getCategoryColor }) => {
  if (templates.length === 0) {
    return (
      <div className="text-center py-12">
        <DocumentTextIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No templates available</h3>
        <p className="text-gray-600">
          Create your first custom template to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {templates.map((template) => (
        <TemplateCard
          key={template.id}
          template={template}
          onSelect={onSelectTemplate}
          getCategoryColor={getCategoryColor}
        />
      ))}
    </div>
  );
};

export default TemplateGrid;