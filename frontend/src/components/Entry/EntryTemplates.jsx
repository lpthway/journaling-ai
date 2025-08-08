import React, { useState, useEffect } from 'react';
import { PlusIcon, ClockIcon } from '@heroicons/react/24/outline';
import { entryAPI } from '../../services/api';
import { toast } from 'react-hot-toast';

// Import new sub-components
import CreateTemplateForm from './Templates/CreateTemplateForm';
import TemplateGrid from './Templates/TemplateGrid';
import { defaultTemplates } from './Templates/DefaultTemplates';
import { getCategoryColor } from './Templates/TemplateUtils';

const EntryTemplates = ({ onSelectTemplate, onClose, isVisible }) => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [customTemplate, setCustomTemplate] = useState({
    name: '',
    description: '',
    category: 'Custom',
    content_template: '',
    tags: []
  });
  const [newTag, setNewTag] = useState('');

  useEffect(() => {
    if (isVisible) {
      loadTemplates();
    }
  }, [isVisible]);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      // For now, just use default templates
      setTemplates([...defaultTemplates]);
      setLoading(false);
    } catch (error) {
      console.error('Error loading templates:', error);
      setTemplates([...defaultTemplates]);
      setLoading(false);
    }
  };

  const handleSelectTemplate = (template) => {
    const processedContent = template.content_template || template.content || '';
    const currentDate = new Date().toLocaleDateString();
    const contentWithDate = processedContent.replace(/{date}/g, currentDate);
    
    const templateWithContent = {
      ...template,
      content: contentWithDate
    };
    
    onSelectTemplate(templateWithContent);
    onClose();
  };

  const handleCreateTemplate = () => {
    if (!customTemplate.name.trim() || !customTemplate.content_template.trim()) {
      toast.error('Please fill in the required fields (name and content)');
      return;
    }

    const newTemplate = {
      ...customTemplate,
      id: `custom-${Date.now()}`,
      category: customTemplate.category || 'Custom'
    };

    setTemplates(prev => [...prev, newTemplate]);
    setShowCreateForm(false);
    setCustomTemplate({
      name: '',
      description: '',
      category: 'Custom',
      content_template: '',
      tags: []
    });
    toast.success('Custom template created successfully!');
  };

  const handleAddTag = () => {
    if (newTag.trim() && !customTemplate.tags.includes(newTag.trim())) {
      setCustomTemplate(prev => ({
        ...prev,
        tags: [...prev.tags, newTag.trim()]
      }));
      setNewTag('');
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    setCustomTemplate(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  if (!isVisible) return null;

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full p-8">
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </div>
    );
  }

  // Custom template creation form
  if (showCreateForm) {
    return (
      <CreateTemplateForm
        customTemplate={customTemplate}
        setCustomTemplate={setCustomTemplate}
        newTag={newTag}
        setNewTag={setNewTag}
        onCreateTemplate={handleCreateTemplate}
        onCancel={() => setShowCreateForm(false)}
        onAddTag={handleAddTag}
        onRemoveTag={handleRemoveTag}
      />
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-white sticky top-0 z-10">
          <div className="flex items-center space-x-3">
            <ClockIcon className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">Entry Templates</h2>
            <span className="text-sm text-gray-500">({templates.length} available)</span>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowCreateForm(true)}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Create Custom
            </button>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-md transition-colors"
            >
              ×
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <div className="mb-6">
            <p className="text-gray-600">
              Choose a template to get started with your journal entry. Templates include guided prompts 
              and structured formats to help you reflect effectively.
            </p>
          </div>

          <TemplateGrid
            templates={templates}
            onSelectTemplate={handleSelectTemplate}
            getCategoryColor={getCategoryColor}
          />
        </div>
      </div>
    </div>
  );
};

export default EntryTemplates;